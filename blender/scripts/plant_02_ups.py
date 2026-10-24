"""plant_02_ups - Schneider Electric Galaxy VX 1500 kW UPS line-up + lithium-ion battery cabinets.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python plant_02_ups.py

Dimensions (Schneider "Galaxy VX 1500 kW Installation" 990-5783J, weights & dimensions table):
  - 1500 kW I/O cabinet: H 2140 x W 2120 x D 1060 mm
  - 250 kW power cabinet: H 2140 x W 760 x D 1060 mm (6 of them for 1500 kW)
  - Li-ion battery cabinet ("Li-ion Battery Rack Type G", reseller data): H 2055 x W 650 x D 530 mm (4 here;
    real runtime sizing would need more - approximate count).
Look: white cabinets, perforated (oblique slot) door vents on the power cabinets as in the EPS 6000 row
photo, colour touch display on the I/O cabinet. Galaxy VX branding/colours from memory (approximate).
Cable entry from the top. Origin = floor centre of the whole line-up footprint, front faces -Y.
"""
import bpy, math, os, sys
exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\plant_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']; P = bpy.app.driver_namespace['PLANT']

ROOT = 'Plant_UPS_GalaxyVX1500'
BLEND = os.path.join(P['BASE'], 'plant_02_ups.blend')
GLB = os.path.join(P['BASE'], 'export', 'plant_02_ups.glb')
root, col, M, PM = P['setup'](ROOT)
mat = H['mat']
WHITE = mat('PL_SE_White', (0.80, 0.81, 0.80), 0.0, 0.42)
PLINTH = mat('PL_SE_Plinth', (0.10, 0.105, 0.11), 0.2, 0.5)
SEAM = mat('PL_SE_Seam', (0.03, 0.03, 0.032), 0.0, 0.8)
SE_GREEN = mat('PL_SE_Green', (0.12, 0.55, 0.12), 0.0, 0.45)
DGREY = mat('PL_SE_DarkGrey', (0.05, 0.055, 0.06), 0.1, 0.45)
BATT = mat('PL_SE_BattDoor', (0.20, 0.21, 0.22), 0.1, 0.45)

D_UPS, D_BAT = 1.06, 0.53
H_UPS, H_BAT = 2.14, 2.055
cabs = [('IO', 2.12)] + [(f'PWR{i}', 0.76) for i in range(6)] + [('GAP', 0.30)] + [(f'BAT{i}', 0.65) for i in range(4)]
TOTAL = sum(w for _, w in cabs)
Y0 = -D_UPS / 2
x = -TOTAL / 2
pos = {}
for n, w in cabs:
    pos[n] = (x, x + w); x += w
yf = Y0 - 0.0006

seams, vents, screws = [], [], []
for n, (xa, xb) in pos.items():
    if n == 'GAP':
        continue
    w = xb - xa; xc = (xa + xb) / 2
    bat = n.startswith('BAT')
    d = D_BAT if bat else D_UPS; h = H_BAT if bat else H_UPS
    yc = Y0 + d / 2
    H['box'](f'Cab_{n}', (w - 0.004, d, h - 0.10), (xc, yc, 0.10 + (h - 0.10) / 2), WHITE, col, bevel=0.003, parent=root)
    H['box'](f'Cab_{n}_Plinth', (w - 0.02, d - 0.03, 0.10), (xc, yc + 0.01, 0.05), PLINTH, col, parent=root)
    # cabinet joint
    seams.append(((xa + 0.001, yf, 0.10 + (h - 0.10) / 2), (0.004, h - 0.10), 0.0))
    if n == 'IO':
        for k in range(1, 4):                          # 4 door leaves
            seams.append(((xa + k * w / 4, yf, 0.10 + (h - 0.10) / 2), (0.003, h - 0.16), 0.0))
        for k in range(4):
            xd = xa + (k + 0.5) * w / 4
            screws.append(((xd + (0.20 if k % 2 == 0 else -0.20), Y0 - 0.012, 1.05), (0.018, 0.025, 0.14)))   # handles
        # lower vent slots on outer leaves
        for k in (1, 2):
            xd = xa + (k + 0.5) * w / 4
            for i in range(10):
                for j in range(14):
                    vents.append(((xd - 0.17 + i * 0.038 + (0.019 if j % 2 else 0), yf - 0.0003, 0.30 + j * 0.03), (0.026, 0.006), math.radians(35)))
    elif n.startswith('PWR'):
        seams.append(((xc, yf, h - 0.09), (w - 0.03, 0.003), 0.0))
        screws.append(((xb - 0.07, Y0 - 0.012, 1.05), (0.018, 0.025, 0.14)))
        for i in range(12):                           # perforated door field
            for j in range(40):
                vents.append(((xc - 0.25 + i * 0.045 + (0.022 if j % 2 else 0), yf - 0.0003, 0.40 + j * 0.034), (0.030, 0.007), math.radians(35)))
    else:  # battery cabinet
        seams.append(((xc, yf, 0.10 + 0.012), (w - 0.03, 0.003), 0.0))
        screws.append(((xb - 0.06, Y0 - 0.012, 1.05), (0.018, 0.025, 0.14)))
        H['box'](f'Cab_{n}_Door', (w - 0.03, 0.006, h - 0.16), (xc, Y0 - 0.003, 0.10 + (h - 0.10) / 2), BATT, col, bevel=0.002, parent=root)
        for i in range(8):
            for j in range(3):
                vents.append(((xc - 0.21 + i * 0.06, Y0 - 0.0068, 0.22 + j * 0.025), (0.04, 0.008), 0.0))
                vents.append(((xc - 0.21 + i * 0.06, Y0 - 0.0068, h - 0.18 + j * 0.025), (0.04, 0.008), 0.0))
        k = int(n[3:])
        H['box'](f'Cab_{n}_BMS', (0.11, 0.004, 0.07), (xc, Y0 - 0.008, 1.55), M['black_gl'], col, parent=root)
        P['led'](f'LED_battery_{k}_screen', (xc, Y0 - 0.0102, 1.55), (0.09, 0.0006, 0.05), PM['screen'], col, root)
        P['led'](f'LED_battery_{k}', (xc - 0.03, Y0 - 0.008, 1.47), (0.012, 0.004, 0.012), PM['led_g'], col, root)
        P['led'](f'LED_battery_{k}_fault', (xc + 0.03, Y0 - 0.008, 1.47), (0.012, 0.004, 0.012), PM['led_a'], col, root)
        P['text'](f'Cab_{n}_Label', 'Li-ion', 0.035, PM['label_w'], col, root, (xc, Y0 - 0.0065, 1.68))
        P['text'](f'Cab_{n}_Brand', 'Schneider Electric', 0.022, PM['label_w'], col, root, (xc, Y0 - 0.0065, 1.78))

P['quads']('UPS_Seams', seams, SEAM, col, root)
P['quads']('UPS_DoorPerforation', vents, PM['vent'], col, root)
H['slat_array']('UPS_Handles', lambda: iter(screws), DGREY, col, root)

# ---------------------------------------------------------------- I/O cabinet front: display + branding
xa, xb = pos['IO']; w = xb - xa
xd = xa + 0.5 * w / 4
H['box']('IO_DisplayBezel', (0.30, 0.012, 0.20), (xd, Y0 - 0.006, 1.58), M['black_gl'], col, bevel=0.004, parent=root)
P['led']('LED_ups_screen', (xd, Y0 - 0.0125, 1.58), (0.26, 0.002, 0.16), PM['screen'], col, root)
# single-line mimic on the screen (input -> rectifier -> inverter -> output)
H['slat_array']('IO_ScreenMimic', lambda: iter([((xd, Y0 - 0.0140, 1.60), (0.20, 0.0006, 0.006)),
                                               ((xd - 0.05, Y0 - 0.0140, 1.60), (0.03, 0.0006, 0.03)),
                                               ((xd + 0.03, Y0 - 0.0140, 1.60), (0.03, 0.0006, 0.03)),
                                               ((xd - 0.01, Y0 - 0.0140, 1.55), (0.006, 0.0006, 0.05))]), PM['label_w'], col, root)
P['led']('LED_ups_status', (xd, Y0 - 0.004, 1.44), (0.20, 0.004, 0.010), PM['led_g'], col, root)
P['text']('IO_Name', 'Galaxy VX', 0.075, DGREY, col, root, (xa + 0.75 * w / 4 + 0.05, Y0 - 0.0008, 1.93))
P['text']('IO_Brand', 'Schneider', 0.050, SE_GREEN, col, root, (xa + 2.5 * w / 4, Y0 - 0.0008, 1.95))
P['text']('IO_Brand2', 'Electric', 0.050, SE_GREEN, col, root, (xa + 2.5 * w / 4, Y0 - 0.0008, 1.89))
P['text']('IO_Rating', '1500 kW', 0.04, DGREY, col, root, (xa + 3.5 * w / 4, Y0 - 0.0008, 1.93))
for i in range(6):
    xa2, xb2 = pos[f'PWR{i}']
    P['text'](f'PWR{i}_Label', f'250 kW  #{i + 1}', 0.03, DGREY, col, root, ((xa2 + xb2) / 2, Y0 - 0.0008, 2.0))

# ---------------------------------------------------------------- top cabling (flow paths) + tray
xa, xb = pos['IO']
x_in, x_out = xa + 0.35, xa + 0.80
y_c = 0.15
Z_TOP = H_UPS
P['flow_path']('FLOW_power_ac_in', [(x_in, y_c, 3.0), (x_in, y_c, Z_TOP + 0.01)], PM['cable'], col, root, radius=0.06, verts=14, kind='power')
P['flow_path']('FLOW_power_ac_out', [(x_out, y_c, Z_TOP + 0.01), (x_out, y_c, 3.0)], PM['cable'], col, root, radius=0.06, verts=14, kind='power')
P['socket']('SOCKET_power_in', (x_in, y_c, 3.0), (0, 0, 1), root, col)
P['socket']('SOCKET_power_out', (x_out, y_c, 3.0), (0, 0, 1), root, col)
P['cylinders']('UPS_CableGlands', [((x, y_c, Z_TOP + 0.01), 0.09, 0.02, (0, 0, 0)) for x in (x_in, x_out)], M['black_mt'], col, root, verts=20)
# battery DC bus: from the far battery cabinet along a ladder tray to the I/O cabinet
xb0 = sum(pos['BAT3']) / 2; yb = Y0 + D_BAT / 2
Z_TRAY = 2.50
x_dc = xa + 1.45
P['flow_path']('FLOW_power_dc_battery', [(xb0, yb, H_BAT + 0.01), (xb0, yb, Z_TRAY + 0.04), (x_dc, yb, Z_TRAY + 0.04), (x_dc, yb, Z_TOP + 0.01)],
               PM['cable'], col, root, rect=(0.16, 0.05), bend=0.12, kind='power')
for k in range(3):   # each battery cabinet drops into the bus
    xk = sum(pos[f'BAT{k}']) / 2
    P['flow_path'](f'FLOW_power_dc_battery_{k}', [(xk, yb, H_BAT + 0.01), (xk, yb, Z_TRAY + 0.02)], PM['cable'], col, root, radius=0.03, verts=10, kind='power')
def tray():
    L = xb0 + 0.25 - (x_dc - 0.25)
    xc = (xb0 + 0.25 + x_dc - 0.25) / 2
    for dy in (-0.16, 0.16):
        yield (xc, yb + dy, Z_TRAY + 0.04), (L, 0.006, 0.08)
    n = int(L / 0.3)
    for i in range(n + 1):
        yield (x_dc - 0.25 + i * L / n, yb, Z_TRAY), (0.03, 0.32, 0.012)
H['slat_array']('UPS_CableTray', tray, PM['galv'], col, root)
# tray hangers (threaded rods up to the ceiling level)
P['cylinders']('UPS_TrayHangers', [((x, yb + dy, Z_TRAY + 0.3), 0.006, 0.6, (0, 0, 0)) for x in (x_dc + 0.2, (x_dc + xb0) / 2, xb0 - 0.1) for dy in (-0.17, 0.17)],
               PM['galv'], col, root, verts=8)

tris = P['finish'](root, BLEND, GLB)
print('FOOTPRINT', round(TOTAL, 3), 'x', D_UPS)
P['render']('plant_02_ups', {
    'front':  ((0, -1, 0.1), 1.55, 50),
    '34':     ((-0.7, -1, 0.45), 1.5, 50),
    'rear34': ((0.8, 1, 0.8), 1.5, 50),
    'io':     ((-0.3, -1, 0.15), 0.42, 50, (pos['IO'][0] + 1.0, -0.5, 1.5)),
    'batt':   ((0.4, -1, 0.3), 0.35, 50, (sum(pos['BAT1']) / 2 + 0.3, -0.3, 1.4)),
}, (0, 0, 1.1), TOTAL)
