"""Shared helpers for the garage-stage rigs (rig_01_tower_2017, rig_02_open_frame).

Load after hw.py:
    exec(open(r'C:\\laragon\\www\\scaling-law\\blender\\lib\\hw.py', encoding='utf-8').read())
    exec(open(r'C:\\laragon\\www\\scaling-law\\blender\\scripts\\garage_lib.py', encoding='utf-8').read())

Parts are built in their own local frame under a sub-empty (`frame_empty`), so the same
motherboard / PSU / fan code serves a vertical tower and a flat open frame.
  - motherboard local: X = rear(I/O) edge -> front edge (0..0.244), Y = bottom edge -> top edge
    (0..0.305), Z = component side, PCB top surface at z=0 (ATX 12" x 9.6").
  - PSU local: X across the 150 mm width (centred), Y = AC face (y=0, facing -Y) -> modular face,
    Z = height (0..0.086), fan on the bottom (z=0, facing -Z).
  - fan local: axis along +Z (airflow), centred on the origin.
Flow cables: tube meshes with UV u = metres along the path (continuous), v = 0..1 around.
"""
import bpy, bmesh, math, mathutils

H = bpy.app.driver_namespace['HW']
V = mathutils.Vector
GPU_LIB = r'C:\laragon\www\scaling-law\blender\gpu_01_gtx1080ti_fe.blend'
GPU_ROOT = 'GTX1080Ti_FE'
# phase-1 card facts read from gpu_01_gtx1080ti_fe.blend (card frame: X length, Y thickness, Z height)
CARD_POWER_IN = V((0.236, -0.0095, 0.1105))   # 8+6-pin on the top edge
CARD_FINGER_BOTTOM = -0.0085                  # PCIe_Edge / gold pads bottom
CARD_PCB_MID = 0.0008                         # PCB y in [0, 0.0016]
CARD_LEN = 0.266


# ---------------------------------------------------------------- transforms
def basis(xa, ya):
    """3x3 matrix whose columns are the world directions of local X and Y (Z = X x Y)."""
    x = V(xa).normalized(); y = V(ya).normalized(); z = x.cross(y)
    return mathutils.Matrix((x, y, z)).transposed()


def frame_empty(name, col, parent, loc, rot3=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'PLAIN_AXES'; e.empty_display_size = 0.03
    col.objects.link(e)
    e.parent = parent
    m = (rot3 or mathutils.Matrix.Identity(3)).to_4x4()
    m.translation = V(loc)
    e.matrix_basis = m
    return e


def marker(name, col, parent, loc, rot3=None, kind='ARROWS', size=0.03):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind; e.empty_display_size = size
    col.objects.link(e)
    e.parent = parent
    m = (rot3 or mathutils.Matrix.Identity(3)).to_4x4()
    m.translation = V(loc)
    e.matrix_basis = m
    return e


def text_at(name, body, font, size, material, col, parent, loc, xdir, ydir, extrude=0.0003):
    """Text whose reading direction is xdir and whose up is ydir (normal = xdir x ydir)."""
    rot = basis(xdir, ydir).to_euler()
    return H['text_mesh'](name, body, font, size, material, col, parent, loc, rot, extrude=extrude)


# ---------------------------------------------------------------- merged primitive arrays
def _bm_obj(name, bm, material, col, parent):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(material)
    col.objects.link(o); o.parent = parent
    return o


def cyl_array(name, items, material, col, parent, segs=16):
    """items: (centre, radius, depth, axis 'x'|'y'|'z') -> one merged mesh."""
    bm = bmesh.new()
    rots = {'z': mathutils.Matrix.Identity(4),
            'x': mathutils.Matrix.Rotation(math.pi / 2, 4, 'Y'),
            'y': mathutils.Matrix.Rotation(math.pi / 2, 4, 'X')}
    for c, r, d, ax in items:
        m = mathutils.Matrix.Translation(c) @ rots[ax]
        bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=d, matrix=m)
    return _bm_obj(name, bm, material, col, parent)


def box_array(name, items, material, col, parent):
    """items: (centre, size) -> one merged mesh (same as hw.slat_array but from a list)."""
    return H['slat_array'](name, lambda: iter(items), material, col, parent)


# ---------------------------------------------------------------- flow cables
def _catmull(pts, step=0.006):
    P = [V(p) for p in pts]
    P = [P[0] + (P[0] - P[1]) * 0.01] + P + [P[-1] + (P[-1] - P[-2]) * 0.01]
    out = [P[1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        n = max(2, int((p2 - p1).length / step))
        for k in range(1, n + 1):
            t = k / n; t2 = t * t; t3 = t2 * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return out


def flow_cable(name, pts, radius, material, col, parent, sides=8, step=0.006, flat=1.0):
    """Smooth tube through control points pts (parent-local). UV u = metres along path, v = 0..1.
    flat < 1 squashes the section (ribbon-ish bundles)."""
    path = _catmull(pts, step)
    # tangents + parallel-transport frames
    T = []
    for i in range(len(path)):
        a = path[max(i - 1, 0)]; b = path[min(i + 1, len(path) - 1)]
        T.append((b - a).normalized())
    up = V((0, 0, 1)) if abs(T[0].z) < 0.9 else V((1, 0, 0))
    N = [(up - T[0] * up.dot(T[0])).normalized()]
    for i in range(1, len(path)):
        n = N[-1] - T[i] * N[-1].dot(T[i])
        if n.length < 1e-6:
            n = N[-1]
        N.append(n.normalized())
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rings = []; L = [0.0]
    for i in range(1, len(path)):
        L.append(L[-1] + (path[i] - path[i - 1]).length)
    for i, p in enumerate(path):
        b = T[i].cross(N[i])
        ring = []
        for k in range(sides + 1):
            a = 2 * math.pi * (k % sides) / sides
            ring.append(bm.verts.new(p + N[i] * (math.cos(a) * radius) + b * (math.sin(a) * radius * flat)))
        rings.append(ring)
    for i in range(len(path) - 1):
        for k in range(sides):
            f = bm.faces.new((rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k]))
            for lp, (u, v) in zip(f.loops, ((L[i], k / sides), (L[i], (k + 1) / sides),
                                            (L[i + 1], (k + 1) / sides), (L[i + 1], k / sides))):
                lp[uvl].uv = (u, v)
    for ring, u in ((rings[0], L[0]), (rings[-1], L[-1])):
        vs = ring[:sides]
        f = bm.faces.new(vs if ring is rings[-1] else list(reversed(vs)))
        for lp in f.loops:
            lp[uvl].uv = (u, 0.5)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me); me.materials.append(material)
    col.objects.link(o); o.parent = parent
    o['flow_u_start'] = 0.0
    o['flow_u_end'] = round(L[-1], 5)
    o['flow_kind'] = 'power'
    return o


# ---------------------------------------------------------------- fan
def fan(name, col, parent, M, size=0.120, depth=0.025, blades=7, loc=(0, 0, 0), rot3=None,
        frame_mat=None, blade_mat=None, hub_label=None):
    """Axial case fan, airflow along local +Z. Returns the fan empty."""
    root = frame_empty(name, col, parent, loc, rot3)
    fm = frame_mat or M['plastic']; bmat = blade_mat or M['plastic']
    s = size / 2; r_in = s * 0.94 - 0.002; n = 48
    outer = []
    for k in range(n):
        a = 2 * math.pi * k / n + math.pi / 4
        c, si = math.cos(a), math.sin(a); m = max(abs(c), abs(si))
        outer.append((s * c / m, s * si / m))
    inner = [(r_in * math.cos(2 * math.pi * k / n + math.pi / 4), r_in * math.sin(2 * math.pi * k / n + math.pi / 4)) for k in range(n)]
    H['ring'](name + '_Frame', outer, inner, 'xy', -depth / 2, depth, fm, col, parent=root)
    r_hub = size * 0.19
    H['cyl'](name + '_Hub', r_hub, depth * 0.78, (0, 0, 0.0), M['plastic'], col, verts=32, parent=root)
    # stator struts on the outlet side: two diagonal bars
    for k, ang in enumerate((math.pi / 4, -math.pi / 4)):
        b = H['box'](name + f'_Strut{k}', (2 * r_in, 0.004, 0.003), (0, 0, depth / 2 - 0.0025), fm, col, parent=root)
        b.rotation_euler = (0, 0, ang)
    # blades: swept, pitched quad patches, solidified
    bm = bmesh.new()
    rt = r_in - 0.0015; nr, nc = 4, 3
    for bi in range(blades):
        a0 = 2 * math.pi * bi / blades
        grid = []
        for i in range(nr + 1):
            r = r_hub + (rt - r_hub) * i / nr
            span = (2 * math.pi / blades) * (0.42 + 0.18 * i / nr)
            sweep = 0.35 * i / nr
            row = []
            for j in range(nc + 1):
                c = -1 + 2 * j / nc
                a = a0 + sweep + c * span / 2
                z = c * depth * 0.30
                row.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
            grid.append(row)
        for i in range(nr):
            for j in range(nc):
                bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    bl = _bm_obj(name + '_Blades', bm, bmat, col, root)
    so = bl.modifiers.new('Solid', 'SOLIDIFY'); so.thickness = 0.0012
    H['apply_all'](bl)
    return root


# ---------------------------------------------------------------- PSU
def psu(name, col, parent, M, loc, rot3, length=0.160, brand='EVGA', model='SUPERNOVA 1000 G3',
        font_b=r'C:\Windows\Fonts\segoeuib.ttf', ports=8):
    """ATX PSU 150 x 86 x length. Returns (empty, info) with local port/inlet points converted to
    parent space."""
    W, Ht = 0.150, 0.086
    root = frame_empty(name, col, parent, loc, rot3)
    body = M.get('psu_body', M['black_st'])
    H['box'](name + '_Body', (W, length - 0.002, Ht), (0, length / 2, Ht / 2), body, col, bevel=0.0015, parent=root)
    # rear (AC) face: honeycomb grille area + inlet + switch
    def hexes():
        for i in range(14):
            for j in range(7):
                x = -0.068 + i * 0.0062 + (0.0031 if j % 2 else 0)
                z = 0.012 + j * 0.0072
                if x < 0.020:
                    yield (x, -0.0004, z), (0.0046, 0.0012, 0.0050)
    box_array(name + '_Grille', list(hexes()), M['port'], col, root)
    H['box'](name + '_Inlet', (0.028, 0.004, 0.024), (0.045, -0.001, 0.058), M['plastic'], col, parent=root)
    H['box'](name + '_InletHole', (0.022, 0.002, 0.016), (0.045, -0.0032, 0.058), M['port'], col, parent=root)
    cyl_array(name + '_InletPins', [((0.045 + dx, -0.0035, 0.058 + dz), 0.0012, 0.006, 'y') for dx, dz in ((-0.0055, -0.002), (0.0055, -0.002), (0, 0.003))], M['steel'], col, root, segs=8)
    H['box'](name + '_Switch', (0.011, 0.005, 0.016), (0.045, -0.0015, 0.030), M['plastic'], col, parent=root)
    # bottom fan grille (135 mm)
    rings = [(0.066, 0.0018), (0.050, 0.0012), (0.034, 0.0012), (0.018, 0.0012)]
    for k, (r, w) in enumerate(rings):
        n = 40; outer = [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]
        inner = [((r - w) * math.cos(2 * math.pi * i / n), (r - w) * math.sin(2 * math.pi * i / n)) for i in range(n)]
        g = H['ring'](name + f'_FanRing{k}', outer, inner, 'xy', -0.0012, 0.0012, M['steel'], col, parent=root)
        g.location = (0, length / 2, 0)
    H['cyl'](name + '_FanHole', 0.066, 0.0004, (0, length / 2, 0.0002), M['port'], col, verts=40, parent=root)
    box_array(name + '_FanSpokes', [((0, length / 2, -0.0006), (0.132, 0.0015, 0.0012)), ((0, length / 2, -0.0006), (0.0015, 0.132, 0.0012))], M['steel'], col, root)
    # modular face sockets
    face_y = length
    port_pts = []
    items = []; holes = []
    cols_n = ports // 2
    for k in range(ports):
        cx = -0.060 + (k % cols_n) * (0.120 / max(cols_n - 1, 1))
        cz = 0.028 if k < cols_n else 0.058
        items.append(((cx, face_y + 0.0015, cz), (0.0195, 0.003, 0.0100)))
        holes.append(((cx, face_y + 0.0031, cz), (0.0170, 0.0004, 0.0080)))
        port_pts.append(V((cx, face_y + 0.004, cz)))
    box_array(name + '_Sockets', items, M['plastic'], col, root)
    box_array(name + '_SocketHoles', holes, M['port'], col, root)
    # side labels (both sides, read upright)
    text_at(name + '_BrandL', brand, font_b, 0.016, M['label'], col, root, (-W / 2 - 0.0003, length * 0.5, 0.055), (0, -1, 0), (0, 0, 1))
    text_at(name + '_ModelL', model, font_b, 0.0075, M['label'], col, root, (-W / 2 - 0.0003, length * 0.5, 0.034), (0, -1, 0), (0, 0, 1))
    text_at(name + '_BrandR', brand, font_b, 0.016, M['label'], col, root, (W / 2 + 0.0003, length * 0.5, 0.055), (0, 1, 0), (0, 0, 1))
    text_at(name + '_ModelR', model, font_b, 0.0075, M['label'], col, root, (W / 2 + 0.0003, length * 0.5, 0.034), (0, 1, 0), (0, 0, 1))
    bpy.context.view_layer.update()
    mw = parent.matrix_world.inverted() @ root.matrix_world if parent else root.matrix_world
    info = {'ports': [mw @ p for p in port_pts], 'inlet': mw @ V((0.045, -0.006, 0.058)),
            'port_out': mw.to_3x3() @ V((0, 1, 0))}
    return root, info


# ---------------------------------------------------------------- motherboard
SLOT_PITCH = 0.02032


def slot_y(k):
    """Centreline (local Y) of expansion position k = 1 (top, nearest the CPU) .. 7."""
    return 0.305 - 0.160 - (k - 1) * SLOT_PITCH


def motherboard(name, col, parent, M, loc, rot3, slot_types=('x1', 'x16', 'x1', 'x1', 'x16', 'x1', 'x16'),
                cooler='tower', x16_start=0.0125, font_b=r'C:\Windows\Fonts\segoeuib.ttf'):
    """Generic 2017 ATX board (Z270-class layout: LGA socket, 4 DIMMs, chipset sink, 7 positions).
    Returns (empty, info) with key points in the parent's space."""
    root = frame_empty(name, col, parent, loc, rot3)
    BW, BH, T = 0.244, 0.305, 0.0016
    H['box'](name + '_PCB', (BW, BH, T), (BW / 2, BH / 2, -T / 2), M['pcb'], col, parent=root)
    sx, sy = 0.105, 0.220                      # CPU socket centre
    # socket + retention frame
    H['box'](name + '_SocketFrame', (0.044, 0.050, 0.004), (sx, sy, 0.002), M['steel'], col, parent=root)
    H['box'](name + '_SocketLever', (0.002, 0.040, 0.003), (sx + 0.025, sy, 0.0035), M['steel'], col, parent=root)
    # VRM heatsinks (L around the socket: rear side + top side)
    H['box'](name + '_VRM_Rear', (0.016, 0.075, 0.024), (0.052, 0.228, 0.012), M['sink'], col, bevel=0.001, parent=root)
    H['box'](name + '_VRM_Top', (0.070, 0.016, 0.020), (0.110, 0.284, 0.010), M['sink'], col, bevel=0.001, parent=root)
    # rear I/O shroud + port stack poking out of the rear edge
    H['box'](name + '_IOShroud', (0.030, 0.120, 0.032), (0.016, 0.205, 0.016), M['shroud'], col, bevel=0.002, parent=root)
    io = [((-0.004, 0.155 + i * 0.020, 0.012), (0.026, 0.016, 0.020)) for i in range(5)]
    box_array(name + '_IOStack', io, M['steel'], col, root)
    # DIMM slots + modules
    dimm_x = (0.160, 0.170, 0.186, 0.196)
    box_array(name + '_DIMMSlots', [((x, 0.207, 0.004), (0.0065, 0.145, 0.008)) for x in dimm_x], M['plastic'], col, root)
    box_array(name + '_DIMMLatch', [((x, y, 0.006), (0.0068, 0.005, 0.012)) for x in dimm_x for y in (0.132, 0.282)], M['shroud'], col, root)
    box_array(name + '_DIMMs', [((x, 0.207, 0.022), (0.0045, 0.134, 0.032)) for x in dimm_x], M['ram'], col, root)
    box_array(name + '_DIMMTops', [((x, 0.207, 0.0385), (0.0060, 0.130, 0.003)) for x in dimm_x], M['black_mt'], col, root)
    # power connectors
    H['box'](name + '_ATX24', (0.010, 0.053, 0.016), (0.236, 0.200, 0.008), M['plastic'], col, parent=root)
    H['box'](name + '_EPS8', (0.019, 0.010, 0.016), (0.039, 0.2975, 0.008), M['plastic'], col, parent=root)
    # chipset sink, SATA, M.2, battery, caps
    H['box'](name + '_PCH', (0.048, 0.045, 0.010), (0.185, 0.060, 0.005), M['sink'], col, bevel=0.001, parent=root)
    H['box'](name + '_PCHBadge', (0.030, 0.020, 0.0008), (0.185, 0.060, 0.0104), M['accent'], col, parent=root)
    box_array(name + '_SATA', [((0.239, 0.020 + i * 0.010, 0.006), (0.010, 0.008, 0.012)) for i in range(4)], M['plastic'], col, root)
    H['box'](name + '_M2', (0.082, 0.022, 0.003), (0.130, slot_y(1) - SLOT_PITCH / 2 + 0.002, 0.0015), M['sink'], col, parent=root)
    H['cyl'](name + '_Battery', 0.010, 0.0032, (0.200, 0.110, 0.0016), M['steel'], col, verts=24, parent=root)
    caps = [((0.068, 0.170 + i * 0.010, 0.005), 0.0035, 0.010, 'z') for i in range(5)] + \
           [((0.080 + i * 0.010, 0.264, 0.005), 0.0035, 0.010, 'z') for i in range(5)]
    cyl_array(name + '_Caps', caps, M['cap'], col, root, segs=12)
    # expansion connectors
    slots = {}
    bodies = []; steel = []; latches = []
    for k, t in enumerate(slot_types, start=1):
        y = slot_y(k)
        if t == 'x16':
            x0, x1 = x16_start, x16_start + 0.0915
            steel.append((((x0 + x1) / 2, y, 0.0056), (x1 - x0 + 0.002, 0.0084, 0.0112)))
            latches.append(((x1 + 0.004, y, 0.006), (0.008, 0.0075, 0.012)))
        else:
            x0, x1 = x16_start, x16_start + 0.025
            bodies.append((((x0 + x1) / 2, y, 0.0056), (x1 - x0, 0.0075, 0.0112)))
        slots[k] = (t, V((x0, y, 0.0)), V((x1, y, 0.0)))
    if bodies:
        box_array(name + '_PCIeX1', bodies, M['plastic'], col, root)
    if steel:
        box_array(name + '_PCIeX16', steel, M['steel'], col, root)
        box_array(name + '_PCIeLatch', latches, M['plastic'], col, root)
    box_array(name + '_SlotMouths', [(((s[1].x + s[2].x) / 2, s[1].y, 0.0113), (s[2].x - s[1].x - 0.003, 0.0020, 0.0004)) for s in slots.values()], M['port'], col, root)
    # CPU cooler
    if cooler == 'tower':
        # Hyper-212-class: 120 x 51 fin stack, 159 mm tall, 4 U heat pipes, 120 mm fan on the front
        H['box'](name + '_CoolerBase', (0.040, 0.040, 0.010), (sx, sy, 0.009), M['copper'], col, parent=root)
        def fins():
            z = 0.045
            while z < 0.158:
                yield (sx, sy, z), (0.051, 0.116, 0.0005)
                z += 0.0021
        box_array(name + '_CoolerFins', list(fins()), M['alu'], col, root)
        pipes = []
        for dy in (-0.030, -0.010, 0.010, 0.030):
            for dx in (-0.016, 0.016):
                pipes.append(((sx + dx, sy + dy, 0.087), 0.003, 0.150, 'z'))
        cyl_array(name + '_HeatPipes', pipes, M['copper'], col, root, segs=10)
        H['box'](name + '_CoolerCap', (0.053, 0.118, 0.004), (sx, sy, 0.160), M['black_mt'], col, bevel=0.0008, parent=root)
        fan(name + '_CoolerFan', col, root, M, size=0.120, depth=0.025, blades=7,
            loc=(sx + 0.0255 + 0.0125, sy, 0.100), rot3=basis((0, 0, 1), (0, 1, 0)))
    else:
        # boxed-cooler class: round alu sink + 90 mm fan
        H['cyl'](name + '_StockSink', 0.045, 0.025, (sx, sy, 0.0145), M['alu'], col, verts=40, parent=root)
        fan(name + '_StockFan', col, root, M, size=0.092, depth=0.020, blades=7, loc=(sx, sy, 0.037))
    # status LED
    led = H['box']('LED_mobo_status', (0.003, 0.002, 0.0012), (0.230, 0.150, 0.0006), M['led_g'], col, parent=root)
    bpy.context.view_layer.update()
    mw = (parent.matrix_world.inverted() @ root.matrix_world) if parent else root.matrix_world
    info = {'mw': mw, 'slots': slots, 'atx24': mw @ V((0.236, 0.200, 0.017)), 'eps8': mw @ V((0.039, 0.2975, 0.017)),
            'cpu': mw @ V((sx, sy, 0.0)), 'normal': mw.to_3x3() @ V((0, 0, 1))}
    return root, info


# ---------------------------------------------------------------- misc
def garage_materials(M, accent=(0.55, 0.02, 0.03)):
    mat = H['mat']
    M['sink'] = mat('GR_SinkGunmetal', (0.05, 0.05, 0.055), 0.8, 0.35)
    M['shroud'] = mat('GR_ShroudPlastic', (0.03, 0.03, 0.032), 0.0, 0.4, spec=0.4)
    M['ram'] = mat('GR_RamSpreaderRed', (0.30, 0.012, 0.015), 0.6, 0.35)
    M['copper'] = mat('GR_Copper', (0.80, 0.42, 0.28), 1.0, 0.28)
    M['cap'] = mat('GR_CapSolid', (0.25, 0.25, 0.27), 0.9, 0.3)
    M['accent'] = mat('GR_Accent', accent, 0.0, 0.35, spec=0.5)
    M['label'] = mat('GR_LabelWhite', (0.75, 0.75, 0.75), 0.0, 0.5)
    M['led_g'] = mat('GR_LED_Green', (0.1, 1.0, 0.2), 0.0, 0.4, emit=(0.1, 1.0, 0.2), emit_str=6.0)
    M['led_w'] = mat('GR_LED_White', (0.9, 0.95, 1.0), 0.0, 0.4, emit=(0.8, 0.9, 1.0), emit_str=6.0)
    M['led_b'] = mat('GR_LED_Blue', (0.1, 0.3, 1.0), 0.0, 0.4, emit=(0.1, 0.35, 1.0), emit_str=8.0)
    M['cable'] = mat('GR_CableSleeve', (0.012, 0.012, 0.013), 0.0, 0.65, spec=0.25)
    M['cable_y'] = mat('GR_CableYellow', (0.75, 0.55, 0.02), 0.0, 0.5)
    M['usb'] = mat('GR_USBBlue', (0.02, 0.10, 0.55), 0.0, 0.45)
    M['rubber'] = mat('GR_Rubber', (0.01, 0.01, 0.01), 0.0, 0.9, spec=0.1)
    M['psu_body'] = mat('GR_PSUBlack', (0.015, 0.015, 0.016), 0.5, 0.45)
    return M


def append_cards(slots, col_name='Preview_GPUs'):
    """Append one GTX1080Ti_FE per SLOT empty (for preview renders only)."""
    pc = bpy.data.collections.get(col_name) or bpy.data.collections.new(col_name)
    if pc.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(pc)
    roots = []
    for s in slots:
        with bpy.data.libraries.load(GPU_LIB, link=False) as (src, dst):
            dst.collections = [GPU_ROOT]
        c = dst.collections[0]
        r = next(o for o in c.objects if o.parent is None and o.name.startswith(GPU_ROOT))
        for o in list(c.all_objects):
            pc.objects.link(o)
        r.matrix_world = s.matrix_world.copy()
        roots.append(r)
    bpy.context.view_layer.update()
    return roots


def look(cam, target):
    d = V(target) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def setup_studio(scale, centre, floor_z=0.0, energy_mul=None):
    """Re-scale the template studio (sized for a ~30 cm card) around `centre`."""
    sc = bpy.context.scene
    em = energy_mul if energy_mul is not None else scale * scale
    for nm in ('Key', 'Fill', 'Rim'):
        L = bpy.data.objects.get(nm)
        if not L:
            continue
        if '_orig' not in L:
            L['_orig'] = list(L.location); L['_e'] = L.data.energy; L['_s'] = getattr(L.data, 'size', 0.1)
        o = V(L['_orig']) - V((0.13, -0.02, 0.05))
        L.location = V(centre) + o * scale
        L.data.energy = L['_e'] * em
        L.hide_render = L['_e'] <= 0.0     # the template Fill light is off; in 5.2 EEVEE its quad shows up in wide shots
        try:
            L.data.size = L['_s'] * scale
        except Exception:
            pass
        look(L, centre)
        try:
            L.visible_camera = False; L.visible_glossy = True
        except Exception:
            pass
    fl = bpy.data.objects.get('Floor')
    if fl:
        fl.location = (centre[0], centre[1], floor_z - 0.0003)
        fl.scale = (fl.scale[0] * scale * 1.5, fl.scale[1] * scale * 1.5, fl.scale[2])
        fl.hide_render = False
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.render.resolution_percentage = 100


def render_views(views, out_fmt, only=None):
    sc = bpy.context.scene
    studio = H['coll']('Studio')
    for nm, (pos, tgt, lens) in views.items():
        if only and nm not in only:
            continue
        cn = 'Cam_' + nm
        cam = bpy.data.objects.get(cn)
        if not cam:
            cam = bpy.data.objects.new(cn, bpy.data.cameras.new(cn)); studio.objects.link(cam)
        cam.data.lens = lens; cam.data.clip_start = 0.01; cam.data.clip_end = 50
        cam.location = pos; look(cam, tgt)
        sc.camera = cam
        sc.render.filepath = out_fmt.format(nm)
        bpy.ops.render.render(write_still=True)


def count_tris(root):
    dg = bpy.context.evaluated_depsgraph_get(); tris = 0
    for o in [root] + list(root.children_recursive):
        if o.type == 'MESH':
            e = o.evaluated_get(dg); m = e.to_mesh(); m.calc_loop_triangles(); tris += len(m.loop_triangles); e.to_mesh_clear()
    return tris


GL = dict(basis=basis, frame_empty=frame_empty, marker=marker, text_at=text_at, cyl_array=cyl_array,
          box_array=box_array, flow_cable=flow_cable, fan=fan, psu=psu, motherboard=motherboard,
          slot_y=slot_y, garage_materials=garage_materials, append_cards=append_cards, look=look,
          setup_studio=setup_studio, render_views=render_views, count_tris=count_tris)
bpy.app.driver_namespace['GL'] = GL
