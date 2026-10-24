"""Shared builder for the air-cooled 8-GPU NVIDIA DGX systems (DGX H100/H200, DGX B200).

Loaded with exec() by srv_04_dgx_h100.py / srv_05_dgx_b200.py, which pass a CFG dict to build(cfg).
Both systems share the same architecture (NVIDIA user guides): front fan wall + U.2 drive row,
midplane, rear-serviceable GPU tray (top), motherboard/CPU tray (middle), 6x 3.3 kW PSUs (bottom).
Only the data in CFG differs (height, fan grid, tray split, GPU/NVSwitch layout, bezel style).

Conventions (brief phase 2, rack-mount equipment):
  metres, Z up; front panel plane XZ at y=0 facing -Y, depth toward +Y; origin bottom-front-centre.
  19" EIA: ears 482.6 mm, body 445 mm.  Rear face of trays/PSUs at y = BODY_D.
  SLOT_gpu_* = SXM module pose (module board top plane XY at z=0, heatsink +Z, module X = airflow +Y).
  Power paths: meshes with UV u = metres along path, v = 0..1 around the profile,
  custom props flow_u_start / flow_u_end (exported as glTF extras).
"""
import bpy, bmesh, math, os, random
import numpy as np
from mathutils import Vector, Matrix

BASE = r'C:\laragon\www\scaling-law\blender'
exec(open(BASE + r'\lib\hw.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']
exec(open(BASE + r'\scripts\sxm_lib.py', encoding='utf-8').read())   # nv_logo, boxes, cyls, mesh_from_quads

FONT_BLACK = r'C:\Windows\Fonts\ariblk.ttf'
FONT_BOLD = r'C:\Windows\Fonts\arialbd.ttf'
RENDER_DIR = BASE + r'\renders'

BODY_HW = 0.2225          # half body width (445 mm)
EAR_HW = 0.2413           # half ear width (482.6 mm)
BODY_D = 0.850            # chassis body depth; bezel (34 mm incl. stand-off) + rear handles (13 mm) = 897 mm spec
RX = Matrix.Rotation(math.pi / 2, 4, 'X')        # XY-plane art -> XZ plane facing -Y (front)
RXR = Matrix.Rotation(math.pi, 4, 'Z') @ RX      # XY-plane art -> XZ plane facing +Y (rear)

box, cyl, sa = H['box'], H['cyl'], H['slat_array']


# ----------------------------------------------------------------------------------------------
# materials and generated textures (packed into the .blend -> embedded in the .glb)
# ----------------------------------------------------------------------------------------------
def _img(name, w, h, rgba):
    img = bpy.data.images.get(name)
    if img:
        bpy.data.images.remove(img)
    img = bpy.data.images.new(name, w, h, alpha=True)
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    img.pack()
    return img


def hex_perf_image():
    """Tileable hex perforation: one lattice cell = 1 pitch wide x sqrt(3) pitches tall. Alpha 0 = hole."""
    W, Hh = 64, 111
    ys, xs = np.mgrid[0:Hh, 0:W]
    px = (xs + 0.5) / W
    py = (ys + 0.5) / Hh * math.sqrt(3)
    d = np.full(px.shape, 9.0)
    for cx, cy in ((0, 0), (1, 0), (0, math.sqrt(3)), (1, math.sqrt(3)), (0.5, math.sqrt(3) / 2)):
        dx, dy = px - cx, py - cy
        dd = np.maximum(np.abs(dx), np.maximum(np.abs(0.5 * dx + 0.866 * dy), np.abs(-0.5 * dx + 0.866 * dy)))
        d = np.minimum(d, dd)
    a = (d > 0.39).astype(np.float32)
    rgba = np.stack([np.ones_like(a), np.ones_like(a), np.ones_like(a), a], -1)
    return _img('DGX_HexPerf', W, Hh, rgba)


def foam_image():
    """Open-cell metal foam (DGX bezel): tileable Worley F2-F1 walls, champagne walls / dark brown pores."""
    N, C = 512, 28
    rng = np.random.default_rng(7)
    pts = rng.random((C, C, 2))
    ys, xs = np.mgrid[0:N, 0:N]
    gx = (xs + 0.5) / N * C; gy = (ys + 0.5) / N * C
    ix = np.floor(gx).astype(int); iy = np.floor(gy).astype(int)
    f1 = np.full(gx.shape, 9.0); f2 = np.full(gx.shape, 9.0)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx = ix + ox; cy = iy + oy
            p = pts[cy % C, cx % C]
            d = np.hypot(cx + p[..., 0] - gx, cy + p[..., 1] - gy)
            f2 = np.where(d < f1, f1, np.minimum(f2, d))
            f1 = np.minimum(f1, d)
    wall = np.clip(1.0 - (f2 - f1) / 0.34, 0, 1) ** 1.3
    depth = np.clip(f1 / 0.7, 0, 1)
    noise = rng.random(gx.shape) * 0.12
    base_dark = np.array([0.075, 0.050, 0.028]); base_wall = np.array([0.66, 0.56, 0.40])
    t = np.clip(wall * 1.1 + noise - depth * 0.25, 0, 1)[..., None]
    rgb = base_dark * (1 - t) + base_wall * t
    rgba = np.concatenate([rgb, np.ones((N, N, 1))], -1)
    return _img('DGX_MetalFoam', N, N, rgba)


def tex_mat(name, img, color=None, metal=0.8, rough=0.4, alpha_clip=False):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type not in ('BSDF_PRINCIPLED', 'OUTPUT_MATERIAL'):
            nt.nodes.remove(n)
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; t.extension = 'REPEAT'
    if color is not None:
        b.inputs['Base Color'].default_value = (*color, 1)
        m.diffuse_color = (*color, 1)
    else:
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if alpha_clip:
        r = nt.nodes.new('ShaderNodeMath'); r.operation = 'ROUND'
        nt.links.new(t.outputs['Alpha'], r.inputs[0])
        nt.links.new(r.outputs[0], b.inputs['Alpha'])
        try:
            m.surface_render_method = 'DITHERED'
        except Exception:
            pass
    return m


def materials():
    M = H['base_materials']()
    mt = H['mat']
    M.update({
        'champ':    mt('DGX_Champagne', (0.47, 0.40, 0.27), 0.85, 0.36),
        'champ_lt': mt('DGX_ChampagneSatin', (0.46, 0.40, 0.29), 0.6, 0.5),
        'champ_dk': mt('DGX_ChampagneDark', (0.30, 0.25, 0.16), 0.7, 0.45),
        'front':    mt('DGX_FrontBlack', (0.010, 0.010, 0.011), 0.35, 0.5, spec=0.3),
        'logo_dk':  mt('DGX_LogoGrey', (0.035, 0.035, 0.038), 0.3, 0.35),
        'silver':   mt('DGX_SilverSteel', (0.72, 0.73, 0.74), 0.9, 0.33),
        'galv':     mt('DGX_Galvanised', (0.42, 0.43, 0.44), 0.85, 0.45),
        'shroud':   mt('DGX_ShroudGrey', (0.30, 0.31, 0.32), 0.0, 0.62),
        'nvgreen':  mt('DGX_TorqueGreen', (0.40, 0.70, 0.02), 0.1, 0.4),
        'pcb_g':    mt('DGX_PCB_Green', (0.035, 0.12, 0.045), 0.0, 0.45),
        'pcb_dk':   mt('DGX_PCB_Dark', (0.012, 0.03, 0.02), 0.0, 0.5),
        'fins':     mt('DGX_FinAlu', (0.75, 0.76, 0.77), 1.0, 0.3),
        'copper':   mt('DGX_Copper', (0.90, 0.48, 0.30), 1.0, 0.3),
        'flow':     mt('DGX_PowerFlow', (0.80, 0.42, 0.16), 0.7, 0.32, emit=(1.0, 0.42, 0.08), emit_str=0.8),
        'densi':    mt('DGX_DensilinkBlue', (0.36, 0.55, 0.62), 0.0, 0.5),
        'usb':      mt('DGX_USB_Blue', (0.03, 0.12, 0.55), 0.0, 0.4),
        'vga':      mt('DGX_VGA_Blue', (0.12, 0.2, 0.65), 0.1, 0.35),
        'tick':     mt('DGX_TickWhite', (0.75, 0.75, 0.75), 0.0, 0.45),
        'led_g':    mt('DGX_LED_Green', (0.1, 0.9, 0.2), 0, 0.3, emit=(0.15, 1.0, 0.2), emit_str=6),
        'led_b':    mt('DGX_LED_Blue', (0.1, 0.3, 1.0), 0, 0.3, emit=(0.15, 0.35, 1.0), emit_str=6),
        'led_a':    mt('DGX_LED_Amber', (1.0, 0.5, 0.05), 0, 0.3, emit=(1.0, 0.45, 0.05), emit_str=3),
        'led_r':    mt('DGX_LED_Red7Seg', (0.25, 0.02, 0.02), 0, 0.4, emit=(1.0, 0.05, 0.03), emit_str=1.5),
    })
    hx = hex_perf_image()
    M['perf_silver'] = tex_mat('DGX_PerfSilver', hx, (0.72, 0.73, 0.74), 0.9, 0.33, alpha_clip=True)
    M['perf_black'] = tex_mat('DGX_PerfBlack', hx, (0.012, 0.012, 0.013), 0.2, 0.55, alpha_clip=True)
    M['foam'] = tex_mat('DGX_MetalFoam', foam_image(), None, 0.75, 0.55)
    return M


# ----------------------------------------------------------------------------------------------
# geometry helpers
# ----------------------------------------------------------------------------------------------
def box_uv(o, su, sv=None):
    """Box-project UVs in world metres (su x sv per tile). For hex perf: su = pitch, sv = pitch*sqrt(3)."""
    sv = sv or su
    me = o.data
    if not me.uv_layers:
        me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    mw = o.matrix_world
    for poly in me.polygons:
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            a, b = {0: (co.y, co.z), 1: (co.x, co.z), 2: (co.x, co.y)}[ax]
            uv[li].uv = (a / su, b / sv)
    return o


def perf(name, size, loc, M, col, parent, pitch=0.006, black=False):
    o = box(name, size, loc, M['perf_black' if black else 'perf_silver'], col, parent=parent)
    return box_uv(o, pitch, pitch * math.sqrt(3))


def bake(o, Mtx):
    o.data.transform(Mtx)
    o.data.update()
    return o


def join(name, objs):
    objs = [o for o in objs if o]
    for o in objs:
        H['apply_all'](o)
    with bpy.context.temp_override(active_object=objs[0], object=objs[0], selected_objects=objs, selected_editable_objects=objs):
        bpy.ops.object.join()
    o = objs[0]
    o.name = name; o.data.name = name
    # bake the object transform so the joined mesh lives in world space with origin (0,0,0)
    o.data.transform(o.matrix_basis); o.matrix_basis = Matrix.Identity(4)
    return o


def empty(name, loc, col, parent, rot=(0, 0, 0), kind='PLAIN_AXES', size=0.02):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind; e.empty_display_size = size
    col.objects.link(e); e.parent = parent
    e.location = loc; e.rotation_euler = rot
    return e


ROT_PY = (-math.pi / 2, 0, 0)    # empty +Z -> +Y (rear-facing socket)
ROT_NY = (math.pi / 2, 0, 0)     # empty +Z -> -Y (front-facing)


def led(name, size, loc, material, col, parent):
    return box(name, size, loc, material, col, parent=parent)


def logo_front(name, cx, cz, y, s, dark, light, col, parent, facing='front'):
    """NVIDIA eye mark (sxm_lib.nv_logo) moved from the XY plane to a vertical face."""
    a, b = nv_logo(name, 0, 0, 0, s, dark, light, col, parent)
    Mt = (Matrix.Translation((cx, y, cz)) @ (RX if facing == 'front' else RXR))
    for o in (a, b):
        bake(o, Mt)
    return a, b


def text_front(name, body, size, loc, material, col, parent, facing='front', spin=0.0, font=FONT_BLACK, extrude=0.0004):
    rot = (math.pi / 2, spin, 0) if facing == 'front' else (math.pi / 2, spin, math.pi)
    t = H['text_mesh'](name, body, font, size, material, col, parent, loc, (0, 0, 0), extrude=extrude)
    t.rotation_euler = rot
    return t


# ---- flow paths (power) ----------------------------------------------------------------------
def fillet(pts, r=0.02, n=6):
    """Polyline -> rounded polyline (quadratic Bezier at each interior corner)."""
    P = [Vector(p) for p in pts]
    out = [P[0]]
    for i in range(1, len(P) - 1):
        a, b, c = P[i - 1], P[i], P[i + 1]
        d1 = (b - a); d2 = (c - b)
        rr = min(r, d1.length * 0.45, d2.length * 0.45)
        p0 = b - d1.normalized() * rr; p2 = b + d2.normalized() * rr
        for k in range(n + 1):
            t = k / n
            out.append(p0 * (1 - t) ** 2 + b * 2 * t * (1 - t) + p2 * t * t)
    out.append(P[-1])
    clean = [out[0]]
    for p in out[1:]:
        if (p - clean[-1]).length > 1e-6:
            clean.append(p)
    return clean


def sweep(name, pts, profile, material, col, parent, width_axis=None, flow=True, caps=True):
    """Sweep a closed 2D profile [(w, t), ...] along pts. UV u = metres along path (continuous),
    v = 0..1 around the profile. width_axis fixes the profile's w direction (busbars); otherwise
    parallel transport is used (round cables)."""
    pts = [Vector(p) for p in pts]
    n = len(profile)
    L = [0.0]
    for i in range(1, len(pts)):
        L.append(L[-1] + (pts[i] - pts[i - 1]).length)
    # profile v coordinates by perimeter
    per = [0.0]
    for k in range(n):
        a = Vector(profile[k]); b = Vector(profile[(k + 1) % n]); per.append(per[-1] + (b - a).length)
    vs = [p / per[-1] for p in per]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    prev_w = None
    for i, p in enumerate(pts):
        if i == 0:
            t = (pts[1] - pts[0]).normalized()
        elif i == len(pts) - 1:
            t = (pts[-1] - pts[-2]).normalized()
        else:
            t = ((pts[i] - pts[i - 1]).normalized() + (pts[i + 1] - pts[i]).normalized()).normalized()
        if width_axis is not None:
            w = Vector(width_axis) - t * t.dot(Vector(width_axis))
            if w.length < 1e-6:
                w = prev_w
            w.normalize()
        else:
            if prev_w is None:
                ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
                w = t.cross(ref).normalized()
            else:
                w = (prev_w - t * t.dot(prev_w)).normalized()
        prev_w = w
        nrm = t.cross(w).normalized()
        rings.append([bm.verts.new(p + w * a + nrm * b) for a, b in profile])
    for i in range(len(pts) - 1):
        for k in range(n):
            j = (k + 1) % n
            f = bm.faces.new((rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]))
            uvs = ((L[i], vs[k]), (L[i], vs[k + 1]), (L[i + 1], vs[k + 1]), (L[i + 1], vs[k]))
            for lp, uv in zip(f.loops, uvs):
                lp[uvl].uv = uv
    if caps:
        for i, rev in ((0, True), (len(pts) - 1, False)):
            vv = rings[i][::-1] if rev else rings[i]
            f = bm.faces.new(vv)
            for lp in f.loops:
                lp[uvl].uv = (L[i], 0.0)
    o = _new_obj(name, bm, material, col, parent)
    if flow:
        o['flow_u_start'] = 0.0
        o['flow_u_end'] = round(L[-1], 5)
        o['flow_kind'] = 'power'
    return o


def rect_profile(w, t):
    return [(-w / 2, -t / 2), (w / 2, -t / 2), (w / 2, t / 2), (-w / 2, t / 2)]


def round_profile(r, n=8):
    return [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)]


# ----------------------------------------------------------------------------------------------
# components
# ----------------------------------------------------------------------------------------------
def rotor(name, r, M, col, parent, loc, blades=7):
    """Fan rotor, spin axis = local +Z (points out of the front, -Y in chassis)."""
    bm = bmesh.new()
    hub = r * 0.36
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=hub, radius2=hub * 0.92, depth=0.016,
                          matrix=Matrix.Translation((0, 0, 0)))
    span = r * 0.97 - hub * 0.95
    chord = 2 * math.pi * (hub + span * 0.6) / blades * 0.78
    for k in range(blades):
        a = 2 * math.pi * k / blades
        Mt = (Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation((hub * 0.95 + span / 2, 0, 0)) @
              Matrix.Rotation(0.62, 4, 'X') @ Matrix.Diagonal((span, chord, 0.0012, 1)))
        bmesh.ops.create_cube(bm, size=1, matrix=Mt)
    o = _new_obj(name, bm, M['plastic'], col, parent)
    o.location = loc; o.rotation_euler = (math.pi / 2, 0, 0)
    o['spin_axis'] = 'local +Z'
    return o


def fan_module(cfg, M, col, parent, rc, x, z0):
    """Hot-swap dual (front/rear contra-rotating) fan module: frame, honeycomb grille, handle, LED, rotor."""
    w, h, d = cfg['fan_w'], cfg['fan_h'], 0.080
    nm = 'FanModule_%d_%d' % rc
    zc = z0 + h / 2
    root = empty(nm, (x, 0, zc), col, parent, kind='CUBE', size=0.01)
    t = 0.0045
    parts = [
        box(nm + '_T', (w, d, t), (0, d / 2, h / 2 - t / 2), M['plastic'], col),
        box(nm + '_B', (w, d, t), (0, d / 2, -h / 2 + t / 2), M['plastic'], col),
        box(nm + '_L', (t, d, h), (-w / 2 + t / 2, d / 2, 0), M['plastic'], col),
        box(nm + '_R', (t, d, h), (w / 2 - t / 2, d / 2, 0), M['plastic'], col),
        box(nm + '_Back', (w - 2 * t, 0.002, h - 2 * t), (0, d - 0.001, 0), M['port'], col),
    ]
    g = perf(nm + '_Grille', (w - 2 * t, 0.0012, h - 2 * t), (0, 0.0025, 0), M, col, None, pitch=cfg['fan_hex'], black=True)
    hw = cfg['fan_handle_w']
    hm = M['champ'] if cfg['fan_handle'] == 'champ' else M['plastic']
    parts += [box(nm + '_Handle', (hw, 0.008, h * 0.86), (0, -0.003, -h * 0.03), hm, col, bevel=0.0015),
              box(nm + '_Latch', (hw * 0.9, 0.006, h * 0.08), (0, -0.002, h * 0.43), M['black_mt'], col)]
    if cfg['fan_ticks']:
        def ticks():
            for sx in (-1, 1):
                for sz in (-1, 1):
                    yield (sx * (w / 2 - 0.0105), -0.0003, sz * (h / 2 - 0.009)), (0.0018, 0.0008, 0.006)
        parts.append(sa(nm + '_Ticks', ticks, M['tick'], col))
    o = join(nm + '_Body', parts + [g])
    for c in (o,):
        c.parent = root; c.location = (0, 0, 0)
    # merged objects keep vertex positions in their own local space: re-centre on root
    rotor(nm + '_Rotor', min(w, h) * 0.46, M, col, root, (0, 0.035, 0))
    led('LED_fan_%d_%d' % rc, (0.003, 0.0015, 0.003), (w / 2 - 0.006, -0.0005, h / 2 - 0.0065), M['led_a'], col, root)
    return root


def u2_drive(name, x, z, w, h, M, col, parent):
    parts = [box(name + '_Body', (w, 0.12, h), (x, 0.06, z), M['black_st'], col),
             box(name + '_Face', (w, 0.004, h), (x, 0.0015, z), M['front'], col)]

    def slots():
        n = int(w / 0.0024)
        for i in range(n):
            yield (x - w * 0.42 + i * (w * 0.84 / (n - 1)), -0.0006, z + h * 0.08), (0.0011, 0.0012, h * 0.52)
    parts.append(sa(name + '_Vent', slots, M['port'], col))
    parts.append(box(name + '_Lever', (w * 0.9, 0.003, h * 0.18), (x, -0.0012, z - h * 0.36), M['black_mt'], col))
    o = join(name, parts)
    o.parent = parent
    return o


def psu(i, x, cfg, M, col, parent):
    """3.3 kW hot-swap PSU, rear face at y = BODY_D, C20 inlet, latch, handle, LED, SOCKET_power_in."""
    w, h, d = cfg['psu_w'], cfg['psu_h'], cfg['psu_d']
    z0 = 0.002
    nm = 'PSU_%d' % i
    root = empty(nm, (x, BODY_D, z0), col, parent, kind='CUBE', size=0.01)
    yb = 0.0  # local: rear face at y=0, body toward -Y
    parts = [box(nm + '_Body', (w, d, h), (0, -d / 2, h / 2), M['galv'], col)]
    g = perf(nm + '_Grille', (w - 0.004, 0.0012, h - 0.004), (0, 0.0012, h / 2), M, col, None, pitch=0.0035)
    parts.append(box(nm + '_GrilleBack', (w - 0.005, 0.001, h - 0.005), (0, 0.0002, h / 2), M['port'], col))
    # rear face (rear view: +X is on the viewer's left). Inlet on the +X half.
    ix = w * 0.13
    parts += [box(nm + '_InletBezel', (0.030, 0.004, 0.027), (ix, 0.002, h * 0.56), M['plastic'], col, bevel=0.0015),
              box(nm + '_InletHole', (0.024, 0.003, 0.020), (ix, 0.0036, h * 0.56), M['port'], col)]
    def pins():
        for dx, dz, sw, sh in ((-0.0065, 0.0025, 0.0015, 0.007), (0.0065, 0.0025, 0.0015, 0.007), (0.0, -0.0045, 0.007, 0.0015)):
            yield (ix + dx, 0.0028, h * 0.56 + dz), (sw, 0.004, sh)
    parts.append(sa(nm + '_Pins', pins, M['steel'], col))
    parts += [box(nm + '_Handle', (w * 0.72, 0.010, 0.006), (0.002, 0.007, 0.007), M['plastic'], col, bevel=0.0015),
              box(nm + '_Latch', (0.005, 0.006, 0.014), (-w / 2 + 0.006, 0.003, h * 0.55), M['nvgreen'], col, bevel=0.001)]
    for o in parts + [g]:
        o.parent = root
    led('LED_psu_%d' % i, (0.003, 0.002, 0.002), (w / 2 - 0.0055, 0.0012, h - 0.006), M['led_g'], col, root)
    empty('SOCKET_power_in_psu%d' % i, (ix, 0.004, h * 0.56), col, root, ROT_PY, 'SINGLE_ARROW', 0.04)
    empty('SOCKET_power_out_psu%d' % i, (0, -d, h / 2), col, root, ROT_NY, 'SINGLE_ARROW', 0.03)
    root['part'] = 'PSU 3.3 kW 200-240 VAC 16 A'
    return root


def heatsink(name, cx, cy, z0, sx, sy, sz, M, col, parent, fin_axis='y', fin_pitch=0.0022, base_t=0.004, mat=None):
    """Base plate + fins (one merged mesh). Fins run along fin_axis (airflow +Y)."""
    mat = mat or M['fins']
    base = box(name + '_Base', (sx, sy, base_t), (cx, cy, z0 + base_t / 2), M['copper'] if mat is M['fins'] else mat, col)

    def fins():
        if fin_axis == 'y':
            n = int(sx / fin_pitch)
            for k in range(n):
                yield (cx - sx / 2 + (k + 0.5) * sx / n, cy, z0 + base_t + (sz - base_t) / 2), (0.0005, sy, sz - base_t)
        else:
            n = int(sy / fin_pitch)
            for k in range(n):
                yield (cx, cy - sy / 2 + (k + 0.5) * sy / n, z0 + base_t + (sz - base_t) / 2), (sx, 0.0005, sz - base_t)
    f = sa(name + '_Fins', fins, mat, col)
    o = join(name, [base, f])
    o.parent = parent
    return o


# ----------------------------------------------------------------------------------------------
# main builder
# ----------------------------------------------------------------------------------------------
def build(cfg):
    root, col = H['new_card_scene'](cfg['root'])
    M = materials()
    HH = cfg['height']
    MID = cfg['mid_y']
    gz0, gz1 = cfg['gpu_tray_z']
    mz0, mz1 = cfg['mb_tray_z']
    root['model'] = cfg['model']; root['rack_units'] = cfg['units']; root['standard'] = 'EIA-310 19in, 1U = 44.45 mm'
    root['dimensions_mm'] = cfg['dims_note']

    # ---------------- chassis shell ----------------
    ch = empty('Chassis', (0, 0, 0), col, root)
    sh = [box('Chassis_Floor', (2 * BODY_HW, BODY_D - 0.004, 0.002), (0, BODY_D / 2 + 0.002, 0.001), M['galv'], col),
          box('Chassis_SideL', (0.0015, BODY_D, HH - 0.001), (-BODY_HW + 0.00075, BODY_D / 2, HH / 2), M['galv'], col),
          box('Chassis_SideR', (0.0015, BODY_D, HH - 0.001), (BODY_HW - 0.00075, BODY_D / 2, HH / 2), M['galv'], col)]
    for o in sh:
        o.parent = ch
    cover = box('Chassis_Cover', (2 * BODY_HW, BODY_D - 0.002, 0.0015), (0, BODY_D / 2 + 0.001, HH - 0.00075), M['galv'], col, parent=ch)
    # ears (champagne) with rack screws
    for s in (-1, 1):
        box('Ear_%s' % ('L' if s < 0 else 'R'), (EAR_HW - BODY_HW, 0.003, HH - 0.002), (s * (EAR_HW + BODY_HW) / 2, 0.0015, HH / 2), M['champ'], col, parent=ch)
        for k, z in enumerate(cfg['ear_screws']):
            ex = s * (EAR_HW + BODY_HW) / 2
            cyl('EarScrew_%s%d' % ('L' if s < 0 else 'R', k), 0.0042, 0.003, (ex, -0.0015, z), M['steel'], col, verts=20, rot=(math.pi / 2, 0, 0), parent=ch)
            cyl('EarScrewRing_%s%d' % ('L' if s < 0 else 'R', k), 0.0058, 0.0012, (ex, -0.0004, z), M['silver'], col, verts=20, rot=(math.pi / 2, 0, 0), parent=ch)
    # front controls on the right ear
    ex = (EAR_HW + BODY_HW) / 2
    zp, zu, zf = cfg['button_z']
    cyl('Btn_Power', 0.0032, 0.002, (ex, -0.001, zp), M['champ_dk'], col, verts=20, rot=(math.pi / 2, 0, 0), parent=ch)
    cyl('Btn_UID', 0.0032, 0.002, (ex, -0.001, zu), M['champ_dk'], col, verts=20, rot=(math.pi / 2, 0, 0), parent=ch)
    led('LED_power', (0.0016, 0.001, 0.0016), (ex, -0.0022, zp), M['led_g'], col, ch)
    led('LED_uid', (0.0016, 0.001, 0.0016), (ex, -0.0022, zu), M['led_b'], col, ch)
    led('LED_fault', (0.0026, 0.001, 0.0022), (ex, -0.0008, zf), M['led_a'], col, ch)

    # ---------------- front: fan wall ----------------
    fans = empty('FanWall', (0, 0, 0), col, root)
    cols, rows = cfg['fan_cols'], cfg['fan_rows']
    px, pz = cfg['fan_pitch_x'], cfg['fan_pitch_z']
    xs = [(c - (cols - 1) / 2) * px for c in range(cols)]
    for r in range(rows):
        for c in range(cols):
            fan_module(cfg, M, col, fans, (r + 1, c + 1), xs[c], cfg['fan_z0'] + r * pz)
    # black front frame strips around/between modules
    fz0 = cfg['fan_z0'] - 0.003; fz1 = cfg['fan_z0'] + (rows - 1) * pz + cfg['fan_h'] + 0.003

    def strips():
        ztop = min(fz1, HH)
        left_edge = xs[0] - cfg['fan_w'] / 2
        wl = left_edge + BODY_HW
        for sgn in (-1, 1):
            yield (sgn * (BODY_HW - wl / 2), 0.004, (fz0 + ztop) / 2), (wl, 0.008, ztop - fz0)
        for c in range(cols - 1):
            yield ((xs[c] + xs[c + 1]) / 2, 0.004, (fz0 + ztop) / 2), (px - cfg['fan_w'], 0.008, ztop - fz0)
        for r in range(rows - 1):
            zr = cfg['fan_z0'] + r * pz + cfg['fan_h'] + (pz - cfg['fan_h']) / 2
            yield (0, 0.004, zr), (2 * BODY_HW, 0.008, max(0.002, pz - cfg['fan_h']))
        if HH - fz1 > 0.0005:
            yield (0, 0.004, (fz1 + HH) / 2), (2 * BODY_HW, 0.008, HH - fz1)
        yield (0, 0.004, (fz0 + cfg['fan_z0']) / 2), (2 * BODY_HW, 0.008, cfg['fan_z0'] - fz0 + 0.001)
    sa('FrontFrame', strips, M['front'], col, ch)
    # bottom band (drives, console, optional logo band)
    box('FrontBand', (2 * BODY_HW, 0.004, fz0), (0, 0.006, fz0 / 2), M['front'], col, parent=ch)
    if cfg.get('logo_band'):
        lz0, lz1, lx, tx, lmm, tsize = cfg['logo_band']
        box('LogoBand', (2 * BODY_HW, 0.003, lz1 - lz0 + 0.008), (0, 0.0015, (lz0 + lz1) / 2), M['front'], col, parent=ch)
        logo_front('FrontLogo', lx, (lz0 + lz1) / 2, -0.0001, lmm, M['logo_dk'], M['front'], col, ch)
        text_front('FrontLogoText', 'nVIDIA', tsize, (tx, -0.0003, (lz0 + lz1) / 2), M['logo_dk'], col, ch)
    # drives + console
    dz0, dh = cfg['drive_z0'], cfg['drive_h']
    drv = empty('Drives', (0, 0, 0), col, root)
    k = 0
    for xd in cfg['drive_x']:
        for rr in range(2):
            u2_drive('U2_SED_%d' % k, xd, dz0 + dh / 2 + rr * (dh + 0.0015), cfg['drive_w'], dh, M, col, drv); k += 1
    cx0, cw = cfg['console']
    ccz = dz0 + dh + 0.0007
    con = [box('Console_Plate', (cw, 0.004, 2 * dh + 0.0015), (cx0, 0.0015, ccz), M['front'], col)]
    for j, ux in enumerate((-0.37, -0.17)):
        con.append(box('Console_USB%d' % j, (0.0135, 0.004, 0.0062), (cx0 + ux * cw, -0.0003, ccz - 0.006), M['steel'], col))
        con.append(box('Console_USBi%d' % j, (0.011, 0.004, 0.0022), (cx0 + ux * cw, -0.0012, ccz - 0.0068), M['usb'], col))
    con.append(box('Console_VGA', (0.018, 0.004, 0.009), (cx0 + 0.24 * cw, -0.0003, ccz - 0.006), M['steel'], col, bevel=0.002))
    con.append(box('Console_VGAi', (0.014, 0.004, 0.0055), (cx0 + 0.24 * cw, -0.0012, ccz - 0.006), M['vga'], col))
    con.append(cyl('Console_Temp', 0.0035, 0.003, (cx0 - 0.02 * cw, -0.0005, ccz - 0.006), M['plastic'], col, verts=16, rot=(math.pi / 2, 0, 0)))
    for sx in (-0.42, 0.42):
        con.append(cyl('Console_Screw%+.0f' % (sx * 10), 0.0027, 0.002, (cx0 + sx * cw, -0.0004, ccz + 0.008), M['black_st'], col, verts=12, rot=(math.pi / 2, 0, 0)))
    join('FrontConsole', con).parent = ch

    # ---------------- midplane ----------------
    mp = []
    for (z0, z1) in ((0.004, 0.022), (mz0 - 0.002, mz0 + 0.03), (gz0 - 0.003, gz0 + 0.045), (HH - 0.02, HH - 0.004)):
        mp.append(box('MP_band', (2 * BODY_HW - 0.006, 0.003, z1 - z0), (0, MID, (z0 + z1) / 2), M['pcb_g'], col))
    for xv in (-BODY_HW + 0.012, 0.0, BODY_HW - 0.012):
        mp.append(box('MP_post', (0.02, 0.003, HH - 0.008), (xv, MID, HH / 2), M['pcb_g'], col))

    def mpconn():
        for zc in (mz0 + 0.014, gz0 + 0.02):
            for xc in np.linspace(-0.18, 0.18, 8):
                yield (xc, MID + 0.006, zc), (0.03, 0.009, 0.014)
    mp.append(sa('MP_Connectors', mpconn, M['plastic'], col))
    join('Midplane', mp).parent = ch

    # ---------------- PSUs + PDB ----------------
    pw = empty('PowerShelf', (0, 0, 0), col, root)
    psu_x = [(i - 2.5) * cfg['psu_pitch'] for i in range(6)]
    for i, x in enumerate(psu_x):
        psu(i, x, cfg, M, col, pw)
        empty('SLOT_psu_%d' % i, (x, BODY_D, 0.002), col, root, kind='CUBE', size=0.01)
    ypdb = BODY_D - cfg['psu_d'] - 0.010
    pdb = [box('PDB_Board', (2 * BODY_HW - 0.01, 0.0025, 0.040), (0, ypdb, 0.023), M['pcb_g'], col)]

    def pdbconn():
        for x in psu_x:
            yield (x, ypdb + 0.006, 0.022), (0.04, 0.009, 0.026)
    pdb.append(sa('PDB_Conn', pdbconn, M['plastic'], col))
    join('PowerDistributionBoard', pdb).parent = pw

    # ---------------- flow-UV internal power paths ----------------
    pp = empty('PowerPaths', (0, 0, 0), col, root)
    bus = rect_profile(0.014, 0.004)
    yfront = MID - 0.016
    for i, x in enumerate(psu_x):
        zf = 0.010 + 0.0045 * (i % 2)
        pts = fillet([(x, BODY_D - cfg['psu_d'], 0.002 + cfg['psu_h'] / 2), (x, ypdb - 0.03, zf), (x, yfront, zf), (x, yfront, gz0 + 0.02), (x, MID - 0.002, gz0 + 0.02)], r=0.018)
        o = sweep('PWR_psu%d_to_gpu_tray' % i, pts, bus, M['flow'], col, pp, width_axis=(1, 0, 0))
        o['flow_from'] = 'SOCKET_power_out_psu%d' % i; o['flow_to'] = 'SOCKET_power_in_gpu_tray_%d' % i
        o['nominal_kw'] = 3.3
        empty('SOCKET_power_in_gpu_tray_%d' % i, (x, MID, gz0 + 0.02), col, root, (-math.pi / 2, 0, 0), 'SINGLE_ARROW', 0.03)
    pts = fillet([(0.0, ypdb - 0.002, 0.034), (0.0, yfront, 0.034), (0.0, yfront, mz0 + 0.014), (0.0, MID - 0.002, mz0 + 0.014)], r=0.015)
    o = sweep('PWR_pdb_to_cpu_tray', pts, bus, M['flow'], col, pp, width_axis=(1, 0, 0))
    o['flow_from'] = 'PowerDistributionBoard'; o['flow_to'] = 'SOCKET_power_in_cpu_tray'
    empty('SOCKET_power_out_pdb_cpu', (0.0, ypdb - 0.002, 0.034), col, root, ROT_NY, 'SINGLE_ARROW', 0.03)
    empty('SOCKET_power_in_cpu_tray', (0.0, MID, mz0 + 0.014), col, root, (-math.pi / 2, 0, 0), 'SINGLE_ARROW', 0.03)

    # ---------------- GPU tray ----------------
    gt = empty('GPU_Tray', (0, 0, 0), col, root, kind='CUBE', size=0.02)
    gt['slide_axis'] = '+Y'; gt['slide_travel_m'] = round(BODY_D - MID - 0.02, 3); gt['service'] = 'pulls out of the rear'
    empty('SLOT_tray_gpu', (0, BODY_D, gz0), col, root, kind='CUBE', size=0.02)
    ty0 = MID + 0.005
    tl = BODY_D - ty0
    tp = [box('GPU_Pan', (2 * BODY_HW - 0.006, tl, 0.002), (0, ty0 + tl / 2, gz0 + 0.001), M['galv'], col)]
    for s in (-1, 1):
        tp.append(box('GPU_Wall', (0.0015, tl, 0.03), (s * (BODY_HW - 0.004), ty0 + tl / 2, gz0 + 0.015), M['galv'], col))
    # front connector bank (mates with midplane)
    tp.append(box('GPU_FrontConn', (0.40, 0.012, 0.03), (0, ty0 + 0.006, gz0 + 0.02), M['plastic'], col))
    bb0, bb1 = cfg['baseboard_y']
    bbz = cfg['baseboard_z']
    tp.append(box('HGX_Baseboard', (2 * BODY_HW - 0.02, bb1 - bb0, 0.0024), (0, (bb0 + bb1) / 2, bbz - 0.0012), M['pcb_dk'], col))
    # standoffs/stiffener rails
    tp.append(box('HGX_Stiffener', (0.006, bb1 - bb0, 0.006), (0, (bb0 + bb1) / 2, bbz - 0.0044), M['steel'], col))
    gpu_tray_parts = tp
    # GPU sockets (mezzanine pairs) + SLOT empties
    mL, mW = cfg['module_lw']
    slot_z = bbz + cfg['mezz_h']
    k = 0
    mez = []
    for yc in cfg['gpu_y']:
        for xc in cfg['gpu_x']:
            e = empty('SLOT_gpu_%d' % k, (xc, yc, slot_z), col, gt, (0, 0, math.pi / 2), 'ARROWS', 0.05)
            e['module'] = cfg['module_root']; e['note'] = 'module X axis -> chassis +Y (airflow); board top plane at this z'
            mez.append(((xc, yc + mL * 0.24, bbz + 0.002), (mW * 0.55, 0.012, 0.004)))
            mez.append(((xc, yc - mL * 0.24, bbz + 0.002), (mW * 0.55, 0.012, 0.004)))
            mez.append(((xc, yc, bbz + 0.0004), (mW * 0.96, mL * 0.96, 0.0008)))
            k += 1
    gpu_tray_parts.append(H['slat_array']('HGX_SXM_Sockets', lambda: iter(mez), M['plastic'], col))
    # NVSwitch heatsinks
    for j, (x, y, sx, sy, sz) in enumerate(cfg['nvswitch']):
        heatsink('NVSwitch_HS_%d' % j, x, y, bbz, sx, sy, sz, M, col, gt, fin_pitch=0.0024)
    if cfg.get('nvswitch_cover'):
        x0, y0, sx, sy, sz = cfg['nvswitch_cover']
        cv = box('NVSwitch_Shroud', (sx, sy, sz), (x0, y0, bbz + sz / 2), M['black_dc'], col, bevel=0.003)
        cv.parent = gt
        logo_t = text_front('NVSwitch_ShroudText', 'nVIDIA', 0.040, (x0 + 0.035, y0, bbz + sz + 0.0002), M['logo_dk'], col, gt)
        logo_t.rotation_euler = (0, 0, 0)
        lg = nv_logo('NVSwitch_ShroudLogo', 0, 0, 0, 34, M['logo_dk'], M['black_dc'], col, gt)
        for o in lg:
            bake(o, Matrix.Translation((x0 - 0.085, y0, bbz + sz + 0.0001)))
    # side air shrouds
    for s in (-1, 1):
        gpu_tray_parts.append(box('GPU_SideShroud', (0.006, bb1 - bb0 - 0.02, cfg['shroud_h']), (s * (BODY_HW - 0.009), (bb0 + bb1) / 2, bbz + cfg['shroud_h'] / 2), M['shroud'], col))
    # baseboard power busbars (inside the tray), flow-UV
    for s, nm in ((-1, 'L'), (1, 'R')):
        xb = s * (BODY_HW - 0.022)
        pts = [(xb, ty0 + 0.012, gz0 + 0.02), (xb, ty0 + 0.04, bbz + 0.003), (xb, bb1 - 0.02, bbz + 0.003)]
        o = sweep('PWR_gpu_baseboard_%s' % nm, fillet(pts, 0.012), rect_profile(0.012, 0.003), M['flow'], col, gt, width_axis=(1, 0, 0))
        o['flow_from'] = 'SOCKET_power_in_gpu_tray_*'; o['flow_to'] = 'SXM modules'
        empty('SOCKET_power_out_gpu_bus_%s' % nm, (xb, bb1 - 0.02, bbz + 0.003), col, gt, ROT_PY, 'SINGLE_ARROW', 0.02)
    # rear panel: hex perforated, frame, baffle, thumbscrews, handle
    rp_y = BODY_D - 0.006
    pr = perf('GPU_RearPerf', (2 * BODY_HW - 0.012, 0.0012, gz1 - gz0 - 0.012), (0, rp_y, (gz0 + gz1) / 2), M, col, gt, pitch=0.0058)
    fr = []
    for (sx, sz, x, z) in ((2 * BODY_HW - 0.004, 0.006, 0, gz0 + 0.003), (2 * BODY_HW - 0.004, 0.006, 0, gz1 - 0.003),
                           (0.006, gz1 - gz0, -BODY_HW + 0.005, (gz0 + gz1) / 2), (0.006, gz1 - gz0, BODY_HW - 0.005, (gz0 + gz1) / 2)):
        fr.append(box('GPU_RearFrame', (sx, 0.012, sz), (x, rp_y, z), M['silver'], col))
    bz = cfg['gpu_rear_baffle']
    if bz:
        fr.append(box('GPU_RearBaffle', (0.33, 0.002, bz[1] - bz[0]), (0.0, rp_y - 0.012, (bz[0] + bz[1]) / 2), M['silver'], col))
    tsz = gz0 + cfg['gpu_thumb_dz']
    for sx in (0.014, -0.010):
        fr.append(cyl('GPU_Thumb', 0.0045, 0.008, (sx, BODY_D + 0.002, tsz), M['steel'], col, verts=16, rot=(math.pi / 2, 0, 0)))
        fr.append(cyl('GPU_ThumbRing', 0.0062, 0.003, (sx, BODY_D - 0.001, tsz), M['nvgreen'], col, verts=20, rot=(math.pi / 2, 0, 0)))
    fr.append(box('GPU_ThumbPlate', (0.05, 0.003, 0.03), (0.002, BODY_D - 0.003, tsz - 0.004), M['silver'], col))
    for s in (-1, 1):
        fr.append(box('GPU_Handle', (0.006, 0.014, 0.08), (s * (BODY_HW - 0.022), BODY_D + 0.007, gz0 + 0.06), M['silver'], col, bevel=0.002))
    gpu_tray_parts += fr
    join('GPU_Tray_Body', gpu_tray_parts).parent = gt

    # ---------------- motherboard / CPU tray ----------------
    mt = empty('CPU_Tray', (0, 0, 0), col, root, kind='CUBE', size=0.02)
    mt['slide_axis'] = '+Y'; mt['slide_travel_m'] = round(BODY_D - MID - 0.02, 3); mt['service'] = 'pulls out of the rear'
    empty('SLOT_tray_cpu', (0, BODY_D, mz0), col, root, kind='CUBE', size=0.02)
    L = BODY_D - ty0
    yr = lambda f: BODY_D - f * L          # fraction from the rear
    mp_ = [box('MB_Pan', (2 * BODY_HW - 0.006, L, 0.002), (0, ty0 + L / 2, mz0 + 0.001), M['galv'], col)]
    for s in (-1, 1):
        mp_.append(box('MB_Wall', (0.0015, L, 0.03), (s * (BODY_HW - 0.004), ty0 + L / 2, mz0 + 0.015), M['galv'], col))
    pcbz = mz0 + 0.008
    mp_.append(box('MB_PCB', (2 * BODY_HW - 0.02, yr(0.30) - ty0 - 0.02, 0.002), (0, (yr(0.30) + ty0 + 0.02) / 2, pcbz - 0.001), M['pcb_g'], col))
    mp_.append(box('MB_FrontConn', (0.40, 0.012, 0.022), (0, ty0 + 0.006, mz0 + 0.014), M['plastic'], col))
    # CPUs + DIMMs
    ycpu = yr(0.435)
    for j, xc in enumerate((0.112, -0.112)):
        heatsink('CPU%d_Heatsink' % j, xc, ycpu, pcbz, 0.09, 0.115, cfg['cpu_hs_h'], M, col, mt, fin_pitch=0.0021)
        empty('SLOT_cpu_%d' % j, (xc, ycpu, pcbz), col, mt, kind='CUBE', size=0.02)

    def dimms():
        for xc in (0.112, -0.112):
            for side in (-1, 1):
                for n in range(8):
                    x = xc + side * (0.050 + n * 0.0068)
                    yield (x, ycpu, pcbz + 0.0155), (0.0055, 0.133, 0.031)
    mp_.append(sa('DIMMs_32x', dimms, M['black_mt'], col))

    def dimm_sockets():
        for xc in (0.112, -0.112):
            for side in (-1, 1):
                for n in range(8):
                    yield (xc + side * (0.050 + n * 0.0068), ycpu, pcbz + 0.003), (0.0062, 0.145, 0.006)
    mp_.append(sa('DIMM_Sockets', dimm_sockets, M['plastic'], col))
    # PCH / retimer heatsinks
    for j, xc in enumerate((0.03, -0.03)):
        heatsink('PCH%d_HS' % j, xc, yr(0.60), pcbz, 0.035, 0.035, 0.022, M, col, mt, mat=M['fins'])
    # networking modules (each 4x ConnectX-7), air ducts
    for j, xc in enumerate((0.11, -0.105)):
        mp_.append(box('NetMod%d_PCB' % j, (0.15, 0.24 * L, 0.002), (xc, yr(0.80), pcbz + 0.012), M['pcb_g'], col))
        for a in (-1, 1):
            for b in (-1, 1):
                heatsink('NetMod%d_CX7_%d%d' % (j, (a + 1) // 2, (b + 1) // 2), xc + a * 0.036, yr(0.80) + b * 0.034, pcbz + 0.013, 0.064, 0.06, 0.03, M, col, mt, fin_pitch=0.0026)
    for f in (0.655, 0.955):
        mp_.append(box('MB_AirDuct', (2 * BODY_HW - 0.02, 0.03, mz1 - mz0 - 0.008), (0, yr(f), (mz0 + mz1) / 2 + 0.002), M['shroud'], col))
    # rear section: risers + OSFP cage block
    for s in (1, -1):
        for lvl, zz in enumerate((0.022, 0.058)):
            mp_.append(box('Riser_Card', (0.14, 0.17, 0.0016), (s * 0.142, BODY_D - 0.095, mz0 + zz), M['pcb_g'], col))
            mp_.append(box('Riser_CardChip', (0.04, 0.04, 0.004), (s * 0.13, BODY_D - 0.11, mz0 + zz + 0.0028), M['fins'], col))
    mp_.append(box('OSFP_CageBlock', (0.12, 0.12, 0.03), (0.0, BODY_D - 0.07, mz0 + 0.048), M['steel'], col))
    # Densilink cables (blue) from OSFP block to the network modules
    for j, (x0, x1) in enumerate(((0.03, 0.08), (0.01, 0.13), (-0.01, -0.08), (-0.03, -0.13))):
        pts = fillet([(x0, BODY_D - 0.13, mz0 + 0.04), (x0, yr(0.62), mz0 + 0.04), (x1, yr(0.66) - 0.02, mz0 + 0.035), (x1, yr(0.70), mz0 + 0.03)], 0.03)
        sweep('Densilink_%d' % j, pts, round_profile(0.004, 8), M['densi'], col, mt, flow=False)
    # rear I/O panel (layout measured from the DGX H100 user-guide rear port image, mm from tray bottom)
    rearz = lambda zr: mz0 + 0.002 + zr * 0.001
    ry = BODY_D - 0.002
    face = [box('MB_RearFace', (2 * BODY_HW - 0.006, 0.003, mz1 - mz0 - 0.002), (0, ry, (mz0 + mz1) / 2), M['silver'], col)]
    perfs = []
    # PCIe slot brackets (slot 3/1 left block = +X, slot 4/2 right block = -X)
    for s, xa, xb in ((1, 0.064, 0.2146), (-1, -0.0575, -0.2104)):
        for z0r, z1r in ((64, 81), (42, 62), (23, 40)):
            sz_ = (abs(xb - xa) - 0.03, 0.001, (z1r - z0r) * 0.001 - 0.002); lc = ((xa + xb) / 2 + s * 0.012, ry + 0.0025, rearz((z0r + z1r) / 2))
            perfs.append(perf('MB_SlotPerf', sz_, lc, M, col, None, pitch=0.003))
            perfs.append(box('MB_SlotPerfBack', (sz_[0] - 0.001, 0.001, sz_[2] - 0.001), (lc[0], ry + 0.0013, lc[2]), M['port'], col))
    perfs.append(perf('MB_CenterPerf', (0.11, 0.001, 0.019), (0.0033, ry + 0.0025, rearz(71.5)), M, col, None, pitch=0.0045))
    perfs.append(box('MB_CenterPerfBack', (0.109, 0.001, 0.018), (0.0033, ry + 0.0013, rearz(71.5)), M['port'], col))
    ports = []
    netsock = []

    def cage(name, x, zr, w, h, sock):
        ports.append(box(name, (w, 0.010, h), (x, ry + 0.004, rearz(zr)), M['steel'], col))
        ports.append(box(name + '_Hole', (w - 0.002, 0.004, h - 0.0025), (x, ry + 0.0075, rearz(zr)), M['port'], col))
        netsock.append((sock, (x, ry + 0.010, rearz(zr))))
    for sl, zr, xp2, xp1 in (('slot3', 72.5, 0.1615, 0.1415), ('slot1', 52, 0.1615, 0.1415), ('slot2', 52, -0.0990, -0.1190)):
        cage('QSFP_%s_p2' % sl, xp2, zr, 0.0185, 0.0095, 'SOCKET_net_%s_p2' % sl)
        cage('QSFP_%s_p1' % sl, xp1, zr, 0.0185, 0.0095, 'SOCKET_net_%s_p1' % sl)
    if cfg.get('slot1_rj45'):
        ports.append(box('RJ45_slot1', (0.016, 0.012, 0.0135), (0.104, ry + 0.004, rearz(52)), M['steel'], col))
        netsock.append(('SOCKET_net_slot1_rj45', (0.104, ry + 0.010, rearz(52))))
    for j, xo in enumerate((0.0398, 0.0151, -0.0124, -0.0374)):
        cage('OSFP%d' % (j + 1), xo, 48, 0.0235, 0.0135, 'SOCKET_net_osfp%d' % (j + 1))
    for nm, xo in (('BMC', 0.0525), ('LAN', 0.0324)):
        ports.append(box('RJ45_' + nm, (0.0165, 0.012, 0.0145), (xo, ry + 0.004, rearz(20.5)), M['steel'], col))
        ports.append(box('RJ45_%s_Hole' % nm, (0.012, 0.004, 0.010), (xo, ry + 0.008, rearz(20)), M['port'], col))
        netsock.append(('SOCKET_net_' + nm.lower(), (xo, ry + 0.010, rearz(20.5))))
    for nm, xo in (('USB0', 0.1590), ('USB1', 0.1400)):
        ports.append(box('Rear_' + nm, (0.0135, 0.006, 0.006), (xo, ry + 0.003, rearz(14)), M['steel'], col))
    ports.append(box('Rear_VGA', (0.018, 0.006, 0.0095), (0.1100, ry + 0.003, rearz(14)), M['vga'], col, bevel=0.002))
    ports.append(box('Rear_COM', (0.018, 0.006, 0.0095), (-0.128, ry + 0.003, rearz(15)), M['plastic'], col, bevel=0.002))
    ports.append(cyl('Rear_UID', 0.0035, 0.004, (0.0131, ry + 0.003, rearz(17)), M['plastic'], col, verts=16, rot=(math.pi / 2, 0, 0)))
    ports.append(cyl('Rear_PWR', 0.0026, 0.004, (-0.0073, ry + 0.003, rearz(16)), M['plastic'], col, verts=16, rot=(math.pi / 2, 0, 0)))
    ports.append(cyl('Rear_BMCRST', 0.0022, 0.004, (-0.017, ry + 0.003, rearz(16)), M['plastic'], col, verts=16, rot=(math.pi / 2, 0, 0)))
    for xo in (0.012, -0.010):
        ports.append(cyl('MB_Thumb', 0.004, 0.008, (xo, ry + 0.005, rearz(30)), M['steel'], col, verts=16, rot=(math.pi / 2, 0, 0)))
        ports.append(cyl('MB_ThumbRing', 0.0058, 0.003, (xo, ry + 0.002, rearz(30)), M['nvgreen'], col, verts=20, rot=(math.pi / 2, 0, 0)))
    for xo in (0.0778, -0.192):
        for zr in (78, 55):
            ports.append(cyl('Slot_Screw', 0.0035, 0.005, (xo, ry + 0.003, rearz(zr)), M['steel'], col, verts=12, rot=(math.pi / 2, 0, 0)))
    join('CPU_Tray_Body', mp_ + face + perfs + ports).parent = mt
    led('LED_code_display', (0.034, 0.002, 0.014), (-0.040, ry + 0.003, rearz(19.5)), M['led_r'], col, mt)
    led('LED_rear_uid', (0.004, 0.001, 0.004), (0.0131, ry + 0.0055, rearz(17)), M['led_b'], col, mt)
    led('LED_rear_power', (0.003, 0.001, 0.003), (-0.0073, ry + 0.0055, rearz(16)), M['led_g'], col, mt)
    for nm, loc in netsock:
        e = empty(nm, loc, col, mt, ROT_PY, 'SINGLE_ARROW', 0.02)
        e['kind'] = 'network'

    # ---------------- bezel (separate, removable) ----------------
    bz = empty('Bezel', (0, -0.008, 0), col, root, kind='CUBE', size=0.02)
    bz['service'] = 'removable front bezel (pull straight out along -Y)'
    build_bezel(cfg, M, col, bz)

    return root, col, M


def build_bezel(cfg, M, col, bz):
    HH = cfg['height']
    bw = 2 * (BODY_HW + 0.0005)
    z0, z1 = 0.004, HH - 0.004
    d = 0.026
    parts = []
    if cfg['bezel'] == 'h100':
        # champagne frame + metal-foam field + satin logo pad on the left (vertical NVIDIA wordmark)
        parts.append(box('Bezel_FrameT', (bw, d, 0.007), (0, -d / 2, z1 - 0.0035), M['champ'], col))
        parts.append(box('Bezel_FrameB', (bw, d, 0.007), (0, -d / 2, z0 + 0.0035), M['champ'], col))
        parts.append(box('Bezel_FrameL', (0.011, d, z1 - z0), (-bw / 2 + 0.0055, -d / 2, (z0 + z1) / 2), M['champ'], col))
        parts.append(box('Bezel_FrameR', (0.011, d, z1 - z0), (bw / 2 - 0.0055, -d / 2, (z0 + z1) / 2), M['champ'], col))
        parts.append(box('Bezel_Back', (bw - 0.02, 0.003, z1 - z0 - 0.012), (0, -0.0035, (z0 + z1) / 2), M['champ_dk'], col))
        foam = box('Bezel_Foam', (bw - 0.022, 0.010, z1 - z0 - 0.014), (0, -d + 0.006, (z0 + z1) / 2), M['foam'], col)
        box_uv(foam, 0.07)
        parts.append(foam)
        pad_x0, pad_x1 = -0.200, -0.129
        pad = box('Bezel_LogoPad', (pad_x1 - pad_x0, 0.004, z1 - z0 - 0.022), ((pad_x0 + pad_x1) / 2, -d + 0.0005, (z0 + z1) / 2), M['champ_lt'], col, bevel=0.012, segs=4)
        parts.append(pad)
        lx = (pad_x0 + pad_x1) / 2
        logo_front('Bezel_Logo', lx, HH * 0.853, -d - 0.0018, 21, M['champ_dk'], M['champ_lt'], col, None)
        t = text_front('Bezel_LogoText', 'nVIDIA', 0.022, (lx, -d - 0.0016, HH * 0.70), M['champ_dk'], col, None, spin=0)
        t.rotation_euler = (math.pi / 2, math.pi / 2, 0)
    else:
        # B200: one rounded metal-foam field, frame only at the edges, NVIDIA mark lower-left
        parts.append(box('Bezel_Back', (bw, 0.004, z1 - z0), (0, -0.002, (z0 + z1) / 2), M['champ_dk'], col))
        parts.append(box('Bezel_Rim', (bw, d - 0.006, z1 - z0), (0, -0.004 - (d - 0.006) / 2, (z0 + z1) / 2), M['champ'], col, bevel=0.014, segs=4))
        foam = box('Bezel_Foam', (bw - 0.010, 0.004, z1 - z0 - 0.010), (0, -d + 0.0015, (z0 + z1) / 2), M['foam'], col, bevel=0.012, segs=4)
        H['apply_all'](foam)
        box_uv(foam, 0.07)
        parts.append(foam)
        lx, lz = -0.170, 0.066
        logo_front('Bezel_Logo', lx, lz, -d - 0.0006, 26, M['champ_lt'], M['champ_dk'], col, None)
        text_front('Bezel_LogoText', 'nVIDIA', 0.030, (lx + 0.072, -d - 0.0008, lz - 0.001), M['champ_lt'], col, None)
    b = join('Bezel_Body', parts)
    b.parent = bz
    for o in list(bpy.data.objects):
        if o.name.startswith('Bezel_Logo') and o.parent is None:
            o.parent = bz
    return b


# ----------------------------------------------------------------------------------------------
# preview assembly, render, export
# ----------------------------------------------------------------------------------------------
def append_modules(cfg, root):
    path, name = cfg['module_blend'], cfg['module_root']
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c == name]
    mc = dst.collections[0]
    mc.name = 'PREVIEW_' + name
    inst = []
    for o in root.children_recursive:
        if o.name.startswith('SLOT_gpu_'):
            e = bpy.data.objects.new('PREVIEW_' + o.name, None)
            e.instance_type = 'COLLECTION'; e.instance_collection = mc
            bpy.context.scene.collection.objects.link(e)
            e.parent = o
            inst.append(e)
    return mc, inst


def remove_modules(mc, inst):
    for e in inst:
        bpy.data.objects.remove(e, do_unlink=True)
    for o in list(mc.all_objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(mc)
    for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.images):
        for x in list(blk):
            if x.users == 0:
                blk.remove(x)


def studio(cfg):
    sc = bpy.context.scene
    for n in ('Key', 'Fill', 'Rim'):
        o = bpy.data.objects.get(n)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
    f = bpy.data.objects.get('Floor')
    if f:
        f.hide_render = True; f.hide_viewport = True
    st = H['coll']('Studio')
    if not bpy.data.objects.get('StudioFloor'):
        bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0.4, -0.0005))
        p = bpy.context.active_object; p.name = 'StudioFloor'
        p.data.materials.append(H['mat']('DGX_StudioFloor', (0.06, 0.062, 0.065), 0.0, 0.6))
        for c in list(p.users_collection):
            c.objects.unlink(p)
        st.objects.link(p)

    def area(name, loc, target, energy, size, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.size = size; ld.color = color
        o = bpy.data.objects.new(name, ld); st.objects.link(o)
        o.location = loc
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return o
    c = (0, 0.45, cfg['height'] / 2)
    area('DGX_Key', (-1.4, -1.6, 1.8), c, 110, 1.6)
    area('DGX_Fill', (1.7, -0.9, 0.9), c, 40, 2.0, (0.92, 0.95, 1.0))
    area('DGX_Rim', (1.0, 2.4, 1.5), c, 90, 1.6)
    area('DGX_Top', (0, 0.45, 1.8), c, 45, 1.2)
    area('DGX_Back2', (-1.3, 2.2, 0.8), c, 35, 1.4)
    w = sc.world
    if w and w.use_nodes:
        bg = next((n for n in w.node_tree.nodes if n.type == 'BACKGROUND'), None)
        if bg:
            bg.inputs['Strength'].default_value = 0.45
    sc.render.resolution_x = 1280; sc.render.resolution_y = 720; sc.render.resolution_percentage = 100
    cam = bpy.data.objects['Camera']; sc.camera = cam
    cam.data.clip_start = 0.01; cam.data.clip_end = 30


def render(prefix, name, eye, target, lens=40):
    sc = bpy.context.scene
    cam = sc.camera
    cam.location = eye
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    sc.render.filepath = RENDER_DIR + '\\' + prefix + '_' + name + '.png'
    bpy.ops.render.render(write_still=True)


def set_hidden(objs, hidden):
    for o in objs:
        o.hide_render = hidden
        for c in o.children_recursive:
            c.hide_render = hidden


def export(root_name, path):
    root = bpy.data.objects[root_name]
    objs = [root] + list(root.children_recursive)
    for o in objs:
        o.hide_render = False; o.hide_viewport = False; o.hide_set(False)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    dg = bpy.context.evaluated_depsgraph_get(); tris = 0
    for o in objs:
        if o.type == 'MESH':
            e = o.evaluated_get(dg); m = e.to_mesh(); m.calc_loop_triangles(); tris += len(m.loop_triangles); e.to_mesh_clear()
    # same as H['export_glb'] plus export_extras so flow_u_* / slot metadata reach the game
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_apply=True, export_extras=True)
    return tris


def run(cfg, views):
    root, col, M = build(cfg)
    studio(cfg)
    mc, inst = append_modules(cfg, root)
    ob = bpy.data.objects
    gt, mt, bz, cover = ob['GPU_Tray'], ob['CPU_Tray'], ob['Bezel'], ob['Chassis_Cover']
    sideL = ob['Chassis_SideL']
    pre = cfg['render_prefix']
    only = os.environ.get('DGX_VIEWS')
    for v in views:
        if only and v['name'] not in only.split(','):
            continue
        set_hidden([bz], v.get('no_bezel', False))
        set_hidden([cover], v.get('no_cover', False))
        set_hidden([sideL], v.get('no_side', False))
        set_hidden([mt], v.get('no_cpu_tray', False))
        gt.location.y = v.get('gpu_out', 0.0); mt.location.y = v.get('cpu_out', 0.0)
        render(pre, v['name'], v['eye'], v['target'], v.get('lens', 40))
    gt.location.y = 0; mt.location.y = 0
    set_hidden([bz, cover, sideL, mt], False)
    remove_modules(mc, inst)
    tris = export(cfg['root'], cfg['glb'])
    bpy.ops.wm.save_as_mainfile(filepath=cfg['blend'])
    sz = os.path.getsize(cfg['glb'])
    names = sorted(o.name for o in root.children_recursive if o.type == 'EMPTY' and (o.name.startswith('SLOT_') or o.name.startswith('SOCKET_')))
    print('DGX_REPORT', cfg['root'], 'tris', tris, 'glb_bytes', sz, 'objects', len(root.children_recursive))
    print('DGX_EMPTIES', ' '.join(names))
    return tris


def default_views(cfg):
    HH = cfg['height']; c = HH / 2
    return [
        dict(name='front_bezel', eye=(-0.95, -1.25, 0.62), target=(0, 0.25, c)),
        dict(name='front', eye=(-0.95, -1.25, 0.62), target=(0, 0.25, c), no_bezel=True),
        dict(name='front_ortho', eye=(0, -2.2, c), target=(0, 0, c), lens=85, no_bezel=True),
        dict(name='rear', eye=(0.95, 2.25, 0.62), target=(0, 0.6, c)),
        dict(name='rear_ortho', eye=(0, 3.0, c), target=(0, 0.85, c), lens=85),
        dict(name='top_cutaway', eye=(-0.55, -0.25, 1.35), target=(0, 0.45, c), lens=32, no_cover=True),
        dict(name='trays_out', eye=(1.1, 2.3, 1.0), target=(0, 0.95, c), lens=35, gpu_out=0.45, cpu_out=0.25),
        dict(name='power_paths', eye=(-1.35, 0.25, 0.45), target=(0, 0.45, HH * 0.35), lens=35,
             no_side=True, no_cpu_tray=True, no_cover=True),
    ]
