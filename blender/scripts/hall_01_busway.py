"""Overhead track busway (Starline / Legrand Track Busway, 400 A class) - tileable pieces.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python hall_01_busway.py [-- --norender]

Real references (see report):
  - Starline 400 A housing 5.05 in W x 5.80 in H (128 x 147 mm) per HCAI seismic certification OSP-0647.
  - Starline cut-away render: finned extruded aluminium housing, central bottom access slot, conductors in
    insulated carriers on both sides of the slot (starlinepower.com/overhead-power).
  - Plug-in units: rectangular box hanging below the slot, two locking ears on top, breaker window + meter
    on the face, drop cord(s) to IEC 60309 pin & sleeve connectors (starline_track.png / starline_flex.png).
  - Tap-off colour is orange (hall art direction from research 02-datacenter.md); Starline's are light grey.
Pieces (origin = floor under the joint plane / piece centre, busway centreline at BUSWAY_Z = 3.10 m):
  Busway_Straight_3m, Busway_Joint, Busway_Elbow90, Busway_EndFeed, Busway_EndCap,
  Busway_TapOff_1C, Busway_TapOff_2C, Busway_Hanger
"""
import bpy, bmesh, math, mathutils, os, sys
from mathutils import Vector

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\hall_lib.py', encoding='utf-8').read())

FILE = 'hall_01_busway'
BLEND = os.path.join(BASE, FILE + '.blend')
reset_scene()
M = mats()
COL = 'HALL_Busway'
stats = []

W, HH = 0.128, 0.147          # housing width / height
SW, SD = 0.030, 0.060         # bottom access slot width / depth
Z = BUSWAY_Z
ZB = Z - HH / 2               # housing bottom
ZT = Z + HH / 2


def housing_profile(scale=1.0):
    p = [(SW / 2, -HH / 2), (W / 2, -HH / 2)]
    for z in (-0.045, -0.015, 0.015, 0.045):
        p += [(W / 2, z - 0.002), (W / 2 + 0.003, z - 0.002), (W / 2 + 0.003, z + 0.002), (W / 2, z + 0.002)]
    p.append((W / 2, HH / 2))
    for x in (0.050, 0.030, 0.010, -0.010, -0.030, -0.050):
        p += [(x + 0.0015, HH / 2), (x + 0.0015, HH / 2 + 0.006), (x - 0.0015, HH / 2 + 0.006), (x - 0.0015, HH / 2)]
    p.append((-W / 2, HH / 2))
    for z in (0.045, 0.015, -0.015, -0.045):
        p += [(-W / 2, z + 0.002), (-W / 2 - 0.003, z + 0.002), (-W / 2 - 0.003, z - 0.002), (-W / 2, z - 0.002)]
    p += [(-W / 2, -HH / 2), (-SW / 2, -HH / 2), (-SW / 2, -HH / 2 + SD), (SW / 2, -HH / 2 + SD)]
    return [(a * scale, b * scale) for a, b in p]


def conductors(name, pts, root, col):
    """L1/L2/L3/N on the slot walls + PE on the slot ceiling, one merged flow mesh (u along the run)."""
    items = []
    for a in (SW / 2 - 0.0025, -(SW / 2 - 0.0025)):
        for b in (-HH / 2 + 0.022, -HH / 2 + 0.044):
            items.append(rect(0.002, 0.010, a, b))
    items.append(rect(0.014, 0.002, 0.0, -HH / 2 + SD - 0.0025))
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    L = 0
    for prof in items:
        L = sweep_bm(bm, uvl, pts, prof, 0.0, 8, True, True)
    o = finish_bm(name, bm, M['copper'], col, root)
    o['flow_u_start'] = 0.0; o['flow_u_end'] = round(L, 5); o['flow_kind'] = 'power'
    tag_obj(o, 'flow', root)
    # dark insulating carriers behind the conductors
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    for a in (SW / 2 - 0.0007, -(SW / 2 - 0.0007)):
        sweep_bm(bm, uvl, pts, rect(0.0012, SD - 0.004, a, -HH / 2 + SD / 2), 0.0, 8, True, True)
    finish_bm(name.replace('FLOW', 'Insulator'), bm, M['insul'], col, root)
    return o


def housing(name, pts, root, col):
    o, L = sweep(name, pts, housing_profile(), M['alu_satin'], col, root)
    return o


# ------------------------------------------------------------------ 1. straight 3 m
root, col = piece('Busway_Straight_3m', 'BW_S3', COL)
pts = [(-1.5, 0, Z), (1.5, 0, Z)]
housing('Housing', pts, root, col)
conductors('FLOW_busbars', pts, root, col)
# printed rating label on the side
H['box']('Label_Rating', (0.12, 0.0006, 0.035), (-1.2, -W / 2 - 0.0005, Z + 0.03), M['label'], col, parent=root)
H['text_mesh']('Text_Brand', 'STARLINE  400A', FONT, 0.016, M['label_blk'], col, root, (-1.2, -W / 2 - 0.0009, Z + 0.03), (math.pi / 2, 0, 0))
joint('JOINT_a', (-1.5, 0, Z), (-1, 0, 0), root, col)
joint('JOINT_b', (1.5, 0, Z), (1, 0, 0), root, col)
socket('SOCKET_power_in', (-1.5, 0, Z), (-1, 0, 0), root, col)
socket('SOCKET_power_out', (1.5, 0, Z), (1, 0, 0), root, col)
root['length_m'] = 3.0
finish_piece(root, 'BW_S3', FILE, stats)

# ------------------------------------------------------------------ 2. joint kit (centred on the butt plane)
root, col = piece('Busway_Joint', 'BW_J', COL)
JL = 0.16
t = 0.006
H['box']('Cover_Top', (JL, W + 2 * t + 0.006, t), (0, 0, ZT + 0.006 + t / 2), M['alu_dark'], col, parent=root, bevel=0.001)
for s in (-1, 1):
    H['box'](f'Cover_Side_{s:+d}', (JL, t, HH + 0.012 + t), (0, s * (W / 2 + 0.003 + t / 2), Z + 0.003), M['alu_dark'], col, parent=root, bevel=0.001)
    H['box'](f'Cover_Bottom_{s:+d}', (JL, (W - SW) / 2 + t, t), (0, s * (SW / 2 + (W - SW) / 4 + t / 2 + 0.002), ZB - t / 2, ), M['alu_dark'], col, parent=root)
    for k, x in enumerate((-0.05, 0.05)):
        for zz in (Z - 0.035, Z + 0.035):
            H['cyl'](f'Bolt_{s:+d}_{k}_{zz:.2f}', 0.0055, 0.006, (x, s * (W / 2 + 0.012), zz), M['steel'], col, verts=6, rot=(math.pi / 2, 0, 0), parent=root)
conductors('FLOW_busbars', [(-JL / 2, 0, Z), (JL / 2, 0, Z)], root, col)
joint('JOINT_a', (0, 0, Z), (-1, 0, 0), root, col)
joint('JOINT_b', (0, 0, Z), (1, 0, 0), root, col)
socket('SOCKET_power_in', (-JL / 2, 0, Z), (-1, 0, 0), root, col)
socket('SOCKET_power_out', (JL / 2, 0, Z), (1, 0, 0), root, col)
finish_piece(root, 'BW_J', FILE, stats)

# ------------------------------------------------------------------ 3. 90 degree horizontal elbow (one grid cell)
root, col = piece('Busway_Elbow90', 'BW_E', COL)
pts = [(-CELL / 2, 0, Z), (0, 0, Z), (0, CELL / 2, Z)]
housing('Housing', pts, root, col)
conductors('FLOW_busbars', pts, root, col)
joint('JOINT_a', (-CELL / 2, 0, Z), (-1, 0, 0), root, col)
joint('JOINT_b', (0, CELL / 2, Z), (0, 1, 0), root, col)
socket('SOCKET_power_in', (-CELL / 2, 0, Z), (-1, 0, 0), root, col)
socket('SOCKET_power_out', (0, CELL / 2, Z), (0, 1, 0), root, col)
finish_piece(root, 'BW_E', FILE, stats)

# ------------------------------------------------------------------ 4. end feed (box at the start of a run, feeds +X)
root, col = piece('Busway_EndFeed', 'BW_F', COL)
FX0, FX1 = -0.47, -0.04
FZ0, FZ1 = ZB - 0.14, ZT + 0.05
housing('Housing_Stub', [(FX1 - 0.01, 0, Z), (0, 0, Z)], root, col)
H['box']('Body', (FX1 - FX0, 0.30, FZ1 - FZ0), ((FX0 + FX1) / 2, 0, (FZ0 + FZ1) / 2), M['light_pl'], col, parent=root, bevel=0.006)
H['box']('Cover', (FX1 - FX0 - 0.04, 0.006, FZ1 - FZ0 - 0.05), ((FX0 + FX1) / 2, -0.153, (FZ0 + FZ1) / 2), M['grey_pl'], col, parent=root, bevel=0.003)
for i, (x, zz) in enumerate([(FX0 + 0.04, FZ0 + 0.04), (FX1 - 0.04, FZ0 + 0.04), (FX0 + 0.04, FZ1 - 0.04), (FX1 - 0.04, FZ1 - 0.04)]):
    H['cyl'](f'Screw_{i}', 0.006, 0.004, (x, -0.157, zz), M['steel'], col, verts=8, rot=(math.pi / 2, 0, 0), parent=root)
H['box']('Label_Warning', (0.07, 0.001, 0.06), ((FX0 + FX1) / 2 + 0.08, -0.157, FZ1 - 0.07), M['yellow'], col, parent=root)
H['box']('Label_Name', (0.16, 0.001, 0.045), ((FX0 + FX1) / 2 - 0.05, -0.157, FZ1 - 0.07), M['label'], col, parent=root)
H['text_mesh']('Text_Feed', 'END FEED 400A', FONT, 0.018, M['label_blk'], col, root, ((FX0 + FX1) / 2 - 0.05, -0.1585, FZ1 - 0.07), (math.pi / 2, 0, 0))
led('LED_power', (0.012, 0.004, 0.012), ((FX0 + FX1) / 2 + 0.08, -0.158, FZ0 + 0.06), (0.1, 1.0, 0.2), root, col)
# conduit hub + flexible conduit to the ceiling (the visible feeder: flow mesh)
cx = (FX0 + FX1) / 2
H['cyl']('Conduit_Hub', 0.05, 0.04, (cx, 0, FZ1 + 0.02), M['zinc'], col, verts=16, parent=root)
cond, Lc = sweep('FLOW_feeder', [(cx, 0, CEIL_Z), (cx, 0, FZ1 + 0.04)], circle(0.038, 14), M['grey_pl'], col, root,
                 smooth=True, flow='power', root=root)
for k in range(1, 8):
    zz = FZ1 + 0.04 + k * (CEIL_Z - FZ1 - 0.04) / 8
    H['cyl'](f'Conduit_Rib_{k}', 0.041, 0.012, (cx, 0, zz), M['grey_pl'], col, verts=14, parent=root)
H['cyl']('Conduit_Ceiling', 0.06, 0.02, (cx, 0, CEIL_Z - 0.01), M['zinc'], col, verts=16, parent=root)
conductors('FLOW_busbars', [(FX1 - 0.01, 0, Z), (0, 0, Z)], root, col)
joint('JOINT_b', (0, 0, Z), (1, 0, 0), root, col)
socket('SOCKET_power_in', (cx, 0, CEIL_Z), (0, 0, 1), root, col)
socket('SOCKET_power_out', (0, 0, Z), (1, 0, 0), root, col)
finish_piece(root, 'BW_F', FILE, stats)

# ------------------------------------------------------------------ 5. end cap
root, col = piece('Busway_EndCap', 'BW_C', COL)
sweep('Cap', [(0.0, 0, Z), (0.014, 0, Z)], rrect(W + 0.012, HH + 0.012, 0.006), M['alu_dark'], col, root)
joint('JOINT_a', (0, 0, Z), (-1, 0, 0), root, col)
finish_piece(root, 'BW_C', FILE, stats)


# ------------------------------------------------------------------ 6/7. plug-in tap-off units
def tapoff(name, tag, ncirc):
    root, col = piece(name, tag, COL)
    BW = 0.30 if ncirc == 1 else 0.42           # along the busway (x)
    BD, BHt = 0.15, 0.25
    zn0 = ZB - 0.03
    zb0, zb1 = zn0 - BHt, zn0
    # head inside the slot and neck through it
    H['box']('Head', (0.12, SW - 0.008, SD - 0.012), (0, 0, ZB + (SD - 0.012) / 2), M['insul'], col, parent=root)
    H['box']('Neck', (0.14, 0.05, 0.03), (0, 0, ZB - 0.015), M['grey_pl'], col, parent=root, bevel=0.004)
    for s in (-1, 1):   # rotating locking ears
        H['box'](f'Ear_{s:+d}', (0.03, 0.05, 0.05), (s * (BW / 2 - 0.03), 0, zb1 + 0.02), M['light_pl'], col, parent=root, bevel=0.008)
    H['box']('Body', (BW, BD, BHt), (0, 0, (zb0 + zb1) / 2), M['orange'], col, parent=root, bevel=0.012, segs=3)
    fy = -BD / 2 - 0.002
    H['box']('Faceplate', (BW - 0.04, 0.004, 0.12), (0, fy, zb1 - 0.08), M['light_pl'], col, parent=root, bevel=0.003)
    # breaker window with MCB toggles
    nb = 3 * ncirc
    ww = 0.022 * nb + 0.02
    wx = BW / 2 - 0.03 - ww / 2
    H['box']('Breaker_Recess', (ww, 0.003, 0.07), (wx, fy - 0.002, zb1 - 0.075), M['port'], col, parent=root)
    for i in range(nb):
        bx = wx - ww / 2 + 0.02 + i * 0.022
        H['box'](f'MCB_{i}', (0.018, 0.006, 0.05), (bx, fy - 0.004, zb1 - 0.075), M['label'], col, parent=root)
        H['box'](f'MCB_Toggle_{i}', (0.006, 0.008, 0.012), (bx, fy - 0.008, zb1 - 0.068), M['plastic'], col, parent=root)
    H['box']('Breaker_Window', (ww + 0.006, 0.002, 0.076), (wx, fy - 0.0125, zb1 - 0.075), M['glass_dark'], col, parent=root)
    # meter display + status
    mx = -BW / 2 + 0.06
    H['box']('Meter_Bezel', (0.06, 0.004, 0.08), (mx, fy - 0.002, zb1 - 0.08), M['plastic'], col, parent=root)
    led('LED_display', (0.044, 0.002, 0.024), (mx, fy - 0.0045, zb1 - 0.065), (0.2, 0.9, 1.0), root, col, 3.0)
    led('LED_status', (0.008, 0.002, 0.008), (mx, fy - 0.0045, zb1 - 0.105), (0.1, 1.0, 0.2), root, col)
    H['text_mesh']('Text_Brand', 'STARLINE', FONT, 0.022, M['label'], col, root, (0, fy + 0.0015, zb0 + 0.045), (math.pi / 2, 0, 0))
    socket('SOCKET_power_in', (0, 0, ZB + SD - 0.012), (0, 0, 1), root, col)
    zc_top = RACK_H + 0.10 + 0.17       # connector top
    xs = [0.0] if ncirc == 1 else [-0.09, 0.09]
    for i, x in enumerate(xs):
        sfx = '' if ncirc == 1 else f'_{i}'
        H['cyl'](f'Gland{sfx}', 0.018, 0.03, (x, 0, zb0 - 0.012), M['grey_pl'], col, verts=12, parent=root)
        H['cyl'](f'Gland_Nut{sfx}', 0.021, 0.012, (x, 0, zb0 - 0.004), M['grey_pl'], col, verts=6, parent=root)
        sweep(f'FLOW_cord{sfx}', [(x, 0, zb0 + 0.01), (x, 0, zb0 - 0.04), (x, 0, zc_top)], circle(0.011, 12),
              M['rubber'], col, root, smooth=True, flow='power', root=root)
        H['cyl'](f'Cord_Relief{sfx}', 0.016, 0.06, (x, 0, zc_top + 0.03), M['rubber'], col, verts=12, parent=root)
        # IEC 60309 5-pin plug (red = 400/415 V 3-phase)
        H['cyl'](f'Plug_Grip{sfx}', 0.036, 0.11, (x, 0, zc_top - 0.055), M['light_pl'], col, verts=20, parent=root, bevel=0.004)
        for k in range(6):
            a = 2 * math.pi * k / 6
            H['box'](f'Plug_Rib{sfx}_{k}', (0.006, 0.006, 0.08), (x + 0.037 * math.cos(a), 0.037 * math.sin(a), zc_top - 0.055), M['light_pl'], col, parent=root)
        H['cyl'](f'Plug_Ring{sfx}', 0.042, 0.06, (x, 0, zc_top - 0.14), M['pin_red'], col, verts=20, parent=root, bevel=0.003)
        socket(f'SOCKET_power_out{sfx}', (x, 0, zc_top - 0.17), (0, 0, -1), root, col)
    root['tapoff_circuits'] = ncirc
    finish_piece(root, tag, FILE, stats)
    return root


tapoff('Busway_TapOff_1C', 'BW_T1', 1)
tapoff('Busway_TapOff_2C', 'BW_T2', 2)

# ------------------------------------------------------------------ 8. hanger (clamp + threaded rod to CEIL_Z)
root, col = piece('Busway_Hanger', 'BW_H', COL)
H['box']('Clamp_Top', (0.04, W + 0.03, 0.006), (0, 0, ZT + 0.009), M['zinc'], col, parent=root)
for s in (-1, 1):
    H['box'](f'Clamp_Side_{s:+d}', (0.04, 0.004, 0.06), (0, s * (W / 2 + 0.013), ZT - 0.02), M['zinc'], col, parent=root)
threaded_rod('Rod', 0, 0, ZT + 0.012, CEIL_Z, root, col, M)
H['cyl']('Rod_Nut', 0.009, 0.01, (0, 0, ZT + 0.017), M['zinc'], col, verts=6, parent=root)
H['cyl']('Anchor', 0.03, 0.008, (0, 0, CEIL_Z - 0.004), M['zinc'], col, verts=12, parent=root)
root['rod_top_z'] = CEIL_Z
finish_piece(root, 'BW_H', FILE, stats)

# ------------------------------------------------------------------ save + export
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
export_all(FILE, stats)

# ------------------------------------------------------------------ renders (layout built from linked duplicates)
if DO_RENDER:
    P = {r.name: r for r, t in PIECES}
    for r, t in PIECES:
        for o in [r] + list(r.children_recursive):
            o.hide_render = True
    # a run over a row of 10 racks: feed | 3 m | joint | 3 m | cap, tap-offs on every rack
    dup(P['Busway_EndFeed'], (-3.0, 0, 0))
    dup(P['Busway_Straight_3m'], (-1.5, 0, 0))
    dup(P['Busway_Joint'], (0, 0, 0))
    dup(P['Busway_Straight_3m'], (1.5, 0, 0))
    dup(P['Busway_EndCap'], (3.0, 0, 0))
    for i in range(10):
        x = -2.7 + i * 0.6
        dup(P['Busway_TapOff_2C'] if i % 3 == 0 else P['Busway_TapOff_1C'], (x, 0, 0))
    for x in (-2.0, 1.0):
        dup(P['Busway_Hanger'], (x + 0.3, 0, 0))
    # elbow leg turning the run into a cross-aisle
    context_racks([-2.7 + i * 0.6 for i in range(10)], -0.535, facing=-1)
    studio(8.0, (0, 0, 2.5))
    add_sun(1.0)
    render_views('hall_01_busway', {
        'run':     ((-5.2, -6.0, 2.2), (0.0, 0.0, 2.8), 30),
        'tapoff':  ((-1.9, -1.10, 2.65), (-2.4, 0.0, 2.75), 35),
        'endfeed': ((-3.0, -1.6, 2.4), (-3.1, 0.0, 3.25), 30),
        'under':   ((-1.4, -0.6, 2.4), (-1.7, 0.0, 3.06), 30),
    })
    # piece gallery
    for o in bpy.data.collections['RenderContext'].objects:
        o.hide_render = True
    gal = [('Busway_Elbow90', (0.7, 0)), ('Busway_Joint', (1.4, 0)), ('Busway_TapOff_2C', (2.1, 0)), ('Busway_EndCap', (2.7, 0))]
    for n, (x, y) in gal:
        d = dup(P[n], (x, y, 0))
        for o in [d] + list(d.children_recursive):
            o.hide_render = False
    render_views('hall_01_busway', {'pieces': ((1.1, -2.6, 3.9), (1.75, 0.0, 2.95), 32)})
