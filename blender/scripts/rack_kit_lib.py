"""Helpers for the standard rack kit (rack cabinet, 0U PDU, 1U switches, accessories, cables).

Load after hw.py:
    exec(open(r'C:\\laragon\\www\\scaling-law\\blender\\lib\\hw.py', encoding='utf-8').read())
    exec(open(r'C:\\laragon\\www\\scaling-law\\blender\\scripts\\rack_kit_lib.py', encoding='utf-8').read())
Published as bpy.app.driver_namespace['RK'].

Conventions (see lib/BRIEF_SERVERS_RACKS.md): metres, Z up, rack gear front at y=0 facing -Y.
"""
import bpy, bmesh, math, mathutils, os, sys

H = bpy.app.driver_namespace['HW']
V = mathutils.Vector
BASE = r'C:\laragon\www\scaling-law\blender'
RENDERS = os.path.join(BASE, 'renders')
EXPORT = os.path.join(BASE, 'export')
TEX = os.path.join(BASE, 'textures')
FONT = r'C:\Windows\Fonts\arialbd.ttf'
FONT_REG = r'C:\Windows\Fonts\arial.ttf'
U = 0.04445


# ---------------------------------------------------------------- generic
def empty(name, loc, parent, col, rot=(0, 0, 0), kind='ARROWS', size=0.02, props=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind; e.empty_display_size = size
    e.location = loc; e.rotation_euler = rot
    col.objects.link(e)
    if parent:
        e.parent = parent
    for k, v in (props or {}).items():
        e[k] = v
    return e


def mesh_obj(name, bm, mats, col, parent=None):
    """bm -> object; mats list is assigned in order (faces keep their material_index)."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    for m in mats:
        me.materials.append(m)
    col.objects.link(o)
    if parent:
        o.parent = parent
    return o


def add_box(bm, c, s, mi=0):
    """Axis-aligned box into bm, returns faces."""
    r = bmesh.ops.create_cube(bm, size=1, matrix=mathutils.Matrix.Translation(c) @ mathutils.Matrix.Diagonal((*s, 1)))
    fs = list({f for v in r['verts'] for f in v.link_faces})
    for f in fs:
        f.material_index = mi
    return fs


def boxes(name, specs, material, col, parent=None):
    """specs: list of (centre, size) in metres -> one merged mesh."""
    lst = list(specs)
    return H['slat_array'](name, lambda: iter(lst), material, col, parent)


def add_cyl(bm, c, r, depth, axis='Y', segs=16, mi=0):
    rot = {'X': mathutils.Matrix.Rotation(math.pi / 2, 4, 'Y'), 'Y': mathutils.Matrix.Rotation(math.pi / 2, 4, 'X'),
           'Z': mathutils.Matrix.Identity(4)}[axis]
    res = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r, depth=depth,
                                matrix=mathutils.Matrix.Translation(c) @ rot)
    fs = list({f for v in res['verts'] for f in v.link_faces})
    for f in fs:
        f.material_index = mi
    return fs


def add_quad_xz(bm, x0, x1, z0, z1, y, mi=0, uv_tile=None, facing=-1):
    """Single quad in the XZ plane at y, normal toward facing*Y. uv_tile=(tu, tv) -> u=x/tu, v=z/tv."""
    vs = [bm.verts.new((x0, y, z0)), bm.verts.new((x1, y, z0)), bm.verts.new((x1, y, z1)), bm.verts.new((x0, y, z1))]
    if facing > 0:
        vs = list(reversed(vs))
    f = bm.faces.new(vs); f.material_index = mi
    if uv_tile:
        uvl = bm.loops.layers.uv.verify()
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x / uv_tile[0], lp.vert.co.z / uv_tile[1])
    return f


def join(objs, name):
    objs = [o for o in objs if o]
    for o in objs:
        if o.modifiers:
            H['apply_all'](o)
    with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs, selected_objects=objs, object=objs[0]):
        bpy.ops.object.join()
    objs[0].name = name; objs[0].data.name = name
    return objs[0]


def set_origin(obj, point):
    """Move object origin to world `point` without moving geometry (obj must be unparented or parent at identity)."""
    p = V(point)
    d = p - obj.matrix_world.translation
    obj.data.transform(mathutils.Matrix.Translation(-d))
    obj.location = obj.location + d


def text_flat(name, body, size, loc, rot, material, col, parent, font=FONT, align='CENTER', res=2):
    """Flat (no extrude) text converted to mesh with a low curve resolution (game budget)."""
    bpy.ops.object.text_add(location=(0, 0, 0))
    t = bpy.context.active_object
    t.name = name
    t.data.body = body; t.data.align_x = align; t.data.align_y = 'CENTER'
    t.data.font = bpy.data.fonts.load(font, check_existing=True)
    t.data.size = size; t.data.extrude = 0.0; t.data.resolution_u = res
    for c in list(t.users_collection):
        c.objects.unlink(t)
    col.objects.link(t)
    t.data.materials.append(material)
    with bpy.context.temp_override(active_object=t, object=t, selected_objects=[t], selected_editable_objects=[t]):
        bpy.ops.object.convert(target='MESH')
    t.parent = parent; t.matrix_parent_inverse.identity()
    t.location = loc; t.rotation_euler = rot
    return t


def tris_of(objs):
    dg = bpy.context.evaluated_depsgraph_get(); n = 0
    for o in objs:
        if o.type == 'MESH':
            e = o.evaluated_get(dg); m = e.to_mesh(); m.calc_loop_triangles(); n += len(m.loop_triangles); e.to_mesh_clear()
    return n


# ---------------------------------------------------------------- perforation texture
def perf_image(name='RK_PerfHex', res=256, open_frac=0.63):
    """Tileable hex hole pattern. One tile = 1 x sqrt(3) hole pitches (2 holes); the UV mapping must use
    tile size (p, p*sqrt3). RGB: 1 plate / 0 hole, A: 1 plate / 0 hole."""
    img = bpy.data.images.get(name)
    if img:
        return img
    os.makedirs(TEX, exist_ok=True)
    path = os.path.join(TEX, 'perf_hex.png')
    # hole radius in pitch units for wanted open fraction: open = 2*pi*r^2 / sqrt3
    r = math.sqrt(open_frac * math.sqrt(3) / (2 * math.pi))
    import numpy as np
    ys, xs = np.mgrid[0:res, 0:res]
    u = (xs + 0.5) / res            # 0..1 across 1 pitch
    v = (ys + 0.5) / res * math.sqrt(3)   # 0..sqrt3 in pitch units
    d = np.full(u.shape, 9.0)
    for cx, cy in ((0, 0), (1, 0), (0, math.sqrt(3)), (1, math.sqrt(3)), (0.5, math.sqrt(3) / 2)):
        d = np.minimum(d, np.sqrt((u - cx) ** 2 + (v - cy) ** 2))
    aa = 1.5 / res
    plate = np.clip((d - r) / aa + 0.5, 0, 1)
    px = np.zeros((res, res, 4), dtype=np.float32)
    px[..., 0] = px[..., 1] = px[..., 2] = plate; px[..., 3] = plate
    img = bpy.data.images.new(name, res, res, alpha=True)
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = path; img.file_format = 'PNG'; img.save()
    img.pack()
    return img


def perf_material(name, base, metal=0.6, rough=0.45, see_through=True):
    """Perforated sheet. see_through: alpha-clipped holes (glTF MASK); else holes are just dark."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = perf_image(); tex.interpolation = 'Linear'
    tex.location = (-600, 0)
    if see_through:
        b.inputs['Base Color'].default_value = (*base, 1)
        # plain alpha -> glTF alphaMode BLEND. (An alpha-clip via a Round node would make the sheet vanish once the
        # texture is minified: mip-averaged alpha = 1 - open fraction < 0.5.)
        nt.links.new(tex.outputs['Alpha'], b.inputs['Alpha'])
        try:
            m.surface_render_method = 'DITHERED'
        except Exception:
            pass
        m.use_backface_culling = False
    else:
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.location = (-300, 100)
        mix.inputs['A'].default_value = (0.002, 0.002, 0.002, 1)
        mix.inputs['B'].default_value = (*base, 1)
        nt.links.new(tex.outputs['Color'], mix.inputs['Factor'])
        nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    m.diffuse_color = (*base, 1)
    return m


# ---------------------------------------------------------------- flow-UV tubes (cables / cords)
def fillet_path(corners, radius, arc_steps=8):
    """Polyline corners -> points with circular-arc fillets of `radius` at each interior corner."""
    P = [V(c) for c in corners]
    out = [P[0].copy()]
    for i in range(1, len(P) - 1):
        a = (P[i] - P[i - 1]); b = (P[i + 1] - P[i])
        la, lb = a.length, b.length
        a.normalize(); b.normalize()
        cosd = max(-1.0, min(1.0, a.dot(b)))
        defl = math.acos(cosd)
        if defl < 1e-4:
            out.append(P[i].copy()); continue
        t = radius * math.tan(defl / 2)
        t = min(t, la * 0.49, lb * 0.49)
        r = t / math.tan(defl / 2)
        q1 = P[i] - a * t; q2 = P[i] + b * t
        bis = (b - a).normalized()
        c = P[i] + bis * (r / math.cos(defl / 2))
        v1 = q1 - c; v2 = q2 - c
        n = max(2, int(arc_steps * defl / (math.pi / 2)) + 1)
        for k in range(n + 1):
            f = k / n
            # slerp v1 -> v2
            ang = v1.angle(v2) if v1.length and v2.length else 0
            if ang < 1e-6:
                out.append(c + v1); continue
            s0 = math.sin((1 - f) * ang) / math.sin(ang); s1 = math.sin(f * ang) / math.sin(ang)
            out.append(c + v1 * s0 + v2 * s1)
    out.append(P[-1].copy())
    # drop duplicates
    res = [out[0]]
    for p in out[1:]:
        if (p - res[-1]).length > 1e-6:
            res.append(p)
    return res


def bezier_pts(p0, h0, h1, p1, n=24):
    p0, h0, h1, p1 = V(p0), V(h0), V(h1), V(p1)
    pts = []
    for k in range(n + 1):
        t = k / n
        pts.append(p0 * (1 - t) ** 3 + h0 * 3 * (1 - t) ** 2 * t + h1 * 3 * (1 - t) * t * t + p1 * t ** 3)
    return pts


def tube(name, pts, radius, material, col, parent=None, segs=8, caps=True, up=(0, 0, 1), props=None, flat=1.0):
    """Sweep a circle (or ellipse: flat<1 squashes the 'side' axis) along pts.
    UV: u = metres along the path (continuous), v = 0..1 around. Custom props flow_u_start / flow_u_end."""
    pts = [V(p) for p in pts]
    n = len(pts)
    tang = []
    for i in range(n):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[i + 1] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()
        tang.append(t.normalized())
    # parallel transport frame
    upv = V(up)
    if abs(upv.dot(tang[0])) > 0.95:
        upv = V((1, 0, 0)) if abs(tang[0].x) < 0.9 else V((0, 1, 0))
    nrm = (upv - tang[0] * upv.dot(tang[0])).normalized()
    frames = []
    for i in range(n):
        if i > 0:
            q = tang[i - 1].rotation_difference(tang[i])
            nrm = (q @ nrm)
            nrm = (nrm - tang[i] * nrm.dot(tang[i])).normalized()
        frames.append((nrm.copy(), tang[i].cross(nrm).normalized()))
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rings = []; ulen = [0.0]
    for i in range(1, n):
        ulen.append(ulen[-1] + (pts[i] - pts[i - 1]).length)
    for i in range(n):
        nn, bb = frames[i]
        ring = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            ring.append(bm.verts.new(pts[i] + nn * (math.cos(a) * radius) + bb * (math.sin(a) * radius * flat)))
        rings.append(ring)
    for i in range(n - 1):
        for k in range(segs):
            j = (k + 1) % segs
            f = bm.faces.new((rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]))
            uvs = ((ulen[i], k / segs), (ulen[i], (k + 1) / segs), (ulen[i + 1], (k + 1) / segs), (ulen[i + 1], k / segs))
            for lp, uv in zip(f.loops, uvs):
                lp[uvl].uv = uv
    if caps:
        for idx, rev in ((0, True), (n - 1, False)):
            r = rings[idx]
            f = bm.faces.new(list(reversed(r)) if rev else r)
            for lp in f.loops:
                lp[uvl].uv = (ulen[idx], 0.5)
    o = mesh_obj(name, bm, [material], col, parent)
    for p in o.data.polygons:
        p.use_smooth = True
    o['flow_u_start'] = 0.0
    o['flow_u_end'] = round(ulen[-1], 5)
    o['flow_radius'] = radius
    for k, v in (props or {}).items():
        o[k] = v
    return o, ulen[-1]


# ---------------------------------------------------------------- studio / renders
def studio_for(size, centre, floor_z=0.0):
    """Scale the template studio (sized for a ~0.3 m card) to an object of `size` metres."""
    k = size / 0.3
    for nm in ('Key', 'Fill', 'Rim'):
        L = bpy.data.objects.get(nm)
        if not L:
            continue
        if '_rk_orig' not in L:
            L['_rk_orig'] = list(L.location); L['_rk_e'] = L.data.energy; L['_rk_s'] = L.data.size
        o = V(L['_rk_orig']) - V((0.13, -0.1, 0.0))
        L.location = V(centre) + o * k
        L.data.energy = max(L['_rk_e'], 8.0) * k * k
        L.data.size = L['_rk_s'] * k
        d = V(centre) - L.location
        L.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    fl = bpy.data.objects.get('Floor')
    if fl:
        if '_rk_scale' not in fl:
            fl['_rk_scale'] = list(fl.scale)
        s0 = V(fl['_rk_scale'])
        f = max(1.0, k * 1.5)
        fl.scale = (s0.x * f, s0.y * f, s0.z)
        fl.location = (centre[0], centre[1], 0)
        bpy.context.view_layer.update()
        top = max((fl.matrix_world @ V(c)).z for c in fl.bound_box)
        fl.location.z = floor_z - top - 0.0003


def render(prefix, views, size, centre, floor_z=0.0, hide_floor=False):
    """views: {name: (eye, target, lens)}. --views=a,b limits; --norender skips."""
    if '--norender' in sys.argv:
        return
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.render.resolution_percentage = 100
    try:
        sc.eevee.taa_render_samples = 48
    except Exception:
        pass
    studio_for(size, centre, floor_z)
    fl = bpy.data.objects.get('Floor')
    if fl:
        fl.hide_render = hide_floor
    cam = bpy.data.objects['Camera']
    cam.data.clip_start = 0.005; cam.data.clip_end = 100
    sc.camera = cam
    only = [a.split('=', 1)[1] for a in sys.argv if a.startswith('--views=')]
    only = only[0].split(',') if only else list(views)
    for nm in only:
        if nm not in views:
            continue
        eye, tgt, lens = views[nm]
        cam.location = eye
        cam.rotation_euler = (V(tgt) - V(eye)).to_track_quat('-Z', 'Y').to_euler()
        cam.data.type = 'PERSP'; cam.data.lens = lens
        sc.render.filepath = os.path.join(RENDERS, f'{prefix}_{nm}.png')
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sc.render.filepath)


def finish(root_name, blend_path, glb_name, hide_for_export=()):
    """Apply modifiers, save .blend, export .glb (objects in hide_for_export are removed from the selection)."""
    root = bpy.data.objects[root_name]
    for o in root.children_recursive:
        if o.type == 'MESH' and o.modifiers:
            H['apply_all'](o)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    glb = os.path.join(EXPORT, glb_name)
    bpy.ops.object.select_all(action='DESELECT')
    objs = [root] + [o for o in root.children_recursive if o.name not in hide_for_export]
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    tris = tris_of(objs)
    bpy.ops.export_scene.gltf(filepath=glb, use_selection=True, export_apply=True, export_extras=True)
    print(f'{root_name} TRIS {tris} GLB {os.path.getsize(glb)} bytes')
    return tris


RK = dict(empty=empty, mesh_obj=mesh_obj, add_box=add_box, boxes=boxes, add_cyl=add_cyl, add_quad_xz=add_quad_xz, join=join,
          set_origin=set_origin, text_flat=text_flat, tris_of=tris_of, perf_image=perf_image, perf_material=perf_material,
          fillet_path=fillet_path, bezier_pts=bezier_pts, tube=tube, studio_for=studio_for, render=render, finish=finish,
          U=U, FONT=FONT, FONT_REG=FONT_REG, BASE=BASE, EXPORT=EXPORT, RENDERS=RENDERS)
bpy.app.driver_namespace['RK'] = RK
