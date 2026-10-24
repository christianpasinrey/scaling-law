"""NVIDIA DGX-1 with 8x Tesla V100 SXM2 (2017) - 3U rack server.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python <this file>

Convention (rack-mount): metres, Z up, front plane y=0 facing -Y, depth +Y, origin bottom-front-centre.
19" EIA rack: ears 482.6 mm, body 444 mm (17.5"), height 131 mm (5.16"), depth 866 mm (34.1") - DGX-1 user guide.
Layout (front->rear): magnetic bezel | drive cage | 4 top-loading fan modules | air baffle |
GPU tray (slides out the rear, upper) over the motherboard tray (slides out the rear, lower) |
4x 1600 W PSUs stacked at the rear right (3+1).
GPU tray: 8 SXM2 on the NVLink hybrid cube-mesh baseboard, 2 columns x 4, module long axis front-to-back
(ISC 2016 DGX-1 photos + DGX-1 user guide GPU-tray photo). Exported GLB has no GPUs: SLOT_gpu_0..7 mark the
phase-1 module pose (module PCB top at the slot, heatsink +Z).
"""
import bpy, math, mathutils
exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\sxm_lib.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\srv_dgx_lib.py', encoding='utf-8').read())

ROOT = 'DGX1_V100'
FILE = 'srv_02_dgx1_v100'
BL = r'C:\laragon\www\scaling-law\blender'
W2, HT, D = 222.0, 131.0, 866.0          # half body width, height, depth (mm)
EAR = 241.3                              # half ear width (482.6 / 2)
LID_Z = HT - 1.2

root, col = H['new_card_scene'](ROOT)
root['standard'] = '19in EIA rack, 3U (spec height 131 mm)'
root['model'] = 'NVIDIA DGX-1 (Tesla V100 SXM2)'
M = H['base_materials']()
mat = H['mat']

# ---------------------------------------------------------------- materials
st_col, st_nrm = stipple_images('DGX1_Stipple', (0.58, 0.52, 0.41), G=150, strength=0.5, contrast=0.16)
M_bezel = mat_tex('DGX1_BezelStipple', st_col, st_nrm, metal=1.0, rough=0.42, nstr=0.6)
M_champ = mat('DGX1_Champagne', (0.56, 0.50, 0.39), 1.0, 0.30)
M_pill = mat('DGX1_PillPolished', (0.62, 0.62, 0.63), 1.0, 0.32)
M_nvgreen = mat('NV_Green', (0.18, 0.48, 0.0), 0.0, 0.45)
M_white = mat('DGX_LogoWhite', (0.85, 0.85, 0.85), 0.2, 0.35)
M_steel = mat('DGX_SteelGalv', (0.42, 0.43, 0.45), 1.0, 0.45)
M_steel_dk = mat('DGX_SteelDark', (0.20, 0.21, 0.22), 0.8, 0.45)
M_black = M['plastic']
M_pcb = mat('DGX_PCBGreen', (0.015, 0.09, 0.035), 0.0, 0.45)
M_alu = M['alu']
M_blue = mat('DGX_ClaspBlue', (0.02, 0.18, 0.65), 0.0, 0.4)
M_cu = mat('DGX_Copper', (0.92, 0.50, 0.30), 1.0, 0.3)
M_cable = mat('DGX_CableBlack', (0.012, 0.012, 0.013), 0.0, 0.55)
M_port = M['port']
M_gold = M['gold']
perf_img = hex_perf_image('DGX_HexPerf', (0.55, 0.56, 0.58), hole=0.78)
M_perf = mat_perf('DGX_PerfSteel', perf_img)
perf_dk = hex_perf_image('DGX_HexPerfDark', (0.04, 0.04, 0.045), hole=0.80)
M_perf_dk = mat_perf('DGX_PerfBlack', perf_dk, metal=0.3)
M_led_g = mat('LED_Green', (0.1, 1.0, 0.2), 0.0, 0.3, emit=(0.1, 1.0, 0.2), emit_str=6.0)
M_led_b = mat('LED_Blue', (0.1, 0.3, 1.0), 0.0, 0.3, emit=(0.1, 0.3, 1.0), emit_str=6.0)
M_led_a = mat('LED_Amber', (1.0, 0.45, 0.05), 0.0, 0.3, emit=(1.0, 0.45, 0.05), emit_str=4.0)

PERF = 6.0   # perforation pitch (mm)


# rear-panel features were measured on rear views, where the viewer's right is -X: mirror them
def bxr(n, x0, x1, *a, **k): return bx(n, -x1, -x0, *a, **k)
def cyr(n, r, d, c, *a, **k): return cy(n, r, d, (-c[0], c[1], c[2]), *a, **k)
def sar(n, specs, *a): return sa(n, [((-c[0], c[1], c[2]), sz) for c, sz in specs], *a)
def emptyr(n, loc, *a, **k): return empty(n, (-loc[0], loc[1], loc[2]), *a, **k)
def flowr(n, pts, *a, **k): return flow_path(n, [(-q[0], q[1], q[2]) for q in pts], *a, **k)



def perf_uv(o, axes='xz'):
    return uv_planar(o, axes, PERF * MM, PERF * MM * math.sqrt(3))


# ================================================================ CHASSIS (fixed shell)
bx('Floor', -W2, W2, 0, D, 0, 1.2, M_steel, 'chassis')
for s in (-1, 1):
    bx('Side', s * W2 - (1.2 if s > 0 else 0), s * W2 + (0 if s > 0 else 1.2), 0, D, 0, LID_Z, M_steel, 'chassis')
    # rack flange (ear plate) at the front-rail plane
    x0, x1 = sorted((s * W2, s * EAR))
    bx('EarFlange', x0, x1, 0, 3.0, 0, HT, M_steel, 'chassis')
    # champagne front post (holds the magnetic bezel)
    x0, x1 = sorted((s * 225.0, s * EAR))
    bx('EarPost', x0, x1, -22.0, 0.0, 0, HT, M_champ, 'chassis', bevel=1.5)
    bx('EarPostGroove', x0 + 5.5, x1 - 5.5, -22.4, -21.0, 18.0, HT - 18.0, M_steel_dk, 'chassis')
    cy('Thumbscrew', 4.6, 5.0, (s * 233.2, -24.0, 9.0), 'y', M_champ, 'chassis', verts=20)
    cy('ThumbscrewSlot', 0.6, 0.6, (s * 233.2, -26.6, 9.0), 'y', M_steel_dk, 'chassis', verts=8)
# front power / ID buttons on the right post (user guide: power top, ID below)
cy('PowerButton', 3.2, 2.5, (233.2, -23.0, 120.0), 'y', M_steel_dk, 'chassis', verts=20)
cy('IDButton', 3.2, 2.5, (233.2, -23.0, 106.0), 'y', M_steel_dk, 'chassis', verts=20)
# perforated front bulkhead behind the bezel
perf_uv(bx('FrontPerf', -W2 + 1.2, W2 - 1.2, 2.0, 3.0, 1.2, LID_Z, M_perf, 'chassis'))
# front drive cage (SSDs) under its silver cover
bx('DriveCage', -205, 205, 12, 150, 8, 122, M_steel, 'chassis')
sa('DriveCageRibs', [((x, 81, 122.4), (3, 130, 0.8)) for x in range(-180, 200, 60)], M_steel_dk, 'chassis')
sa('DriveSleds', [((-150 + 100 * i, 13.0, 30.0), (88, 2, 18)) for i in range(4)], M_black, 'chassis')
# fan cage rails + air baffle
bx('FanCageFront', -W2 + 1.2, W2 - 1.2, 208, 211, 1.2, 8, M_steel_dk, 'chassis')
bx('FanCageRear', -W2 + 1.2, W2 - 1.2, 304, 307, 1.2, 8, M_steel_dk, 'chassis')
bx('BaffleTop', -W2 + 1.2, W2 - 1.2, 307, 328, LID_Z - 6, LID_Z, M_black, 'chassis')
sa('BaffleFins', [((x, 317, 66), (2.0, 20, 112)) for x in (-110, 0, 110)], M_black, 'chassis')
# PSU cage separator (PSUs stacked at the rear right, 1600 W each, 3+1)
bxr('PSUCageWall', 180.0, 182.0, 760, D, 1.2, LID_Z, M_steel, 'chassis')
bxr('PSUCageBack', 182.0, W2 - 1.2, 758, 760, 1.2, LID_Z, M_steel_dk, 'chassis')
chassis = join('chassis', 'Chassis', root)

# lid (separate so the game can hide it), with the front flip-up access seam and latch windows
bx('Lid', -W2, W2, 0, D, LID_Z, HT, M_steel, 'lid')
bx('LidSeam', -W2, W2, 198.5, 200.0, HT, HT + 0.05, M_steel_dk, 'lid')
sa('LidLatches', [((sx * 150, 188, HT + 0.05), (14, 9, 0.12)) for sx in (-1, 1)], M_black, 'lid')
lid = join('lid', 'Chassis_Lid', root)

# ================================================================ BEZEL (separate, magnetic)
bz = bx('BezelPlate', -224.0, 224.0, -20.0, -2.0, 3.0, 128.0, M_bezel, 'bezel', bevel=2.5)
PILL_X, PILL_W, PILL_Z, PILL_H, PILL_R = 185.0, 64.0, 64.0, 98.0, 24.0
for s in (-1, 1):
    cut = pr('PillCut', rrect(s * PILL_X, PILL_Z, PILL_W, PILL_H, PILL_R), 'xz', -26.0, 18.0, M_bezel, None)
    H['cut'](bz, cut)
uv_planar(bz, 'xz', 0.16, 0.16)
for s in (-1, 1):
    pr('PillFloor', rrect(s * PILL_X, PILL_Z, PILL_W, PILL_H, PILL_R), 'xz', -8.3, 0.4, M_pill, 'bezel')
    pr('PillLip', rrect(s * PILL_X, PILL_Z, PILL_W + 1.2, PILL_H + 1.2, PILL_R + 0.6), 'xz', -8.05, 0.1, M_steel_dk, 'bezel')
# left pill: green NVIDIA eye on top, white NVIDIA wordmark reading downward (NVIDIA DGX-1 product photo)
front_logo('BezelLogo', 17.0, (-PILL_X, -8.4, 95.0), M_nvgreen, M_pill, 'bezel', vertical=True)
front_text('BezelWordmark', 'NVIDIA', 12.5, (-PILL_X, -8.6, 52.0), M_white, 'bezel', vertical=True,
           font=r'C:\Windows\Fonts\ariblk.ttf', extrude=0.25, scale=(1.0, 1.0, 1.0))
bezel = join('bezel', 'Bezel', root)
bezel['removable'] = True
bezel['note'] = 'magnetic front bezel; remove to reach drive cage'

# ================================================================ FAN MODULES (4, top-loading)
FAN_X = (-165.0, -55.0, 55.0, 165.0)
fans = []
for i, fx in enumerate(FAN_X):
    n = 32
    outer = []
    inner = []
    for k in range(n):
        a = 2 * math.pi * k / n + math.pi / 4
        c, s_ = math.cos(a), math.sin(a)
        f = 1.0 / max(abs(c), abs(s_))
        outer.append(((fx + 51.0 * c * f) * MM, (64.0 + 60.0 * s_ * f) * MM))
        inner.append(((fx + 45.0 * c) * MM, (64.0 + 45.0 * s_) * MM))
    o = H['ring'](f'FanHousing{i}', outer, inner, 'xz', 214.0 * MM, 86.0 * MM, M_black, _scratch())
    GROUPS.setdefault(f'fan{i}', []).append(o)
    bx('FanStrutH', fx - 45, fx + 45, 296, 299, 62.5, 65.5, M_black, f'fan{i}')
    bx('FanStrutV', fx - 1.5, fx + 1.5, 296, 299, 19, 109, M_black, f'fan{i}')
    cy('FanMotor', 17.0, 10.0, (fx, 293.0, 64.0), 'y', M_black, f'fan{i}')
    bx('FanTopTab', fx - 30, fx + 30, 240, 275, 124, 126.5, M_steel_dk, f'fan{i}')
    sa('FanReleaseTabs', [((fx + sx * 47.5, 257, 122), (4, 22, 8)) for sx in (-1, 1)], M_blue, f'fan{i}')
    fo = join(f'fan{i}', f'FAN_{i}', root)
    fo['hot_swap'] = 'lift up (top access)'
    rot = fan_rotor(f'FAN_rotor_{i}', 43.0, 17.0, 24.0, 7, (fx, 252.0, 64.0), M_black, col)
    reparent(rot, fo); rot['spin_axis'] = 'Y'
    led = cy(f'LED_fan_{i}', 1.6, 0.8, (fx + 22, 258.0, 126.8), 'z', M_led_g, None, verts=12)
    reparent(led, fo)
    fans.append(fo)

# ================================================================ GPU TRAY (upper, slides out the rear)
tray_g = emptyr('TRAY_gpu', (-20.0, D, 28.0), root, col, kind='PLAIN_AXES', size=0.05,
               props={'slide_axis': '+Y', 'slide_travel_m': 0.53, 'access': 'rear', 'note': 'GPU tray: 8x SXM2 baseboard + 4x IB'})
G = 'gtray'
BB_Z = 32.3                                # baseboard top
MOD_Z = BB_Z + 6.6                         # SXM2 module PCB top (mezzanine stack height, phase-1 module)
bxr('PanFront', -220, 178, 330, 762, 28.0, 29.5, M_steel, G)
bxr('PanStep', -220, 178, 760, 762, 29.5, 46.0, M_steel, G)
bxr('PanRear', -220, 178, 762, 866, 44.5, 46.0, M_steel, G)
for x0 in (-220.0, 176.5):
    bxr('TrayRail', x0, x0 + 1.5, 330, 866, 29.5, 60.0, M_steel, G)
bxr('TrayFrontLip', -220, 178, 330, 332, 29.5, 50.0, M_steel, G)
# NVLink hybrid cube-mesh baseboard
bxr('Baseboard', -218, 176, 334, 759, 30.5, BB_Z, M_pcb, G)
GPU_X = (-176.0, -44.0, 44.0, 176.0)
GPU_Y = (475.0, 680.0)
sar('SXM2_SocketFrames', [((x, y, BB_Z + 0.3), (82, 1.5, 0.6)) for x in GPU_X for y in GPU_Y for y in (y - 72, y + 72)] +
   [((x + sx * 40.5, y, BB_Z + 0.3), (1.5, 146, 0.6)) for x in GPU_X for y in GPU_Y for sx in (-1, 1)], M_steel_dk, G)
sar('SXM2_Mezz', [((x + dx, y + dy, BB_Z + 1.0), (56, 18, 2.0)) for x in GPU_X for y in GPU_Y for dx in (0,) for dy in (-33, 33)], M_black, G)
# NVLink cube-mesh traces between sockets (silkscreened copper bands between the two columns)
sar('NVLink_Traces', [((x, 577.5, BB_Z + 0.05), (60, 38, 0.1)) for x in GPU_X] +
   [((0, y, BB_Z + 0.05), (70, 50, 0.1)) for y in GPU_Y], mat('DGX_PCBTrace', (0.03, 0.16, 0.06), 0.3, 0.35), G)
# 4x PCIe switch heatsinks at the front edge of the baseboard (user-guide GPU-tray photo)
for k, x in enumerate((-170.0, -60.0, 50.0, 140.0)):
    bxr('PLX_Base', x - 22, x + 22, 338, 384, BB_Z, BB_Z + 3, M_alu, G)
    sar('PLX_Fins', [((x - 20 + 3.0 * j, 361, BB_Z + 16), (1.0, 46, 26)) for j in range(14)], M_alu, G)
sar('BB_Caps', [((x, y, BB_Z + 3.5), (6, 6, 7)) for x in (-110, 110) for y in (420, 540, 620, 740)], M_alu, G)
# rear IB riser board + 4x ConnectX-4 EDR low-profile cards (standing, brackets at the rear)
bxr('RiserBoard', -218, 176, 764, 862, 46.0, 47.6, M_pcb, G)
IB_X = (-122.0, -102.0, 100.0, 120.0)
for k, x in enumerate(IB_X):
    bxr('IB_PCB', x - 0.8, x + 0.8, 696, 860, 50, 118, M_pcb, G)
    bxr('IB_Heatsink', x + 0.8, x + 9.0, 740, 800, 62, 108, M_steel_dk, G)
    bxr('IB_Slot', x - 4, x + 4, 760, 856, 47.6, 58, M_black, G)
    bxr('IB_Bracket', x - 9, x + 9, 862, 864.5, 48, 127, M_steel, G)
    bxr('IB_QSFP', x - 7, x + 7, 864.5, 869, 92, 104, M_steel, G)
    bxr('IB_QSFP_Port', x - 5.5, x + 5.5, 868.9, 869.2, 93.5, 102.5, M_port, G)
# rear faceplate: perforated sheet with dark exhaust discs behind, solid frame + IB bracket strips
pf = bxr('RearPerf', -219, 176, 864, 865.2, 47.0, 128.0, M_perf, G)
perf_uv(pf)
for x, r in ((-176.0, 38.0), (-47.0, 38.0), (40.0, 38.0), (152.0, 22.0)):
    cyr('ExhaustShadow', r, 1.0, (x, 856.0, 87.5), 'y', M_black, G, verts=28)
sar('RearFrame', [((-21.5, 865.5, 46.8), (397, 1.6, 1.6)), ((-21.5, 865.5, 128.6), (397, 1.6, 1.6)),
                 ((-219.2, 865.5, 87.5), (1.6, 1.6, 83)), ((176.8, 865.5, 87.5), (1.6, 1.6, 83))], M_steel, G)
# locking levers (upper set) + blue retention clasps
for x in (-205.0, 160.0):
    bxr('Lever', x - 8, x + 8, 866, 871, 50, 60, M_steel_dk, G, bevel=0.8)
    bxr('Clasp', x - 4, x + 4, 869, 873, 60, 66, M_blue, G, bevel=0.8)
# baseboard power connectors (behind the rear GPU column)
bxr('BB_PowerConn_A', 140, 172, 752, 759, BB_Z, BB_Z + 10, M_black, G)
bxr('BB_PowerConn_B', -214, -182, 752, 759, BB_Z, BB_Z + 10, M_black, G)
gtray = join(G, 'GPU_Tray', tray_g)
# SXM2 module slots: module long axis front-to-back, wordmark reading toward the front (ISC 2016 photos);
# Rz(-90): module +X -> chassis -Y, module +Y -> chassis +X. 0-3 front column (-X..+X), 4-7 rear column.
for j, y in enumerate(GPU_Y):
    for i, x in enumerate(GPU_X):
        empty(f'SLOT_gpu_{j * 4 + i}', (x, y, MOD_Z), tray_g, col, rot=(0, 0, -math.pi / 2), size=0.06,
              props={'module': 'V100_SXM2', 'glb': 'gpu_v100_sxm2.glb'})

# ================================================================ MOTHERBOARD TRAY (lower, slides out the rear)
tray_m = emptyr('TRAY_mb', (-20.0, D, 1.5), root, col, kind='PLAIN_AXES', size=0.05,
               props={'slide_axis': '+Y', 'slide_travel_m': 0.53, 'access': 'rear', 'note': 'motherboard tray: 2x Xeon E5-2698 v4, 16 DIMMs'})
G = 'mtray'
bxr('MBPan', -220, 178, 330, 866, 1.5, 3.0, M_steel, G)
for x0 in (-220.0, 176.5):
    bxr('MBRail', x0, x0 + 1.5, 330, 866, 3.0, 26.0, M_steel, G)
bxr('MBBoard', -216, 175, 336, 862, 3.0, 4.6, M_pcb, G)
CPU_Y = (470.0, 650.0)
for k, yc in enumerate(CPU_Y):
    bxr('CPU_Socket', -30, 30, yc - 38, yc + 38, 4.6, 7.0, M_steel_dk, G)
    bxr('CPU_HSBase', -45, 45, yc - 45, yc + 45, 7.0, 10.0, M_cu, G)
    sar('CPU_HSFins', [((0, yc - 44 + 2.4 * j, 18.0), (88, 0.6, 16)) for j in range(37)], M_alu, G)
    sar('DIMMs', [((sx * (58 + 8 * d), yc, 14.0), (1.3, 133, 18.8)) for sx in (-1, 1) for d in range(4)], M_pcb, G)
    sar('DIMM_Chips', [((sx * (58 + 8 * d) + 0.9, yc + 14 * (c - 4), 15.0), (0.6, 10, 9)) for sx in (-1, 1) for d in range(4) for c in range(9)], M_black, G)
    sar('DIMM_Slots', [((sx * (58 + 8 * d), yc, 6.0), (6, 145, 3)) for sx in (-1, 1) for d in range(4)], M_black, G)
bxr('PCH_HS', -150, -110, 560, 600, 4.6, 14, M_alu, G)
bxr('MB_PowerConn', 140, 160, 790, 812, 4.6, 16, M_black, G)
# rear I/O (user guide rear view: USB x2, VGA, RS-232, IPMI RJ45, 2x 10GbE RJ45, power button + LEDs)
bxr('MBRearPlate', -219, 177, 863, 866, 3.0, 44.0, M_steel, G)
pp = bxr('MBRearPerf', -110, -10, 865.9, 866.4, 8.0, 40.0, M_perf, G); perf_uv(pp)
bxr('MBRearSlotCover', -205, -125, 865.9, 866.6, 12.0, 34.0, M_steel_dk, G)
ports = [('USB', 18.0, 12.0, 14.0, 6.0), ('USB', 18.0, 22.0, 14.0, 6.0), ('VGA', 48.0, 17.0, 31.0, 12.5),
         ('Serial', 80.0, 17.0, 25.0, 12.5), ('RJ45_IPMI', 108.0, 17.0, 16.0, 14.0), ('RJ45_LAN0', 128.0, 17.0, 16.0, 14.0),
         ('RJ45_LAN1', 146.0, 17.0, 16.0, 14.0)]
for nm, x, z, w, h in ports:
    bxr(f'Port_{nm}_Shell', x - w / 2, x + w / 2, 860, 867.0, z - h / 2, z + h / 2, M_steel if 'RJ45' not in nm else M_black, G)
    bxr(f'Port_{nm}_Hole', x - w / 2 + 1.5, x + w / 2 - 1.5, 866.9, 867.2, z - h / 2 + 1.5, z + h / 2 - 1.5, M_port, G)
cyr('RearPowerButton', 3.0, 2.0, (0.0, 867.0, 16.0), 'y', M_steel_dk, G, verts=16)
for x in (-205.0, 160.0):
    bxr('MBLever', x - 8, x + 8, 866, 871, 6, 16, M_steel_dk, G, bevel=0.8)
    bxr('MBClasp', x - 4, x + 4, 869, 873, 16, 22, M_blue, G, bevel=0.8)
mtray = join(G, 'MB_Tray', tray_m)
for k, yc in enumerate(CPU_Y):
    emptyr(f'SLOT_cpu_{k}', (0.0, yc, 4.6), tray_m, col, size=0.04, props={'cpu': 'Intel Xeon E5-2698 v4 (LGA2011-3)'})
for nm, x, z in (('LED_power_rear', 6.5, 19.0), ('LED_id_rear', 6.5, 13.0)):
    reparent(cyr(nm, 1.2, 0.6, (x, 867.3, z), 'y', M_led_g if 'power' in nm else M_led_b, None, verts=10), tray_m)

# ================================================================ PSUs (4x 1600 W, 3+1, rear right, stacked)
PSU_Z = [1.5 + 32.0 * i for i in range(4)]
psus = []
for i, z0 in enumerate(PSU_Z):
    g = f'psu{i}'
    zc = z0 + 15.5
    bxr('PSU_Body', 183, W2 - 1.4, 762, 866, z0 + 0.5, z0 + 31.0, M_steel_dk, g)
    bxr('PSU_Face', 183, W2 - 1.4, 865.5, 867.0, z0 + 0.5, z0 + 31.0, M_steel_dk, g)
    pf = bxr('PSU_Vent', 184, 196, 866.9, 867.2, z0 + 3, z0 + 28.5, M_perf_dk, g); perf_uv(pf)
    # IEC C14 inlet (vertical)
    bxr('C14_Body', 198, 218, 860, 868.5, zc - 12.5, zc + 12.5, M_black, g)
    bxr('C14_Recess', 200.5, 215.5, 868.4, 868.7, zc - 10, zc + 10, M_port, g)
    sar('C14_Pins', [((208 + dx, 866.0, zc + dz), (1.2, 5, 3.2)) for dx, dz in ((0, 4.5), (0, -1), (0, -6.5))], M_steel, g)
    bxr('PSU_Latch', 186, 196, 867.0, 870.0, z0 + 27.5, z0 + 30.5, mat('DGX_LatchGreen', (0.15, 0.45, 0.05), 0.0, 0.5), g)
    po = join(g, f'PSU_{i}', root)
    po['rating'] = '1600 W @ 200-240 V'; po['hot_swap'] = 'rear'
    emptyr(f'SLOT_psu_{i}', (202.0, 866.0, z0), po, col, size=0.03)
    # AC inlet socket: arrow (+Z of the empty) points out of the inlet (+Y)
    emptyr(f'SOCKET_power_in_psu{i}', (208.0, 868.7, zc), po, col, rot=(-math.pi / 2, 0, 0), kind='SINGLE_ARROW', size=0.03,
          props={'connector': 'IEC C14', 'rating_w': 1600})
    reparent(cyr(f'LED_psu_{i}', 1.3, 0.6, (191.0, 867.3, z0 + 25.0), 'y', M_led_g, None, verts=10), po)
    psus.append(po)

# ================================================================ LEDs on the front post
reparent(cy('LED_power', 4.0, 0.5, (233.2, -24.35, 120.0), 'y', M_led_g, None, verts=20), chassis)
reparent(cy('LED_id', 4.0, 0.5, (233.2, -24.35, 106.0), 'y', M_led_b, None, verts=20), chassis)

# ================================================================ POWER PATHS (flow UVs)
# PSU outputs -> vertical PDB busbar (x=170, y=768) -> baseboard power connectors / motherboard
BUS_X, BUS_Y = 168.0, 770.0
for i, z0 in enumerate(PSU_Z):
    zc = z0 + 15.5
    flowr(f'PWR_psu{i}', [(200.0, 761.5, zc), (200.0, 755.0, zc), (BUS_X + 6, 755.0, zc), (BUS_X + 6, BUS_Y, zc)],
              M_cable, col, root, radius=3.0, fillet=4.0, src=f'psu{i}', dst=f'pdb_from_psu{i}')
bus = flowr('PWR_pdb_bus', [(BUS_X, BUS_Y, 6.0), (BUS_X, BUS_Y, 124.0)], M_cu, col, root, rect=(10.0, 4.0),
                fillet=0.0, src='pdb_bus', dst='pdb_bus_top')
flowr('PWR_gpu_A', [(BUS_X, BUS_Y - 3, 70.0), (BUS_X, 756.0, 70.0), (156.0, 756.0, 70.0), (156.0, 756.0, BB_Z + 10.5)],
          M_cable, col, root, radius=4.0, fillet=8.0, src='pdb_gpu_A', dst='baseboard_A')
flowr('PWR_gpu_B', [(BUS_X, BUS_Y - 3, 118.0), (BUS_X, 755.5, 118.0), (-198.0, 755.5, 118.0), (-198.0, 755.5, BB_Z + 10.5)],
          M_cable, col, root, radius=4.0, fillet=12.0, src='pdb_gpu_B', dst='baseboard_B')
flowr('PWR_mb', [(BUS_X, BUS_Y + 2, 12.0), (BUS_X, 801.0, 12.0), (150.0, 801.0, 12.0), (150.0, 801.0, 16.5)],
          M_cable, col, root, radius=3.0, fillet=6.0, src='pdb_mb', dst='motherboard')

# ================================================================ save / export (no GPUs)
for c in list(bpy.data.collections):
    if c.name == 'SRV_Build':
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(c)
bpy.ops.wm.save_as_mainfile(filepath=BL + '\\' + FILE + '.blend')
tris = H['export_glb'](ROOT, BL + '\\export\\' + FILE + '.glb')
objs = [root] + list(root.children_recursive)
print('TRIS_TOTAL', tris)
for o in sorted([o for o in objs if o.type == 'MESH'], key=lambda o: -tri_count([o]))[:12]:
    print('  TRIS', o.name, tri_count([o]))
print('SLOTS', sorted(o.name for o in objs if o.name.startswith(('SLOT_', 'SOCKET_', 'LED_', 'TRAY_', 'PWR_'))))
for o in objs:
    if o.name.startswith('PWR_'):
        print('  FLOW', o.name, o['flow_u_start'], o['flow_u_end'])

# ================================================================ preview renders with appended V100 modules
v100 = append_collection(BL + '\\gpu_12a_v100_sxm2.blend', 'V100_SXM2')
for o in [o for o in objs if o.name.startswith('SLOT_gpu_')]:
    instance_at(o, v100, col)
setup_studio(1.0)


def hide(*objs_):
    def f():
        for o in objs_:
            o.hide_render = True
        def u():
            for o in objs_:
                o.hide_render = False
        return u
    return f


def slide_out(tray, dy, *also_hide):
    def f():
        tray.location.y += dy * MM
        for o in also_hide:
            o.hide_render = True
        def u():
            tray.location.y -= dy * MM
            for o in also_hide:
                o.hide_render = False
        return u
    return f


import sys
only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
views = {
    'front34': ((-0.62, -0.95, 0.42), (0.0, 0.25, 0.05), 50, None),
    'front': ((0.0, -1.55, 0.066), (0.0, 0.0, 0.066), 85, None),
    'rear34': ((0.75, 1.75, 0.42), (0.0, 0.62, 0.05), 50, None),
    'rear': ((0.0, 2.45, 0.066), (0.0, 0.87, 0.066), 85, None),
    'open34': ((-0.60, -0.38, 0.85), (0.0, 0.48, 0.03), 45, hide(lid)),
    'top': ((0.0, 0.43, 1.75), (0.0, 0.4301, 0.0), 50, hide(lid)),
    'trayout': ((0.85, 1.85, 0.75), (0.0, 0.85, 0.05), 45, slide_out(tray_g, 450.0, lid)),
    'nobezel': ((-0.55, -0.85, 0.30), (0.0, 0.2, 0.05), 50, hide(bezel)),
}
render(FILE, {k: v for k, v in views.items() if not only or k in only})
print('DONE')
