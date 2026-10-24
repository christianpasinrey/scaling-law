"""NVIDIA Tesla V100 SXM2 (2017) as installed in DGX-1 / HGX-1, with its tall DGX-1 heatsink.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python <this file>

Module lies flat: PCB top = z 0, X = long side (140 mm), Y = short side (78 mm), origin = module centre.
Heatsink parts are parented to the child empty 'V100_SXM2_Heatsink' (hide it to show the bare module).
Dimensions (mm) measured from NVIDIA P100 SXM2 front/back press renders (same SXM2 form factor,
scaled to 140 x 78) and ISC 2016 DGX-1 photos (iThome); see report for sources.
"""
import bpy, math
exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\sxm_lib.py', encoding='utf-8').read())

ROOT = 'V100_SXM2'
L, W, T = 140.0, 78.0, 2.0          # module PCB (mm)
HS_TOP = 90.0                        # heatsink top above PCB top (mm), estimated (3U chassis)

root, col = H['new_card_scene'](ROOT)
M = H['base_materials']()
mat = H['mat']
M_pcb = mat('HW_PCB_SXM', (0.009, 0.010, 0.010), 0.0, 0.62, spec=0.3)
M_ring = mat('HW_PlatedRing', (0.80, 0.52, 0.30), 1.0, 0.35)
M_hole = M['port']
M_ind = mat('HW_InductorGrey', (0.20, 0.20, 0.205), 0.75, 0.42)
M_chip = mat('HW_ChipBlack', (0.015, 0.015, 0.017), 0.0, 0.35, spec=0.4)
M_stiff = mat('HW_StiffenerBlack', (0.012, 0.012, 0.013), 0.5, 0.42)
M_frame = mat('HW_PkgStiffener', (0.50, 0.50, 0.48), 1.0, 0.33)
M_sub = mat('HW_SubstrateGreen', (0.03, 0.09, 0.07), 0.0, 0.45)
M_die = mat('HW_DieGlossBlack', (0.01, 0.011, 0.014), 0.2, 0.12)
M_hbm = mat('HW_HBMBlack', (0.025, 0.026, 0.03), 0.3, 0.25)
M_mold = mat('HW_MoldDark', (0.04, 0.045, 0.045), 0.0, 0.5)
M_screw = mat('HW_ScrewBlack', (0.02, 0.02, 0.02), 0.7, 0.35)
M_conn = mat('HW_MezzBeige', (0.62, 0.50, 0.36), 0.0, 0.55)
M_pin = M['gold']
M_pad = mat('HW_ThermalPadGrey', (0.13, 0.13, 0.125), 0.0, 0.8)
M_white = mat('HW_LabelWhite', (0.8, 0.8, 0.8), 0.0, 0.5)
M_cap = mat('HW_CapAlu', (0.55, 0.55, 0.57), 1.0, 0.3)
# DGX-1 heatsink: olive/green anodised fins, black logo
M_green = mat('HW_DGX1Green', (0.085, 0.105, 0.008), 0.6, 0.45)
M_green_dk = mat('HW_DGX1GreenDark', (0.03, 0.04, 0.004), 0.5, 0.55)
M_core = mat('HW_FinCoreBlack', (0.008, 0.008, 0.008), 0.3, 0.7)
M_nickel = mat('HW_NickelBase', (0.62, 0.60, 0.56), 1.0, 0.3)
M_endplate = mat('HW_EndPlateAlu', (0.66, 0.67, 0.68), 1.0, 0.28)
M_logo = mat('HW_LogoBlack', (0.003, 0.003, 0.003), 0.0, 0.85, spec=0.1)

box = lambda n, size, loc, m, **k: H['box'](n, tuple(v * mm for v in size), tuple(v * mm for v in loc), m, col, parent=k.pop('parent', root), **k)

# ---------------------------------------------------------------- module PCB
box('PCB', (L, W, T), (0, 0, -T / 2), M_pcb, bevel=0.0004)
ring_xy = [(x, y) for x in (-64.5, -32.6, -23.6, 22.8, 31.7, 64.5) for y in (-34.7, 34.7)]
rings_mesh('PCB_Rings_Top', ring_xy, 3.2, 1.6, 0.03, M_ring, col, root)
rings_mesh('PCB_Rings_Bot', ring_xy, 3.2, 1.6, -T - 0.03, M_ring, col, root)
discs('PCB_Holes_Top', ring_xy, 1.6, 0.04, M_hole, col, root)
discs('PCB_Holes_Bot', ring_xy, 1.6, -T - 0.04, M_hole, col, root)

# ---------------------------------------------------------------- top side (from ISC2016-3 bare P100 SXM2 photo)
# 2 rows of 8 power inductors at both X ends
boxes('VRM_Inductors', [((sx * 49.0, -31.5 + 9.0 * i, 2.6), (14.5, 8.2, 5.2)) for sx in (-1, 1) for i in range(8)], M_ind, col, root)
boxes('VRM_PowerStages', [((sx * 62.5, -31.5 + 9.0 * i, 0.5), (4.5, 4.0, 1.0)) for sx in (-1, 1) for i in range(8)], M_chip, col, root)
# black stiffener bars across the module + side bars around the package
boxes('Stiffener', [((sx * 31.0, 0, 2.0), (8.7, 74.0, 4.0)) for sx in (-1, 1)] +
      [((0, sy * 33.0, 2.0), (53.3, 9.0, 4.0)) for sy in (-1, 1)], M_stiff, col, root)
cyls('Stiffener_Screws', [(sx * 31.0, y, 4.3, 1.9, 0.8) for sx in (-1, 1) for y in (-33.0, 0.0, 33.0)] +
     [(x, sy * 33.0, 4.3, 1.6, 0.8) for sy in (-1, 1) for x in (-19.0, -6.5, 6.5, 19.0)], M_screw, col, root, verts=12)
# GV100 package: substrate + nickel stiffener ring + interposer with die and 4 HBM2 stacks
box('Pkg_Substrate', (52.0, 56.0, 1.2), (0, 0, 0.6), M_sub)
ring_o = [(-26.75, -27.5), (26.75, -27.5), (26.75, 27.5), (-26.75, 27.5)]
ring_i = [(-21.5, -22.5), (21.5, -22.5), (21.5, 22.5), (-21.5, 22.5)]
H['ring']('Pkg_Stiffener', [(a * mm, b * mm) for a, b in ring_o], [(a * mm, b * mm) for a, b in ring_i], 'xy', 0.0, 2.0 * mm, M_frame, col, root)
box('Pkg_Interposer', (33.0, 44.0, 0.6), (0, 0, 1.5), M_mold)
box('GPU_Die', (31.0, 25.5, 0.9), (0, 0, 2.2), M_die, bevel=0.0002)
boxes('HBM2_Stacks', [((x, sy * 17.4, 2.15), (11.9, 7.75, 0.8)) for x in (-6.3, 6.3) for sy in (-1, 1)], M_hbm, col, root)
boxes('Pkg_Caps', [((x, sy * 24.6, 1.45), (1.0, 0.5, 0.5)) for x in [-15 + i * 1.6 for i in range(19)] for sy in (-1, 1)], M_chip, col, root)
scatter_smd('PCB_SMD_Top', [(-69, -57, -38, 38), (57, 69, -38, 38), (-26, 26, -38.5, -37.5), (-26, 26, 37.5, 38.5)], 70, M_chip, col, root, seed=3,
            avoid=[(x - 3.4, x + 3.4, y - 3.4, y + 3.4) for x, y in ring_xy] + [(-65, -60, -34, 34), (60, 65, -34, 34)])

# ---------------------------------------------------------------- underside (from NVIDIA P100_SXM2_back render)
zb = -T
for i, sx in enumerate((-1, 1)):
    cx = sx * 33.0
    box(f'Mezz_{i}_Housing', (17.0, 55.0, 4.6), (cx, 0, zb - 2.3), M_conn, bevel=0.0003)
    box(f'Mezz_{i}_Frame', (20.0, 58.5, 1.0), (cx, 0, zb - 0.5), M_stiff)
    boxes(f'Mezz_{i}_Pins', [((cx - 6.0 + 1.33 * c, -25.0 + 1.27 * r, zb - 4.65), (0.55, 0.55, 0.3)) for c in range(10) for r in range(40)], M_pin, col, root)
boxes('Bot_ThermalPads', [((sx * 19.6, 0, zb - 0.25), (7.5, 42.0, 0.5)) for sx in (-1, 1)] + [((0, 0, zb - 0.15), (16.0, 36.0, 0.3))], M_pad, col, root)
boxes('Bot_StripPads', [((sx * 56.0, 0, zb - 0.1), (5.0, 60.0, 0.2)) for sx in (-1, 1)], M_stiff, col, root)
for i, sy in enumerate((-1, 1)):
    cy = sy * 33.5
    boxes(f'Bot_VRM_{i}', [((1.5, cy, zb - 2.0), (9.5, 8.5, 4.0)), ((-8.5, cy, zb - 0.8), (5.0, 5.0, 1.6))], M_ind, col, root)
    cyls(f'Bot_VRM_{i}_Caps', [(9.5, cy + 2.6, zb - 1.6, 1.9, 3.2), (9.5, cy - 2.6, zb - 1.6, 1.9, 3.2)], M_cap, col, root, verts=14)
cyls('Bot_CornerBosses', [(sx * 65.9, sy * 34.6, zb - 1.2, 3.4, 2.4) for sx in (-1, 1) for sy in (-1, 1)], M_stiff, col, root, verts=18)
cyls('Bot_GuidePins', [(sx * 63.6, -7.3, zb - 2.8, 1.2, 5.6) for sx in (-1, 1)], M_screw, col, root, verts=12)
scatter_smd('PCB_SMD_Bot', [(-46, 46, -38, -30), (-46, 46, 30, 38)], 40, M_chip, col, root, seed=7, z0=zb - 0.001,
            avoid=[(-16, 16, -38, -28), (-16, 16, 28, 38)] + [(x - 3.4, x + 3.4, y - 3.4, y + 3.4) for x, y in ring_xy])

# ---------------------------------------------------------------- DGX-1 heatsink (ISC2016-2/-4 photos)
hs = bpy.data.objects.new(ROOT + '_Heatsink', None); hs.empty_display_size = 0.02
col.objects.link(hs); hs.parent = root
X0, X1 = -66.0, 70.0                 # fin box (end plate occupies -70..-66)
XC, XL = (X0 + X1) / 2, X1 - X0
box('HS_Base', (XL, 76.0, 4.6), (XC, 0, 6.6), M_nickel, parent=hs)
box('HS_Core', (XL - 3.0, W - 3.0, HS_TOP - 10.0), (XC, 0, 8.9 + (HS_TOP - 10.0) / 2), M_core, parent=hs)
pitch, ft = 2.2, 0.95
nf = int((HS_TOP - 1.6 - 9.4) / pitch)
boxes('HS_Fins', [((XC, 0, 9.4 + ft / 2 + i * pitch), (XL, W, ft)) for i in range(nf)], M_green, col, hs)
box('HS_TopPlate', (XL, W, 1.2), (XC, 0, HS_TOP - 0.6 - 0.5), M_green_dk, parent=hs)
rp = 2.4
boxes('HS_TopRibs', [((XC, -W / 2 + rp / 2 + k * rp, HS_TOP - 0.25), (XL, 1.5, 0.5)) for k in range(int(W / rp))], M_green, col, hs)
box('HS_EndPlate', (4.0, 74.0, HS_TOP - 3.0), (-68.0, 0, 3.0 + (HS_TOP - 3.0) / 2), M_endplate, parent=hs, bevel=0.0004)
for k, (y, z) in enumerate([(y, z) for y in (-28, 28) for z in (20, HS_TOP - 15)]):
    H['cyl'](f'HS_EndPlate_Screw{k}', 1.6 * mm, 0.6 * mm, (-70.2 * mm, y * mm, z * mm), M_screw, col, verts=12, rot=(0, math.pi / 2, 0), parent=hs)
# logo + wordmark on top, reading along +X
lz = HS_TOP
nv_logo('HS_Logo', -33.0, 0.0, lz, 15.0, M_logo, M_green, col, hs)
label_text('HS_NVIDIA', 'nVIDIA', 18.5, (21.0, 0.0, lz + 0.1), M_logo, col, hs, scale=(1.0, 1.0, 1.0))

sxm_sockets(root, col, power_in=(0, 0, -0.0045), mezz=(0, 0, -T * mm - 0.0046),
            extra=[('SOCKET_mezzanine_A', (-0.033, 0, -T * mm - 0.0046)), ('SOCKET_mezzanine_B', (0.033, 0, -T * mm - 0.0046))])

# ---------------------------------------------------------------- save / export / render
bpy.ops.wm.save_as_mainfile(filepath=r'C:\laragon\www\scaling-law\blender\gpu_12a_v100_sxm2.blend')
tris = H['export_glb'](ROOT, r'C:\laragon\www\scaling-law\blender\export\gpu_v100_sxm2.glb')
print('TRIS', tris)
render_views('v100_sxm2', {
    'top':   ((0, -0.001, 0.40), (0, 0, 0.0), 60, False, False),
    'side':  ((0, -0.42, 0.045), (0, 0, 0.045), 60, False, False),
    '34':    ((0.21, -0.30, 0.26), (0, 0, 0.035), 55, False, False),
    'under': ((0.08, -0.16, -0.36), (0, 0, -0.002), 60, True, True),
})
# bare module (heatsink hidden) for verification only
for o in hs.children_recursive:
    o.hide_render = True
render_views('v100_sxm2', {'bare34': ((0.15, -0.20, 0.17), (0, 0, 0.0), 55, False, False)})
for o in hs.children_recursive:
    o.hide_render = False
