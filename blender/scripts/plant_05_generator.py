"""plant_05_generator - Caterpillar 3516C diesel generator set, 2000 ekW standby, in a sound-attenuated
walk-around enclosure on a sub-base fuel tank.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python plant_05_generator.py

Dimensions (used-equipment listings, Equipt #1170400 2007 3516C: enclosure ~558 x 142 x 150 in, bare genset
287 x 102 x 120 in; Surplus Record 2015 3516C package with 7,450 gal sub-base tank: 585 x 150 x 163 in, ~90,000 lb).
Used: enclosure L 14.17 x W 3.61 m, top of enclosure 3.81 m above the pad, sub-base tank 0.95 m high, plus
roof silencers/stacks to ~5.6 m. Pad 15.0 x 4.4 x 0.15 m. Exact enclosure layouts vary per package.
Look: Wikimedia "Caterpillar (Olympian) Generator Set" - Cat yellow enclosure with hinged doors and
chrome latches on a black sub-base tank with "OLYMPIAN"/model decals, louvred radiator end.
Origin = floor centre of the pad, long axis along X, the control-panel side faces -Y, radiator at +X.
Exterior stub convention: power out conduit at z = 0.30 m (on the -X end).
"""
import bpy, math, os, sys
exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\plant_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']; P = bpy.app.driver_namespace['PLANT']

ROOT = 'Plant_Genset_Cat3516C'
BLEND = os.path.join(P['BASE'], 'plant_05_generator.blend')
GLB = os.path.join(P['BASE'], 'export', 'plant_05_generator.glb')
root, col, M, PM = P['setup'](ROOT)
mat = H['mat']
CAT = mat('PL_CatYellow', (0.90, 0.50, 0.012), 0.0, 0.42)
CAT_D = mat('PL_CatYellowDark', (0.55, 0.30, 0.01), 0.0, 0.5)
TANK = mat('PL_GensetTankBlack', (0.012, 0.012, 0.013), 0.2, 0.5)
SEAM = mat('PL_Genset_Seam', (0.03, 0.022, 0.005), 0.0, 0.8)
CHROME = mat('PL_Chrome', (0.8, 0.8, 0.82), 1.0, 0.15)
SILENCER = mat('PL_SilencerSteel', (0.18, 0.18, 0.19), 0.7, 0.55)

L, W = 14.17, 3.61
PAD_L, PAD_W, PAD_T = 15.0, 4.4, 0.15
TANK_H = 0.95
ENC_TOP = 3.81
Z0 = PAD_T
ZT = Z0 + TANK_H              # enclosure floor
ZE = Z0 + ENC_TOP             # enclosure roof
X0, X1 = -L / 2, L / 2
Y0, Y1 = -W / 2, W / 2

H['box']('GEN_Pad', (PAD_L, PAD_W, PAD_T), (0, 0, PAD_T / 2), PM['conc'], col, bevel=0.01, parent=root)
# ---------------------------------------------------------------- sub-base tank (black, ribbed, decals)
H['box']('GEN_Tank', (L, W, TANK_H), (0, 0, Z0 + TANK_H / 2), TANK, col, bevel=0.01, parent=root)
H['box']('GEN_TankLip', (L + 0.04, W + 0.04, 0.05), (0, 0, ZT - 0.025), TANK, col, parent=root)
def ribs():
    n = 14
    for i in range(1, n):
        x = X0 + i * L / n
        for y in (Y0 - 0.02, Y1 + 0.02):
            yield (x, y, Z0 + TANK_H / 2), (0.08, 0.04, TANK_H - 0.12)
    for x in (X0 - 0.02, X1 + 0.02):
        for y in (-W / 4, W / 4):
            yield (x, y, Z0 + TANK_H / 2), (0.04, 0.08, TANK_H - 0.12)
H['slat_array']('GEN_TankRibs', ribs, TANK, col, root)
H['box']('GEN_Tank_RedStripe', (L, 0.004, 0.025), (0, Y0 - 0.003, ZT - 0.10), PM['label_r'], col, parent=root)
P['text']('GEN_Tank_Model', '3516C', 0.16, PM['label_w'], col, root, (X1 - 1.4, Y0 - 0.004, Z0 + 0.72))
P['text']('GEN_Tank_Brand', 'CATERPILLAR', 0.13, PM['label_w'], col, root, (X0 + 1.6, Y0 - 0.004, Z0 + 0.72))
P['text']('GEN_Tank_Fuel', 'DIESEL FUEL  7450 GAL', 0.07, PM['label_y'], col, root, (L / 28, Y0 - 0.004, Z0 + 0.40))
# fuel fill box, vents, gauge
H['box']('GEN_FuelFillBox', (0.45, 0.20, 0.40), (-2.0, Y0 - 0.10, Z0 + 0.45), TANK, col, bevel=0.01, parent=root)
P['cylinders']('GEN_TankVents', [((x, Y0 + 0.15, ZE + 0.25), 0.04, 0.5, (0, 0, 0)) for x in (X0 + 0.3,)], M['steel'], col, root, verts=10)
P['cylinders']('GEN_FuelGauge', [((-1.2, Y0 - 0.02, Z0 + 0.60), 0.07, 0.03, (math.pi / 2, 0, 0))], CHROME, col, root, verts=20)

# ---------------------------------------------------------------- enclosure
H['box']('GEN_Enclosure', (L - 0.06, W - 0.06, ZE - ZT), (0, 0, (ZT + ZE) / 2), CAT, col, bevel=0.02, parent=root)
H['box']('GEN_RoofDrip', (L, W, 0.05), (0, 0, ZE + 0.02), CAT, col, bevel=0.01, parent=root)
# doors along both long sides, recessed seams, hinges + chrome latches (Olympian photo)
seams, hinges, latches = [], [], []
door_w, door_h = 1.05, 2.25
zd = ZT + 0.25 + door_h / 2
door_xs = [X0 + 2.4 + i * 1.25 for i in range(8)]
for side, face, ys in ((-1, '-Y', Y0 + 0.03 - 0.0008), (1, '+Y', Y1 - 0.03 + 0.0008)):
    for x in door_xs:
        for (cx, cz, w, h) in ((x, zd + door_h / 2, door_w, 0.012), (x, zd - door_h / 2, door_w, 0.012),
                               (x - door_w / 2, zd, 0.012, door_h), (x + door_w / 2, zd, 0.012, door_h)):
            seams.append(((cx, ys, cz), (w, h), 0.0))
        for dz in (-0.8, 0.0, 0.8):
            hinges.append(((x - door_w / 2 + 0.03, ys + side * 0.012, zd + dz), (0.03, 0.024, 0.10)))
        for dz in (0.55, -0.55):
            latches.append(((x + door_w / 2 - 0.07, ys + side * 0.015, zd + dz), (0.05, 0.03, 0.05)))
    # roof edge band seam
    seams.append(((0, ys, ZE - 0.25), (L - 0.1, 0.01), 0.0))
P['quads']('GEN_DoorSeams_F', [s for s in seams if s[0][1] < 0], SEAM, col, root, face='-Y')
P['quads']('GEN_DoorSeams_B', [s for s in seams if s[0][1] > 0], SEAM, col, root, face='+Y')
H['slat_array']('GEN_DoorHinges', lambda: iter(hinges), CAT_D, col, root)
H['slat_array']('GEN_DoorLatches', lambda: iter(latches), M['steel'], col, root)
# intake louvres on both long sides at the generator (-X) end, and above the doors
louv = []
for side, ys in ((-1, Y0 + 0.03 - 0.001), (1, Y1 - 0.03 + 0.001)):
    for j in range(22):
        louv.append(((X0 + 1.05, ys, ZT + 0.35 + j * 0.11), (1.4, 0.045), 0.0))
P['quads']('GEN_IntakeLouvres_F', [s for s in louv if s[0][1] < 0], PM['vent'], col, root, face='-Y')
P['quads']('GEN_IntakeLouvres_B', [s for s in louv if s[0][1] > 0], PM['vent'], col, root, face='+Y')
# radiator discharge end (+X): deep louvre hood with black core
H['box']('GEN_RadiatorCore', (0.05, W - 0.4, ZE - ZT - 0.4), (X1 - 0.04, 0, (ZT + ZE) / 2), M['fin_dark'], col, parent=root)
H['slat_array']('GEN_RadiatorLouvres', lambda: (((X1 - 0.03, 0, ZT + 0.35 + j * 0.13), (0.10, W - 0.42, 0.018)) for j in range(int((ZE - ZT - 0.6) / 0.13) + 1)), CAT, col, root)
for y in (Y0 + 0.17, Y1 - 0.17):
    H['box'](f'GEN_RadiatorFrame_{y:+.1f}', (0.12, 0.10, ZE - ZT - 0.1), (X1 - 0.03, y, (ZT + ZE) / 2), CAT, col, parent=root)
# brand on the enclosure (large CAT wordmark, both sides)
P['text']('GEN_Brand_F', 'CAT', 0.55, PM['label_k'], col, root, (X1 - 1.25, Y0 + 0.03 - 0.002, ZE - 0.75))
P['text']('GEN_Brand_B', 'CAT', 0.55, PM['label_k'], col, root, (X1 - 1.25, Y1 - 0.03 + 0.002, ZE - 0.75), face='+Y')
P['text']('GEN_Rating', '2000 ekW', 0.18, PM['label_k'], col, root, (X1 - 1.25, Y0 + 0.03 - 0.002, ZE - 1.20))

# control panel viewing window (EMCP 4) on the first door + E-stop
xcp = door_xs[0]
H['box']('GEN_CP_Window', (0.55, 0.012, 0.45), (xcp, Y0 + 0.02, zd + 0.35), PM['glass'], col, parent=root)
H['box']('GEN_CP_Panel', (0.50, 0.01, 0.40), (xcp, Y0 + 0.032, zd + 0.35), M['black_mt'], col, parent=root)
P['led']('LED_ecp_screen', (xcp - 0.08, Y0 + 0.025, zd + 0.40), (0.18, 0.003, 0.12), PM['screen'], col, root)
P['led']('LED_running', (xcp + 0.12, Y0 + 0.025, zd + 0.44), (0.035, 0.003, 0.035), PM['led_g'], col, root)
P['led']('LED_alarm', (xcp + 0.12, Y0 + 0.025, zd + 0.38), (0.035, 0.003, 0.035), PM['led_r'], col, root)
P['led']('LED_warning', (xcp + 0.12, Y0 + 0.025, zd + 0.32), (0.035, 0.003, 0.035), PM['led_a'], col, root)
H['box']('GEN_EStop_Box', (0.14, 0.08, 0.14), (X0 + 1.1, Y0 - 0.01, ZT + 0.0 + 2.75), PM['label_y'], col, bevel=0.005, parent=root)
P['cylinders']('GEN_EStop_Button', [((X0 + 1.1, Y0 - 0.06, ZT + 2.75), 0.045, 0.03, (math.pi / 2, 0, 0))], PM['label_r'], col, root, verts=16)

# ---------------------------------------------------------------- roof: twin critical silencers + stacks
stacks = []
for k, y in enumerate((-0.75, 0.75)):
    P['cylinders'](f'GEN_Silencer_{k}', [((-0.4, y, ZE + 0.55), 0.38, 3.4, (0, math.pi / 2, 0))], SILENCER, col, root, verts=28)
    P['cylinders'](f'GEN_SilencerBands_{k}', [((x, y, ZE + 0.55), 0.395, 0.06, (0, math.pi / 2, 0)) for x in (-2.0, -0.4, 1.2)], M['black_st'], col, root, verts=28)
    H['slat_array'](f'GEN_SilencerSaddles_{k}', lambda y=y: (((x, y, ZE + 0.10), (0.12, 0.6, 0.18)) for x in (-1.6, 0.8)), CAT_D, col, root)
    # elbow up to the stack
    P['flow_path'](f'GEN_ExhaustStack_{k}', [(1.3, y, ZE + 0.55), (1.9, y, ZE + 0.55), (1.9, y, ZE + 1.85)], SILENCER, col, root, radius=0.17, verts=20, bend=0.35, kind='exhaust')
    P['cylinders'](f'GEN_RainCap_{k}', [((1.9, y - 0.04, ZE + 1.88), 0.19, 0.012, (math.radians(-12), 0, 0))], M['black_st'], col, root, verts=20)
    P['marker'](f'FX_exhaust_{k}', (1.9, y, ZE + 1.9), root, col, size=0.3)
    stacks.append(y)
# roof lifting eyes
H['slat_array']('GEN_LiftEyes', lambda: (((x, y, ZE + 0.08), (0.06, 0.16, 0.12)) for x in (X0 + 0.4, X1 - 0.4) for y in (Y0 + 0.3, Y1 - 0.3)), CAT_D, col, root)

# ---------------------------------------------------------------- power out (conduit stub on -X end, z=0.30)
ZP = P['EXT_POWER_Z']
yo = -0.6
H['box']('GEN_StubUpBox', (0.04, 0.80, 0.30), (X0 - 0.02, yo, ZP), M['black_mt'], col, parent=root)
for k, dy in enumerate((-0.24, -0.08, 0.08, 0.24)):
    P['flow_path'](f'FLOW_power_out_{k}', [(X0, yo + dy, ZP), (X0 - 0.70, yo + dy, ZP)], PM['cable'], col, root, radius=0.04, verts=12, kind='power')
P['socket']('SOCKET_power_out', (X0 - 0.70, yo, ZP), (-1, 0, 0), root, col)
P['socket']('SOCKET_fuel_fill', (-2.0, Y0 - 0.21, Z0 + 0.45), (0, -1, 0), root, col)

tris = P['finish'](root, BLEND, GLB)
print('FOOTPRINT pad', PAD_L, 'x', PAD_W, ' enclosure', L, W, ENC_TOP)
P['render']('plant_05_generator', {
    '34':     ((-0.7, -1, 0.45), 1.35, 50),
    'front':  ((0, -1, 0.1), 1.5, 50),
    'rad34':  ((1, -0.7, 0.35), 1.35, 50),
    'rear34': ((0.6, 1, 0.6), 1.35, 50),
    'panel':  ((0.15, -1, 0.15), 0.25, 50, (X0 + 2.4, -1.8, 2.4)),
}, (0, 0, 2.0), 15.0)
