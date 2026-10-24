"""Shared helpers for the data-hall infrastructure assets (hall_*.py).

Load inside Blender after hw.py:
    exec(open(r'C:\\laragon\\www\\scaling-law\\blender\\lib\\hw.py', encoding='utf-8').read())
    exec(open(r'C:\\laragon\\www\\scaling-law\\blender\\scripts\\hall_lib.py', encoding='utf-8').read())

Conventions (see lib/BRIEF_SERVERS_RACKS.md):
  - metres, Z up, origin of every piece = floor (z=0) under the centre of its footprint / joint plane,
    overhead pieces hang at the default elevations below (the game may offset Z).
  - each script builds several tileable *pieces*; each piece is a root empty with its children.
  - every piece is exported twice: alone (clean child names: SOCKET_power_in, LED_status, ...)
    and inside the combined file (child names suffixed '__<TAG>' because Blender names are unique).
    Every special empty/object also carries custom props (extras) {'role','piece'} so the game
    can find it without parsing names.
  - flow meshes (busbars, cords, hoses, pipes, bundles): UV u = metres along the path (continuous),
    v = 0..1 around the profile; custom props flow_u_start / flow_u_end / flow_kind.
  - JOINT_a / JOINT_b empties mark the tiling ports of linear pieces (arrow = outward direction).
"""
import bpy, bmesh, math, mathutils, os, sys
from mathutils import Vector, Matrix

H = bpy.app.driver_namespace['HW']
BASE = r'C:\laragon\www\scaling-law\blender'
EXPORT = os.path.join(BASE, 'export')
RENDERS = os.path.join(BASE, 'renders')
FONT = r'C:\Windows\Fonts\arialbd.ttf'
FONT_R = r'C:\Windows\Fonts\arial.ttf'
DO_RENDER = '--norender' not in sys.argv

# ------------------------------------------------------------------ hall standard elevations
RACK_W = 0.600            # rack pitch along a row (APC NetShelter SX 600 mm)
RACK_H = 2.258            # 48U NetShelter SX (AR3307) height, top of rack
CELL = 0.600              # overhead routing grid cell
BUSWAY_Z = 3.100          # busway centreline
BASKET_Z = 3.450          # wire-basket bottom
FIBER_Z = 3.800           # fibre raceway bottom
CEIL_Z = 4.600            # structural ceiling / hanger anchor (renders only, hangers are 1 m rods)

# ------------------------------------------------------------------ scene

def reset_scene():
    studio = H['coll']('Studio')
    for o in list(bpy.data.objects):
        if o.type in ('CAMERA', 'LIGHT'):
            if studio not in o.users_collection:
                studio.objects.link(o)
            continue
        if not any(c.name == 'Studio' for c in o.users_collection):
            bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        if c.name != 'Studio' and not c.objects:
            bpy.data.collections.remove(c)
    for m in list(bpy.data.meshes):
        if m.users == 0:
            bpy.data.meshes.remove(m)


PIECES = []   # (root, tag)


def piece(name, tag, col_name):
    col = H['coll'](col_name)
    root = bpy.data.objects.new(name, None)
    root.empty_display_type = 'PLAIN_AXES'; root.empty_display_size = 0.1
    col.objects.link(root)
    root['piece'] = name
    PIECES.append((root, tag))
    return root, col


def tag_obj(o, role, root):
    o['role'] = role
    o['piece'] = root.name
    return o


def empty(name, loc, direction, root, col, role, size=0.06, kind='SINGLE_ARROW'):
    """Empty whose local +Z arrow points along `direction`."""
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind; e.empty_display_size = size
    e.location = loc
    d = Vector(direction).normalized()
    e.rotation_euler = Vector((0, 0, 1)).rotation_difference(d).to_euler()
    col.objects.link(e); e.parent = root
    return tag_obj(e, role, root)


def socket(name, loc, direction, root, col, **props):
    e = empty(name, loc, direction, root, col, 'socket', 0.08)
    for k, v in props.items():
        e[k] = v
    return e


def joint(name, loc, direction, root, col):
    return empty(name, loc, direction, root, col, 'joint', 0.12, 'ARROWS')


# ------------------------------------------------------------------ materials

def mats():
    m = H['mat']
    M = H['base_materials']()
    M.update({
        'alu_satin':  m('HALL_AluSatin', (0.62, 0.63, 0.65), 1.0, 0.38),
        'alu_dark':   m('HALL_AluDark', (0.10, 0.10, 0.11), 0.8, 0.40),
        'copper':     m('HALL_Copper', (0.93, 0.47, 0.27), 1.0, 0.28),
        'insul':      m('HALL_Insulator', (0.02, 0.02, 0.022), 0.0, 0.6),
        'orange':     m('HALL_TapOffOrange', (0.90, 0.20, 0.015), 0.0, 0.42),
        'grey_pl':    m('HALL_GreyPlastic', (0.42, 0.43, 0.45), 0.0, 0.45),
        'light_pl':   m('HALL_LightGreyPlastic', (0.70, 0.71, 0.72), 0.0, 0.45),
        'rubber':     m('HALL_CordRubber', (0.012, 0.012, 0.013), 0.0, 0.65),
        'pin_red':    m('HALL_IEC309_Red', (0.70, 0.02, 0.02), 0.0, 0.40),
        'pin_blue':   m('HALL_IEC309_Blue', (0.02, 0.10, 0.60), 0.0, 0.40),
        'yellow':     m('HALL_FiberYellow', (0.95, 0.62, 0.0), 0.0, 0.42),
        'fiber_core': m('HALL_FiberBundleYellow', (0.85, 0.55, 0.02), 0.0, 0.55),
        'aqua':       m('HALL_FiberAqua', (0.05, 0.55, 0.60), 0.0, 0.5),
        'black_pc':   m('HALL_BlackPowderCoat', (0.012, 0.012, 0.013), 0.3, 0.55, spec=0.3),
        'zinc':       m('HALL_Zinc', (0.55, 0.56, 0.57), 1.0, 0.45),
        'glass':      m('HALL_Polycarbonate', (0.80, 0.85, 0.88), 0.0, 0.08, alpha=0.22),
        'glass_dark': m('HALL_TintedGlass', (0.20, 0.22, 0.24), 0.0, 0.08, alpha=0.40),
        'white_pnl':  m('HALL_WhitePanel', (0.80, 0.80, 0.78), 0.0, 0.45),
        'beige_pnl':  m('HALL_CRAH_Panel', (0.78, 0.77, 0.72), 0.0, 0.45),
        'cab_black':  m('HALL_CabinetBlack', (0.010, 0.010, 0.011), 0.25, 0.48, spec=0.3),
        'pipe_blue':  m('HALL_InsulBlue', (0.02, 0.12, 0.62), 0.0, 0.5),
        'pipe_red':   m('HALL_InsulRed', (0.65, 0.02, 0.02), 0.0, 0.5),
        'ss':         m('HALL_Stainless', (0.70, 0.70, 0.72), 1.0, 0.25),
        'bristle':    m('HALL_Bristle', (0.008, 0.008, 0.009), 0.0, 0.85),
        'label':      m('HALL_LabelWhite', (0.85, 0.86, 0.88), 0.0, 0.6),
        'label_blk':  m('HALL_LabelBlack', (0.01, 0.01, 0.01), 0.0, 0.6),
        'fan':        m('HALL_FanBlack', (0.02, 0.02, 0.022), 0.1, 0.5),
        'tbar':       m('HALL_TBarWhite', (0.85, 0.85, 0.84), 0.3, 0.35),
        'concrete_side': m('HALL_ConcreteSide', (0.35, 0.35, 0.34), 0.0, 0.8),
        'pedestal':   m('HALL_PedestalZinc', (0.55, 0.56, 0.57), 1.0, 0.45),
    })
    return M


def led_mat(name, rgb, strength=6.0):
    return H['mat']('HALL_LED_' + name, tuple(c * 0.3 for c in rgb), 0.0, 0.4, emit=rgb, emit_str=strength)


def led(name, size, loc, rgb, root, col, strength=6.0, rot=(0, 0, 0)):
    o = H['box'](name, size, loc, led_mat(name.split('__')[0].replace('LED_', ''), rgb, strength), col, parent=root)
    o.rotation_euler = rot
    return tag_obj(o, 'led', root)


# ------------------------------------------------------------------ textures (procedural, packed, exported)

def np_image(name, arr):
    """arr: H x W x 4 float32 (linear for colour data written as sRGB image)."""
    import numpy as np
    h, w = arr.shape[:2]
    img = bpy.data.images.get(name)
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(name, w, h, alpha=True)
    img.pixels.foreach_set(np.ascontiguousarray(arr, dtype=np.float32).ravel())
    img.file_format = 'PNG'
    img.pack()
    return img


def tex_mat(name, img, metal=0.0, rough=0.5, alpha_from_tex=False, emit_img=None, emit_str=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    for n in list(nt.nodes):
        if n.type == 'TEX_IMAGE':
            nt.nodes.remove(n)
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.location = (-400, 200)
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    if alpha_from_tex:
        nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    if emit_img is not None:
        nt.links.new(t.outputs['Color'], b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = emit_str
    return m


def quad(name, sx, sy, loc, material, col, parent=None, uv_rep=(1, 1), rot=(0, 0, 0)):
    """Single quad in its local XY plane (normal +Z) with UV 0..rep."""
    bm = bmesh.new()
    vs = [bm.verts.new((x * sx / 2, y * sy / 2, 0)) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new('UVMap')
    for l, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        l[uv].uv = (u * uv_rep[0], v * uv_rep[1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(material)
    col.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    if parent:
        o.parent = parent
    return o


# ------------------------------------------------------------------ paths and sweeps

def fillet(pts, radius=0.0, segs90=8):
    """Polyline -> sampled path with circular fillets of `radius` (scalar or per-vertex list)."""
    pts = [Vector(p) for p in pts]
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        r = radius[i] if isinstance(radius, (list, tuple)) else radius
        p, a, b = pts[i], pts[i - 1], pts[i + 1]
        di = (p - a).normalized(); do = (b - p).normalized()
        cosang = max(-1.0, min(1.0, di.dot(do)))
        th = math.acos(cosang)
        if r <= 0 or th < 1e-4:
            out.append(p); continue
        t = r * math.tan(th / 2)
        t = min(t, (p - a).length * 0.999, (b - p).length * 0.999)
        r_eff = t / math.tan(th / 2)
        s = p - di * t
        n = (do - di * cosang).normalized()
        c = s + n * r_eff
        axis = di.cross(do).normalized()
        k = max(2, int(math.ceil(segs90 * th / (math.pi / 2))))
        for j in range(k + 1):
            q = mathutils.Quaternion(axis, th * j / k)
            out.append(c + q @ (s - c))
    out.append(pts[-1])
    # drop duplicates
    clean = [out[0]]
    for q in out[1:]:
        if (q - clean[-1]).length > 1e-6:
            clean.append(q)
    return clean


def frames(path, up0=None):
    """Per-sample (pos, tangent, side, up, mitre_dir, mitre_scale, u)."""
    n = len(path)
    seg = [(path[i + 1] - path[i]).normalized() for i in range(n - 1)]
    tans, mdir, msc = [], [], []
    for i in range(n):
        if i == 0:
            t = seg[0]; m = None; s = 1.0
        elif i == n - 1:
            t = seg[-1]; m = None; s = 1.0
        else:
            di, do = seg[i - 1], seg[i]
            t = (di + do)
            if t.length < 1e-6:
                t = do
            t.normalize()
            c = max(1e-3, di.dot(t))
            d = do - di
            d = d - t * d.dot(t)
            m = d.normalized() if d.length > 1e-7 else None
            s = 1.0 / c
        tans.append(t); mdir.append(m); msc.append(s)
    t0 = tans[0]
    ref = Vector(up0) if up0 is not None else (Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((-1, 0, 0)))
    up = (ref - t0 * ref.dot(t0)).normalized()
    out = []
    u = 0.0
    for i in range(n):
        if i > 0:
            u += (path[i] - path[i - 1]).length
            rot = tans[i - 1].rotation_difference(tans[i])
            up = (rot @ up)
            up = (up - tans[i] * up.dot(tans[i])).normalized()
        side = up.cross(tans[i]).normalized()
        out.append((path[i], tans[i], side, up, mdir[i], msc[i], u))
    return out


def profile_v(profile, closed=True):
    L = [0.0]
    m = len(profile)
    rng = range(m) if closed else range(m - 1)
    for j in rng:
        a = Vector(profile[j]); b = Vector(profile[(j + 1) % m])
        L.append(L[-1] + (b - a).length)
    tot = L[-1] or 1.0
    return [x / tot for x in L]


def sweep_bm(bm, uvl, path_pts, profile, radius=0.0, segs90=8, closed=True, caps=True, up0=None, u0=0.0, smooth=False):
    path = fillet(path_pts, radius, segs90)
    F = frames(path, up0)
    vs = profile_v(profile, closed)
    rings = []
    for (p, t, side, up, m, s, u) in F:
        ring = []
        for (a, b) in profile:
            off = side * a + up * b
            if m is not None:
                off = off + m * (off.dot(m) * (s - 1.0))
            ring.append(bm.verts.new(p + off))
        rings.append((ring, u + u0))
    nprof = len(profile)
    edges = range(nprof) if closed else range(nprof - 1)
    faces = []
    for i in range(len(rings) - 1):
        (ra, ua), (rb, ub) = rings[i], rings[i + 1]
        for j in edges:
            k = (j + 1) % nprof
            f = bm.faces.new((ra[j], ra[k], rb[k], rb[j]))
            f.smooth = smooth
            for l, uvv in zip(f.loops, ((ua, vs[j]), (ua, vs[j + 1]), (ub, vs[j + 1]), (ub, vs[j]))):
                l[uvl].uv = uvv
            faces.append(f)
    if closed and caps:
        tris = cap_tris(profile)
        for (ring, uu), rev in ((rings[0], True), (rings[-1], False)):
            for tri in tris:
                vv = [ring[k] for k in tri]
                if rev:
                    vv.reverse()
                try:
                    f = bm.faces.new(vv)
                except ValueError:
                    continue
                for l in f.loops:
                    l[uvl].uv = (uu, 0.0)
    return F[-1][6]


def cap_tris(poly2d):
    """Concave-safe triangulation of a 2D outline (indices, CCW like the outline)."""
    from mathutils.geometry import tessellate_polygon
    tris = tessellate_polygon([[Vector((a, b, 0.0)) for a, b in poly2d]])
    out = []
    for t in tris:
        a, b, c = (Vector(poly2d[i]) for i in t)
        cr = (b - a).x * (c - a).y - (b - a).y * (c - a).x
        out.append(tuple(t) if cr > 0 else (t[0], t[2], t[1]))
    return out


def finish_bm(name, bm, material, col, parent):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    if isinstance(material, (list, tuple)):
        for mm in material:
            me.materials.append(mm)
    else:
        me.materials.append(material)
    col.objects.link(o)
    if parent:
        o.parent = parent
    return o


def sweep(name, path_pts, profile, material, col, parent=None, radius=0.0, segs90=8, closed=True, caps=True,
          up0=None, smooth=False, flow=None, root=None):
    """Sweep a 2D profile (a=side, b=up) along a polyline (with fillets). flow='power'|'coolant'|'data'
    marks a flow mesh (u = metres along path)."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    L = sweep_bm(bm, uvl, path_pts, profile, radius, segs90, closed, caps, up0, 0.0, smooth)
    o = finish_bm(name, bm, material, col, parent)
    if flow:
        o['flow_u_start'] = 0.0
        o['flow_u_end'] = round(L, 5)
        o['flow_kind'] = flow
        if root is not None:
            tag_obj(o, 'flow', root)
    return o, L


def multi_sweep(name, items, material, col, parent=None, closed=True, caps=True, smooth=False):
    """items: list of dicts {pts, profile, radius, up0}. One merged mesh (e.g. wire basket)."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    for it in items:
        sweep_bm(bm, uvl, it['pts'], it['profile'], it.get('radius', 0.0), it.get('segs90', 6), closed, caps,
                 it.get('up0'), 0.0, smooth)
    return finish_bm(name, bm, material, col, parent)


def circle(r, n=12, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def ellipse(rx, ry, n=12, cx=0.0, cy=0.0):
    return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n)]


def rect(w, h, cx=0.0, cy=0.0):
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]


def rrect(w, h, r, n=3, cx=0.0, cy=0.0):
    pts = []
    for (qx, qy, a0) in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + qx + r * math.cos(a), cy + qy + r * math.sin(a)))
    return pts


def poly_prism(name, outline_xy, z0, z1, material, col, parent=None):
    """Extrude a (possibly concave) XY outline between z0 and z1 using ear-clip caps."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    v0 = [bm.verts.new((x, y, z0)) for x, y in outline_xy]
    v1 = [bm.verts.new((x, y, z1)) for x, y in outline_xy]
    n = len(outline_xy)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((v0[k], v0[j], v1[j], v1[k]))
    for tri in cap_tris(outline_xy):
        for f in (bm.faces.new([v1[i] for i in tri]), bm.faces.new([v0[i] for i in reversed(tri)])):
            for l in f.loops:
                l[uvl].uv = (l.vert.co.x, l.vert.co.y)
    return finish_bm(name, bm, material, col, parent)


def arc_pts(c, r, a0, a1, n=8):
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


# ------------------------------------------------------------------ generic hardware

def threaded_rod(name, x, y, z0, z1, root, col, M, r=0.005):
    return H['cyl'](name, r, z1 - z0, (x, y, (z0 + z1) / 2), M['zinc'], col, verts=8, parent=root)


def strut(name, length, loc, axis, root, col, M):
    """41x41 strut channel (Unistrut P1000) along axis 'x' or 'y'."""
    s = (length, 0.041, 0.041) if axis == 'x' else (0.041, length, 0.041)
    return H['box'](name, s, loc, M['zinc'], col, parent=root)


# ------------------------------------------------------------------ finishing, export

def apply_mods(root):
    for o in [root] + list(root.children_recursive):
        if o.type == 'MESH' and o.modifiers:
            H['apply_all'](o)


def tri_count(objs):
    dg = bpy.context.evaluated_depsgraph_get(); tris = 0
    for o in objs:
        if o.type == 'MESH':
            e = o.evaluated_get(dg); m = e.to_mesh(); m.calc_loop_triangles(); tris += len(m.loop_triangles); e.to_mesh_clear()
    return tris


def _select(roots):
    bpy.ops.object.select_all(action='DESELECT')
    objs = []
    for r in roots:
        objs += [r] + list(r.children_recursive)
    for o in objs:
        o.hide_set(False); o.hide_render = False
        o.select_set(True)
    bpy.context.view_layer.objects.active = roots[0]
    return objs


def gltf(path, roots):
    objs = _select(roots)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_apply=True, export_extras=True,
                              export_yup=True)
    return tri_count(objs)


def finish_piece(root, tag, file_base, stats):
    """Apply modifiers, export the piece alone (clean names), then suffix child names with __TAG."""
    apply_mods(root)
    os.makedirs(os.path.join(EXPORT, file_base), exist_ok=True)
    p = os.path.join(EXPORT, file_base, f'{root.name}.glb')
    tris = gltf(p, [root])
    stats.append((root.name, tris, os.path.getsize(p), [c.name for c in root.children_recursive if c.type == 'EMPTY']))
    for c in root.children_recursive:
        c.name = f'{c.name}__{tag}'
        if c.type == 'MESH':
            c.data.name = c.name


def export_all(file_base, stats):
    roots = [r for r, t in PIECES]
    p = os.path.join(EXPORT, f'{file_base}.glb')
    tris = gltf(p, roots)
    print(f'=== {file_base}: {len(roots)} pieces, total tris {tris}, combined glb {os.path.getsize(p)} bytes')
    for name, t, size, empties in stats:
        print(f'PIECE {name}: tris {t}, glb {size} B, empties {sorted(empties)}')
    return tris


# ------------------------------------------------------------------ render helpers

_STUDIO0 = {}


def studio(scale, centre=(0, 0, 0), floor_z=0.0):
    """Scale the template key/fill/rim rig (made for a 30 cm card) around `centre`."""
    C = Vector(centre)
    for n in ('Key', 'Fill', 'Rim'):
        o = bpy.data.objects.get(n)
        if not o:
            continue
        if n not in _STUDIO0:
            _STUDIO0[n] = (o.location.copy(), o.data.energy, o.data.size)
        loc, en, sz = _STUDIO0[n]
        o.location = C + (loc - Vector((0.13, -0.05, 0.05))) * scale
        o.data.energy = en * scale * scale * 0.55
        o.data.size = sz * scale
    f = bpy.data.objects.get('Floor')
    if f:
        f.location = (C.x, C.y, floor_z - 0.002)
        f.scale = (200, 200, 1)
        f.hide_render = False
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.render.resolution_percentage = 100
    sc.view_settings.exposure = -0.6
    try:
        sc.eevee.taa_render_samples = 48
    except Exception:
        pass
    cam = bpy.data.objects['Camera']
    cam.data.clip_start = 0.01; cam.data.clip_end = 200


def add_sun(strength=2.5, rot=(math.radians(50), 0, math.radians(30))):
    s = bpy.data.objects.get('HallSun')
    if not s:
        d = bpy.data.lights.new('HallSun', 'SUN')
        s = bpy.data.objects.new('HallSun', d)
        H['coll']('Studio').objects.link(s)
    s.data.energy = strength
    s.rotation_euler = rot
    return s


def render_views(prefix, views):
    sc = bpy.context.scene
    cam = bpy.data.objects['Camera']
    only = [a.split('=', 1)[1] for a in sys.argv if a.startswith('--views=')]
    only = only[0].split(',') if only else list(views)
    out = []
    for name in only:
        if name not in views:
            continue
        loc, tgt, lens = views[name][:3]
        cam.location = loc
        d = Vector(tgt) - Vector(loc)
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        cam.data.type = 'PERSP'; cam.data.lens = lens
        sc.camera = cam
        sc.render.filepath = os.path.join(RENDERS, f'{prefix}_{name}.png')
        bpy.ops.render.render(write_still=True)
        out.append(sc.render.filepath)
        print('RENDERED', sc.render.filepath)
    return out


def context_racks(xs, y_front, depth=1.07, name='CTX_Rack', facing=-1):
    """Plain black dummy racks for render context only (not exported)."""
    col = H['coll']('RenderContext')
    M = mats()
    objs = []
    for i, x in enumerate(xs):
        yc = y_front + depth / 2 if facing < 0 else y_front - depth / 2
        o = H['box'](f'{name}_{i}', (RACK_W - 0.004, depth, RACK_H), (x, yc, RACK_H / 2), M['cab_black'], col)
        objs.append(o)
    return objs


def place(root, loc, rot_z=0.0):
    root.location = loc
    root.rotation_euler = (0, 0, rot_z)


def dup(root, loc, rot_z=0.0):
    """Linked duplicate of a piece hierarchy for layout renders (RenderContext collection)."""
    col = H['coll']('RenderContext')
    mp = {}

    def cp(o, parent):
        n = o.copy()
        col.objects.link(n)
        n.hide_render = False
        mp[o] = n
        if parent:
            n.parent = parent
        for c in o.children:
            cp(c, n)
        return n
    r = cp(root, None)
    r.location = loc; r.rotation_euler = (0, 0, rot_z)
    return r


# ------------------------------------------------------------------ perforations, fans

def perf_image(name, px=256, holes=16, r_frac=0.32, rgb=(0.01, 0.01, 0.011), hex_grid=True, alpha_holes=True,
               hole_rgb=(0.0, 0.0, 0.0)):
    """Tileable perforated-sheet texture: `holes` x `holes` round holes per tile (alpha 0 in holes)."""
    import numpy as np
    y, x = np.mgrid[0:px, 0:px].astype(np.float32) + 0.5
    p = px / holes
    gx = x / p; gy = y / p
    if hex_grid:
        row = np.floor(gy)
        gx = gx + 0.5 * (row % 2)
    fx = gx - np.floor(gx) - 0.5; fy = gy - np.floor(gy) - 0.5
    d = np.sqrt(fx * fx + fy * fy)
    hole = np.clip((r_frac - d) * p * 1.5 + 0.5, 0, 1)
    img = np.zeros((px, px, 4), np.float32)
    for c in range(3):
        img[..., c] = rgb[c] * (1 - hole) + hole_rgb[c] * hole
    img[..., 3] = 1 - hole if alpha_holes else 1.0
    return np_image(name, img)


def fan_blades(name, r_hub, r_tip, n_blades, material, col, parent, loc, axis='Y', pitch=0.35, sweep_deg=40, depth=0.02):
    """Fan rotor (hub + blades) built around its own origin; spin axis = local `axis`. One object = FAN_*."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    segs = 4
    for k in range(n_blades):
        a0 = 2 * math.pi * k / n_blades
        span = math.radians(sweep_deg)
        lead, trail = [], []
        for j in range(segs + 1):
            r = r_hub * 0.95 + (r_tip - r_hub * 0.95) * j / segs
            sk = 0.25 * span * j / segs          # forward skew toward the tip
            for lst, da, dz in ((lead, 0.0, depth / 2), (trail, span, -depth / 2)):
                a = a0 + da + sk
                lst.append(bm.verts.new((r * math.cos(a), r * math.sin(a), dz)))
        for j in range(segs):
            bm.faces.new((lead[j], lead[j + 1], trail[j + 1], trail[j]))
    # hub disc
    n = 16
    top = [bm.verts.new((r_hub * math.cos(2 * math.pi * i / n), r_hub * math.sin(2 * math.pi * i / n), depth * 0.8)) for i in range(n)]
    bot = [bm.verts.new((r_hub * math.cos(2 * math.pi * i / n), r_hub * math.sin(2 * math.pi * i / n), -depth * 0.8)) for i in range(n)]
    bm.faces.new(top); bm.faces.new(list(reversed(bot)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(material)
    col.objects.link(o); o.parent = parent
    o.location = loc
    o.rotation_euler = {'Y': (math.pi / 2, 0, 0), 'X': (0, math.pi / 2, 0), 'Z': (0, 0, 0)}[axis]
    o['spin_axis'] = 'local_Z'
    return tag_obj(o, 'fan', parent)
