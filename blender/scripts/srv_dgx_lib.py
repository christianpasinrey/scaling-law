"""Shared helpers for the DGX server build scripts (srv_02_dgx1_v100.py, srv_03_dgx_a100.py).

Load after hw.py and sxm_lib.py:
    exec(open(r'C:\\laragon\\www\\scaling-law\\blender\\lib\\hw.py', encoding='utf-8').read())
    exec(open(r'C:\\laragon\\www\\scaling-law\\blender\\scripts\\sxm_lib.py', encoding='utf-8').read())
    exec(open(r'C:\\laragon\\www\\scaling-law\\blender\\scripts\\srv_dgx_lib.py', encoding='utf-8').read())

Rack-mount convention: metres, Z up, front panel plane y=0 facing -Y, depth toward +Y,
origin bottom-front-centre. All helper inputs below are in millimetres unless noted.
Parts are built unparented in world space, collected into named groups and joined into one mesh
per group (chassis, bezel, trays, PSUs, fans...) so the exported GLB stays light.
"""
import bpy, bmesh, math, mathutils
import numpy as np

H = bpy.app.driver_namespace['HW']
MM = 0.001
GROUPS = {}


def _grp(o, g):
    if g:
        GROUPS.setdefault(g, []).append(o)
    return o


def bx(name, x0, x1, y0, y1, z0, z1, m, g, bevel=0.0):
    """Axis-aligned box from min/max (mm)."""
    o = H['box'](name, ((x1 - x0) * MM, (y1 - y0) * MM, (z1 - z0) * MM),
                 ((x0 + x1) / 2 * MM, (y0 + y1) / 2 * MM, (z0 + z1) / 2 * MM), m, _scratch(), bevel=bevel * MM)
    return _grp(o, g)


def cy(name, r, depth, c, axis, m, g, verts=24, bevel=0.0):
    rot = {'x': (0, math.pi / 2, 0), 'y': (math.pi / 2, 0, 0), 'z': (0, 0, 0)}[axis]
    o = H['cyl'](name, r * MM, depth * MM, tuple(v * MM for v in c), m, _scratch(), verts=verts, rot=rot, bevel=bevel * MM)
    return _grp(o, g)


def pr(name, pts, plane, d0, depth, m, g):
    o = H['prism'](name, [(a * MM, b * MM) for a, b in pts], plane, d0 * MM, depth * MM, m, _scratch())
    return _grp(o, g)


def sa(name, specs, m, g):
    """Merged boxes: specs = [((cx,cy,cz),(sx,sy,sz))] in mm."""
    lst = [(tuple(c * MM for c in ce), tuple(s * MM for s in si)) for ce, si in specs]
    return _grp(H['slat_array'](name, lambda: iter(lst), m, _scratch()), g)


def rrect(cx, cz, w, h, r, n=6):
    """Rounded rectangle outline (mm) in a 2D plane, counter-clockwise."""
    r = min(r, w / 2, h / 2)
    pts = []
    for (qx, qz, a0) in ((cx + w / 2 - r, cz - h / 2 + r, -90), (cx + w / 2 - r, cz + h / 2 - r, 0),
                         (cx - w / 2 + r, cz + h / 2 - r, 90), (cx - w / 2 + r, cz - h / 2 + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((qx + r * math.cos(a), qz + r * math.sin(a)))
    return pts


def _scratch():
    return H['coll']('SRV_Build')


def uv_planar(o, axes, su, sv, ou=0.0, ov=0.0):
    """Planar UVs from world coordinates: u = (coord[a]-ou)/su, v = (coord[b]-ov)/sv (metres)."""
    ia, ib = 'xyz'.index(axes[0]), 'xyz'.index(axes[1])
    me = o.data
    if not me.uv_layers:
        me.uv_layers.new(name='UVMap')
    uv = me.uv_layers[0]
    mw = o.matrix_world
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((co[ia] - ou) / su, (co[ib] - ov) / sv)
    return o


def join(g, name, parent=None):
    """Apply modifiers, make sure every part has 'UVMap', join the group into one mesh."""
    objs = [o for o in GROUPS.pop(g, []) if o.name in bpy.data.objects]
    if not objs:
        return None
    for o in objs:
        if o.type != 'MESH':
            continue
        if o.modifiers:
            H['apply_all'](o)
        if not o.data.uv_layers:
            o.data.uv_layers.new(name='UVMap')
        else:
            o.data.uv_layers[0].name = 'UVMap'
    act = objs[0]
    if len(objs) > 1:
        with bpy.context.temp_override(active_object=act, object=act, selected_objects=objs, selected_editable_objects=objs):
            bpy.ops.object.join()
    act.name = name
    act.data.name = name
    if parent:
        mw = act.matrix_world.copy()
        act.parent = parent
        act.matrix_world = mw
    for c in list(act.users_collection):
        c.objects.unlink(act)
    (parent.users_collection[0] if parent else _scratch()).objects.link(act)
    return act


def empty(name, loc_mm, parent, col, rot=(0, 0, 0), kind='ARROWS', size=0.03, props=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind; e.empty_display_size = size
    col.objects.link(e)
    e.matrix_world = mathutils.Matrix.Translation(tuple(v * MM for v in loc_mm)) @ mathutils.Euler(rot).to_matrix().to_4x4()
    if parent:
        mw = e.matrix_world.copy(); e.parent = parent; e.matrix_world = mw
    for k, v in (props or {}).items():
        e[k] = v
    return e


def reparent(o, parent):
    mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = mw
    for c in list(o.users_collection):
        c.objects.unlink(o)
    parent.users_collection[0].objects.link(o)
    return o


# ---------------------------------------------------------------- flow paths (power / coolant)
def _fillet(pts, rad, seg=6):
    """Round the corners of a polyline (metres) with arcs of radius rad (clamped)."""
    if len(pts) < 3 or rad <= 0:
        return [mathutils.Vector(p) for p in pts]
    P = [mathutils.Vector(p) for p in pts]
    out = [P[0]]
    for i in range(1, len(P) - 1):
        a, b, c = P[i - 1], P[i], P[i + 1]
        d0 = (a - b); d1 = (c - b)
        l0, l1 = d0.length, d1.length
        if l0 < 1e-9 or l1 < 1e-9:
            continue
        d0.normalize(); d1.normalize()
        ang = d0.angle(d1)
        if ang > math.pi - 1e-3:
            out.append(b); continue
        t = rad / math.tan(ang / 2)
        t = min(t, l0 * 0.45, l1 * 0.45)
        p0 = b + d0 * t; p2 = b + d1 * t
        for k in range(seg + 1):          # quadratic Bezier approximates the arc
            s = k / seg
            out.append((1 - s) ** 2 * p0 + 2 * (1 - s) * s * b + s * s * p2)
    out.append(P[-1])
    return out


def flow_path(name, pts_mm, m, col, parent, radius=None, rect=None, sides=10, fillet=15.0,
              src=None, dst=None, kind='power'):
    """Sweep a round (radius mm) or rectangular (rect=(w,h) mm, busbar) profile along a polyline.
    UV: u = metres along the path (continuous), v = 0..1 around the profile.
    Custom props flow_u_start / flow_u_end, flow_kind. Sockets at both ends:
      SOCKET_<kind>_out_<src> at the start, SOCKET_<kind>_in_<dst> at the end (names given by caller)."""
    P = _fillet([tuple(v * MM for v in p) for p in pts_mm], fillet * MM)
    # cumulative length
    S = [0.0]
    for i in range(1, len(P)):
        S.append(S[-1] + (P[i] - P[i - 1]).length)
    # tangents
    T = []
    for i in range(len(P)):
        a = P[max(i - 1, 0)]; b = P[min(i + 1, len(P) - 1)]
        t = (b - a); t.normalize(); T.append(t)
    # parallel-transport frame
    up = mathutils.Vector((0, 0, 1)) if abs(T[0].z) < 0.9 else mathutils.Vector((1, 0, 0))
    N = [(up - T[0] * up.dot(T[0])).normalized()]
    for i in range(1, len(P)):
        n = N[-1] - T[i] * N[-1].dot(T[i]); n.normalize(); N.append(n)
    if rect:
        w, h = rect[0] * MM / 2, rect[1] * MM / 2
        prof = [(-w, -h), (w, -h), (w, h), (-w, h)]
        # perimeter fraction for v
        per = [0.0]
        for k in range(4):
            a, b = prof[k], prof[(k + 1) % 4]
            per.append(per[-1] + math.dist(a, b))
        vs = [p / per[-1] for p in per]
        ring = prof + [prof[0]]
    else:
        r = radius * MM
        ring = [(r * math.cos(2 * math.pi * k / sides), r * math.sin(2 * math.pi * k / sides)) for k in range(sides + 1)]
        vs = [k / sides for k in range(sides + 1)]
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    rows = []
    for i, p in enumerate(P):
        b = T[i].cross(N[i])
        rows.append([bm.verts.new(p + N[i] * a + b * c) for a, c in ring])
    nr = len(ring)
    for i in range(len(P) - 1):
        for k in range(nr - 1):
            f = bm.faces.new((rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k]))
            for lp, (u, v) in zip(f.loops, ((S[i], vs[k]), (S[i], vs[k + 1]), (S[i + 1], vs[k + 1]), (S[i + 1], vs[k]))):
                lp[uvl].uv = (u, v)
    # caps (uv pinned to the end u so pulses stay continuous)
    for i, rr in ((0, rows[0]), (len(P) - 1, rows[-1])):
        f = bm.faces.new(rr[:-1] if i == 0 else list(reversed(rr[:-1])))
        for lp in f.loops:
            lp[uvl].uv = (S[i], 0.5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if not rect:
        for poly in me.polygons:
            poly.use_smooth = True
    o = bpy.data.objects.new(name, me); me.materials.append(m); col.objects.link(o)
    if parent:
        o.parent = parent
    o['flow_u_start'] = 0.0
    o['flow_u_end'] = round(S[-1], 5)
    o['flow_kind'] = kind
    if src:
        empty(f'SOCKET_{kind}_out_{src}', tuple(v / MM for v in P[0]), parent, col, kind='SINGLE_ARROW', size=0.015,
              rot=T[0].to_track_quat('Z', 'Y').to_euler())
    if dst:
        empty(f'SOCKET_{kind}_in_{dst}', tuple(v / MM for v in P[-1]), parent, col, kind='SINGLE_ARROW', size=0.015,
              rot=T[-1].to_track_quat('Z', 'Y').to_euler())
    return o


# ---------------------------------------------------------------- procedural textures (baked to packed images)
def _img(name, rgba, non_color=False):
    h, w = rgba.shape[:2]
    old = bpy.data.images.get(name)
    if old:
        bpy.data.images.remove(old)
    im = bpy.data.images.new(name, w, h, alpha=True, is_data=non_color)
    if non_color:
        im.colorspace_settings.name = 'Non-Color'      # set before writing pixels (changing it regenerates the buffer)
    im.pixels.foreach_set(np.ascontiguousarray(rgba, dtype=np.float32).ravel())
    im.update(); im.pack()
    return im


def _worley(res, G, seed):
    """Tileable F1/F2 (cell units) on a res x res image with a G x G jittered grid."""
    rng = np.random.default_rng(seed)
    jit = rng.random((G, G, 2))
    ys, xs = np.mgrid[0:res, 0:res].astype(np.float32)
    px, py = (xs + 0.5) / res * G, (ys + 0.5) / res * G
    cx, cy_ = np.floor(px).astype(int), np.floor(py).astype(int)
    F1 = np.full(px.shape, 9.0, np.float32); F2 = F1.copy()
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            gx, gy = cx + ox, cy_ + oy
            j = jit[gy % G, gx % G]
            d = np.hypot(gx + j[..., 0] - px, gy + j[..., 1] - py)
            F2 = np.where(d < F1, F1, np.minimum(F2, d))
            F1 = np.minimum(F1, d)
    return F1, F2


def foam_images(name, base, res=512, G=34, seed=7, pore=0.40, floor=0.05, strength=1.2, **_):
    """Metal foam: mostly solid struts with dark round pores at the Worley cell centres.
    Returns (color, normal, rough) images; tile it with planar UVs."""
    F1, F2 = _worley(res, G, seed)
    F1s, F2s = _worley(res, G * 2, seed + 5)                          # second octave: small pores
    rng = np.random.default_rng(seed + 1)
    def pores(F1_, F2_, rr):
        t = np.clip((F1_ - rr * 0.55) / (rr * 0.6), 0.0, 1.0)        # dark centre fading to the rim
        return t * t * (3 - 2 * t)
    h = np.minimum(pores(F1, F2, pore), 0.35 + 0.65 * pores(F1s, F2s, pore * 0.8))
    h = h * np.clip((F2 - F1) / 0.10, 0.55, 1.0)                        # grooves where big cells meet
    noise = rng.random((res, res)).astype(np.float32)
    shade = floor + (1 - floor) * h                                     # no per-pixel noise: keeps the PNG small
    col = np.ones((res, res, 4), np.float32)
    for c in range(3):
        col[..., c] = base[c] * shade
    gy, gx = np.gradient(h)
    k = strength * res / 128
    n = np.dstack((-gx * k, gy * k, np.ones_like(h)))
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    nrm = np.ones((res, res, 4), np.float32); nrm[..., :3] = n * 0.5 + 0.5
    rough = np.ones((res, res, 4), np.float32)
    rv = 0.85 - 0.45 * h
    rough[..., 0] = rough[..., 1] = rough[..., 2] = rv
    return (_img(name + '_Col', col), _img(name + '_Nrm', nrm, True), _img(name + '_Rgh', rough, True))


def stipple_images(name, base, res=512, G=90, seed=3, strength=1.2, contrast=0.35):
    """Fine sand-cast / hammered stipple (DGX-1 bezel)."""
    F1, F2 = _worley(res, G, seed)
    h = np.clip(F1 / 0.75, 0, 1)                                         # bumps: low at seeds
    h = 1 - h ** 2
    shade = (1 - contrast) + contrast * h
    col = np.ones((res, res, 4), np.float32)
    for c in range(3):
        col[..., c] = base[c] * shade
    gy, gx = np.gradient(h)
    n = np.dstack((-gx * strength * res / 64, -gy * strength * res / 64, np.ones_like(h)))
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    nrm = np.ones((res, res, 4), np.float32); nrm[..., :3] = n * 0.5 + 0.5
    return _img(name + '_Col', col), _img(name + '_Nrm', nrm, True)


def hex_perf_image(name, base, res=96, hole=0.80, round_holes=False):
    """One tile of a hexagonal perforated sheet: width = pitch, height = sqrt(3) * pitch.
    Alpha 0 in the holes. u = x / pitch, v = z / (pitch*sqrt3)."""
    W, Hh = res, int(round(res * math.sqrt(3)))
    ys, xs = np.mgrid[0:Hh, 0:W].astype(np.float32)
    x = (xs + 0.5) / W; y = (ys + 0.5) / Hh * math.sqrt(3)
    best = np.full(x.shape, 9.0, np.float32)
    for (cx, cy_) in ((0, 0), (1, 0), (0, math.sqrt(3)), (1, math.sqrt(3)), (0.5, math.sqrt(3) / 2)):
        dx, dy = np.abs(x - cx), np.abs(y - cy_)
        d = np.hypot(dx, dy) if round_holes else np.maximum(dx, dx * 0.5 + dy * math.sqrt(3) / 2)
        best = np.minimum(best, d)
    r = 0.5 * hole
    a = (best > r).astype(np.float32)
    col = np.ones((Hh, W, 4), np.float32)
    for c in range(3):
        col[..., c] = base[c]
    col[..., 3] = a
    return _img(name, col)


def mat_tex(name, col_img, nrm_img=None, rough_img=None, metal=1.0, rough=0.45, nstr=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = col_img
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if nrm_img:
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = nrm_img
        nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = nstr
        nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    if rough_img:
        tr = nt.nodes.new('ShaderNodeTexImage'); tr.image = rough_img
        sep = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(tr.outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs[0], b.inputs['Roughness'])
    m.diffuse_color = (*[col_img.pixels[i] for i in range(3)], 1)
    return m


def mat_perf(name, img, metal=0.6, rough=0.45):
    """Alpha-clipped perforated sheet (glTF: Math Round -> alpha = MASK 0.5)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    rnd = nt.nodes.new('ShaderNodeMath'); rnd.operation = 'ROUND'
    nt.links.new(t.outputs['Alpha'], rnd.inputs[0])
    nt.links.new(rnd.outputs[0], b.inputs['Alpha'])
    try:
        m.surface_render_method = 'DITHERED'
    except Exception:
        pass
    m.use_backface_culling = False
    return m


# ---------------------------------------------------------------- fans, text, logos
def fan_rotor(name, r, hub, depth, blades, c, m, col, axis_sign=-1):
    """Axial fan rotor (mm) with its axis along Y; blades as twisted quads (merged mesh)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=hub * MM, radius2=hub * MM, depth=depth * MM,
                          matrix=mathutils.Matrix.Rotation(math.pi / 2, 4, 'X'))
    th = 0.9 * MM
    for i in range(blades):
        a0 = 2 * math.pi * i / blades
        pts = []
        for (rr, da, dy) in ((hub * 0.95, 0.0, -0.35), (r, 0.30, -0.45), (r, 0.95, 0.40), (hub * 0.95, 0.75, 0.35)):
            a = a0 + da
            pts.append((rr * MM * math.cos(a), dy * depth * MM * axis_sign, rr * MM * math.sin(a)))
        v0 = [bm.verts.new(p) for p in pts]
        v1 = [bm.verts.new((p[0], p[1] + th, p[2])) for p in pts]
        bm.faces.new(v0); bm.faces.new(list(reversed(v1)))
        for k in range(4):
            j = (k + 1) % 4
            bm.faces.new((v0[k], v0[j], v1[j], v1[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(m); col.objects.link(o)
    o.matrix_world = mathutils.Matrix.Translation(tuple(v * MM for v in c))
    me.uv_layers.new(name='UVMap')
    return o


def front_text(name, body, size, loc, m, g, vertical=False, font=r'C:\Windows\Fonts\arialbd.ttf', extrude=0.3, scale=(1, 1, 1)):
    """Text on a plane facing -Y. vertical=True reads top-to-bottom (rotated 90 deg clockwise)."""
    R = mathutils.Matrix.Rotation(math.pi / 2, 4, 'X')
    if vertical:
        R = mathutils.Matrix.Rotation(math.pi / 2, 4, 'Y') @ R
    t = H['text_mesh'](name, body, font, size * MM, m, _scratch(), None, (0, 0, 0), (0, 0, 0), extrude=extrude * MM, scale=scale)
    t.matrix_world = mathutils.Matrix.Translation(tuple(v * MM for v in loc)) @ R @ mathutils.Matrix.Diagonal((*scale, 1))
    return _grp(t, g)


def front_logo(name, s, loc, dark, light, g, vertical=False):
    """NVIDIA eye mark (sxm_lib.nv_logo) moved onto a plane facing -Y."""
    a, b = nv_logo(name, 0.0, 0.0, 0.0, s, dark, light, _scratch(), None)
    R = mathutils.Matrix.Rotation(math.pi / 2, 4, 'X')
    if vertical:
        R = mathutils.Matrix.Rotation(math.pi / 2, 4, 'Y') @ R
    M = mathutils.Matrix.Translation(tuple(v * MM for v in loc)) @ R
    for o in (a, b):
        o.matrix_world = M
        _grp(o, g)
    return a, b


# ---------------------------------------------------------------- modules, studio, render
def append_collection(path, name):
    c = bpy.data.collections.get(name)
    if c:
        return c
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = [name]
    return bpy.data.collections[name]


def instance_at(slot, coll, col):
    e = bpy.data.objects.new('PREVIEW_' + slot.name, None)
    e.instance_type = 'COLLECTION'; e.instance_collection = coll
    col.objects.link(e)
    e.parent = slot
    e.matrix_parent_inverse.identity()
    return e


def setup_studio(span=1.0):
    sc = bpy.context.scene
    sc.render.resolution_x = 1280; sc.render.resolution_y = 720; sc.render.resolution_percentage = 100
    fl = bpy.data.objects.get('Floor')
    if fl:
        fl.location = (0, 0.4, -0.0005); fl.scale = (6, 6, 1)
    L = {'Key': ((1.2 * span, -1.6 * span, 1.7 * span), 380 * span * span, 1.6 * span),
         'Fill': ((-1.8 * span, -0.9 * span, 0.8 * span), 110 * span * span, 2.0 * span),
         'Rim': ((0.9 * span, 2.2 * span, 1.4 * span), 320 * span * span, 1.5 * span)}
    for n, (loc, en, size) in L.items():
        o = bpy.data.objects.get(n)
        if not o:
            continue
        o.location = loc
        look_at(o, loc, (0, 0.45 * span, 0.08))
        o.data.energy = en
        if hasattr(o.data, 'size'):
            o.data.size = size
        if hasattr(o.data, 'shadow_soft_size'):
            o.data.shadow_soft_size = size * 0.3
    cam = bpy.data.objects['Camera']; sc.camera = cam
    cam.data.clip_start = 0.01; cam.data.clip_end = 50


def render(prefix, views, out_dir=r'C:\laragon\www\scaling-law\blender\renders'):
    """views: {name: (eye_m, target_m, lens, prep_fn_or_None)}"""
    sc = bpy.context.scene
    cam = bpy.data.objects['Camera']
    for vname, (eye, target, lens, prep) in views.items():
        undo = prep() if prep else None
        look_at(cam, eye, target); cam.data.lens = lens
        sc.render.filepath = out_dir + '\\' + prefix + '_' + vname + '.png'
        bpy.ops.render.render(write_still=True)
        if undo:
            undo()


def tri_count(objs):
    dg = bpy.context.evaluated_depsgraph_get(); n = 0
    for o in objs:
        if o.type == 'MESH':
            e = o.evaluated_get(dg); me = e.to_mesh(); me.calc_loop_triangles(); n += len(me.loop_triangles); e.to_mesh_clear()
    return n
