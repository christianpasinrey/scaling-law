"""Shared helpers for the GB200 NVL72 assets (srv_06 compute tray, srv_07 switch tray, rack_02 rack).

Loaded with exec() from the asset scripts; loads hw.py and blackwell_common.py itself.
Does not modify hw.py.
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix

BASE = r'C:\laragon\www\scaling-law\blender'
exec(open(BASE + r'\lib\hw.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']
exec(open(BASE + r'\scripts\blackwell_common.py', encoding='utf-8').read())

U = 0.04445            # EIA 1U (the NVIDIA MGX NVL72 rack uses 19" EIA rails, 48U)
BLENDER = r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'


# ------------------------------------------------------------------ materials
def perf_image(name='NV_Perf', n=32, hole=0.62, base=0.10, hole_col=0.004):
    """Tileable square-hole perforation texture (one hole per tile)."""
    img = bpy.data.images.get(name)
    if img:
        return img
    img = bpy.data.images.new(name, n, n, alpha=False)
    px = []
    a = int(n * (1 - hole) / 2); b = n - a
    for j in range(n):
        for i in range(n):
            c = hole_col if (a <= i < b and a <= j < b) else base
            px += [c, c, c * 1.04, 1.0]
    img.pixels = px
    img.pack()
    return img


def tex_mat(name, img, metal=0.6, rough=0.45):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = H['mat'](name, (0.1, 0.1, 0.1), metal, rough)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.interpolation = 'Closest'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    return m


def nv_materials():
    M = H['base_materials'](); M.update(extra_materials())
    m = H['mat']
    M.update({
        'gold':     m('NV_Champagne', (0.50, 0.38, 0.22), 1.0, 0.30),
        'gold_dk':  m('NV_ChampagneDark', (0.30, 0.22, 0.12), 1.0, 0.40),
        'panel':    m('NV_PanelDark', (0.030, 0.032, 0.035), 0.6, 0.45),
        'module':   m('NV_ModuleGrey', (0.20, 0.205, 0.21), 0.7, 0.40),
        'sheet':    m('NV_SheetSteel', (0.55, 0.56, 0.58), 1.0, 0.36),
        'rack':     m('NV_RackBlack', (0.014, 0.014, 0.015), 0.5, 0.48),
        'rack_hole': m('NV_RackHole', (0.0, 0.0, 0.0), 0.0, 0.9),
        'busbar':   m('NV_BusbarCopper', (0.90, 0.52, 0.34), 1.0, 0.25),
        'stainless': m('NV_Stainless', (0.74, 0.74, 0.75), 1.0, 0.24),
        'cable_nv': m('NV_SpineCable', (0.70, 0.70, 0.68), 0.0, 0.45),
        'teal':     m('NV_TealCable', (0.06, 0.45, 0.42), 0.0, 0.40),
        'label':    m('NV_LabelWhite', (0.80, 0.80, 0.80), 0.0, 0.55),
        'pcb_g':    m('NV_PCB_Green', (0.02, 0.08, 0.04), 0.0, 0.45),
        'brass':    m('NV_Brass', (0.80, 0.60, 0.30), 1.0, 0.30),
        'led_g':    m('NV_LED_Green', (0.05, 0.9, 0.2), 0.0, 0.3, emit=(0.1, 1.0, 0.25), emit_str=6.0),
        'led_b':    m('NV_LED_Blue', (0.05, 0.3, 1.0), 0.0, 0.3, emit=(0.15, 0.4, 1.0), emit_str=6.0),
        'led_a':    m('NV_LED_Amber', (1.0, 0.5, 0.05), 0.0, 0.3, emit=(1.0, 0.55, 0.1), emit_str=6.0),
        'led_w':    m('NV_LED_White', (0.9, 0.9, 0.9), 0.0, 0.3, emit=(1.0, 1.0, 1.0), emit_str=4.0),
    })
    M['grille'] = tex_mat('NV_Grille', perf_image())
    M['grille_lt'] = tex_mat('NV_GrilleLight', perf_image('NV_PerfLight', base=0.30, hole_col=0.01), metal=0.8, rough=0.4)
    return M


# ------------------------------------------------------------------ geometry helpers
def mesh_obj(name, verts, faces, uvs, material, col, parent=None, smooth=False):
    """faces: lists of vertex indices; uvs: per-face list of (u,v) per corner (or None)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if uvs:
        uvl = me.uv_layers.new(name='UVMap')
        k = 0
        for poly, fu in zip(me.polygons, uvs):
            for li, uv in zip(poly.loop_indices, fu):
                uvl.data[li].uv = uv
    me.materials.append(material)
    o = bpy.data.objects.new(name, me); col.objects.link(o)
    if parent:
        o.parent = parent
    for p in me.polygons:
        p.use_smooth = smooth
    return o


def grille(name, a0, a1, b0, b1, d, material, col, parent=None, plane='xz', facing=-1, pitch=0.0028):
    """Perforated panel quad. plane 'xz': a=x, b=z at y=d, normal facing -Y (facing=-1) or +Y.
    plane 'yz': a=y, b=z at x=d, normal facing -X/+X. plane 'xy': a=x, b=y at z=d, normal -Z/+Z."""
    def P(a, b):
        return {'xz': (a, d, b), 'yz': (d, a, b), 'xy': (a, b, d)}[plane]
    vs = [P(a0, b0), P(a1, b0), P(a1, b1), P(a0, b1)]
    uv = [(0, 0), ((a1 - a0) / pitch, 0), ((a1 - a0) / pitch, (b1 - b0) / pitch), (0, (b1 - b0) / pitch)]
    f = [0, 1, 2, 3]
    # xz with order above has normal -Y; yz has +X; xy has +Z
    natural = {'xz': -1, 'yz': 1, 'xy': 1}[plane]
    if facing != natural:
        f = [0, 3, 2, 1]; uv = [uv[0], uv[3], uv[2], uv[1]]
    return mesh_obj(name, vs, [f], [uv], material, col, parent)


def flow_box(name, p0, p1, w, d, material, col, parent=None, u0=0.0, side=(1, 0, 0)):
    """Rectangular bar (busbar, square manifold) from p0 to p1, section w (along `side`) x d.
    UV u = u0 + metres along the bar (continuous), v = 0..1 around the section. Sets flow_u_start/end."""
    p0, p1 = Vector(p0), Vector(p1)
    ax = (p1 - p0); L = ax.length; ax.normalize()
    s = Vector(side); s = (s - ax * s.dot(ax)).normalized(); t = ax.cross(s)
    corners = [s * w / 2 + t * d / 2, -s * w / 2 + t * d / 2, -s * w / 2 - t * d / 2, s * w / 2 - t * d / 2]
    per = 2 * (w + d); vfr = [0, w / per, (w + d) / per, (2 * w + d) / per, 1.0]
    verts = [tuple(p0 + c) for c in corners] + [tuple(p1 + c) for c in corners]
    faces, uvs = [], []
    for k in range(4):
        j = (k + 1) % 4
        faces.append([k, j, 4 + j, 4 + k])
        uvs.append([(u0, vfr[k]), (u0, vfr[k + 1]), (u0 + L, vfr[k + 1]), (u0 + L, vfr[k])])
    faces.append([3, 2, 1, 0]); uvs.append([(u0, 0)] * 4)
    faces.append([4, 5, 6, 7]); uvs.append([(u0 + L, 0)] * 4)
    o = mesh_obj(name, verts, faces, uvs, material, col, parent)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    o['flow_u_start'] = u0; o['flow_u_end'] = u0 + L
    return o, u0 + L


def slot(name, loc, col, parent, rot=(0, 0, 0), scale=(1, 1, 1), size=0.03, kind='ARROWS'):
    e = bpy.data.objects.new(name, None); e.empty_display_type = kind; e.empty_display_size = size
    e.location = loc; e.rotation_euler = rot; e.scale = scale
    col.objects.link(e); e.parent = parent
    return e


def merge(name, objs):
    objs = [o for o in objs if o]
    for o in objs:
        H['apply_all'](o)
    with bpy.context.temp_override(active_object=objs[0], object=objs[0], selected_objects=objs, selected_editable_objects=objs):
        bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


# ------------------------------------------------------------------ assets / scene
def append_tree(blend, root_name):
    """Append the collection named root_name from blend, link it to the scene, return its root object."""
    with bpy.data.libraries.load(blend, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c == root_name]
    c = dst.collections[0]
    bpy.context.scene.collection.children.link(c)
    roots = [o for o in c.objects if o.parent is None]
    return next(o for o in roots if o.name.startswith(root_name))


def dup_tree(o, col, parent=None):
    n = o.copy()
    col.objects.link(n)
    if parent is not None:
        n.parent = parent
    for ch in o.children:
        dup_tree(ch, col, n)
    return n


def tree(o):
    return [o] + list(o.children_recursive)


def stage(k, target=(0, 0, 0), floor_z=0.0, floor_scale=None):
    """Scale the studio (sized for ~30 cm cards) by k around target."""
    T = Vector(target)
    for nm in ('Key', 'Fill', 'Rim'):
        L = bpy.data.objects.get(nm)
        if not L:
            continue
        if '_orig' not in L:
            L['_orig'] = list(L.location) + [L.data.energy, L.data.size]
        o = L['_orig']
        L.location = T + Vector(o[:3]) * k
        L.data.energy = max(o[3], 4.0) * k * k
        L.data.size = o[4] * k
    fl = bpy.data.objects.get('Floor')
    if fl:
        fl.location = (T.x, T.y, floor_z)
        fl.scale = (floor_scale or k, floor_scale or k, 1)
    for c in bpy.data.objects:
        if c.type == 'CAMERA':
            c.data.clip_end = 200
    setup_render(floor_z)
    if fl:
        fl.location = (T.x, T.y, floor_z)


def cam_view(path, eye, target, lens=50, ortho=None):
    cam = bpy.data.objects['Camera']
    look_at(cam, eye, target, lens=lens, ortho=ortho)
    if ortho:
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    render(path)


def bbox(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == 'MESH' for c in o.bound_box]
    return ([round(min(p[i] for p in pts), 4) for i in range(3)], [round(max(p[i] for p in pts), 4) for i in range(3)])


def finalize_modifiers(root):
    for o in tree(root):
        if o.type == 'MESH' and o.modifiers:
            H['apply_all'](o)
