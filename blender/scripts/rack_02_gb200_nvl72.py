"""NVIDIA GB200 NVL72 rack (MGX rack, 2025): 18 compute trays + 9 NVLink switch trays, 8 power shelves,
rear 54 V DC busbar, NVLink copper spine cartridges, vertical coolant manifolds, 2 TOR management switches.

Run headless (build srv_06 and srv_07 first; their .blend files are appended for the previews):
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python rack_02_gb200_nvl72.py

Conventions: metres, Z up, origin = floor, front-centre; front face at y=0 facing -Y; depth toward +Y.
Real dimensions (Supermicro SRS-GB200-NVL72 datasheet, Feb 2025): 2236 H x 600 W x 1068 D mm, ~1.36 t,
8x 1U 33 kW power shelves (4+4, 6x 5.5 kW PSUs each, 132 kW), 18x 1U compute + 9x 1U NVLink switch trays.
Rails: 19" EIA, 48U, 1U = 44.45 mm; U01 bottom at z = 70.2 mm (plinth), rail plane y = 40 mm.
Elevation (bottom-up, after the NVIDIA/STH photos: 10 compute above the switches, 8 below):
  U01 blank | U02-U05 power shelves | U06-U13 compute 01-08 | U14-U22 NVLink switch 01-09 |
  U23-U32 compute 09-18 | U33 status LED blank | U34-U37 power shelves | U38 blank |
  U39-U42 TOR bezel (switches in U40, U41) | U43-U48 blank
Export: rack shell + power shelves + TOR + busbar + spine + manifolds; trays are SLOT_tray_* empties.
"""
import bpy, math, os
from mathutils import Matrix, Vector
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\nvl72_lib.py', encoding='utf-8').read())

ROOT = 'rack_02_gb200_nvl72'
root, col = H['new_card_scene'](ROOT)
M = nv_materials()
box, cyl, sa = H['box'], H['cyl'], H['slat_array']

RW, RD, RH = 0.600, 1.068, 2.236
NU = 48
Z0 = RH - NU * U - 0.0322          # plinth height = 0.0702 (top frame 32.2 mm)
RAIL_Y = 0.040
TRAY_D = 0.875
YR = RAIL_Y + TRAY_D               # tray rear wall plane (0.915)


def zU(n):
    return Z0 + (n - 1) * U


COMPUTE_U = list(range(6, 14)) + list(range(23, 33))
SWITCH_U = list(range(14, 23))
SHELF_U = [2, 3, 4, 5, 35, 36, 37, 38]
TOR_U = [40, 41]
BLANK_U = [1, 34, 39, 42] + list(range(43, 49))

# ------------------------------------------------------------------ frame: plinth, posts, sides, top
box('Plinth', (RW, RD, Z0 - 0.012), (0, RD / 2, 0.012 + (Z0 - 0.012) / 2), M['rack'], col, parent=root)
feet = []
for sx in (-1, 1):
    for y in (0.06, RD - 0.06):
        feet.append(cyl(f'Foot_{sx}_{y:.2f}', 0.022, 0.012, (sx * 0.25, y, 0.006), M['black_st'], col, verts=16, parent=root))
merge('Leveling_Feet', feet)
posts = []
for sx in (-1, 1):
    for y in (0.020, RD - 0.020):
        posts.append(box(f'Post_{sx}_{y:.2f}', (0.040, 0.040, RH - Z0), (sx * (RW / 2 - 0.020), y, Z0 + (RH - Z0) / 2), M['rack'], col, parent=root))
merge('Frame_Posts', posts)
box('Side_L', (0.0020, RD, RH - Z0), (-RW / 2 + 0.0010, RD / 2, Z0 + (RH - Z0) / 2), M['rack'], col, parent=root)
box('Side_R', (0.0020, RD, RH - Z0), (RW / 2 - 0.0010, RD / 2, Z0 + (RH - Z0) / 2), M['rack'], col, parent=root)
box('Top_Cover', (RW, RD, 0.0030), (0, RD / 2, RH - 0.0015), M['rack'], col, parent=root)
for i, y in enumerate((0.25, 0.85)):
    box(f'Top_CableOpening_{i}', (0.30, 0.10, 0.0010), (0, y, RH + 0.0001), M['rack_hole'], col, parent=root)
# front frame band between post and rail, front top header
for sx in (-1, 1):
    box(f'Front_Band_{sx}', (0.035, 0.012, RH - Z0 - 0.032), (sx * 0.2625, 0.006, Z0 + (RH - Z0 - 0.032) / 2), M['rack'], col, parent=root)
    box(f'Rear_Band_{sx}', (0.035, 0.012, RH - Z0 - 0.032), (sx * 0.2625, RD - 0.006, Z0 + (RH - Z0 - 0.032) / 2), M['rack'], col, parent=root)
box('Front_Top_Header', (RW, 0.020, 0.0322), (0, 0.010, RH - 0.0161), M['rack'], col, parent=root)
box('Rear_Top_Header', (RW, 0.020, 0.0322), (0, RD - 0.010, RH - 0.0161), M['rack'], col, parent=root)
# EIA rails (front) with square-hole texture: one hole column per rail, pitch = U/3
for sx in (-1, 1):
    box(f'Rail_Front_{sx}', (0.027, 0.0025, NU * U), (sx * 0.239, RAIL_Y + 0.00125, Z0 + NU * U / 2), M['rack'], col, parent=root)
    grille(f'Rail_Front_Holes_{sx}', sx * 0.23255 - 0.0074, sx * 0.23255 + 0.0074, Z0, Z0 + NU * U, RAIL_Y - 0.0002,
           M['grille'], col, root, pitch=U / 3)
    box(f'Rail_Rear_{sx}', (0.027, 0.0025, NU * U), (sx * 0.239, RD - 0.050, Z0 + NU * U / 2), M['rack'], col, parent=root)
# side branding (vertical "NVIDIA" on the left side panel, as on the NVIDIA renders)
rot_side = (Matrix.Rotation(-math.pi / 2, 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'X') @ Matrix.Rotation(math.pi / 2, 4, 'Z')).to_euler()
H['text_mesh']('Side_Logo_L', 'NVIDIA', FONT_LOGO, 0.110, M['module'], col, root, (-RW / 2 - 0.0004, 0.16, 1.80), rot_side, extrude=0.0003)


# ------------------------------------------------------------------ gold bezels (rounded-rect rings)
def rrect(cx, cz, w, h, r, seg=6):
    pts = []
    for (qx, qz, a0) in ((cx + w / 2 - r, cz - h / 2 + r, -90), (cx + w / 2 - r, cz + h / 2 - r, 0),
                         (cx - w / 2 + r, cz + h / 2 - r, 90), (cx - w / 2 + r, cz - h / 2 + r, 180)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((qx + r * math.cos(a), qz + r * math.sin(a)))
    return pts


def gold_frame(name, z0, z1, w=0.512, bar=0.013, r=0.030, y0=0.004, depth=0.030):
    cz = (z0 + z1) / 2; h = z1 - z0
    o = H['ring'](name, rrect(0, cz, w, h, r), rrect(0, cz, w - 2 * bar, h - 2 * bar, r - bar * 0.8), 'xz', y0, depth, M['gold'], col, root)
    return o


TZ0, TZ1 = zU(6) - 0.006, zU(33) + 0.040        # tray block + NVIDIA header
gold_frame('Bezel_Trays', TZ0, TZ1)
box('Bezel_Header_Plate', (0.486, 0.004, 0.034), (0, 0.020, zU(33) + 0.018), M['panel'], col, parent=root)
H['text_mesh']('Bezel_Header_Logo', 'NVIDIA', FONT_LOGO, 0.020, M['label'], col, root, (0.180, 0.0175, zU(33) + 0.018), (math.pi / 2, 0, 0),
               extrude=0.0002)
box('Bezel_Header_Eye', (0.020, 0.0010, 0.015), (0.122, 0.0175, zU(33) + 0.018), M['label'], col, parent=root)
gold_frame('Bezel_TOR', zU(39) + 0.004, zU(43) - 0.004, w=0.470, r=0.040, bar=0.016)
for sx in (-1, 1):
    for z in (zU(40) + U / 2, zU(42) - U / 2):
        cyl(f'Bezel_TOR_Screw_{sx}_{z:.3f}', 0.0050, 0.004, (sx * 0.222, 0.002, z), M['steel'], col, verts=16, rot=(math.pi / 2, 0, 0), parent=root)

# ------------------------------------------------------------------ blank panels + status strip
blanks = [((0, RAIL_Y - 0.002, zU(n) + U / 2), (0.482, 0.003, U - 0.0006)) for n in BLANK_U if n not in (39, 42)]
blanks.append(((0, RAIL_Y - 0.002, zU(39) + U / 2), (0.440, 0.003, U - 0.0006)))
blanks.append(((0, RAIL_Y - 0.002, zU(42) + U / 2), (0.440, 0.003, U - 0.0006)))
sa('Blank_Panels', lambda: iter(blanks), M['rack'], col, root)
leds_g = [((-0.10 + i * 0.006, RAIL_Y - 0.004, zU(34) + U / 2), (0.004, 0.0015, 0.0025)) for i in range(16)]
leds_r = [((0.03 + i * 0.006, RAIL_Y - 0.004, zU(34) + U / 2), (0.004, 0.0015, 0.0025)) for i in range(8)]
sa('LED_rack_status', lambda: iter(leds_g), M['led_g'], col, root)
sa('LED_rack_alarm', lambda: iter(leds_r), M['led_a'], col, root)

# ------------------------------------------------------------------ power shelves (1U, 6x 5.5 kW PSU), built once, linked copies
SH_D = 0.800


def build_shelf(name):
    e = bpy.data.objects.new(name, None); e.empty_display_type = 'CUBE'; e.empty_display_size = 0.02; col.objects.link(e)
    parts = []
    parts.append(box(name + '_Body', (0.440, SH_D, 0.0432), (0, SH_D / 2, 0.0216), M['black_st'], col))
    parts.append(box(name + '_Ears', (0.482, 0.004, 0.0430), (0, 0.002, 0.0215), M['rack'], col))
    psu_x = [-0.145 + 0.0292 + i * 0.0583 for i in range(6)]
    face = [((x, -0.0010, 0.0216), (0.0560, 0.0030, 0.0405)) for x in psu_x]
    parts.append(sa(name + '_PSU_Faces', lambda: iter(face), M['panel'], col))
    fans = [cyl(f'{name}_Fan_{i}', 0.0165, 0.0016, (x - 0.008, -0.0032, 0.0216), M['grille'], col, verts=24, rot=(math.pi / 2, 0, 0))
            for i, x in enumerate(psu_x)]
    hubs = [cyl(f'{name}_Hub_{i}', 0.0060, 0.0020, (x - 0.008, -0.0040, 0.0216), M['black_mt'], col, verts=12, rot=(math.pi / 2, 0, 0))
            for i, x in enumerate(psu_x)]
    handles = [((x + 0.0215, -0.006, 0.0216), (0.0040, 0.008, 0.032)) for x in psu_x]
    parts += fans + hubs
    parts.append(sa(name + '_Handles', lambda: iter(handles), M['steel'], col))
    parts.append(box(name + '_Mgmt', (0.058, 0.0030, 0.0405), (-0.180, -0.0010, 0.0216), M['module'], col))
    pr = [((-0.192 + c * 0.017, -0.0028, 0.0145 + r * 0.0145), (0.0130, 0.0010, 0.0110)) for c in range(2) for r in range(2)]
    parts.append(sa(name + '_MgmtPorts', lambda: iter(pr), M['rack_hole'], col))
    parts.append(box(name + '_RearClip', (0.040, RAIL_Y + TRAY_D + 0.030 - (RAIL_Y + SH_D), 0.026),
                     (0, SH_D + (TRAY_D + 0.030 - SH_D) / 2, 0.022), M['black_st'], col))
    parts.append(box(name + '_ACInlet', (0.050, 0.030, 0.034), (0.150, SH_D + 0.015, 0.022), M['plastic'], col))
    for p in parts:
        p.parent = e
    for p in parts:
        H['apply_all'](p)
    body = merge(name + '_Mesh', [p for p in parts if p.data.materials[0] == M['black_st']])
    led = [((x + 0.016, -0.0029, 0.036), (0.0030, 0.0010, 0.0020)) for x in psu_x]
    return e, led


shelf0, shelf_leds = build_shelf('PowerShelf_01')
shelves = [shelf0]
for i, n in enumerate(SHELF_U):
    s = shelf0 if i == 0 else dup_tree(shelf0, col)
    s.name = f'PowerShelf_{i + 1:02d}'
    s.parent = root; s.location = (0, RAIL_Y, zU(n))
    sa(f'LED_power_shelf_{i + 1:02d}', lambda: iter(shelf_leds), M['led_g'], col, s)
    if i:
        shelves.append(s)

# ------------------------------------------------------------------ TOR management switches (1U, 48x RJ45 + 4x QSFP28)
def build_tor(name, z):
    e = bpy.data.objects.new(name, None); e.empty_display_type = 'CUBE'; e.empty_display_size = 0.02; col.objects.link(e)
    e.parent = root; e.location = (0, RAIL_Y, z)
    box(name + '_Body', (0.440, 0.50, 0.0432), (0, 0.25, 0.0216), M['black_st'], col, parent=e)
    box(name + '_Face', (0.440, 0.0030, 0.0420), (0, -0.0010, 0.0216), M['module'], col, parent=e)
    ports = []
    for g in range(3):
        for c in range(8):
            for r in range(2):
                ports.append(((-0.185 + g * 0.110 + c * 0.0135, -0.0030, 0.0145 + r * 0.0145), (0.0120, 0.0012, 0.0105)))
    for c in range(2):
        for r in range(2):
            ports.append(((0.150 + c * 0.024, -0.0030, 0.0145 + r * 0.0145), (0.0190, 0.0012, 0.0090)))
    sa(name + '_Ports', lambda: iter(ports), M['rack_hole'], col, e)
    led = [((-0.185 + g * 0.110 + c * 0.0135 + 0.004, -0.0032, 0.0072), (0.0025, 0.0008, 0.0015)) for g in range(3) for c in range(8)]
    sa('LED_' + name + '_ports', lambda: iter(led), M['led_g'], col, e)
    box('LED_' + name + '_sys', (0.0025, 0.0012, 0.0025), (0.205, -0.0030, 0.034), M['led_b'], col, parent=e)
    H['text_mesh'](name + '_Label', 'NVIDIA', FONT_LOGO, 0.0060, M['label'], col, e, (0.198, -0.0029, 0.012), (math.pi / 2, 0, 0), extrude=0.0001)
    return e


build_tor('TOR_inband', zU(41))
build_tor('TOR_oob', zU(40))

# ------------------------------------------------------------------ slots
for n in range(1, NU + 1):
    slot(f'SLOT_U{n:02d}', (0, RAIL_Y, zU(n)), col, root, size=0.02, kind='PLAIN_AXES')
tray_slots = []
for i, n in enumerate(COMPUTE_U):
    e = slot(f'SLOT_tray_compute_{i + 1:02d}', (0, RAIL_Y, zU(n)), col, root, size=0.06)
    e['asset'] = 'srv_06_gb200_compute_tray'; e['U'] = n; tray_slots.append(e)
for i, n in enumerate(SWITCH_U):
    e = slot(f'SLOT_tray_switch_{i + 1:02d}', (0, RAIL_Y, zU(n)), col, root, size=0.06)
    e['asset'] = 'srv_07_nvl72_switch_tray'; e['U'] = n; tray_slots.append(e)

# ------------------------------------------------------------------ rear 54 V DC busbar (flow UV, two halves fed from top/bottom shelves)
QZ = 0.022
BB_Z0, BB_Z1 = zU(2) + 0.004, zU(39) - 0.004
BB_MID = zU(18) + QZ
YB_P, YB_N = YR + 0.0275, YR + 0.0475         # + bar and return bar centres (tray clip fingers reach YR+0.023..0.049)
bus = []
o, _ = flow_box('Busbar_Pos_Lower', (0, YB_P, BB_Z0), (0, YB_P, BB_MID), 0.009, 0.018, M['busbar'], col, root); bus.append(o)
o, _ = flow_box('Busbar_Pos_Upper', (0, YB_P, BB_Z1), (0, YB_P, BB_MID), 0.009, 0.018, M['busbar'], col, root); bus.append(o)
o, _ = flow_box('Busbar_Ret_Lower', (0, YB_N, BB_MID), (0, YB_N, BB_Z0), 0.009, 0.018, M['busbar'], col, root); bus.append(o)
o, _ = flow_box('Busbar_Ret_Upper', (0, YB_N, BB_MID), (0, YB_N, BB_Z1), 0.009, 0.018, M['busbar'], col, root); bus.append(o)
box('Busbar_Insulator', (0.016, 0.0020, BB_Z1 - BB_Z0), (0, YR + 0.0375, (BB_Z0 + BB_Z1) / 2), M['plastic'], col, parent=root)
for zz in (BB_Z0 + 0.02, BB_MID, BB_Z1 - 0.02):
    box(f'Busbar_Bracket_{zz:.2f}', (0.020, 0.030, 0.030), (0, YR + 0.070, zz), M['black_st'], col, parent=root)
for e in tray_slots:
    tag = e.name.replace('SLOT_tray_', '')
    slot(f'SOCKET_power_out_{tag}', (0, YR + 0.020, e.location.z + QZ), col, root, rot=(math.pi / 2, 0, 0), size=0.02, kind='SINGLE_ARROW')

# AC power whips from the facility (top and bottom) to each shelf's rear AC inlet (flow UV, u from facility end)
whips = []
for i, n in enumerate(SHELF_U):
    zt = zU(n) + QZ
    top = n > 20
    xw = 0.140 - (i % 4) * 0.014
    if top:
        ctrl = [(xw, YR + 0.10, RH + 0.25), (xw, YR + 0.10, RH + 0.02), (xw, YR + 0.10, zt + 0.10), (0.170, RAIL_Y + SH_D + 0.060, zt + 0.004),
                (0.150, RAIL_Y + SH_D + 0.032, zt)]
        sock = (xw, YR + 0.10, RH + 0.25)
    else:
        ctrl = [(xw, YR + 0.10, -0.02), (xw, YR + 0.10, 0.02), (xw, YR + 0.10, zt - 0.10), (0.170, RAIL_Y + SH_D + 0.060, zt - 0.004),
                (0.150, RAIL_Y + SH_D + 0.032, zt)]
        sock = (xw, YR + 0.10, -0.02)
    o, _ = tube(f'Power_Whip_{i + 1:02d}', ctrl, 0.0090, M['black_mt'], col, root, u0=0.0, res=8, ring=10)
    whips.append(o)
    slot(f'SOCKET_power_in_{i + 1:02d}', sock, col, root, rot=(0, 0, 0) if top else (math.pi, 0, 0), size=0.05, kind='SINGLE_ARROW')

# ------------------------------------------------------------------ NVLink spine: two cable cartridges + connector faces + rear grilles
CZ0, CZ1 = zU(6) - 0.010, zU(33) + 0.010
CY0, CY1 = YR + 0.008, RD - 0.060
for sx, nm in ((-1, 'L'), (1, 'R')):
    xa, xb = sx * 0.042, sx * 0.188
    cx = (xa + xb) / 2; cw = abs(xb - xa)
    box(f'Spine_Cartridge_{nm}_Shell', (cw, CY1 - CY0, CZ1 - CZ0), (cx, (CY0 + CY1) / 2, (CZ0 + CZ1) / 2), M['black_st'], col, parent=root)
    grille(f'Spine_Cartridge_{nm}_Grille', min(xa, xb) + 0.004, max(xa, xb) - 0.004, CZ0 + 0.01, CZ1 - 0.01, CY1 + 0.0004,
           M['grille_lt'], col, root, facing=1, pitch=0.004)
    # visible twisted cable bundles behind the gold rear bezel window
conn = []
for e in tray_slots:
    z = e.location.z + 0.018
    xs = [-0.1355, -0.064, 0.064, 0.1355] if 'compute' in e.name else [-0.170, -0.130, -0.090, -0.050, 0.050, 0.090, 0.130, 0.170]
    for x in xs:
        conn.append(((x, CY0 - 0.004, z), (0.040 if 'compute' in e.name else 0.030, 0.008, 0.024)))
sa('Spine_Connectors', lambda: iter(conn), M['plastic'], col, root)
gold_frame('Bezel_Rear_Spine', CZ0 - 0.012, CZ1 + 0.012, w=0.420, r=0.030, bar=0.012, y0=CY1 - 0.010, depth=0.030)

# ------------------------------------------------------------------ coolant manifolds (supply left, return right) with per-tray stubs
def pipe_geo(p0, p1, r, n, u0, V, F, UV):
    """Straight pipe p0->p1 appended to V/F/UV lists. u = u0 + metres along, v around."""
    p0, p1 = Vector(p0), Vector(p1); ax = p1 - p0; L = ax.length; ax.normalize()
    ref = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
    a = ax.cross(ref).normalized(); b = ax.cross(a)
    base = len(V)
    for end, pp in enumerate((p0, p1)):
        for k in range(n):
            t = 2 * math.pi * k / n
            V.append(tuple(pp + (a * math.cos(t) + b * math.sin(t)) * r))
    for k in range(n):
        j = (k + 1) % n
        F.append([base + k, base + j, base + n + j, base + n + k])
        UV.append([(u0, k / n), (u0, (k + 1) / n), (u0 + L, (k + 1) / n), (u0 + L, k / n)])
    F.append([base + k for k in range(n)][::-1]); UV.append([(u0, 0)] * n)
    F.append([base + n + k for k in range(n)]); UV.append([(u0 + L, 0)] * n)
    return u0 + L


MX, MY, MR = 0.222, YR + 0.088, 0.024
MZ0, MZ1 = zU(6) - 0.030, zU(33) + 0.030
flowobjs = []
for sx, tag in ((-1, 'Supply'), (1, 'Return')):
    x = sx * MX
    in_ctrl = [(x, RD + 0.16, 0.12), (x, RD - 0.02, 0.12), (x, MY + 0.01, 0.13), (x, MY, 0.20), (x, MY, MZ0)]
    if tag == 'Supply':
        o, u_in = tube('Coolant_1_Supply_Inlet', in_ctrl, MR * 0.85, M['hose'], col, root, u0=0.0, res=10, ring=16)
        V, F, UV = [], [], []
        u_top = pipe_geo((x, MY, MZ0), (x, MY, MZ1), MR, 16, u_in, V, F, UV)
        man = mesh_obj('Coolant_2_Supply_Manifold', V, F, UV, M['stainless'], col, root, smooth=True)
        man['flow_u_start'] = u_in; man['flow_u_end'] = u_top
        flowobjs += [o, man]
        slot('SOCKET_coolant_in', in_ctrl[0], col, root, rot=(-math.pi / 2, 0, 0), size=0.06, kind='SINGLE_ARROW')
        u_at = lambda z: u_in + (z - MZ0)
    else:
        V, F, UV = [], [], []
        u_bot = pipe_geo((x, MY, MZ1), (x, MY, MZ0), MR, 16, 0.06, V, F, UV)
        man = mesh_obj('Coolant_4_Return_Manifold', V, F, UV, M['stainless'], col, root, smooth=True)
        man['flow_u_start'] = 0.06; man['flow_u_end'] = u_bot
        o, u_out = tube('Coolant_5_Return_Outlet', in_ctrl[::-1], MR * 0.85, M['hose'], col, root, u0=u_bot, res=10, ring=16)
        flowobjs += [man, o]
        slot('SOCKET_coolant_out', in_ctrl[0], col, root, rot=(-math.pi / 2, 0, 0), size=0.06, kind='SINGLE_ARROW')
    for zz in (MZ0, MZ1):
        cyl(f'Manifold_{tag}_Cap_{zz:.2f}', MR + 0.003, 0.012, (x, MY, zz), M['stainless'], col, verts=16, parent=root)
    for zz in (MZ0 + 0.15, (MZ0 + MZ1) / 2, MZ1 - 0.15):
        box(f'Manifold_{tag}_Clamp_{zz:.2f}', (0.070, 0.060, 0.020), (x + sx * 0.012, MY + 0.008, zz), M['black_st'], col, parent=root)
    # stubs: manifold -> blind-mate female coupler at each tray's rear UQD
    V, F, UV = [], [], []
    cpl = []
    xq = sx * 0.200
    for e in tray_slots:
        z = e.location.z + QZ
        tagt = e.name.replace('SLOT_tray_', '')
        yq = YR + 0.035                              # tray UQD tip
        if tag == 'Supply':
            pipe_geo((xq, MY - MR + 0.004, z), (xq, yq + 0.020, z), 0.0075, 12, u_at(z), V, F, UV)
            slot(f'SOCKET_coolant_out_{tagt}', (xq, yq, z), col, root, rot=(math.pi / 2, 0, 0), size=0.02, kind='SINGLE_ARROW')
        else:
            Ls = (MY - MR + 0.004) - (yq + 0.020)
            pipe_geo((xq, yq + 0.020, z), (xq, MY - MR + 0.004, z), 0.0075, 12, 0.06 + (MZ1 - z) - Ls, V, F, UV)
            slot(f'SOCKET_coolant_in_{tagt}', (xq, yq, z), col, root, rot=(math.pi / 2, 0, 0), size=0.02, kind='SINGLE_ARROW')
        cpl.append(((xq, yq + 0.012, z), (0.020, 0.018, 0.020)))
    st = mesh_obj(f'Coolant_3_{tag}_Stubs' if tag == 'Supply' else f'Coolant_3_{tag}_Stubs', V, F, UV, M['stainless'], col, root, smooth=True)
    us = [d.uv[0] for d in st.data.uv_layers['UVMap'].data]
    st['flow_u_start'] = min(us); st['flow_u_end'] = max(us)
    flowobjs.append(st)
    sa(f'Manifold_{tag}_Couplers', lambda c=cpl: iter(c), M['qd_blue' if tag == 'Supply' else 'qd_red'], col, root)
for o in flowobjs + bus + whips[:1]:
    print('FLOW', o.name, round(o['flow_u_start'], 3), round(o['flow_u_end'], 3))

root['standard'] = '19in EIA rails, 48U, 1U = 44.45 mm (NVIDIA MGX NVL72 rack)'
root['size_mm'] = '600 W x 1068 D x 2236 H'
root['mass_kg'] = 1360
root['power_kw'] = 132
root['footprint_m'] = '0.600 x 1.068'

# ------------------------------------------------------------------ finalize + export
finalize_modifiers(root)
objs = tree(root)
print('TRIS rack', tri_count(objs))
print('NAMES', sorted(set(o.name.rsplit('_', 1)[0] if o.name[-2:].isdigit() else o.name for o in objs if o.type == 'EMPTY' and o.name.startswith(('SLOT', 'SOCKET')))))
print('COUNTS', sum(o.name.startswith('SLOT') for o in objs), sum(o.name.startswith('SOCKET') for o in objs), sum(o.name.startswith('LED') for o in objs))
print('BBOX', bbox(objs))
glb = BASE + r'\export\rack_02_gb200_nvl72.glb'
H['export_glb'](ROOT, glb)
print('GLB', os.path.getsize(glb))

# ------------------------------------------------------------------ previews with the trays appended
ct = append_tree(BASE + r'\srv_06_gb200_compute_tray.blend', 'srv_06_gb200_compute_tray')
stt = append_tree(BASE + r'\srv_07_nvl72_switch_tray.blend', 'srv_07_nvl72_switch_tray')
for t in (ct, stt):
    for o in tree(t):
        if o.name.startswith('Lid_Rear'):
            o.hide_render = False
pc = ct.users_collection[0]
first = {'compute': ct, 'switch': stt}
bpy.context.view_layer.update()
for e in tray_slots:
    kind = 'compute' if 'compute' in e.name else 'switch'
    t = first[kind]
    if t is None:
        t = dup_tree(ct if kind == 'compute' else stt, pc)
    first[kind] = None
    t.matrix_world = e.matrix_world.copy()
bpy.context.view_layer.update()

def flip_lights(yc=0.534):
    for nm in ('Key', 'Fill', 'Rim'):
        L = bpy.data.objects.get(nm)
        if L:
            L.location.y = 2 * yc - L.location.y
            L.location.x = -L.location.x
            L.rotation_euler.z += math.pi


stage(7.5, target=(0, 0.5, 0.0), floor_z=0.0, floor_scale=8)
for nm in ('Key', 'Fill', 'Rim'):
    L = bpy.data.objects.get(nm)
    if L:
        L.location.z += 1.0
R = BASE + r'\renders\rack_02_gb200_nvl72_'
cam_view(R + 'front34.png', (-2.2, -3.3, 1.75), (0, 0.5, 1.10), lens=35)
cam_view(R + 'front.png', (0, -5, 1.12), (0, 0, 1.12), ortho=4.2)
flip_lights()
cam_view(R + 'rear34.png', (2.0, 4.6, 1.70), (0, 0.6, 1.10), lens=35)
cam_view(R + 'rear.png', (0, 6, 1.12), (0, 1, 1.12), ortho=4.2)
cam_view(R + 'rear_close.png', (0.62, 1.70, 0.95), (0, 0.95, 0.62), lens=35)
flip_lights()
cam_view(R + 'front_close.png', (-0.55, -0.95, 1.65), (0, 0.04, 1.45), lens=35)
bpy.ops.wm.save_as_mainfile(filepath=BASE + r'\rack_02_gb200_nvl72.blend')
print('DONE')
