"""plant_03_switchgear - low-voltage main switchboard line-up + floor-standing PDU (transformer cabinet).

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python plant_03_switchgear.py

Switchboard: Eaton Pow-R-Line XD style compartmentalised switchboard. Eaton spec page: standard indoor
widths 20/22/24/36/44 in, depths 60-90 in, standard height 96 in. Used: 5 sections x 36 in (914 mm) wide,
96 in (2438 mm) high, 60 in (1524 mm) deep. Section 1 = main incomer with a drawout air circuit breaker
(Magnum DS style) + power meter; sections 2-5 = stacked feeder breaker compartments.
PDU: floor-standing 300 kVA power distribution unit with isolation transformer (Eaton / Vertiv class);
size approximate: 1320 W x 910 D x 1980 H mm, front aligned with the switchboard.
Origin = floor centre of the whole footprint, front faces -Y. Cable/bus entries on top.
"""
import bpy, math, os, sys
exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\plant_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']; P = bpy.app.driver_namespace['PLANT']

ROOT = 'Plant_Switchboard_PDU'
BLEND = os.path.join(P['BASE'], 'plant_03_switchgear.blend')
GLB = os.path.join(P['BASE'], 'export', 'plant_03_switchgear.glb')
root, col, M, PM = P['setup'](ROOT)
mat = H['mat']
ANSI61 = mat('PL_ANSI61_Grey', (0.50, 0.53, 0.55), 0.05, 0.45)
DOOR = mat('PL_ANSI61_Door', (0.55, 0.58, 0.60), 0.05, 0.42)
SEAM = mat('PL_SWB_Seam', (0.02, 0.02, 0.022), 0.0, 0.8)
BKR = mat('PL_Breaker_Black', (0.02, 0.02, 0.022), 0.0, 0.45)
PDU_W = mat('PL_PDU_Body', (0.13, 0.135, 0.14), 0.15, 0.45)

SW, SD, SH = 0.914, 1.524, 2.438        # section width, depth, height
NS = 5
GAP = 1.20
PW, PD, PH = 1.32, 0.91, 1.98
TOTAL = NS * SW + GAP + PW
X0 = -TOTAL / 2
Y0 = -SD / 2
yf = Y0 - 0.0006
secs = [(X0 + i * SW, X0 + (i + 1) * SW) for i in range(NS)]

seams, holes, handles, labels_y = [], [], [], []
for i, (xa, xb) in enumerate(secs):
    xc = (xa + xb) / 2
    H['box'](f'SWB_Section_{i}', (SW - 0.004, SD, SH - 0.10), (xc, 0, 0.10 + (SH - 0.10) / 2), ANSI61, col, bevel=0.003, parent=root)
    seams.append(((xa + 0.002, yf, SH / 2), (0.006, SH - 0.02), 0.0))
H['box']('SWB_Base', (NS * SW, SD - 0.04, 0.10), (X0 + NS * SW / 2, 0.0, 0.05), M['black_mt'], col, parent=root)
H['box']('SWB_TopHeader', (NS * SW, 0.02, 0.12), (X0 + NS * SW / 2, Y0 - 0.008, SH - 0.08), PM['dgrey'], col, parent=root)
P['text']('SWB_Brand', 'EATON', 0.07, PM['label_w'], col, root, (X0 + 0.45, Y0 - 0.0185, SH - 0.08))
P['text']('SWB_Model', 'Pow-R-Line XD   480Y/277V  4000A', 0.04, PM['label_w'], col, root, (X0 + 2.3, Y0 - 0.0185, SH - 0.08))

# ---- section 1: main incomer (drawout ACB)
xa, xb = secs[0]; xc = (xa + xb) / 2
for z0, z1 in ((0.12, 0.85), (0.85, 1.75), (1.75, 2.30)):
    seams.append(((xc, yf, z0), (SW - 0.04, 0.005), 0.0))
H['box']('Main_ACB_Face', (0.62, 0.05, 0.62), (xc, Y0 - 0.02, 1.30), BKR, col, bevel=0.01, parent=root)
H['box']('Main_ACB_Escutcheon', (0.70, 0.012, 0.70), (xc, Y0 - 0.004, 1.30), M['black_st'], col, bevel=0.003, parent=root)
H['box']('Main_ACB_ChargeHandle', (0.05, 0.05, 0.16), (xc + 0.20, Y0 - 0.07, 1.20), BKR, col, bevel=0.008, parent=root)
H['box']('Main_ACB_TripUnit', (0.18, 0.012, 0.14), (xc - 0.15, Y0 - 0.051, 1.45), M['black_gl'], col, parent=root)
P['led']('LED_main_trip_unit', (xc - 0.15, Y0 - 0.0575, 1.45), (0.12, 0.002, 0.05), PM['screen'], col, root)
P['cylinders']('Main_ACB_Buttons', [((xc + 0.05 + k * 0.08, Y0 - 0.048, 1.48), 0.022, 0.016, (math.pi / 2, 0, 0)) for k in range(2)], PM['label_r'], col, root, verts=16)
P['led']('LED_main_breaker', (xc + 0.09, Y0 - 0.05, 1.40), (0.10, 0.008, 0.025), PM['led_g'], col, root)
P['text']('Main_ACB_Label', 'MAIN 4000A', 0.035, PM['label_w'], col, root, (xc, Y0 - 0.0462, 1.08))
# power meter on the upper door
H['box']('Main_Meter', (0.20, 0.03, 0.20), (xc, Y0 - 0.015, 2.02), M['black_gl'], col, bevel=0.004, parent=root)
P['led']('LED_meter_main', (xc, Y0 - 0.031, 2.04), (0.15, 0.002, 0.10), PM['screen'], col, root)
labels_y.append(((xc, Y0 - 0.001, 0.55), (0.25, 0.002, 0.12)))

# ---- feeder sections: 6 stacked breaker compartments each
FEED_Z = [0.15 + k * 0.345 for k in range(7)]   # compartment boundaries 0.15 .. 2.22
for i in range(1, NS):
    xa, xb = secs[i]; xc = (xa + xb) / 2
    for k, z0 in enumerate(FEED_Z):
        seams.append(((xc, yf, z0), (SW - 0.04, 0.005), 0.0))
    seams.append(((xc + 0.30, yf, (FEED_Z[0] + FEED_Z[-1]) / 2), (0.004, FEED_Z[-1] - FEED_Z[0]), 0.0))   # wireway door
    for k in range(6):
        zc = FEED_Z[k] + 0.1725
        if (i + k) % 5 == 4:
            continue                      # spare / blank compartment
        holes.append(((xc - 0.06, yf - 0.0004, zc), (0.20, 0.13), 0.0))
        handles.append(((xc - 0.06, Y0 - 0.025, zc + (0.02 if (i * 7 + k) % 3 else -0.02)), (0.035, 0.05, 0.06)))
        handles.append(((xc - 0.06, Y0 - 0.008, zc), (0.17, 0.016, 0.10)))
    labels_y.append(((xc + 0.36, Y0 - 0.001, 1.75), (0.08, 0.002, 0.06)))
    P['led'](f'LED_feeder_{i}', (xc - 0.06, Y0 - 0.004, FEED_Z[-1] - 0.06), (0.05, 0.006, 0.015), PM['led_g'], col, root)
P['quads']('SWB_Seams', seams, SEAM, col, root)
P['quads']('SWB_BreakerOpenings', holes, M['black_mt'], col, root)
H['slat_array']('SWB_BreakerHandles', lambda: iter(handles), BKR, col, root)
H['slat_array']('SWB_WarningLabels', lambda: iter(labels_y), PM['label_y'], col, root)
P['text']('SWB_Danger', 'DANGER  ARC FLASH', 0.022, PM['label_k'], col, root, (secs[0][0] + SW / 2, Y0 - 0.0022, 0.57))
# latches on the right edge of each section
P['cylinders']('SWB_Latches', [((xb - 0.05, Y0 - 0.006, z), 0.012, 0.012, (math.pi / 2, 0, 0)) for xa, xb in secs for z in (0.5, 1.3, 2.0)], M['steel'], col, root, verts=12)

# ---------------------------------------------------------------- PDU
pxa = X0 + NS * SW + GAP; pxc = pxa + PW / 2; pyc = Y0 + PD / 2
H['box']('PDU_Body', (PW, PD, PH - 0.08), (pxc, pyc, 0.08 + (PH - 0.08) / 2), PDU_W, col, bevel=0.004, parent=root)
H['box']('PDU_Base', (PW - 0.03, PD - 0.03, 0.08), (pxc, pyc, 0.04), M['black_mt'], col, parent=root)
pseams = [((pxc, Y0 - 0.0006, (0.08 + PH) / 2), (0.004, PH - 0.12), 0.0)]
louv = []
for side in (-1, 1):
    for j in range(16):
        louv.append(((pxc + side * PW / 4, Y0 - 0.0007, 0.20 + j * 0.03), (PW / 2 - 0.16, 0.010), 0.0))
        louv.append(((pxc + side * PW / 4, Y0 - 0.0007, PH - 0.55 + j * 0.022), (PW / 2 - 0.16, 0.008), 0.0))
P['quads']('PDU_Seams', pseams, SEAM, col, root)
P['quads']('PDU_Louvres', louv, PM['vent'], col, root)
H['box']('PDU_ScreenBezel', (0.22, 0.012, 0.15), (pxc - PW / 4, Y0 - 0.006, 1.25), M['black_gl'], col, bevel=0.003, parent=root)
P['led']('LED_pdu_screen', (pxc - PW / 4, Y0 - 0.0125, 1.25), (0.19, 0.002, 0.11), PM['screen'], col, root)
P['led']('LED_pdu_status', (pxc - PW / 4, Y0 - 0.004, 1.13), (0.14, 0.004, 0.01), PM['led_g'], col, root)
P['text']('PDU_Brand', 'EATON', 0.06, PM['label_w'], col, root, (pxc + PW / 4, Y0 - 0.0007, 1.30))
P['text']('PDU_Model', 'PDU 300 kVA', 0.035, PM['label_w'], col, root, (pxc + PW / 4, Y0 - 0.0007, 1.22))
H['slat_array']('PDU_Handles', lambda: iter([((pxc - 0.06, Y0 - 0.012, 1.0), (0.02, 0.025, 0.15)), ((pxc + 0.06, Y0 - 0.012, 1.0), (0.02, 0.025, 0.15))]),
                M['black_mt'], col, root)

# ---------------------------------------------------------------- power flow: busway in, feeders out, PDU feed
Z_ENT = 3.30
xa, xb = secs[0]
P['flow_path']('FLOW_power_busway_in', [((xa + xb) / 2, 0.15, Z_ENT), ((xa + xb) / 2, 0.15, SH + 0.01)], mat('PL_Busway', (0.22, 0.23, 0.24), 0.2, 0.45), col, root, rect=(0.16, 0.60), bend=0.1, kind='power')
H['slat_array']('SWB_BuswayJoints', lambda: iter([(((xa + xb) / 2, 0.15, z), (0.64, 0.20, 0.05)) for z in (2.75, 3.15)]), M['black_st'], col, root)
H['box']('SWB_BuswayFlange', (0.70, 0.26, 0.04), ((xa + xb) / 2, 0.15, SH + 0.02), M['black_st'], col, parent=root)
P['socket']('SOCKET_power_in', ((xa + xb) / 2, 0.15, Z_ENT), (0, 0, 1), root, col)
for k, i in enumerate((2, 3)):
    xa, xb = secs[i]
    for j, dx in enumerate((-0.15, 0.15)):
        nm = f'FLOW_power_out_{k + 1}{"ab"[j]}'
        P['flow_path'](nm, [((xa + xb) / 2 + dx, 0.30, SH + 0.01), ((xa + xb) / 2 + dx, 0.30, Z_ENT)], PM['cable'], col, root, radius=0.045, verts=12, kind='power')
    P['socket'](f'SOCKET_power_out_{k + 1}', ((xa + xb) / 2, 0.30, Z_ENT), (0, 0, 1), root, col)
    H['box'](f'SWB_GlandPlate_{i}', (0.50, 0.25, 0.012), ((xa + xb) / 2, 0.30, SH + 0.006), M['black_mt'], col, parent=root)
# section 5 feeds the PDU over a ladder tray
xa, xb = secs[4]
Z_TRAY = 2.85
src = ((xa + xb) / 2, 0.25)
dst = (pxc, pyc)
for j, dy in enumerate((-0.07, 0.07)):
    P['flow_path'](f'FLOW_power_pdu_feed_{j}', [(src[0], src[1] + dy, SH + 0.01), (src[0], src[1] + dy, Z_TRAY + 0.05), (dst[0], dst[1] + dy, Z_TRAY + 0.05),
                                                 (dst[0], dst[1] + dy, PH + 0.01)], PM['cable'], col, root, radius=0.04, verts=12, bend=0.25, kind='power')
H['box']('SWB_GlandPlate_4', (0.50, 0.30, 0.012), (src[0], src[1], SH + 0.006), M['black_mt'], col, parent=root)
H['box']('PDU_GlandPlate', (0.40, 0.30, 0.012), (dst[0], dst[1], PH + 0.006), M['black_mt'], col, parent=root)
def tray():
    xs, xe = src[0] - 0.2, dst[0] + 0.2
    L = xe - xs; yc = (src[1] + dst[1]) / 2
    for dy in (-0.2, 0.2):
        yield ((xs + xe) / 2, yc + dy, Z_TRAY + 0.04), (L, 0.006, 0.08)
    n = int(L / 0.3)
    for i in range(n + 1):
        yield (xs + i * L / n, yc, Z_TRAY), (0.03, 0.40, 0.012)
H['slat_array']('SWB_CableTray', tray, PM['galv'], col, root)
# PDU output to the hall (to RPPs / busway)
P['flow_path']('FLOW_power_pdu_out', [(pxc + 0.40, pyc + 0.15, PH + 0.01), (pxc + 0.40, pyc + 0.15, Z_ENT)], PM['cable'], col, root, radius=0.05, verts=12, kind='power')
P['socket']('SOCKET_power_out_pdu', (pxc + 0.40, pyc + 0.15, Z_ENT), (0, 0, 1), root, col)

tris = P['finish'](root, BLEND, GLB)
print('FOOTPRINT', round(TOTAL, 3), 'x', SD)
P['render']('plant_03_switchgear', {
    'front':  ((0, -1, 0.15), 1.5, 50, (0, 0, 1.5)),
    '34':     ((-0.7, -1, 0.5), 1.45, 50, (0, 0, 1.4)),
    'rear34': ((0.8, 1, 0.9), 1.45, 50, (0, 0, 1.4)),
    'main':   ((-0.25, -1, 0.1), 0.42, 50, (secs[0][0] + 0.9, -0.8, 1.45)),
    'pdu':    ((0.35, -1, 0.25), 0.55, 50, (pxc - 0.3, -0.5, 1.6)),
}, (0, 0, 1.4), TOTAL)
