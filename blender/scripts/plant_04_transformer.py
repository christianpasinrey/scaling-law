"""plant_04_transformer - outdoor three-phase pad-mounted transformer, 2500 kVA, 13.2 kV delta -> 480Y/277 V.
The "2-4 year lead-time" item.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python plant_04_transformer.py

Dimensions: Eaton Cooper Power series catalog CA202003EN (April 2016), Table 7, 2500 kVA row:
  A (height) 73 in = 1854 mm, B (width) 72 in = 1829 mm, C (overall depth) 99 in = 2515 mm,
  D (cabinet depth) 42 in = 1067 mm; pad G x H = 76 x 103 in (1930 x 2616 mm). Fluid 490 gal, ~12,500 lb.
Look: Wikimedia "Pad mount substation in Baltimore County, MD with cooling oil fins on side visible"
(panel radiators on the tank sides, front cabinet with doors, lifting hooks) and "Prolec GE Pad Mounted"
(green tank, hinged sloped cabinet roof, padlock hasp at the sill).
Origin = floor centre of the concrete pad (ground z=0), cabinet front faces -Y.
Exterior stub convention: power conduits at z = 0.30 m. MV in on the -X side, LV out on the +X side.
"""
import bpy, math, os, sys
exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\plant_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']; P = bpy.app.driver_namespace['PLANT']

ROOT = 'Plant_Transformer_Padmount2500'
BLEND = os.path.join(P['BASE'], 'plant_04_transformer.blend')
GLB = os.path.join(P['BASE'], 'export', 'plant_04_transformer.glb')
root, col, M, PM = P['setup'](ROOT)
mat = H['mat']
GREEN = mat('PL_PadmountGreen', (0.045, 0.085, 0.045), 0.15, 0.5)          # Munsell 7GY 3.29/1.5 pad-mount green
GREEN_D = mat('PL_PadmountGreenDark', (0.03, 0.055, 0.03), 0.15, 0.55)
SEAM = mat('PL_PM_Seam', (0.01, 0.015, 0.01), 0.0, 0.8)

IN = 0.0254
W, DEP, HT = 72 * IN, 99 * IN, 73 * IN
CAB_D = 42 * IN
PAD_W, PAD_D, PAD_T = 76 * IN, 103 * IN, 0.15
Z0 = PAD_T
Y_FRONT = -DEP / 2
Y_CAB = Y_FRONT + CAB_D           # cabinet / tank interface
TANK_W = W - 2 * 0.20             # radiators take 0.20 m on each side
TANK_H = HT - 0.10

# ---------------------------------------------------------------- pad
H['box']('TX_Pad', (PAD_W, PAD_D, PAD_T), (0, 0, PAD_T / 2), PM['conc'], col, bevel=0.01, parent=root)
# ---------------------------------------------------------------- cabinet (front compartment)
H['box']('TX_Cabinet', (W, CAB_D, HT - 0.06), (0, Y_FRONT + CAB_D / 2, Z0 + (HT - 0.06) / 2), GREEN, col, bevel=0.006, parent=root)
# hinged roof lid, slightly sloped toward the front (as on the Prolec unit)
H['prism']('TX_CabinetRoof', [(Y_FRONT - 0.02, Z0 + HT - 0.06), (Y_CAB, Z0 + HT - 0.06), (Y_CAB, Z0 + HT), (Y_FRONT - 0.02, Z0 + HT - 0.035)], 'yz', -W / 2 - 0.015, W + 0.03, GREEN, col, parent=root)
P['cylinders']('TX_RoofHinges', [((x, Y_CAB - 0.03, Z0 + HT + 0.005), 0.012, 0.10, (0, math.pi / 2, 0)) for x in (-0.55, 0.55)], GREEN_D, col, root, verts=12)
yf = Y_FRONT - 0.0008
seams = [((0, yf, Z0 + HT / 2), (0.008, HT - 0.12), 0.0),                       # centre sill between doors
         ((0, yf, Z0 + 0.06), (W - 0.04, 0.006), 0.0)]
P['quads']('TX_DoorSeams', seams, SEAM, col, root)
H['box']('TX_DoorSill', (W - 0.04, 0.03, 0.10), (0, Y_FRONT - 0.015, Z0 + 0.05), GREEN_D, col, parent=root)
H['box']('TX_PadlockHasp', (0.08, 0.05, 0.07), (0, Y_FRONT - 0.035, Z0 + 0.12), GREEN_D, col, bevel=0.004, parent=root)
H['box']('TX_PentaBolt', (0.03, 0.03, 0.03), (0.12, Y_FRONT - 0.02, Z0 + 0.12), M['steel'], col, parent=root)
# padlock (as in the Prolec photo)
P['tori']('TX_Padlock_Shackle', [((0, Y_FRONT - 0.07, Z0 + 0.10), 0.02, 0.004, (0, math.pi / 2, 0))], M['steel'], col, root, major_segs=16)
H['box']('TX_Padlock_Body', (0.05, 0.022, 0.05), (0, Y_FRONT - 0.07, Z0 + 0.065), M['steel'], col, bevel=0.006, parent=root)
# door handles
P['cylinders']('TX_DoorHandles', [((x, Y_FRONT - 0.02, Z0 + 1.0), 0.015, 0.04, (math.pi / 2, 0, 0)) for x in (-0.12, 0.12)], M['steel'], col, root, verts=12)
# labels: unit number, DANGER, nameplate area, brand
H['box']('TX_Label_UnitNo', (0.24, 0.002, 0.10), (-0.60, Y_FRONT - 0.001, Z0 + 1.60), PM['label_y'], col, parent=root)
P['text']('TX_Text_UnitNo', 'T-01', 0.07, PM['label_k'], col, root, (-0.60, Y_FRONT - 0.0025, Z0 + 1.60))
for x in (-0.45, 0.45):
    H['box'](f'TX_Label_Danger_{x:+.0f}', (0.36, 0.002, 0.22), (x, Y_FRONT - 0.001, Z0 + 1.20), PM['label_w'], col, parent=root)
    H['box'](f'TX_Label_DangerHdr_{x:+.0f}', (0.36, 0.0025, 0.07), (x, Y_FRONT - 0.0012, Z0 + 1.275), PM['label_r'], col, parent=root)
    P['text'](f'TX_Text_Danger_{x:+.0f}', 'DANGER', 0.045, PM['label_w'], col, root, (x, Y_FRONT - 0.0028, Z0 + 1.275))
    P['text'](f'TX_Text_HV_{x:+.0f}', 'HIGH VOLTAGE', 0.035, PM['label_k'], col, root, (x, Y_FRONT - 0.0025, Z0 + 1.19))
    P['text'](f'TX_Text_Keep_{x:+.0f}', 'KEEP OUT', 0.030, PM['label_k'], col, root, (x, Y_FRONT - 0.0025, Z0 + 1.135))
H['box']('TX_Label_Brand', (0.36, 0.002, 0.08), (0.0, Y_FRONT - 0.001, Z0 + 0.40), PM['label_r'], col, parent=root)
P['text']('TX_Text_Brand', 'EATON', 0.05, PM['label_w'], col, root, (0.0, Y_FRONT - 0.0025, Z0 + 0.40))
H['box']('TX_Label_NonPCB', (0.16, 0.002, 0.09), (0.66, Y_FRONT - 0.001, Z0 + 1.60), mat('PL_LabelBlue', (0.05, 0.12, 0.6), 0.0, 0.5), col, parent=root)
P['text']('TX_Text_NonPCB', 'NON PCB', 0.03, PM['label_w'], col, root, (0.66, Y_FRONT - 0.0025, Z0 + 1.60))
P['text']('TX_Text_kVA', '2500 kVA', 0.06, PM['label_k'], col, root, (0.45, Y_FRONT - 0.0025, Z0 + 0.75))
P['text']('TX_Text_V', '13200 - 480Y/277', 0.035, PM['label_k'], col, root, (0.45, Y_FRONT - 0.0025, Z0 + 0.68))
# faulted-circuit / status indicator the game can drive (pad-mounts carry external fault indicators)
P['cylinders']('TX_IndicatorBezel', [((-0.70, Y_FRONT - 0.01, Z0 + 1.40), 0.035, 0.02, (math.pi / 2, 0, 0))], M['black_mt'], col, root, verts=16)
P['led']('LED_fault_indicator', (-0.70, Y_FRONT - 0.022, Z0 + 1.40), (0.04, 0.004, 0.04), PM['led_g'], col, root)

# ---------------------------------------------------------------- tank + radiators
tank_d = DEP - CAB_D - 0.02
yc_t = Y_CAB + tank_d / 2
H['box']('TX_Tank', (TANK_W, tank_d, TANK_H), (0, yc_t, Z0 + TANK_H / 2), GREEN, col, bevel=0.01, parent=root)
H['box']('TX_TankCover', (TANK_W + 0.04, tank_d + 0.04, 0.03), (0, yc_t, Z0 + TANK_H + 0.015), GREEN, col, bevel=0.005, parent=root)
H['box']('TX_TankBase', (TANK_W + 0.08, tank_d + 0.06, 0.08), (0, yc_t, Z0 + 0.04), GREEN_D, col, parent=root)
# lifting hooks at the 4 tank corners (as in the photo)
for sx in (-1, 1):
    for sy in (-1, 1):
        H['prism'](f'TX_LiftHook_{sx}{sy}', [(0, 0), (0.09, 0), (0.09, 0.06), (0.05, 0.10), (0.0, 0.10)], 'yz',
                   sx * (TANK_W / 2 - 0.02), 0.025 * sx, GREEN_D, col, parent=root).location = (0, yc_t + sy * (tank_d / 2 - 0.12) - 0.045, Z0 + TANK_H - 0.02)
# panel radiators: 4 banks per side, each bank = 5 plates parallel to the tank wall (Baltimore photo)
plates, headers = [], []
rad_h = TANK_H - 0.45
for sx in (-1, 1):
    for b in range(4):
        yb = Y_CAB + 0.18 + b * (tank_d - 0.30) / 4 + (tank_d - 0.30) / 8
        for k in range(5):
            xk = sx * (TANK_W / 2 + 0.03 + k * 0.032)
            plates.append(((xk, yb, Z0 + 0.20 + rad_h / 2), (0.008, (tank_d - 0.30) / 4 - 0.05, rad_h)))
        for zh in (Z0 + 0.25, Z0 + 0.15 + rad_h):
            headers.append(((sx * (TANK_W / 2 + 0.08), yb, zh), 0.025, 0.17, (0, math.pi / 2, 0)))
H['slat_array']('TX_RadiatorPlates', lambda: iter(plates), GREEN, col, root)
P['cylinders']('TX_RadiatorHeaders', headers, GREEN_D, col, root, verts=12)
# chevron pressing on the outer plates (decal lines)
chev = []
for sx in (-1, 1):
    for b in range(4):
        yb = Y_CAB + 0.18 + b * (tank_d - 0.30) / 4 + (tank_d - 0.30) / 8
        xo = sx * (TANK_W / 2 + 0.03 + 4 * 0.032 + 0.0045)
        for j in range(14):
            z = Z0 + 0.35 + j * (rad_h - 0.3) / 14
            for s in (-1, 1):
                chev.append(((xo, yb + s * 0.07, z), (0.13, 0.012), s * math.radians(-30) * sx))
P['quads']('TX_RadiatorChevrons_L', [c for c in chev if c[0][0] < 0], GREEN_D, col, root, face='-X')
P['quads']('TX_RadiatorChevrons_R', [c for c in chev if c[0][0] > 0], GREEN_D, col, root, face='+X')
# accessories on the tank wall at the cabinet: pressure relief valve, fill plug, drain valve
P['cylinders']('TX_Accessories', [((0.3, Y_CAB + 0.02, Z0 + TANK_H - 0.15), 0.03, 0.06, (math.pi / 2, 0, 0)),
                                   ((-0.3, Y_CAB + 0.02, Z0 + TANK_H - 0.15), 0.025, 0.05, (math.pi / 2, 0, 0))], M['steel'], col, root, verts=12)

# ---------------------------------------------------------------- MV in / LV out (conduit stubs at z=0.30)
ZP = P['EXT_POWER_Z']
y_mv = Y_FRONT + CAB_D * 0.5
x_side = W / 2
# MV: three single-core 15 kV cables entering the left (-X) side of the primary compartment
for k, dy in enumerate((-0.12, 0.0, 0.12)):
    P['flow_path'](f'FLOW_power_mv_in_{k}', [(-x_side - 0.60, y_mv + dy, ZP), (-x_side + 0.02, y_mv + dy, ZP)], PM['cable'], col, root, radius=0.028, verts=12, kind='power')
P['cylinders']('TX_MV_ConduitHub', [((-x_side - 0.01, y_mv, ZP), 0.20, 0.03, (0, math.pi / 2, 0))], M['black_mt'], col, root, verts=20)
P['socket']('SOCKET_power_in', (-x_side - 0.60, y_mv, ZP), (-1, 0, 0), root, col)
# LV: bundle of parallel 480 V runs leaving the right (+X) side of the secondary compartment
P['flow_path']('FLOW_power_lv_out', [(x_side - 0.02, y_mv, ZP), (x_side + 0.60, y_mv, ZP)], PM['cable'], col, root, rect=(0.30, 0.12), bend=0.0, kind='power')
H['box']('TX_LV_ConduitHub', (0.03, 0.40, 0.20), (x_side + 0.01, y_mv, ZP), M['black_mt'], col, parent=root)
P['socket']('SOCKET_power_out', (x_side + 0.60, y_mv, ZP), (1, 0, 0), root, col)

tris = P['finish'](root, BLEND, GLB)
print('FOOTPRINT pad', round(PAD_W, 3), 'x', round(PAD_D, 3), 'unit', round(W, 3), round(DEP, 3), round(HT + Z0, 3))
P['render']('plant_04_transformer', {
    '34':     ((-0.9, -1, 0.55), 2.5, 50),
    'front':  ((0, -1, 0.12), 2.5, 50),
    'side':   ((-1, -0.25, 0.25), 2.5, 50),
    'rear34': ((0.9, 1, 0.6), 2.5, 50),
    'labels': ((0.15, -1, 0.1), 0.7, 50, (-0.1, -1.3, 1.3)),
}, (0, 0, 1.0), 3.0)
