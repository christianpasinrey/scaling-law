"""Shared helpers for the power & cooling plant assets (plant_01 ... plant_07).

Load after hw.py:
    exec(open(r'C:\\laragon\\www\\scaling-law\\blender\\lib\\hw.py', encoding='utf-8').read())
    exec(open(r'C:\\laragon\\www\\scaling-law\\blender\\scripts\\plant_lib.py', encoding='utf-8').read())
    P = bpy.app.driver_namespace['PLANT']

Conventions (room / yard infrastructure):
  - metres, Z up, origin = floor centre of the footprint, front faces -Y.
  - flow paths (pipes, cables, busbars): mesh with UV u = metres along the path (continuous),
    v = 0..1 around/across; custom props flow_kind, flow_u_start, flow_u_end. u grows in the
    direction of the energy / coolant flow.
  - SOCKET_* empties at path ends (single arrow pointing out of the equipment along the stub).
  - LED_* separate emissive objects; FAN_* separate objects, origin at hub, spin about local +Z.
  - Exterior stub heights (above ground z=0): power conduits z=0.30 m, coolant pipes z=1.00 m.
"""
import bpy, bmesh, math, mathutils, os, sys
from mathutils import Vector, Matrix, Euler

H = bpy.app.driver_namespace['HW']
BASE = r'C:\laragon\www\scaling-law\blender'
RENDERS = os.path.join(BASE, 'renders')
FONT = r'C:\Windows\Fonts\arialbd.ttf'
FONT_REG = r'C:\Windows\Fonts\arial.ttf'
EXT_POWER_Z = 0.30
EXT_COOLANT_Z = 1.00


# ------------------------------------------------------------------ materials
def plant_materials():
    m = H['mat']
    return {
        'conc':     m('PL_Concrete', (0.42, 0.41, 0.39), 0.0, 0.9),
        'galv':     m('PL_Galvanised', (0.55, 0.57, 0.58), 0.9, 0.45),
        'white':    m('PL_PaintWhite', (0.80, 0.80, 0.78), 0.0, 0.45),
        'grey':     m('PL_PaintGrey', (0.45, 0.47, 0.48), 0.0, 0.5),
        'dgrey':    m('PL_PaintDarkGrey', (0.06, 0.065, 0.07), 0.1, 0.5),
        'black':    m('PL_PaintBlack', (0.012, 0.012, 0.013), 0.1, 0.55),
        'vent':     m('PL_VentHole', (0.002, 0.002, 0.002), 0.0, 1.0, spec=0.05),
        'rubber':   m('PL_Rubber', (0.01, 0.01, 0.01), 0.0, 0.8),
        'steel':    m('PL_Stainless', (0.62, 0.63, 0.64), 1.0, 0.3),
        'copper':   m('PL_Copper', (0.85, 0.45, 0.28), 1.0, 0.3),
        'fin':      m('PL_CoilFin', (0.38, 0.40, 0.41), 0.8, 0.45),
        'coil':     m('PL_CoilDark', (0.05, 0.055, 0.06), 0.6, 0.5),
        'pipe_blue': m('PL_PipeBlue', (0.04, 0.18, 0.55), 0.2, 0.4),
        'pipe_red':  m('PL_PipeRed', (0.60, 0.05, 0.04), 0.2, 0.4),
        'pipe_ins':  m('PL_PipeInsulation', (0.70, 0.71, 0.70), 0.6, 0.45),
        'cable':     m('PL_CableBlack', (0.015, 0.015, 0.016), 0.0, 0.6),
        'bus':       m('PL_BuswayGrey', (0.62, 0.63, 0.63), 0.3, 0.45),
        'label_w':   m('PL_LabelWhite', (0.85, 0.85, 0.85), 0.0, 0.5),
        'label_y':   m('PL_LabelYellow', (0.95, 0.70, 0.02), 0.0, 0.5),
        'label_r':   m('PL_LabelRed', (0.70, 0.03, 0.03), 0.0, 0.5),
        'label_k':   m('PL_LabelBlack', (0.01, 0.01, 0.01), 0.0, 0.5),
        'glass':     m('PL_Glass', (0.05, 0.06, 0.07), 0.0, 0.05, alpha=0.35),
        'led_g':     m('PL_LED_Green', (0.05, 1.0, 0.2), 0.0, 0.3, emit=(0.1, 1.0, 0.25), emit_str=6.0),
        'led_r':     m('PL_LED_Red', (1.0, 0.05, 0.03), 0.0, 0.3, emit=(1.0, 0.06, 0.03), emit_str=6.0),
        'led_a':     m('PL_LED_Amber', (1.0, 0.55, 0.05), 0.0, 0.3, emit=(1.0, 0.5, 0.05), emit_str=6.0),
        'screen':    m('PL_Screen', (0.05, 0.25, 0.45), 0.0, 0.2, emit=(0.15, 0.45, 0.85), emit_str=2.5),
    }


# ------------------------------------------------------------------ generic mesh builders
def boxes(name, items, material, col, parent=None):
    """items yields (centre, size, rot_euler) or (centre, size); merged into one mesh."""
    bm = bmesh.new()
    for it in items:
        c, s = it[0], it[1]
        r = it[2] if len(it) > 2 else (0, 0, 0)
        M = Matrix.Translation(c) @ Euler(r).to_matrix().to_4x4() @ Matrix.Diagonal((*s, 1))
        bmesh.ops.create_cube(bm, size=1, matrix=M)
    return _pl_obj(name, bm, material, col, parent)


def _pl_obj(name, bm, material, col, parent):
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    if material:
        me.materials.append(material)
    col.objects.link(o)
    if parent:
        o.parent = parent
    return o


def cylinders(name, items, material, col, parent=None, verts=24):
    """items yields (centre, radius, depth, rot_euler). Merged mesh of capped cylinders."""
    bm = bmesh.new()
    for c, r, d, rot in items:
        M = Matrix.Translation(c) @ Euler(rot).to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts, radius1=r, radius2=r, depth=d, matrix=M)
    return _pl_obj(name, bm, material, col, parent)


def tori(name, items, material, col, parent=None, major_segs=40, minor_segs=4):
    """items yields (centre, R, r, rot_euler). Torus rings (fan guards, flanges)."""
    bm = bmesh.new()
    for c, R, r, rot in items:
        M = Matrix.Translation(c) @ Euler(rot).to_matrix().to_4x4()
        rings = []
        for i in range(major_segs):
            a = 2 * math.pi * i / major_segs
            ca, sa = math.cos(a), math.sin(a)
            ring = []
            for j in range(minor_segs):
                b = 2 * math.pi * j / minor_segs
                rr = R + r * math.cos(b)
                ring.append(bm.verts.new(M @ Vector((rr * ca, rr * sa, r * math.sin(b)))))
            rings.append(ring)
        for i in range(major_segs):
            a, b = rings[i], rings[(i + 1) % major_segs]
            for j in range(minor_segs):
                k = (j + 1) % minor_segs
                bm.faces.new((a[j], b[j], b[k], a[k]))
    return _pl_obj(name, bm, material, col, parent)


def quads(name, items, material, col, parent=None, face='-Y'):
    """Flat rectangles (2 tris each) for perforations / decals.
    items yield (centre(x,y,z), (w,h), angle_rad). face '-Y'/'+Y': rect in XZ; '-X'/'+X': in YZ; '+Z': in XY."""
    bm = bmesh.new()
    for c, (w, h), ang in items:
        ca, sa = math.cos(ang), math.sin(ang)
        pts = []
        for a, b in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
            u, v = a * ca - b * sa, a * sa + b * ca
            pts.append({'-Y': (c[0] + u, c[1], c[2] + v), '+Y': (c[0] - u, c[1], c[2] + v),
                        '-X': (c[0], c[1] - u, c[2] + v), '+X': (c[0], c[1] + u, c[2] + v),
                        '+Z': (c[0] + u, c[1] + v, c[2])}[face])
        f = bm.faces.new([bm.verts.new(q) for q in pts])
        n = {'-Y': (0, -1, 0), '+Y': (0, 1, 0), '-X': (-1, 0, 0), '+X': (1, 0, 0), '+Z': (0, 0, 1)}[face]
        if f.normal.dot(Vector(n)) < 0:
            f.normal_flip()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(material); col.objects.link(o)
    if parent:
        o.parent = parent
    return o


# ------------------------------------------------------------------ flow paths
def _fillet(points, rb, seg):
    pts = [Vector(p) for p in points]
    if rb <= 0 or len(pts) < 3:
        return pts
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        d1 = (p1 - p0); d2 = (p2 - p1)
        l1, l2 = d1.length, d2.length
        d1.normalize(); d2.normalize()
        ang = d1.angle(d2, 0.0)
        if ang < 1e-3:
            out.append(p1); continue
        t = min(rb * math.tan(ang / 2), 0.49 * l1, 0.49 * l2)
        a = p1 - d1 * t; b = p1 + d2 * t
        for k in range(seg + 1):
            s = k / seg
            out.append(a * (1 - s) ** 2 + p1 * 2 * (1 - s) * s + b * s * s)
    out.append(pts[-1])
    # drop duplicates
    clean = [out[0]]
    for p in out[1:]:
        if (p - clean[-1]).length > 1e-6:
            clean.append(p)
    return clean


def _profile_circle(r, n):
    return [((r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)), k / n) for k in range(n + 1)]


def _profile_rect(w, h):
    corners = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2), (-w / 2, -h / 2)]
    per = 2 * (w + h); acc = 0.0; out = []
    for i, c in enumerate(corners):
        if i:
            acc += (Vector(c) - Vector(corners[i - 1])).length
        out.append((c, acc / per))
    return out


def flow_path(name, points, material, col, parent=None, radius=None, rect=None, bend=None, seg=8,
              verts=16, kind='coolant', cap=True, up=None):
    """Tube (radius) or rectangular bar (rect=(w,h); w along the frame 'side' axis, h along 'up').
    UV u = metres along the path from points[0]; v = 0..1 around the profile."""
    rb = bend if bend is not None else (2.0 * radius if radius else 0.5 * max(rect))
    pts = _fillet(points, rb, seg)
    prof = _profile_circle(radius, verts) if radius else _profile_rect(*rect)
    n = len(pts)
    tans = []
    for i in range(n):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[i] - pts[i - 1]).normalized() + (pts[i + 1] - pts[i]).normalized()
        tans.append(t.normalized())
    ref = Vector(up) if up else Vector((0, 0, 1))
    if abs(ref.dot(tans[0])) > 0.95:
        ref = Vector((1, 0, 0)) if abs(tans[0].x) < 0.9 else Vector((0, 1, 0))
    nrm = (ref - tans[0] * ref.dot(tans[0])).normalized()
    frames = []
    for i in range(n):
        if i:
            q = tans[i - 1].rotation_difference(tans[i])
            nrm = q @ nrm
            nrm = (nrm - tans[i] * nrm.dot(tans[i])).normalized()
        side = tans[i].cross(nrm).normalized()
        frames.append((nrm, side))
    us = [0.0]
    for i in range(1, n):
        us.append(us[-1] + (pts[i] - pts[i - 1]).length)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    m = len(prof) - 1          # last profile point duplicates the first (v=1): share the vertex, split only UVs
    for i in range(n):
        nr, sd = frames[i]
        rings.append([bm.verts.new(pts[i] + sd * px + nr * py) for (px, py), v in prof[:m]])
    for i in range(n - 1):
        a, b = rings[i], rings[i + 1]
        for k in range(m):
            k1 = (k + 1) % m
            f = bm.faces.new((a[k], a[k1], b[k1], b[k]))
            f.smooth = bool(radius)
            uv = [(us[i], prof[k][1]), (us[i], prof[k + 1][1]), (us[i + 1], prof[k + 1][1]), (us[i + 1], prof[k][1])]
            for loop, c in zip(f.loops, uv):
                loop[uvl].uv = c
    if cap:
        for ring, u in ((rings[0], us[0]), (rings[-1], us[-1])):
            f = bm.faces.new(ring)
            f.smooth = False
            for loop in f.loops:
                loop[uvl].uv = (u, 0.5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = _pl_obj(name, bm, material, col, parent)
    o['flow_kind'] = kind
    o['flow_u_start'] = 0.0
    o['flow_u_end'] = round(us[-1], 5)
    return o


# ------------------------------------------------------------------ gameplay markers
def socket(name, loc, direction, root, col, size=0.25):
    """Empty whose local +Z (single arrow) points along `direction` (out of the equipment)."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'SINGLE_ARROW'; e.empty_display_size = size
    e.location = loc
    e.rotation_euler = Vector(direction).normalized().to_track_quat('Z', 'Y').to_euler()
    col.objects.link(e); e.parent = root
    return e


def marker(name, loc, root, col, size=0.2, rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'ARROWS'; e.empty_display_size = size
    e.location = loc; e.rotation_euler = rot
    col.objects.link(e); e.parent = root
    return e


def led(name, loc, size, material, col, root):
    o = H['box'](name, size, loc, material, col, parent=root)
    return o


def text(name, body, size, material, col, root, loc, face='-Y', font=FONT, extrude=0.0, res=2):
    """Low-poly flat text (curve resolution `res`), readable from the given face direction."""
    rot = {'-Y': (math.pi / 2, 0, 0), '+Y': (math.pi / 2, 0, math.pi),
           '+X': (math.pi / 2, 0, math.pi / 2), '-X': (math.pi / 2, 0, -math.pi / 2),
           '+Z': (0, 0, 0)}[face]
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.size = size; cu.extrude = extrude; cu.resolution_u = res
    t = bpy.data.objects.new(name, cu); col.objects.link(t)
    cu.materials.append(material)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(t.evaluated_get(dg))
    bpy.data.objects.remove(t); bpy.data.curves.remove(cu)
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    if not me.materials:
        me.materials.append(material)
    o.parent = root; o.location = loc; o.rotation_euler = rot
    return o


def fan(name, centre, dia, col, root, mats, blades=6, hub_r=None, pitch=0.35):
    """Axial fan rotor as its own object; origin at hub centre, spins about local Z."""
    R = dia / 2 * 0.96
    hub_r = hub_r or dia * 0.12
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=hub_r, radius2=hub_r * 0.8, depth=hub_r * 0.9,
                          matrix=Matrix.Translation((0, 0, hub_r * 0.2)))
    for b in range(blades):
        a0 = 2 * math.pi * b / blades
        # blade: twisted quad strip from hub to tip, swept chord
        nseg = 4; rows = []
        for i in range(nseg + 1):
            r = hub_r * 0.9 + (R - hub_r * 0.9) * i / nseg
            chord = (0.55 - 0.15 * i / nseg) * (2 * math.pi * r / blades)
            sweep = 0.25 * i / nseg
            tw = pitch * (1.2 - 0.5 * i / nseg)
            ring = []
            for s in (-0.5, 0.5):
                ang = a0 + sweep + s * chord / r
                z = s * chord * math.sin(tw)
                ring.append(bm.verts.new((r * math.cos(ang), r * math.sin(ang), z)))
            rows.append(ring)
        for i in range(nseg):
            bm.faces.new((rows[i][0], rows[i][1], rows[i + 1][1], rows[i + 1][0]))
    o = _pl_obj(name, bm, mats['black'], col, root)
    sm = o.modifiers.new('Solid', 'SOLIDIFY'); sm.thickness = 0.006
    o.location = centre
    o['spin_axis'] = 'Z'
    return o


# ------------------------------------------------------------------ scene, export, render
def setup(root_name):
    root, col = H['new_card_scene'](root_name)
    return root, col, H['base_materials'](), plant_materials()


def finish(root, blend, glb):
    for o in list(root.children_recursive):
        if o.type == 'MESH' and o.modifiers:
            H['apply_all'](o)
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    objs = [root] + list(root.children_recursive)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    dg = bpy.context.evaluated_depsgraph_get(); tris = 0
    for o in objs:
        if o.type == 'MESH':
            e = o.evaluated_get(dg); m = e.to_mesh(); m.calc_loop_triangles(); tris += len(m.loop_triangles); e.to_mesh_clear()
    # same as H['export_glb'] plus export_extras so flow_u_* / spin_axis custom props reach the game
    bpy.ops.export_scene.gltf(filepath=glb, use_selection=True, export_apply=True, export_extras=True)
    names = sorted(o.name for o in objs if o.name.startswith(('SOCKET_', 'LED_', 'FAN_', 'FX_', 'SLOT_')))
    print(f'PLANT {root.name} TRIS {tris} GLB {os.path.getsize(glb)} bytes')
    print('PLANT MARKERS', ', '.join(names))
    flows = [(o.name, o['flow_kind'], o['flow_u_end']) for o in objs if 'flow_u_end' in o.keys()]
    print('PLANT FLOWS', flows)
    return tris


def render(prefix, views, centre, size):
    """views: {name: (direction_from_centre, distance_factor, lens)}; size = largest dimension (m)."""
    if '--norender' in sys.argv:
        return
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.render.resolution_percentage = 100
    try:
        sc.eevee.taa_render_samples = 32
    except Exception:
        pass
    f = size / 0.3
    c0 = Vector((0.13, -0.10, 0.05)); C = Vector(centre)
    for name in ('Key', 'Fill', 'Rim'):
        L = bpy.data.objects.get(name)
        if L and not L.get('_scaled'):
            L.location = C + (L.location - c0) * f
            L.data.size = L.data.size * f
            if hasattr(L.data, 'size_y'):
                L.data.size_y = L.data.size_y * f
            L.data.energy = L.data.energy * f * f * 0.35
            L['_scaled'] = 1
    fl = bpy.data.objects.get('Floor')
    if fl:
        fl.location = (C.x, C.y, -0.002)
        fl.scale = (fl.scale.x * f * 4, fl.scale.y * f * 4, 1)
    if not bpy.data.objects.get('PL_Sun'):
        sd = bpy.data.lights.new('PL_Sun', 'SUN'); sd.energy = 1.5; sd.angle = 0.1
        s = bpy.data.objects.new('PL_Sun', sd); bpy.context.scene.collection.objects.link(s)
        s.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
    cam = bpy.data.objects['Camera']
    cam.data.clip_end = 1000; cam.data.clip_start = 0.05
    only = [a.split('=', 1)[1] for a in sys.argv if a.startswith('--views=')]
    only = only[0].split(',') if only else list(views)
    for name in only:
        d, k, lens = views[name][:3]
        tgt = Vector(views[name][3]) if len(views[name]) > 3 else C
        d = Vector(d).normalized()
        cam.location = tgt + d * size * k
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = lens
        sc.camera = cam
        sc.render.filepath = os.path.join(RENDERS, f'{prefix}_{name}.png')
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sc.render.filepath)


PLANT = dict(materials=plant_materials, boxes=boxes, quads=quads, cylinders=cylinders, tori=tori, flow_path=flow_path,
             socket=socket, marker=marker, led=led, text=text, fan=fan, setup=setup, finish=finish, render=render,
             new_obj=_pl_obj, EXT_POWER_Z=EXT_POWER_Z, EXT_COOLANT_Z=EXT_COOLANT_Z, FONT=FONT, BASE=BASE)
bpy.app.driver_namespace['PLANT'] = PLANT
