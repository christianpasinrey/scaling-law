"""plant_07_chiller - Carrier AquaForce 30XA-1002 air-cooled screw chiller (~950 kW cooling).

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python plant_07_chiller.py

Dimensions: used 2017 Carrier 30XA 1002 (Exapro listing): 9574 x 2253 x 2297 mm, 7327 kg, two screw
compressors on two refrigerant circuits, ~952 kW. (Carrier US 30XA table: size 102 = 188 x 88 x 91 in.)
Look: Wikimedia "Air Cooled Liquid Chiller" (light grey casing, coil section over a lower bay of compressors
behind wire-mesh guards, fans on top, steel base rails) and "Trane AquaStream 3G chiller" (control panel
with display, mesh guards, V coils). 30XA specifics (2 rows of fans over V coils, Touch Pilot display at the
control-box end) from Carrier product imagery knowledge - approximate.
Fans: separate objects FAN_01..FAN_14 (origin at hub, spin about local Z).
Origin = floor centre of the pad (ground z=0), long axis X, water connections at -X, control box at +X.
Exterior stub convention: coolant z = 1.00 m, power z = 0.30 m.
"""
import bpy, math, os, sys
exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\plant_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']; P = bpy.app.driver_namespace['PLANT']

ROOT = 'Plant_Chiller_Carrier30XA'
BLEND = os.path.join(P['BASE'], 'plant_07_chiller.blend')
GLB = os.path.join(P['BASE'], 'export', 'plant_07_chiller.glb')
root, col, M, PM = P['setup'](ROOT)
mat = H['mat']
CASE = mat('PL_CH_Casing', (0.62, 0.64, 0.65), 0.1, 0.45)
CASE_D = mat('PL_CH_CasingDark', (0.38, 0.40, 0.41), 0.1, 0.5)
COIL = mat('PL_CH_Coil', (0.10, 0.11, 0.115), 0.7, 0.45)
FINL = mat('PL_CH_FinLines', (0.36, 0.30, 0.25), 0.9, 0.4)     # copper-tube/alu-fin tint
MESH = mat('PL_CH_WireMesh', (0.25, 0.26, 0.27), 0.8, 0.4)
COMP = mat('PL_CH_Compressor', (0.55, 0.57, 0.60), 0.3, 0.45)
INSUL = mat('PL_CH_Insulation', (0.015, 0.015, 0.016), 0.0, 0.85)
CBLUE = mat('PL_CarrierBlue', (0.01, 0.10, 0.40), 0.0, 0.45)

L, W, HT = 9.574, 2.253, 2.297
PAD_T = 0.12
Z0 = PAD_T
ZR = Z0 + 0.15                 # top of base rails
ZM = Z0 + 1.05                 # top of the lower (compressor/evaporator) bay
ZT = Z0 + 2.15                 # coil top / fan deck
X0, X1 = -L / 2, L / 2
XC = X1 - 0.65                 # control box starts here
YB, YT = 0.30, W / 2 - 0.03

H['box']('CH_Pad', (L + 0.5, W + 0.5, PAD_T), (0, 0, PAD_T / 2), PM['conc'], col, bevel=0.01, parent=root)
# ---------------------------------------------------------------- base rails + lower frame
H['slat_array']('CH_BaseRails', lambda: iter([((0, s * (W / 2 - 0.08), Z0 + 0.075), (L, 0.16, 0.15)) for s in (-1, 1)] +
                                            [((x, 0, Z0 + 0.075), (0.12, W - 0.1, 0.15)) for x in (X0 + 0.1, 0, XC - 0.1)]), PM['galv'], col, root)
posts = []
n_bays = 5
for i in range(n_bays + 1):
    x = X0 + 0.04 + i * (XC - X0 - 0.08) / n_bays
    for s in (-1, 1):
        posts.append(((x, s * (W / 2 - 0.04), (ZR + ZM) / 2), (0.08, 0.08, ZM - ZR)))
posts += [((( X0 + XC) / 2, s * (W / 2 - 0.04), ZM - 0.03), (XC - X0, 0.08, 0.06)) for s in (-1, 1)]
posts += [((( X0 + XC) / 2, s * (W / 2 - 0.04), ZR + 0.03), (XC - X0, 0.08, 0.06)) for s in (-1, 1)]
H['slat_array']('CH_LowerFrame', lambda: iter(posts), CASE, col, root)
H['box']('CH_LowerFloor', (XC - X0, W - 0.1, 0.03), ((X0 + XC) / 2, 0, ZR + 0.015), CASE_D, col, parent=root)
H['box']('CH_CoilTray', (XC - X0, W - 0.04, 0.10), ((X0 + XC) / 2, 0, ZM + 0.05), CASE, col, parent=root)
H['box']('CH_EndPanel_A_Lower', (0.03, W - 0.1, ZM - ZR), (X0 + 0.015, 0, (ZR + ZM) / 2), CASE, col, parent=root)

# evaporator (insulated shell-and-tube) + two screw compressors + oil separators inside the lower bay
P['cylinders']('CH_Evaporator', [(((X0 + XC) / 2 - 0.4, 0.0, Z0 + 0.62), 0.36, XC - X0 - 1.6, (0, math.pi / 2, 0))], INSUL, col, root, verts=28)
P['cylinders']('CH_EvapHeads', [((x, 0.0, Z0 + 0.62), 0.38, 0.08, (0, math.pi / 2, 0)) for x in (X0 + 0.40, XC - 1.20)], COMP, col, root, verts=28)
comps = []
for k, x in enumerate((X0 + 2.6, X0 + 5.6)):
    for s in (-1, 1):
        if (k + (s > 0)) % 2:
            continue
    comps.append(((x, -0.55, Z0 + 0.60), 0.24, 1.10, (0, math.pi / 2, 0)))
    comps.append(((x, 0.55, Z0 + 0.62), 0.22, 0.90, (0, math.pi / 2, 0)))       # oil separator
P['cylinders']('CH_Compressors', comps, COMP, col, root, verts=20)
H['slat_array']('CH_CompMotors', lambda: (((x + 0.75, -0.55, Z0 + 0.60), (0.45, 0.42, 0.42)) for x in (X0 + 2.6, X0 + 5.6)), COMP, col, root)
# wire-mesh guards on both long sides of the lower bay (merged grid)
def mesh_grid():
    xa, xb = X0 + 0.08, XC - 0.08
    for s in (-1, 1):
        y = s * (W / 2 - 0.02)
        nx = int((xb - xa) / 0.06)
        for i in range(nx + 1):
            yield (xa + i * (xb - xa) / nx, y, (ZR + ZM) / 2), (0.004, 0.004, ZM - ZR - 0.06)
        nz = int((ZM - ZR) / 0.06)
        for j in range(nz):
            yield ((xa + xb) / 2, y, ZR + 0.04 + j * 0.06), (xb - xa, 0.004, 0.004)
H['slat_array']('CH_WireMeshGuards', mesh_grid, MESH, col, root)

# ---------------------------------------------------------------- V coil section (upper)
dy, dz = YT - YB, ZT - ZM - 0.10
slope = math.atan2(dz, dy); clen = math.hypot(dy, dz)
LC = XC - X0
xcc = (X0 + XC) / 2
trap = [(-YB - 0.04, ZM + 0.10), (YB + 0.04, ZM + 0.10), (YT, ZT), (-YT, ZT)]
H['prism']('CH_CoilEnd_A', trap, 'yz', X0, 0.04, CASE, col, parent=root)
n_mod = 7
mpitch = (LC - 0.1) / n_mod
for i in range(1, n_mod):
    H['prism'](f'CH_CoilPartition_{i}', [(a * 0.97, b) for a, b in trap], 'yz', X0 + 0.05 + i * mpitch - 0.01, 0.02, CASE, col, parent=root)
for s in (-1, 1):
    yc, zc = s * (YB + dy / 2), ZM + 0.10 + dz / 2
    rx = -s * (math.pi / 2 - slope)
    P['boxes'](f'CH_Coil_{"L" if s < 0 else "R"}', [((xcc, yc, zc), (LC - 0.08, 0.10, clen), (rx, 0, 0))], COIL, col, root)
    ny, nz = s * math.sin(slope), -math.cos(slope)
    def fins(s=s, yc=yc, zc=zc, ny=ny, nz=nz, rx=rx):
        n = int((LC - 0.15) / 0.045)
        for i in range(n):
            x = X0 + 0.08 + i * (LC - 0.15) / n
            yield (x, yc + ny * 0.052, zc + nz * 0.052), (0.006, 0.004, clen - 0.05), (rx, 0, 0)
    P['boxes'](f'CH_CoilFins_{"L" if s < 0 else "R"}', fins(), FINL, col, root)
H['box']('CH_FanDeck', (LC, W - 0.02, 0.04), (xcc, 0, ZT + 0.02), CASE, col, parent=root)
H['slat_array']('CH_DeckEdge', lambda: iter([((xcc, s * (W / 2 - 0.02), ZT + 0.07), (LC, 0.04, 0.10)) for s in (-1, 1)]), CASE, col, root)

# ---------------------------------------------------------------- fans 2 x 7
FD = 0.80
fan_pos = [(X0 + 0.05 + (i + 0.5) * mpitch, s * 0.53) for i in range(n_mod) for s in (-1, 1)]
P['cylinders']('CH_FanOpenings', [((x, y, ZT + 0.045), FD / 2 + 0.01, 0.01, (0, 0, 0)) for x, y in fan_pos], PM['vent'], col, root, verts=32)
P['tori']('CH_FanShrouds', [((x, y, ZT + 0.07 + k * 0.045), FD / 2 + 0.025, 0.022, (0, 0, 0)) for x, y in fan_pos for k in range(2)], CASE, col, root, major_segs=32, minor_segs=4)
P['tori']('CH_FanGuards', [((x, y, ZT + 0.147), r, 0.004, (0, 0, 0)) for x, y in fan_pos for r in (0.10, 0.19, 0.28, 0.37)], M['black_st'], col, root, major_segs=28, minor_segs=3)
P['boxes']('CH_FanGuardSpokes', (((x, y, ZT + 0.147), (FD - 0.03, 0.006, 0.006), (0, 0, a * math.pi / 4)) for x, y in fan_pos for a in range(4)), M['black_st'], col, root)
for i, (x, y) in enumerate(fan_pos):
    P['fan'](f'FAN_{i + 1:02d}', (x, y, ZT + 0.10), FD, col, root, PM, blades=4, pitch=0.4)

# ---------------------------------------------------------------- control box (+X end) with Touch Pilot display
cb_l = X1 - XC
H['box']('CH_ControlBox', (cb_l, W - 0.02, ZT + 0.06 - ZR), ((XC + X1) / 2, 0, (ZR + ZT + 0.06) / 2), CASE, col, bevel=0.006, parent=root)
seams = [((X1 + 0.0008, y, (ZR + ZT) / 2), (0.006, ZT - ZR - 0.1), 0.0) for y in (-0.37, 0.37)]
P['quads']('CH_ControlDoorSeams', seams, CASE_D, col, root, face='+X')
H['box']('CH_DisplayBezel', (0.012, 0.26, 0.19), (X1 + 0.006, -0.55, 1.65), M['black_gl'], col, bevel=0.003, parent=root)
P['led']('LED_hmi_screen', (X1 + 0.0125, -0.55, 1.65), (0.002, 0.22, 0.15), PM['screen'], col, root)
P['led']('LED_status', (X1 + 0.004, -0.55, 1.50), (0.004, 0.12, 0.012), PM['led_g'], col, root)
P['led']('LED_alarm', (X1 + 0.004, -0.40, 1.50), (0.004, 0.03, 0.012), PM['led_r'], col, root)
H['slat_array']('CH_DoorHandles', lambda: (((X1 + 0.015, y, 1.1), (0.03, 0.03, 0.18)) for y in (-0.42, 0.32)), M['black_mt'], col, root)
H['box']('CH_MainSwitch', (0.06, 0.12, 0.12), (X1 + 0.03, 0.75, 1.3), PM['label_y'], col, parent=root)
H['box']('CH_MainSwitchHandle', (0.06, 0.03, 0.10), (X1 + 0.07, 0.75, 1.3), PM['label_r'], col, parent=root)
P['text']('CH_Brand_End', 'Carrier', 0.13, CBLUE, col, root, (X1 + 0.002, 0.0, ZT - 0.25), face='+X')
P['text']('CH_Brand_Side', 'Carrier', 0.16, CBLUE, col, root, (X1 - cb_l / 2, -W / 2 + 0.01 - 0.002, ZT - 0.30))
P['text']('CH_Model_Side', 'AquaForce 30XA', 0.07, CASE_D, col, root, (X1 - cb_l / 2, -W / 2 + 0.01 - 0.002, ZT - 0.48))
P['text']('CH_Brand_Side_B', 'Carrier', 0.16, CBLUE, col, root, (X1 - cb_l / 2, W / 2 - 0.01 + 0.002, ZT - 0.30), face='+Y')

# ---------------------------------------------------------------- water connections (-X end, z=1.00) + power (+X, z=0.30)
ZC = P['EXT_COOLANT_Z']
r_n = 0.084   # DN150 victaulic nozzles
x_e = X0 + 0.40
for name, y, pm, d in (('in', 0.20, PM['pipe_red'], 'in'), ('out', -0.20, PM['pipe_blue'], 'out')):
    pts = [(X0 - 0.80, y, ZC), (x_e - 0.55, y, ZC), (x_e - 0.55, y, Z0 + 0.62), (x_e - 0.04, y, Z0 + 0.62)]
    if d == 'out':
        pts = list(reversed(pts))
    P['flow_path'](f'FLOW_coolant_{name}', pts, pm, col, root, radius=r_n, verts=18, bend=0.18, kind='coolant')
    P['socket'](f'SOCKET_coolant_{name}', (X0 - 0.80, y, ZC), (-1, 0, 0), root, col)
    P['cylinders'](f'CH_Victaulic_{name}', [((x, y, ZC), r_n + 0.015, 0.04, (0, math.pi / 2, 0)) for x in (X0 - 0.70, X0 - 0.30)], M['steel'], col, root, verts=20)
P['flow_path']('FLOW_power_in', [(X1 + 0.80, 0.55, P['EXT_POWER_Z']), (X1 + 0.10, 0.55, P['EXT_POWER_Z']), (X1 + 0.10, 0.55, 0.80), (X1 - 0.02, 0.55, 0.80)],
               PM['cable'], col, root, radius=0.04, verts=12, bend=0.12, kind='power')
P['socket']('SOCKET_power_in', (X1 + 0.80, 0.55, P['EXT_POWER_Z']), (1, 0, 0), root, col)

tris = P['finish'](root, BLEND, GLB)
print('FOOTPRINT', L, 'x', W, 'H', HT, '+pad', PAD_T)
P['render']('plant_07_chiller', {
    '34':     ((-0.8, -1, 0.6), 1.25, 50),
    'ctrl34': ((1, -0.8, 0.4), 1.2, 50),
    'side':   ((0, -1, 0.12), 1.35, 50),
    'water':  ((-1, -0.6, 0.3), 0.35, 50, (X0, 0, 1.0)),
    'panel':  ((1, -0.3, 0.15), 0.3, 50, (X1, -0.3, 1.4)),
}, (0, 0, 1.2), L)
