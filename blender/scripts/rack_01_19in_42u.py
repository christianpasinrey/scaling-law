"""APC NetShelter SX 42U 600 x 1200 mm enclosure with sides (AR3300) - the standard colo/data-hall rack.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python rack_01_19in_42u.py
  (--norender to skip renders, --views=a,b to limit)

Sources: se.com AR3300 product page + photos (front, rear, 3/4, doors open, rail close-up with U numbers,
side-panel lock), retailer spec listings: 1991 H x 600 W x 1200 D mm, 42U, max mounting depth 1048 mm,
134 kg with doors and sides. Front: single perforated door hinged on the left, handle on the right.
Rear: split perforated doors with the handle at the centre. Side panels split in two (upper/lower) with a key
lock. Square-hole EIA-310 rails with printed U numbers + U tick marks. Casters + levelling feet.

Conventions: origin = floor, front-centre; front face (closed front door) at y=0 facing -Y; depth toward +Y.
SLOT_U01..SLOT_U42: bottom of each U on the FRONT rail plane (y = front face of the front rail), identity
rotation (mounted gear has its front panel facing -Y, ears on the rail).
Doors are separate objects whose origin is on the hinge axis: rotate about local Z by `open_angle_deg`.
"""
import bpy, bmesh, math, mathutils, os, sys

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\rack_kit_lib.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\net_switch_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']; RK = bpy.app.driver_namespace['RK']
V = mathutils.Vector
U = RK['U']
mm = 0.001

ROOT = 'rack_01_19in_42u'
BLEND = os.path.join(RK['BASE'], ROOT + '.blend')
root, col = H['new_card_scene'](ROOT)
mat = H['mat']; M = H['base_materials']()
FRAME = mat('RK_RackFrame', (0.010, 0.010, 0.011), 0.45, 0.42, spec=0.35)
PANEL = mat('RK_RackPanel', (0.011, 0.011, 0.012), 0.5, 0.30, spec=0.4)
RAIL = mat('RK_RackRail', (0.016, 0.016, 0.018), 0.55, 0.45)
PERF = RK['perf_material']('RK_DoorPerf', (0.07, 0.07, 0.075), 0.35, 0.5, see_through=True)
WHITE = mat('RK_PrintWhite', (0.75, 0.75, 0.74), 0.0, 0.6)
HANDLE = mat('RK_HandleChrome', (0.55, 0.56, 0.58), 1.0, 0.25)
RUBBER = mat('RK_Rubber', (0.02, 0.02, 0.02), 0.0, 0.8)
BRUSH = mat('RK_Brush', (0.004, 0.004, 0.004), 0.0, 0.95, spec=0.05)
APC_RED = mat('RK_APC_Red', (0.65, 0.02, 0.02), 0.0, 0.45)

W, D, HT = 0.600, 1.200, 1.991
NU = 42
Y_FR = 0.100                 # front rail mounting face
Y_RR = 0.850                 # rear rail mounting face (adjustable in the real rack; 750 mm spacing)
Z_U1 = 0.086                 # bottom of U1
Z_TOP = Z_U1 + NU * U        # 1.9529
HOLE_X = 0.23255             # EIA hole centres (465.1 mm)
Z_FB0, Z_FB1 = 0.050, 0.086  # base frame
Z_TF0, Z_TF1 = 1.955, 1.975  # top frame (under the roof)
DOOR_T = 0.025
DOOR_Z0, DOOR_Z1 = 0.052, 1.972


def bm_box(bm, c, s, mi=0):
    return RK['add_box'](bm, c, s, mi)


# ---------------------------------------------------------------- frame (posts, base, top, roof)
bm = bmesh.new()
PX0, PX1 = 0.245, 0.285
for sx in (-1, 1):
    for (y0, y1) in ((0.030, 0.070), (1.130, 1.170)):
        bm_box(bm, (sx * (PX0 + PX1) / 2, (y0 + y1) / 2, (Z_FB0 + Z_TF1) / 2), (PX1 - PX0, y1 - y0, Z_TF1 - Z_FB0))
    # side beams (front-to-back) top and bottom
    for (z0, z1) in ((Z_FB0, Z_FB1), (Z_TF0, Z_TF1)):
        bm_box(bm, (sx * (PX0 + PX1) / 2, D / 2, (z0 + z1) / 2), (PX1 - PX0, 1.10, z1 - z0))
# front/rear beams
for (y0, y1) in ((0.030, 0.070), (1.130, 1.170)):
    for (z0, z1) in ((Z_FB0, Z_FB1), (Z_TF0, Z_TF1)):
        bm_box(bm, (0, (y0 + y1) / 2, (z0 + z1) / 2), (2 * PX0, y1 - y0, z1 - z0))
# base kick plates (front / rear) with vent slots
for y in (0.027, 1.173):
    bm_box(bm, (0, y, (Z_FB0 + Z_FB1) / 2 - 0.004), (W - 0.004, 0.003, Z_FB1 - Z_FB0 + 0.008))
    for i in range(14):
        bm_box(bm, (-0.234 + i * 0.036, y - 0.0018 * (1 if y < 0.5 else -1), (Z_FB0 + Z_FB1) / 2), (0.024, 0.0008, 0.010), 1)
# floor plate (bottom closure with cable cut-out)
bm_box(bm, (0, 0.30, Z_FB0 + 0.002), (2 * PX0, 0.48, 0.002))
bm_box(bm, (0, 0.95, Z_FB0 + 0.002), (2 * PX0, 0.30, 0.002))
# rail depth brackets (connect front and rear rails at top and bottom)
for sx in (-1, 1):
    for z in (Z_U1 - 0.010, Z_TOP + 0.002):
        bm_box(bm, (sx * 0.2555, (Y_FR + Y_RR) / 2 + 0.02, z), (0.005, Y_RR - Y_FR + 0.04, 0.008))
    for y in (Y_FR + 0.02, Y_RR + 0.02):
        for z in (Z_U1 - 0.010, Z_TOP + 0.002):
            bm_box(bm, (sx * 0.270, y, z), (0.030, 0.012, 0.008))
frame = RK['mesh_obj']('Frame', bm, [FRAME, M['port']], col, root)

# roof: plate with cable entry slots (brush inserts) - built from strips (XY plane)
bm = bmesh.new()
RX, RY0, RY1 = W / 2, 0.026, 1.174
slots = [(-0.27, -0.10, 0.96, 1.10), (0.10, 0.27, 0.96, 1.10), (-0.10, 0.10, 0.10, 0.17)]
ys = sorted({RY0, RY1} | {s[2] for s in slots} | {s[3] for s in slots})
for ya, yb in zip(ys[:-1], ys[1:]):
    ym = (ya + yb) / 2
    cuts = sorted((s[0], s[1]) for s in slots if s[2] <= ym <= s[3])
    xa = -RX
    for c0, c1 in cuts + [(RX, RX)]:
        if c0 > xa + 1e-6:
            for z, flip in ((HT, False), (Z_TF1, True)):
                vs = [bm.verts.new((xa, ya, z)), bm.verts.new((c0, ya, z)), bm.verts.new((c0, yb, z)), bm.verts.new((xa, yb, z))]
                bm.faces.new(list(reversed(vs)) if flip else vs)
        xa = max(xa, c1)
# roof rim
for (c, s) in (((0, RY0, (HT + Z_TF1) / 2), (W, 0.002, HT - Z_TF1)), ((0, RY1, (HT + Z_TF1) / 2), (W, 0.002, HT - Z_TF1)),
               ((-RX, D / 2, (HT + Z_TF1) / 2), (0.002, RY1 - RY0, HT - Z_TF1)), ((RX, D / 2, (HT + Z_TF1) / 2), (0.002, RY1 - RY0, HT - Z_TF1))):
    bm_box(bm, c, s)
# slot walls + brush strips
for (x0, x1, y0, y1) in slots:
    for c, s in ((((x0 + x1) / 2, y0, (HT + Z_TF1) / 2), (x1 - x0, 0.001, HT - Z_TF1)), (((x0 + x1) / 2, y1, (HT + Z_TF1) / 2), (x1 - x0, 0.001, HT - Z_TF1)),
                 ((x0, (y0 + y1) / 2, (HT + Z_TF1) / 2), (0.001, y1 - y0, HT - Z_TF1)), ((x1, (y0 + y1) / 2, (HT + Z_TF1) / 2), (0.001, y1 - y0, HT - Z_TF1))):
        bm_box(bm, c, s)
    bm_box(bm, ((x0 + x1) / 2, (y0 + y1) / 2, HT - 0.006), (x1 - x0 - 0.002, y1 - y0 - 0.002, 0.004), 1)
roof = RK['mesh_obj']('Roof', bm, [PANEL, BRUSH], col, root)
prints = [RK['text_flat']('roof_logo', 'APC', 0.045, (0.0, 0.55, HT + 0.0002), (0, 0, 0), APC_RED, col, root)]

# ---------------------------------------------------------------- casters + levelling feet
bm = bmesh.new()
for sx in (-1, 1):
    for y in (0.085, 1.115):
        x = sx * 0.232
        bm_box(bm, (x, y, Z_FB0 - 0.004), (0.060, 0.060, 0.006), 1)             # mounting plate
        bm_box(bm, (x, y + 0.010, 0.030), (0.034, 0.008, 0.036), 1)              # swivel fork
        bm_box(bm, (x, y - 0.010, 0.030), (0.034, 0.008, 0.036), 1)
        RK['add_cyl'](bm, (x, y, 0.024), 0.024, 0.016, 'X', 20, 0)               # wheel (axis X)
        RK['add_cyl'](bm, (x, y, 0.024), 0.008, 0.026, 'X', 12, 1)               # hub
    for y in (0.170, 1.030):
        x = sx * 0.232
        RK['add_cyl'](bm, (x, y, 0.030), 0.006, 0.040, 'Z', 12, 1)              # threaded stem
        RK['add_cyl'](bm, (x, y, 0.040), 0.010, 0.006, 'Z', 6, 1)                # hex nut
        RK['add_cyl'](bm, (x, y, 0.008), 0.022, 0.008, 'Z', 20, 0)               # pad (raised 4 mm)
casters = RK['mesh_obj']('Casters_Levellers', bm, [RUBBER, M['steel']], col, root)

# ---------------------------------------------------------------- vertical mounting rails (square holes)
HW_ = 9.5 * mm
hole_offs = (6.35 * mm, 22.225 * mm, 38.1 * mm)
holes_z = [Z_U1 + n * U + o for n in range(NU) for o in hole_offs]
RX0, RX1 = 0.2250, 0.2530        # flange inner/outer |x|
bm = bmesh.new()
for y in (Y_FR, Y_RR):
    for sx in (-1, 1):
        a, b = sorted((sx * RX0, sx * RX1))
        hx0, hx1 = sorted((sx * (HOLE_X - HW_ / 2), sx * (HOLE_X + HW_ / 2)))
        hs = [(hx0, hx1, z - HW_ / 2, z + HW_ / 2) for z in holes_z]
        plate_with_holes(bm, a, b, Z_U1 - 0.012, Z_TOP + 0.010, y, hs, 0)
        # returns: outer flange toward +Y (40 mm) and inner lip
        bm_box(bm, (sx * (RX1 - 0.001), y + 0.020, (Z_U1 + Z_TOP) / 2 - 0.001), (0.002, 0.040, Z_TOP - Z_U1 + 0.022))
        bm_box(bm, (sx * (RX0 + 0.001), y + 0.005, (Z_U1 + Z_TOP) / 2 - 0.001), (0.002, 0.010, Z_TOP - Z_U1 + 0.022))
rails = RK['mesh_obj']('Rails', bm, [RAIL], col, root)

# U numbers + U tick marks on the front rails (outer side of the holes)
ticks = []
for n in range(NU + 1):
    z = Z_U1 + n * U
    for sx in (-1, 1):
        ticks.append(((sx * 0.2445, Y_FR - 0.0002, z), (0.010, 0.0002, 0.0006)))
RK['boxes']('Rail_Ticks', ticks, WHITE, col, root)
for n in range(NU):
    zc = Z_U1 + n * U + U / 2
    for sx in (-1, 1):
        prints.append(RK['text_flat'](f'u{n}', str(n + 1), 0.0042, (sx * 0.2453, Y_FR - 0.0003, zc), (math.pi / 2, 0, 0), WHITE, col, root))
RK['join'](prints, 'Print')

# ---------------------------------------------------------------- 0U accessory channels (rear) + cable tie bars
bm = bmesh.new()
Y_CH = 1.048
X_PDU = 0.235                # PDU / 0U channel centre |x| (cord clears the top-frame side beam)
for sx in (-1, 1):
    x = sx * X_PDU
    bm_box(bm, (x, Y_CH, (Z_U1 + Z_TOP) / 2), (0.050, 0.004, Z_TOP - Z_U1 + 0.04))
    bm_box(bm, (x - sx * 0.024, Y_CH - 0.010, (Z_U1 + Z_TOP) / 2), (0.002, 0.020, Z_TOP - Z_U1 + 0.04))
    for z in (Z_U1 - 0.010, Z_TOP + 0.020):
        bm_box(bm, (sx * 0.267, (Y_CH + 1.13) / 2, z), (0.026, 1.13 - Y_CH, 0.010))
    for k in range(18):                                          # keyhole slots for PDU mounting buttons
        z = Z_U1 + 0.03 + k * 0.104
        bm_box(bm, (x, Y_CH - 0.0021, z), (0.010, 0.0004, 0.018), 1)
        RK['add_cyl'](bm, (x, Y_CH - 0.0021, z + 0.010), 0.0065, 0.0004, 'Y', 12, 1)
    # cable tie bars between the rear rail and the channel, every 6U, + vertical lacing bar
    for k in range(7):
        z = Z_U1 + (k * 6 + 3) * U
        bm_box(bm, (sx * 0.262, (Y_RR + 0.045 + Y_CH) / 2, z), (0.008, Y_CH - Y_RR - 0.045, 0.004))
        for j in range(4):
            bm_box(bm, (sx * 0.262, Y_RR + 0.07 + j * 0.035, z + 0.0035), (0.006, 0.004, 0.003), 1)
    bm_box(bm, (sx * 0.262, Y_RR + 0.12, (Z_U1 + Z_TOP) / 2), (0.006, 0.006, Z_TOP - Z_U1))
channels = RK['mesh_obj']('ZeroU_Channels', bm, [FRAME, M['port']], col, root)


# ---------------------------------------------------------------- doors
def door(name, x0, x1, y0, hinge_x, handle_x, open_deg, handle=True):
    bm = bmesh.new()
    y1 = y0 + DOOR_T
    fw_s, fw_t, fw_b = 0.040, 0.060, 0.055
    ym = (y0 + y1) / 2
    zc = (DOOR_Z0 + DOOR_Z1) / 2; h = DOOR_Z1 - DOOR_Z0
    # frame tubes
    bm_box(bm, (x0 + fw_s / 2, ym, zc), (fw_s, DOOR_T, h))
    bm_box(bm, (x1 - fw_s / 2, ym, zc), (fw_s, DOOR_T, h))
    bm_box(bm, ((x0 + x1) / 2, ym, DOOR_Z1 - fw_t / 2), (x1 - x0 - 2 * fw_s, DOOR_T, fw_t))
    bm_box(bm, ((x0 + x1) / 2, ym, DOOR_Z0 + fw_b / 2), (x1 - x0 - 2 * fw_s, DOOR_T, fw_b))
    # perforated insert (single quad, UV in hole-pattern tiles; holes are alpha-clipped)
    p = 0.0055
    RK['add_quad_xz'](bm, x0 + fw_s, x1 - fw_s, DOOR_Z0 + fw_b, DOOR_Z1 - fw_t, y0 + 0.006, 1, (p, p * math.sqrt(3)))
    # inner stiffener (mid rail behind the mesh)
    bm_box(bm, ((x0 + x1) / 2, y1 - 0.004, zc), (x1 - x0 - 2 * fw_s, 0.006, 0.020))
    # hinges
    for z in (DOOR_Z0 + 0.12, zc, DOOR_Z1 - 0.12):
        RK['add_cyl'](bm, (hinge_x, ym, z), 0.006, 0.060, 'Z', 12, 2)
    if handle:
        hz = 1.02
        hy = y0 if y0 < 0.5 else y1
        sgn = -1 if y0 < 0.5 else 1
        bm_box(bm, (handle_x, hy + sgn * 0.004, hz), (0.026, 0.008, 0.190), 3)          # handle escutcheon
        bm_box(bm, (handle_x, hy + sgn * 0.010, hz - 0.01), (0.016, 0.006, 0.140), 2)   # swing handle
        RK['add_cyl'](bm, (handle_x, hy + sgn * 0.009, hz + 0.075), 0.0055, 0.004, 'Y', 16, 2)   # key cylinder
    o = RK['mesh_obj'](name, bm, [PANEL, PERF, HANDLE, FRAME], col, root)
    RK['set_origin'](o, (hinge_x, ym, 0.0))
    o['hinge_axis'] = 'Z'; o['open_angle_deg'] = open_deg
    o['note'] = 'rotate about local Z (hinge axis at the origin) by 0..open_angle_deg to open'
    return o


door_f = door('Door_Front', -0.298, 0.298, 0.0, -0.291, 0.268, -110.0)
door_rl = door('Door_Rear_L', -0.298, -0.0015, D - DOOR_T, -0.291, 0.0, 110.0, handle=False)
door_rr = door('Door_Rear_R', 0.0015, 0.298, D - DOOR_T, 0.291, 0.022, -110.0)

# ---------------------------------------------------------------- side panels (upper/lower, removable)
panels = []
for sx, side in ((-1, 'L'), (1, 'R')):
    for part, (z0, z1) in (('lower', (0.054, 1.010)), ('upper', (1.016, 1.972))):
        bm = bmesh.new()
        x = sx * (W / 2 - 0.006)
        bm_box(bm, (x, D / 2, (z0 + z1) / 2), (0.012, D - 2 * DOOR_T - 0.006, z1 - z0))
        # pressed recess outline (subtle) and lock
        bm_box(bm, (sx * (W / 2 + 0.0002), D / 2, (z0 + z1) / 2), (0.0004, D - 0.20, z1 - z0 - 0.10), 0)
        lz = z1 - 0.055
        bm_box(bm, (sx * (W / 2 + 0.0008), D / 2, lz), (0.0016, 0.034, 0.050), 1)
        RK['add_cyl'](bm, (sx * (W / 2 + 0.0018), D / 2, lz + 0.010), 0.0055, 0.003, 'X', 16, 2)
        bm_box(bm, (sx * (W / 2 + 0.0018), D / 2, lz - 0.010), (0.003, 0.018, 0.012), 1)
        o = RK['mesh_obj'](f'Panel_Side_{side}_{part}', bm, [PANEL, FRAME, HANDLE], col, root)
        o['removable'] = True
        panels.append(o)

# ---------------------------------------------------------------- slots / sockets
for n in range(NU):
    RK['empty'](f'SLOT_U{n + 1:02d}', (0, Y_FR, Z_U1 + n * U), root, col, kind='PLAIN_AXES', size=0.02,
                props={'u': n + 1, 'rear_rail_y': Y_RR})
for sx, side in ((-1, 'L'), (1, 'R')):
    RK['empty'](f'SLOT_pdu_rear_{side}', (sx * X_PDU, Y_CH + 0.062, 0.100), root, col,
                rot=(0, 0, math.pi), kind='ARROWS', size=0.05,
                props={'mount': '0U PDU, outlets facing the rear door (+Y)', 'asset': 'rack_pdu_0u'})
for name, loc in (('SLOT_roof_cable_L', (-0.185, 1.03, HT)), ('SLOT_roof_cable_R', (0.185, 1.03, HT)), ('SLOT_roof_cable_F', (0.0, 0.135, HT)),
                  ('SLOT_floor_cable', (0.0, 0.70, Z_FB0))):
    RK['empty'](name, loc, root, col, kind='PLAIN_AXES', size=0.05)

root['model'] = 'APC NetShelter SX AR3300'
root['rack_units'] = NU; root['mount'] = '19in EIA-310 square hole'
root['dimensions_mm'] = '600 W x 1200 D x 1991 H'; root['footprint_m'] = '0.60 x 1.20'
root['front_rail_y'] = Y_FR; root['rear_rail_y'] = Y_RR; root['u1_bottom_z'] = Z_U1
root['variant_open_frame'] = 'hide Door_* and Panel_Side_* objects'

tris = RK['finish'](ROOT, BLEND, ROOT + '.glb')

# ================================================================ preview: populate the rack (not exported)
def append_tree(blend, root_name):
    path = os.path.join(RK['BASE'], blend)
    if not os.path.exists(path):
        return None
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects]
    prev = H['coll']('Preview')
    new_root = None
    for o in dst.objects:
        if o is None:
            continue
        if o.type in ('CAMERA', 'LIGHT') or o.name.startswith('Floor'):
            bpy.data.objects.remove(o, do_unlink=True); continue
        prev.objects.link(o)
        if o.name.split('.')[0] == root_name and o.parent is None:
            new_root = o
    for o in list(dst.objects):
        try:
            if o and o.parent is None and o is not new_root and o.users_collection and o.name.split('.')[0] != root_name:
                o.hide_render = True
        except ReferenceError:
            pass
    return new_root


def copy_tree(src_root, col_):
    mp = {}
    for o in [src_root] + list(src_root.children_recursive):
        c = o.copy(); col_.objects.link(c); mp[o] = c
    for o, c in mp.items():
        if o.parent in mp:
            c.parent = mp[o.parent]
    return mp[src_root]


if '--norender' not in sys.argv:
    prev = H['coll']('Preview')
    slot = lambda n: bpy.data.objects[f'SLOT_U{n:02d}'].matrix_world.translation.copy()
    sw2 = append_tree('net_02_ib_quantum2_qm9700.blend', 'net_02_ib_quantum2_qm9700')
    sw1 = append_tree('net_01_ib_quantum_qm8700.blend', 'net_01_ib_quantum_qm8700')
    acc = append_tree('rack_accessories.blend', 'rack_accessories')
    pdu = append_tree('rack_pdu_0u.blend', 'rack_pdu_0u')
    if sw2:
        sw2.location = slot(42)
    if sw1:
        sw1.location = slot(40)
    if acc:
        acc.location = (0, 0, 0)
        subs = {c.name.split('.')[0]: c for c in acc.children}
        acc.location = (0, 1000, 0)   # park the original set
        placements = [('cablemgr_1u', 41), ('cablemgr_2u', 38)] + [('blank_2u', n) for n in list(range(1, 23, 2)) + list(range(31, 37, 2))] + [('cablemgr_1u', 37)]
        for nm, n in placements:
            if nm in subs:
                c = copy_tree(subs[nm], prev); c.parent = None; c.location = slot(n)
    if pdu:
        pdu.location = bpy.data.objects['SLOT_pdu_rear_L'].matrix_world.translation; pdu.rotation_euler = (0, 0, math.pi)
        p2 = copy_tree(pdu, prev); p2.location = bpy.data.objects['SLOT_pdu_rear_R'].matrix_world.translation; p2.rotation_euler = (0, 0, math.pi)

    C = (0, 0.6, 1.0)
    views = {
        'front34': ((-1.9, -3.2, 1.7), (0, 0.6, 0.98), 35),
        'rear34': ((2.0, 4.6, 1.8), (0, 0.6, 0.98), 35),
        'front': ((0, -4.4, 1.0), (0, 0.5, 1.0), 35),
    }
    RK['render']('rack_01_42u', views, 2.0, C, floor_z=0.0)
    # doors open + side panel off
    door_f.rotation_euler = (0, 0, math.radians(-100))
    door_rl.rotation_euler = (0, 0, math.radians(100)); door_rr.rotation_euler = (0, 0, math.radians(-100))
    for p_ in panels:
        if '_L_' in p_.name:
            p_.hide_render = True
    RK['render']('rack_01_42u', {
        'open34': ((-2.4, -2.6, 1.6), (0, 0.5, 1.0), 35),
        'open_rear': ((1.6, 3.6, 1.5), (0, 0.8, 1.0), 35),
        'rails': ((0.02, -0.42, 1.30), (0.21, Y_FR, 1.22), 45),
        'switches': ((-0.05, -0.55, 1.88), (0.20, Y_FR, 1.80), 50),
        'top': ((0.9, -1.0, 2.9), (0, 0.6, 1.9), 35),
        'bottom': ((-0.9, -1.2, 0.35), (0, 0.3, 0.08), 35),
    }, 2.0, C, floor_z=0.0)
