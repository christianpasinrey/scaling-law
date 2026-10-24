"""NVIDIA A100 SXM4 (2020) with its HGX A100 / DGX A100 passive heatsink.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python <this file>

Module lies flat: PCB top = z 0, X = long side, Y = short side, origin = module centre.
Module footprint measured from NVIDIA's orthographic 'A100 GPU on SXM4' render, scaled by the
HBM2e stack footprint (7.75 x 11.87 mm): 139 x 77 mm (same envelope as SXM2).
Heatsink measured from ServeTheHome ISC 2022 side/bottom photos and the DGX A100 user-guide tray image.
Heatsink parts are parented to the child empty 'A100_SXM4_Heatsink'.
"""
import bpy, math
exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\sxm_lib.py', encoding='utf-8').read())

ROOT = 'A100_SXM4'
L, W, T = 139.0, 77.0, 2.0
HL, HW_, HS_TOP = 143.0, 79.0, 94.0     # heatsink length / width / top above PCB (mm)

root, col = H['new_card_scene'](ROOT)
M = H['base_materials']()
mat = H['mat']
M_pcb = mat('HW_PCB_SXM', (0.009, 0.010, 0.010), 0.0, 0.62, spec=0.3)
M_ring = mat('HW_PlatedRing', (0.80, 0.52, 0.30), 1.0, 0.35)
M_hole = M['port']
M_goldpad = mat('HW_GoldPad', (0.72, 0.48, 0.20), 1.0, 0.42)
M_chip = mat('HW_ChipBlack', (0.015, 0.015, 0.017), 0.0, 0.35, spec=0.4)
M_mlcc = mat('HW_MLCCBrown', (0.16, 0.08, 0.04), 0.0, 0.5)
M_ind = mat('HW_InductorGrey', (0.20, 0.20, 0.205), 0.75, 0.42)
M_sub = mat('HW_SubstrateTeal', (0.012, 0.075, 0.07), 0.0, 0.45)
M_under = mat('HW_UnderfillBlack', (0.01, 0.01, 0.012), 0.0, 0.4)
M_die = mat('HW_DieMirror', (0.75, 0.76, 0.78), 1.0, 0.12)
M_hbm = mat('HW_HBMSilver', (0.62, 0.63, 0.65), 1.0, 0.22)
M_stiff = mat('HW_StiffenerBlack', (0.012, 0.012, 0.013), 0.5, 0.42)
M_conn = mat('HW_MezzHousingBlack', (0.03, 0.03, 0.032), 0.0, 0.5)
M_pin = M['gold']
M_padsil = mat('HW_ThermalPadSilver', (0.22, 0.215, 0.20), 0.6, 0.55)
M_white = mat('HW_LabelWhite', (0.8, 0.8, 0.8), 0.0, 0.5)
M_screw = mat('HW_ScrewBlack', (0.02, 0.02, 0.02), 0.7, 0.35)
M_steel = M['steel']
# heatsink
M_champ = mat('HW_A100HSChampagne', (0.50, 0.47, 0.42), 1.0, 0.32)
M_rib = mat('HW_A100HSRib', (0.58, 0.55, 0.50), 1.0, 0.26)
M_band = mat('HW_A100HSBand', (0.012, 0.016, 0.018), 0.4, 0.3)
M_window = mat('HW_A100HSWindow', (0.012, 0.016, 0.018), 0.1, 0.2)
M_fin = mat('HW_A100HSFin', (0.42, 0.42, 0.43), 1.0, 0.38)
M_nickel = mat('HW_NickelBase', (0.62, 0.60, 0.56), 1.0, 0.3)
M_logo = mat('HW_LogoBlack', (0.003, 0.003, 0.003), 0.0, 0.85, spec=0.1)

box = lambda n, size, loc, m, **k: H['box'](n, tuple(v * mm for v in size), tuple(v * mm for v in loc), m, col, parent=k.pop('parent', root), **k)

# ---------------------------------------------------------------- PCB + plated holes
box('PCB', (L, W, T), (0, 0, -T / 2), M_pcb, bevel=0.0012, segs=3)
ring_xy = [(x, y) for x in (-46.3, -35.9, 35.1, 45.1) for y in (-34.3, 34.3)]
rings_mesh('PCB_Rings_Top', ring_xy, 3.7, 1.9, 0.03, M_ring, col, root)
rings_mesh('PCB_Rings_Bot', ring_xy, 3.7, 1.9, -T - 0.03, M_ring, col, root)
discs('PCB_Holes_Top', ring_xy + [(-66.0, -35.2), (61.9, 7.1), (65.5, 36.0)], 1.9, 0.04, M_hole, col, root)
discs('PCB_Holes_Bot', ring_xy + [(-66.0, -35.2), (61.9, 7.1), (65.5, 36.0)], 1.9, -T - 0.04, M_hole, col, root)

# ---------------------------------------------------------------- GA100 package (55 x 55 mm), 6 HBM2e
box('Pkg_Substrate', (55.0, 55.0, 1.3), (-0.4, -0.5, 0.65), M_sub, bevel=0.0002)
box('Pkg_Underfill', (44.5, 38.5, 0.5), (-0.4, -0.5, 1.45), M_under, bevel=0.0004)
box('GPU_Die', (26.4, 32.7, 0.9), (-0.4, -0.5, 1.95), M_die)
boxes('HBM2e_Stacks', [((sx * 17.6 - 0.4, -0.5 + dy, 1.9), (7.75, 11.87, 0.8)) for sx in (-1, 1) for dy in (-12.2, 0.0, 12.2)], M_hbm, col, root)
boxes('Pkg_Caps', [((-15.0 + i * 1.3, sy * 22.8 - 0.5, 1.45), (0.8, 0.45, 0.3)) for i in range(24) for sy in (-1, 1)], M_chip, col, root)
nv_logo('Die_Logo', -0.4, 3.2, 2.4, 7.5, M_logo, M_die, col, root)
label_text('Die_NVIDIA', 'nVIDIA', 4.6, (-0.4, -5.0, 2.42), M_logo, col, root, extrude_mm=0.02)

# ---------------------------------------------------------------- gold power-stage shields and components
boxes('Gold_Pads', [((-0.45, sy * 32.6, 0.6), (45.7, 8.6, 1.2)) for sy in (-1, 1)] +
      [((-50.4, -0.3, 0.6), (10.4, 44.6, 1.2)), ((52.4, 13.6, 0.6), (10.8, 29.3, 1.2))], M_goldpad, col, root)
boxes('Gold_Pad_Dots', [((-23.0 + i * 2.95, sy * (32.6 - 3.3), 1.22), (1.4, 1.0, 0.06)) for i in range(16) for sy in (-1, 1)],
      M_hole, col, root)
boxes('Chips_Black', [((-63.7, 32.0, 0.9), (5.9, 9.6, 1.8)), ((-58.0, 28.5, 0.9), (7.0, 6.7, 1.8)), ((-62.0, -30.0, 0.9), (8.0, 9.0, 1.8)),
                      ((63.0, -21.5, 1.4), (11.0, 10.4, 2.8)), ((62.2, -32.8, 1.6), (12.6, 9.8, 3.2)), ((-63.5, -12.0, 0.5), (4.0, 4.0, 1.0)),
                      ((63.0, 30.0, 0.5), (4.0, 3.5, 1.0)), ((53.0, 31.0, 0.5), (3.0, 3.0, 1.0))], M_chip, col, root)
boxes('Inductors', [((57.0, -8.5, 1.2), (5.5, 5.0, 2.4)), ((60.5, 18.0, 1.2), (4.0, 4.0, 2.4)), ((55.0, -26.0, 1.2), (5.0, 5.0, 2.4)),
                    ((-63.0, 22.0, 1.0), (4.5, 4.5, 2.0))], M_ind, col, root)
boxes('MLCC_Columns', [((-57.5, 13.5 - 2.3 * k, 0.6), (3.2, 1.6, 1.2)) for k in range(4)] +
      [((-57.5, -10.0 - 2.3 * k, 0.6), (3.2, 1.6, 1.2)) for k in range(4)] +
      [((-43.0, 12.0 - 6.0 * k, 0.6), (1.6, 3.2, 1.2)) for k in range(4)] +
      [((67.0, 6.0 - 2.3 * k, 0.6), (3.2, 1.6, 1.2)) for k in range(7)] +
      [((44.5, 22.0 - 2.4 * k, 0.6), (1.6, 3.2, 1.2)) for k in range(5)] +
      [((-57.0, -34.0 + 2.2 * k, 0.5), (1.6, 1.0, 1.0)) for k in range(3)] +
      [((58.0, -12.0 - 2.0 * k, 0.5), (2.0, 1.25, 1.0)) for k in range(5)], M_mlcc, col, root)
avoid_top = [(-28.5, 27.7, -28.5, 27.5), (-23.5, 22.6, 28.0, 37.5), (-23.5, 22.6, -37.5, -28.0), (-56.0, -44.8, -23.0, 22.5),
             (46.6, 58.2, -1.4, 28.6), (-67.5, -54.5, 26.0, 37.5), (56.5, 69.0, -38.0, -15.5)] + \
            [(x - 4.2, x + 4.2, y - 4.2, y + 4.2) for x, y in ring_xy]
scatter_smd('PCB_SMD_Top', [(-68.5, -29.5, -37.5, 37.5), (28.5, 68.5, -37.5, 37.5)], 260, M_chip, col, root, seed=11, avoid=avoid_top,
            sizes=((1.0, 0.5), (1.0, 0.5), (1.6, 0.8), (2.0, 1.25), (0.6, 0.3)), h=(0.3, 0.7))
scatter_smd('PCB_SMD_Top_Brown', [(-68.5, -29.5, -37.5, 37.5), (28.5, 68.5, -37.5, 37.5)], 60, M_mlcc, col, root, seed=12, avoid=avoid_top,
            sizes=((1.6, 0.8), (2.0, 1.25)), h=(0.5, 0.9))

# ---------------------------------------------------------------- underside (STH ISC 2022 bottom photo + SXM2 back layout)
zb = -T
for i, sx in enumerate((-1, 1)):
    cx = sx * 35.4
    box(f'Mezz_{i}_Housing', (20.0, 56.0, 4.6), (cx, 0, zb - 2.3), M_conn, bevel=0.0004)
    box(f'Mezz_{i}_PinField', (15.0, 50.0, 0.2), (cx, 0, zb - 4.55), M_hole)
    boxes(f'Mezz_{i}_Pins', [((cx - 6.3 + 1.4 * c, -23.5 + 1.27 * r, zb - 4.62), (0.55, 0.55, 0.25)) for c in range(10) for r in range(38)], M_pin, col, root)
    boxes(f'Mezz_{i}_Latches', [((cx, sy * 28.6, zb - 2.0), (6.0, 1.6, 3.6)) for sy in (-1, 1)], M_stiff, col, root)
boxes('Bot_Bolster', [((0, sy * 35.0, zb - 0.6), (L - 2.0, 6.5, 1.2)) for sy in (-1, 1)] +
      [((sx * 64.5, 0, zb - 0.6), (8.0, 63.5, 1.2)) for sx in (-1, 1)] +
      [((sx * 47.5, 0, zb - 0.6), (8.6, 63.5, 1.2)) for sx in (-1, 1)] +
      [((0, 0, zb - 0.6), (49.6, 63.5, 1.2))], M_stiff, col, root)
boxes('Bot_Pads', [((-55.7, 0, zb - 1.3), (9.0, 62.0, 0.3)), ((54.1, -1.0, zb - 1.3), (7.4, 60.0, 0.3)),
                   ((-20.6, 0, zb - 1.3), (6.8, 42.0, 0.3)), ((18.9, 0, zb - 1.3), (6.8, 42.0, 0.3)), ((-0.8, 0, zb - 1.3), (19.0, 52.0, 0.3))],
      M_padsil, col, root)
box('Bot_Label', (5.8, 26.0, 0.1), (54.1, 15.0, zb - 1.5), M_white)
cyls('Bot_Screws', [(sx * 36.8, sy * 34.0, zb - 1.6, 3.0, 0.9) for sx in (-1, 1) for sy in (-1, 1)] +
     [(-67.0, 34.0, zb - 1.5, 1.6, 0.7), (67.0, 34.0, zb - 1.5, 1.6, 0.7), (-47.0, -34.6, zb - 1.5, 1.6, 0.7), (44.0, -34.6, zb - 1.5, 1.6, 0.7)],
     M_screw, col, root, verts=16)
cyls('Bot_GuidePins', [(sx * 67.0, -sx * 5.0, zb - 3.0, 1.2, 6.0) for sx in (-1, 1)], M_steel, col, root, verts=12)

# ---------------------------------------------------------------- heatsink
hs = bpy.data.objects.new(ROOT + '_Heatsink', None); hs.empty_display_size = 0.02
col.objects.link(hs); hs.parent = root
hx, hy = HL / 2, HW_ / 2
CAP = 30.0                                   # end-cap shroud width along X (ISC side photo)
xin = hx - CAP                               # 41.5: open fin window between the caps
# black retention frame between PCB and heatsink (dark band in the side photo)
box('HS_Frame', (HL - 2, HW_ - 2, 8.0), (0, 0, 0.3 + 4.0), M_stiff, parent=hs)
box('HS_Base', (2 * xin + 2, HW_ - 4, 6.0), (0, 0, 8.3 + 3.0), M_nickel, parent=hs)
# end caps (solid champagne shroud blocks)
for i, sx in enumerate((-1, 1)):
    box(f'HS_EndCap_{i}', (CAP, HW_, HS_TOP - 8.3), (sx * (hx - CAP / 2), 0, 8.3 + (HS_TOP - 8.3) / 2), M_champ, parent=hs, bevel=0.0006)
# fins: YZ plates stacked along X between the caps (air flows along Y)
fp, ftk = 1.55, 0.32
fins = []
x = -xin + 0.6
while x < xin - 0.4:
    z0 = 45.0 if 12.0 < abs(x) < 20.0 else 14.3
    fins.append(((x, 0, (z0 + 91.5) / 2), (ftk, HW_ - 3.0, 91.5 - z0)))
    x += fp
boxes('HS_Fins', fins, M_fin, col, hs)
# spring-screw posts seen through the fin window
cyls('HS_Posts', [(sx * 16.0, sy * 33.5, 29.0, 3.2, 30.0) for sx in (-1, 1) for sy in (-1, 1)], M_nickel, col, hs, verts=16)
cyls('HS_PostHeads', [(sx * 16.0, sy * 33.5, 42.0, 4.0, 4.0) for sx in (-1, 1) for sy in (-1, 1)], M_steel, col, hs, verts=16)
# long-face horizontal bar + upper hood (trapezoid) with three slots, both long faces
for i, sy in enumerate((-1, 1)):
    yf = sy * (hy - 1.0)
    box(f'HS_Bar_{i}', (2 * xin, 2.0, 14.2), (0, yf, 27.8), M_champ, parent=hs)
    hood = [(-xin, HS_TOP - 2.0), (xin, HS_TOP - 2.0), (30.0, 73.0), (-30.0, 73.0)]
    H['prism'](f'HS_Hood_{i}', [(a * mm, b * mm) for a, b in hood], 'xz', (yf - 1.0) * mm, 2.0 * mm, M_champ, col, hs)
    boxes(f'HS_Hood_Slots_{i}', [((0, yf + sy * 1.05, z), (34.0, 0.2, 1.5)) for z in (79.5, 84.0, 88.0)], M_band, col, hs)
# top cover: champagne plate, dark chevron bands + smoked windows along the long edges, ribs along X
box('HS_TopPlate', (HL, HW_, 2.0), (0, 0, HS_TOP - 1.0), M_champ, parent=hs, bevel=0.0005)
for i, sy in enumerate((-1, 1)):
    band = [(-46.0, sy * (hy - 0.3)), (46.0, sy * (hy - 0.3)), (33.0, sy * 28.0), (-33.0, sy * 28.0)]
    win = [(-31.0, sy * (hy - 0.3)), (31.0, sy * (hy - 0.3)), (29.0, sy * 33.5), (-29.0, sy * 33.5)]
    H['prism'](f'HS_TopBand_{i}', [(a * mm, b * mm) for a, b in band], 'xy', (HS_TOP + 0.02) * mm, 0.1 * mm, M_band, col, hs)
    H['prism'](f'HS_TopWindow_{i}', [(a * mm, b * mm) for a, b in win], 'xy', (HS_TOP + 0.12) * mm, 0.1 * mm, M_window, col, hs)
ribs = []
rp = 2.2
for k in range(int(HW_ / rp)):
    y = -hy + 1.2 + k * rp
    if abs(y) <= 27.0:
        ribs.append(((0, y, HS_TOP + 0.12), (HL - 2.0, 1.1, 0.24)))
    elif abs(y) < hy - 0.8:
        hw = 33.0 + (46.0 - 33.0) * (abs(y) - 28.0) / (hy - 0.3 - 28.0) + 1.0
        ln = hx - 1.0 - hw
        for sx in (-1, 1):
            ribs.append(((sx * (hw + ln / 2), y, HS_TOP + 0.12), (ln, 1.1, 0.24)))
boxes('HS_TopRibs', ribs, M_rib, col, hs)
# logo + wordmark (DGX A100 tray image: centred, reading along +X)
nv_logo('HS_Logo', -27.0, 0.0, HS_TOP + 0.25, 13.0, M_logo, M_rib, col, hs)
label_text('HS_NVIDIA', 'nVIDIA', 13.5, (9.0, 0.0, HS_TOP + 0.3), M_logo, col, hs)

sxm_sockets(root, col, power_in=(0, 0, -0.0045), mezz=(0, 0, -T * mm - 0.0046),
            extra=[('SOCKET_mezzanine_A', (-0.0354, 0, -T * mm - 0.0046)), ('SOCKET_mezzanine_B', (0.0354, 0, -T * mm - 0.0046))])

# ---------------------------------------------------------------- save / export / render
bpy.ops.wm.save_as_mainfile(filepath=r'C:\laragon\www\scaling-law\blender\gpu_12b_a100_sxm4.blend')
tris = H['export_glb'](ROOT, r'C:\laragon\www\scaling-law\blender\export\gpu_a100_sxm4.glb')
print('TRIS', tris)
render_views('a100_sxm4', {
    'top':   ((0, -0.001, 0.42), (0, 0, 0.0), 60, False, False),
    'side':  ((0, -0.42, 0.048), (0, 0, 0.048), 60, False, False),
    '34':    ((0.21, -0.30, 0.27), (0, 0, 0.038), 55, False, False),
    'under': ((0.08, -0.16, -0.36), (0, 0, -0.002), 60, True, True),
})
for o in hs.children_recursive:
    o.hide_render = True
render_views('a100_sxm4', {'bare34': ((0.15, -0.20, 0.17), (0, 0, 0.0), 55, False, False),
                           'baretop': ((0, -0.001, 0.30), (0, 0, 0.0), 60, False, False)})
for o in hs.children_recursive:
    o.hide_render = False
