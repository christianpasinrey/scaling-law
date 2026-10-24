"""plant_06_dry_cooler - V-shape dry cooler (Guentner GFD V-shape VARIO class), 2 x 6 EC fans, yard/roof unit.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python plant_06_dry_cooler.py

Reference: Guentner V-shape VARIO dry cooler pages (up to 2x12 fans, 75-2,600 kW, width designed around
lorry transport) and a used GFD090.1D/2x3 listing (2 x 3 fans, 900 mm diameter, 410 kW, 2,200 kg);
Wikimedia "Dry cooler LU-VE" photo (white V-shaped casing, inclined dark finned coils, fans on top, legs).
Used (approximate - Guentner does not publish outline dims on the web pages): 2 x 6 fans of 910 mm,
L 7.80 x W 2.26 x H 2.55 m incl. legs; ~1 MW class at data-centre conditions.
Fans are separate objects FAN_01..FAN_12 (origin at hub, spin about local Z).
Origin = floor centre of the pad (ground z=0), long axis X, header/connection end at -X.
Exterior stub convention: coolant pipe stubs at z = 1.00 m.
"""
import bpy, math, os, sys
exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\plant_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']; P = bpy.app.driver_namespace['PLANT']

ROOT = 'Plant_DryCooler_VShape'
BLEND = os.path.join(P['BASE'], 'plant_06_dry_cooler.blend')
GLB = os.path.join(P['BASE'], 'export', 'plant_06_dry_cooler.glb')
root, col, M, PM = P['setup'](ROOT)
mat = H['mat']
CASE = mat('PL_DC_CasingWhite', (0.78, 0.79, 0.79), 0.1, 0.45)
COIL = mat('PL_DC_CoilFins', (0.10, 0.11, 0.115), 0.7, 0.45)
FINL = mat('PL_DC_FinLines', (0.32, 0.33, 0.34), 0.9, 0.4)
GUARD = mat('PL_DC_Guard', (0.05, 0.05, 0.055), 0.5, 0.45)

L, W, HT = 7.80, 2.26, 2.55
PAD_T = 0.12
Z0 = PAD_T
ZB = Z0 + 0.60              # bottom of the V (frame on legs)
ZT = Z0 + 2.25              # top deck
YB = 0.28                   # half-width at the bottom of the V
YT = W / 2 - 0.03           # half-width at the top
X0, X1 = -L / 2, L / 2
NF = 6
pitch = (L - 0.30) / NF

H['box']('DC_Pad', (L + 0.4, W + 0.4, PAD_T), (0, 0, PAD_T / 2), PM['conc'], col, bevel=0.01, parent=root)
# ---------------------------------------------------------------- end walls + partitions (trapezoids in YZ)
trap = [(-YB - 0.04, ZB - 0.05), (YB + 0.04, ZB - 0.05), (YT, ZT), (-YT, ZT)]
H['prism']('DC_EndWall_A', trap, 'yz', X0, 0.04, CASE, col, parent=root)
H['prism']('DC_EndWall_B', trap, 'yz', X1 - 0.04, 0.04, CASE, col, parent=root)
for i in range(1, NF):
    H['prism'](f'DC_Partition_{i}', [(a * 0.98, b) for a, b in trap], 'yz', X0 + 0.15 + i * pitch - 0.01, 0.02, CASE, col, parent=root)
# bottom drip tray / base channel of the V
H['box']('DC_BaseChannel', (L, 2 * YB + 0.08, 0.12), (0, 0, ZB - 0.06), CASE, col, parent=root)
# top deck with a raised edge
H['box']('DC_TopDeck', (L, W - 0.02, 0.04), (0, 0, ZT + 0.02), CASE, col, parent=root)
H['slat_array']('DC_TopEdge', lambda: iter([((0, s * (W / 2 - 0.02), ZT + 0.09), (L, 0.04, 0.14)) for s in (-1, 1)] +
                                          [((s * (L / 2 - 0.02), 0, ZT + 0.09), (0.04, W, 0.14)) for s in (-1, 1)]), CASE, col, root)

# ---------------------------------------------------------------- inclined coils (dark finned slabs) + fin lines
dy, dz = YT - YB, ZT - ZB
slope = math.atan2(dz, dy)
clen = math.hypot(dy, dz)
for s in (-1, 1):
    yc, zc = s * (YB + dy / 2), ZB + dz / 2
    rot = (s * (math.pi / 2 - slope) * -1, 0, 0)
    P['boxes'](f'DC_Coil_{"L" if s < 0 else "R"}', [((0, yc, zc), (L - 0.10, 0.12, clen), (-s * (math.pi / 2 - slope), 0, 0))], COIL, col, root)
    # fin lines on the outer face (along the slope), merged
    off = 0.062
    ny, nz = s * math.sin(slope), -math.cos(slope)
    def fins(s=s, yc=yc, zc=zc, ny=ny, nz=nz):
        n = int((L - 0.2) / 0.045)
        for i in range(n):
            x = X0 + 0.1 + i * (L - 0.2) / n
            yield (x, yc + ny * off, zc + nz * off), (0.006, 0.004, clen - 0.05), (-s * (math.pi / 2 - slope), 0, 0)
    P['boxes'](f'DC_CoilFins_{"L" if s < 0 else "R"}', fins(), FINL, col, root)
    # coil frame rails top and bottom (galvanised)
    H['slat_array'](f'DC_CoilRails_{"L" if s < 0 else "R"}', lambda s=s: iter([((0, s * (YB + 0.02), ZB + 0.03), (L, 0.06, 0.06)), ((0, s * (YT - 0.03), ZT - 0.03), (L, 0.06, 0.06))]), PM['galv'], col, root)

# ---------------------------------------------------------------- legs and cross bracing
legs = []
for x in (X0 + 0.15, X0 + 0.15 + 2 * pitch, X0 + 0.15 + 4 * pitch, X1 - 0.15):
    for s in (-1, 1):
        legs.append(((x, s * (YB + 0.25), Z0 + (ZB + 0.45 - Z0) / 2), (0.08, 0.08, ZB + 0.45 - Z0)))
        legs.append(((x, s * (YB + 0.25), Z0 + 0.01), (0.20, 0.20, 0.02)))      # foot plates
    legs.append(((x, 0, Z0 + 0.25), (0.06, 2 * YB + 0.5, 0.06)))
H['slat_array']('DC_Legs', lambda: iter(legs), PM['galv'], col, root)

# ---------------------------------------------------------------- fans: shroud rings, guards, rotors
FD = 0.91
fan_pos = [(X0 + 0.15 + (i + 0.5) * pitch, s * 0.56) for i in range(NF) for s in (-1, 1)]
P['cylinders']('DC_FanOpenings', [((x, y, ZT + 0.045), FD / 2 + 0.01, 0.01, (0, 0, 0)) for x, y in fan_pos], PM['vent'], col, root, verts=32)
shrouds = []
for x, y in fan_pos:
    shrouds.append(((x, y, ZT + 0.12), FD / 2 + 0.02, 0.02, (0, 0, 0)))
P['tori']('DC_FanShrouds', [((x, y, ZT + 0.08 + k * 0.05), FD / 2 + 0.025, 0.025, (0, 0, 0)) for x, y in fan_pos for k in range(3)], CASE, col, root, major_segs=32, minor_segs=4)
guards = []
for x, y in fan_pos:
    for r in (0.12, 0.22, 0.32, 0.42):
        guards.append(((x, y, ZT + 0.215), r, 0.004, (0, 0, 0)))
P['tori']('DC_FanGuards', guards, GUARD, col, root, major_segs=28, minor_segs=3)
def spokes():
    for x, y in fan_pos:
        for a in range(4):
            ang = a * math.pi / 4
            yield (x, y, ZT + 0.215), (FD - 0.04, 0.006, 0.006), (0, 0, ang)
P['boxes']('DC_FanGuardSpokes', spokes(), GUARD, col, root)
fans = []
for i, (x, y) in enumerate(fan_pos):
    fans.append(P['fan'](f'FAN_{i + 1:02d}', (x, y, ZT + 0.15), FD, col, root, PM, blades=5))
P['cylinders']('DC_FanMotors', [((x, y, ZT + 0.10), 0.13, 0.12, (0, 0, 0)) for x, y in fan_pos], M['black_mt'], col, root, verts=20)

# ---------------------------------------------------------------- headers + coolant connections at -X (z=1.00)
ZC = P['EXT_COOLANT_Z']
hdr = []
for s in (-1, 1):
    # header manifold along each coil's -X edge, following the coil slope
    hdr.append(((X0 - 0.07, s * (YB + YT) / 2 - s * 0.03, (ZB + ZT) / 2 + 0.03), 0.07, clen - 0.25, (-s * (math.pi / 2 - slope), 0, 0)))
P['cylinders']('DC_Headers', hdr, M['steel'], col, root, verts=16)
# inlet (hot water from the CDUs / chiller condenser loop) on +Y side, outlet on -Y side
y_in, y_out = 0.55, -0.55
P['flow_path']('FLOW_coolant_in', [(X0 - 0.90, y_in, ZC), (X0 - 0.12, y_in, ZC), (X0 - 0.12, y_in, ZB + 0.62)], PM['pipe_red'], col, root, radius=0.084, verts=18, bend=0.2, kind='coolant')
P['flow_path']('FLOW_coolant_out', [(X0 - 0.12, y_out, ZB + 0.62), (X0 - 0.12, y_out, ZC), (X0 - 0.90, y_out, ZC)], PM['pipe_blue'], col, root, radius=0.084, verts=18, bend=0.2, kind='coolant')
P['cylinders']('DC_PipeFlanges', [((X0 - 0.80, y, ZC), 0.11, 0.025, (0, math.pi / 2, 0)) for y in (y_in, y_out)], M['steel'], col, root, verts=20)
P['socket']('SOCKET_coolant_in', (X0 - 0.90, y_in, ZC), (-1, 0, 0), root, col)
P['socket']('SOCKET_coolant_out', (X0 - 0.90, y_out, ZC), (-1, 0, 0), root, col)
# pipe supports
H['slat_array']('DC_PipeSupports', lambda: iter([((X0 - 0.5, y, (Z0 + ZC - 0.09) / 2), (0.06, 0.06, ZC - 0.09 - Z0)) for y in (y_in, y_out)]), PM['galv'], col, root)
# EC fan control box + power (on the -X end wall)
H['box']('DC_ControlBox', (0.20, 0.60, 0.50), (X0 - 0.10, 0, ZB + 0.55), CASE, col, bevel=0.01, parent=root)
P['led']('LED_status', (X0 - 0.202, 0, ZB + 0.70), (0.004, 0.08, 0.025), PM['led_g'], col, root)
P['flow_path']('FLOW_power_in', [(X0 - 0.90, 0, P['EXT_POWER_Z']), (X0 - 0.25, 0, P['EXT_POWER_Z']), (X0 - 0.25, 0, ZB + 0.35), (X0 - 0.15, 0, ZB + 0.35)],
               PM['cable'], col, root, radius=0.025, verts=10, bend=0.1, kind='power')
P['socket']('SOCKET_power_in', (X0 - 0.90, 0, P['EXT_POWER_Z']), (-1, 0, 0), root, col)
# branding on both end walls (trapezoid face)
P['text']('DC_Brand_A', 'Güntner', 0.16, mat('PL_GuentnerBlue', (0.02, 0.15, 0.45), 0.0, 0.5), col, root, (X0 - 0.002, 0, ZT - 0.35), face='-X')
P['text']('DC_Brand_B', 'Güntner', 0.16, bpy.data.materials['PL_GuentnerBlue'], col, root, (X1 + 0.002, 0, ZT - 0.35), face='+X')

tris = P['finish'](root, BLEND, GLB)
print('FOOTPRINT', L, 'x', W, 'H', HT + PAD_T, 'pad', L + 0.4, W + 0.4)
P['render']('plant_06_dry_cooler', {
    '34':     ((-0.8, -1, 0.6), 1.3, 50),
    'end':    ((-1, -0.35, 0.25), 1.5, 50),
    'side':   ((0, -1, 0.15), 1.4, 50),
    'top':    ((0.3, -0.5, 1), 1.1, 50),
    'fans':   ((0.2, -0.6, 0.7), 0.35, 50, (X0 + 1.5, 0, ZT)),
}, (0, 0, 1.3), L)
