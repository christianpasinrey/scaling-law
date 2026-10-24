"""NVIDIA DGX A100 (2020) - 6U rack server, 8x A100 SXM4 + 6x NVSwitch.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python <this file> [-- view ...]

Convention (rack-mount): metres, Z up, front plane y=0 facing -Y, depth +Y, origin bottom-front-centre.
19" EIA rack, 6U. DGX A100 user guide: height 264 mm, width 482.3 mm max (ears), depth 897.1 mm max, 123 kg.
Body 446 mm wide, 850 mm deep + 27 mm bezel + rear latches.
Front (bezel removed, user guide): 8 fan modules (2 rows x 4) over 8 U.2 NVMe bays + front console board.
Rear (user guide): GPU board tray (top, ~124 mm), motherboard tray (~84 mm), 6x 3 kW PSUs (bottom row, 3+3).
GPU tray (user-guide top view): 8x A100 SXM4 in 2 columns x 4, NVSwitch 0-5 behind them, module long axis
front-to-back, 'NVIDIA' wordmark reading front->rear. Exported GLB has no GPUs: SLOT_gpu_0..7.
"""
import bpy, math, mathutils
exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\sxm_lib.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\srv_dgx_lib.py', encoding='utf-8').read())

ROOT = 'DGX_A100'
FILE = 'srv_03_dgx_a100'
BL = r'C:\laragon\www\scaling-law\blender'
W2, HT, D = 223.0, 264.0, 850.0
EAR = 241.15
LID_Z = HT - 1.2

root, col = H['new_card_scene'](ROOT)
root['standard'] = '19in EIA rack, 6U (spec height 264 mm)'
root['model'] = 'NVIDIA DGX A100 (8x A100 SXM4 40/80GB)'
M = H['base_materials']()
mat = H['mat']

# ---------------------------------------------------------------- materials
fo_col, fo_nrm, fo_rgh = foam_images('DGXA100_Foam', (0.78, 0.60, 0.28), res=512, G=36, pore=0.42)
M_foam = mat_tex('DGXA100_GoldFoam', fo_col, fo_nrm, None, metal=1.0, rough=0.42, nstr=1.0)
M_gold = mat('DGXA100_GoldSatin', (0.86, 0.67, 0.34), 1.0, 0.30)
M_gold_pol = mat('DGXA100_GoldPolished', (0.86, 0.65, 0.31), 1.0, 0.26)
M_gold_dk = mat('DGXA100_GoldEngraved', (0.30, 0.21, 0.08), 0.5, 0.65)
M_steel = mat('DGX_SteelGalv', (0.42, 0.43, 0.45), 1.0, 0.45)
M_steel_dk = mat('DGX_SteelDark', (0.20, 0.21, 0.22), 0.8, 0.45)
M_black = M['plastic']
M_blackmt = M['black_mt']
M_pcb = mat('DGX_PCBGreen', (0.015, 0.09, 0.035), 0.0, 0.45)
M_pcb_bk = mat('DGX_PCBBlack', (0.012, 0.014, 0.014), 0.0, 0.5)
M_alu = M['alu']
M_cu = mat('DGX_Copper', (0.92, 0.50, 0.30), 1.0, 0.3)
M_beige = mat('DGXA100_HandleBeige', (0.80, 0.66, 0.46), 0.0, 0.5)
M_latch = mat('DGXA100_LatchGreen', (0.45, 0.80, 0.08), 0.0, 0.45)
M_cable = mat('DGX_CableBlack', (0.012, 0.012, 0.013), 0.0, 0.55)
M_port = M['port']
perf_img = hex_perf_image('DGX_HexPerf', (0.55, 0.56, 0.58), hole=0.78)
M_perf = mat_perf('DGX_PerfSteel', perf_img)
perf_dk = hex_perf_image('DGX_HexPerfDark', (0.04, 0.04, 0.045), hole=0.80)
M_perf_dk = mat_perf('DGX_PerfBlack', perf_dk, metal=0.3)
M_led_g = mat('LED_Green', (0.1, 1.0, 0.2), 0.0, 0.3, emit=(0.1, 1.0, 0.2), emit_str=6.0)
M_led_b = mat('LED_Blue', (0.1, 0.3, 1.0), 0.0, 0.3, emit=(0.1, 0.3, 1.0), emit_str=6.0)
M_led_a = mat('LED_Amber', (1.0, 0.45, 0.05), 0.0, 0.3, emit=(1.0, 0.45, 0.05), emit_str=4.0)


def perf_uv(o, pitch=6.0, axes='xz'):
    return uv_planar(o, axes, pitch * MM, pitch * MM * math.sqrt(3))


# ================================================================ CHASSIS
bx('Floor', -W2, W2, 0, D, 0, 1.5, M_steel, 'chassis')
for s in (-1, 1):
    bx('Side', s * W2 - (1.5 if s > 0 else 0), s * W2 + (0 if s > 0 else 1.5), 0, D, 0, LID_Z, M_steel, 'chassis')
    x0, x1 = sorted((s * W2, s * EAR))
    bx('EarFlange', x0, x1, 0, 3.0, 0, HT, M_steel, 'chassis')
    x0, x1 = sorted((s * 214.0, s * EAR))
    bx('EarPost', x0, x1, -27.0, 0.0, 0, HT, M_gold, 'chassis', bevel=1.2)
    for z in (34.0, 229.0):
        cy('EarScrew', 5.5, 1.6, (s * 228.0, -27.6, z), 'y', M_gold_dk, 'chassis', verts=24)
        cy('EarScrewHead', 3.6, 1.2, (s * 228.0, -28.6, z), 'y', M_gold, 'chassis', verts=20)
# front console buttons on the right post: power, ID, fault (user guide front view)
cy('PowerButton', 3.4, 2.0, (228.0, -28.0, 203.0), 'y', M_gold_dk, 'chassis', verts=20)
cy('IDButton', 3.4, 2.0, (228.0, -28.0, 182.0), 'y', M_gold_dk, 'chassis', verts=20)
# front frame (black) around fans / NVMe, between the posts
FAN_X = (-156.0, -52.0, 52.0, 156.0)
FAN_ROWS = ((155.0, 256.0), (52.0, 153.0))          # z ranges (row 0 top: fans 0-3, row 1: fans 4-7)
sa('FrontFrame', [((0, 1.5, 259.5), (2 * W2 - 3, 3, 5)), ((0, 1.5, 154.0), (2 * W2 - 3, 3, 2)),
                  ((0, 1.5, 49.0), (2 * W2 - 3, 3, 6)), ((0, 1.5, 3.0), (2 * W2 - 3, 3, 6))] +
   [((x, 1.5, 154), (8, 3, 210)) for x in (-208.0, -104.0, 0.0, 104.0, 208.0)], M_blackmt, 'chassis')
# NVMe cage + 8 U.2 bays (2 rows, 2x2 each side) + front console board
bx('NVMeCage', -212, 212, 3, 210, 4, 47, M_steel_dk, 'chassis')
BAYS_X = (-169.5, -91.0, 84.5, 163.5)
for r, (z0, z1) in enumerate(((29.0, 43.0), (13.0, 27.0))):
    for c, bxc in enumerate(BAYS_X):
        bx('Bay', bxc - 37, bxc + 37, -1.0, 3.0, z0, z1, M_black, 'chassis', bevel=0.4)
        bx('BayHandle', bxc - 33, bxc + 25, -1.6, -1.0, z0 + 4.5, z1 - 4.5, M_steel_dk, 'chassis')
        bx('BayLatch', bxc + 27, bxc + 34, -1.6, -1.0, z0 + 3, z1 - 3, M_steel, 'chassis')
bx('ConsolePanel', -47, 41, -0.8, 3.0, 12, 44, M_blackmt, 'chassis')
for x in (-36.0, -24.0):
    bx('Console_USB', x - 6.5, x + 6.5, -1.4, 3.0, 17, 23, M_steel, 'chassis')
    bx('Console_USB_In', x - 5.5, x + 5.5, -1.6, -1.3, 18.5, 21.5, M_port, 'chassis')
bx('Console_VGA', 10, 30, -1.4, 3.0, 15, 24, M_steel, 'chassis')
bx('Console_VGA_In', 12, 28, -1.6, -1.3, 16.5, 22.5, M_port, 'chassis')
front_logo('ConsoleLogo', 9.0, (-18.0, -0.85, 36.0), mat('DGX_LogoGrey', (0.08, 0.08, 0.085), 0.3, 0.5), M_blackmt, 'chassis')
front_text('ConsoleWord', 'NVIDIA', 6.0, (5.0, -0.9, 36.0), mat('DGX_LogoGrey', (0.08, 0.08, 0.085), 0.3, 0.5), 'chassis',
           font=r'C:\Windows\Fonts\ariblk.ttf', extrude=0.15)
# internal: fan-wall bulkhead, tray guide rails, PSU shelf, PDB
bx('FanBulkhead', -W2 + 1.5, W2 - 1.5, 128, 132, 50, LID_Z, M_steel_dk, 'chassis')
for s in (-1, 1):
    for z in (51.0, 139.0):
        x0, x1 = sorted((s * (W2 - 1.5), s * (W2 - 4.5)))
        bx('TrayRail', x0, x1, 125, D, z - 1, z + 1, M_steel, 'chassis')
bx('PSUShelf', -W2 + 1.5, W2 - 1.5, 520, D, 49.0, 51.0, M_steel, 'chassis')
bx('PDB', -205, 205, 506, 512, 4, 46, M_pcb_bk, 'chassis')
chassis = join('chassis', 'Chassis', root)

bx('Lid', -W2, W2, 0, D, LID_Z, HT, M_steel, 'lid')
lid = join('lid', 'Chassis_Lid', root)

# ================================================================ BEZEL (gold metal-foam, separate)
bz = bx('BezelFoam', -212.0, 212.0, -27.0, -4.0, 4.0, 260.0, M_foam, 'bezel', bevel=1.0)
uv_planar(bz, 'xz', 0.10, 0.10)
sa('BezelRim', [((0, -16, 4.6), (424, 22, 1.2)), ((0, -16, 259.4), (424, 22, 1.2)),
                ((-211.4, -16, 132), (1.2, 22, 256)), ((211.4, -16, 132), (1.2, 22, 256))], M_gold, 'bezel')
PILL = rrect(-167.5, 132.0, 70.0, 246.0, 18.0)
pr('BezelPill', PILL, 'xz', -30.0, 6.0, M_gold_pol, 'bezel')
# embossed NVIDIA eye on top, wordmark reading downward (user guide front view)
front_logo('PillLogo', 26.0, (-167.5, -30.05, 226.0), M_gold_dk, M_gold_pol, 'bezel', vertical=True)
front_text('PillWord', 'NVIDIA', 25.0, (-167.5, -30.2, 152.0), M_gold_dk, 'bezel', vertical=True,
           font=r'C:\Windows\Fonts\ariblk.ttf', extrude=0.4)
bezel = join('bezel', 'Bezel', root)
bezel['removable'] = True
bezel['note'] = 'gold metal-foam front bezel; remove to reach fans / NVMe'

# ================================================================ FAN MODULES (8, front hot-swap)
fans = []
for r, (z0, z1) in enumerate(FAN_ROWS):
    zc = (z0 + z1) / 2
    for c, fx in enumerate(FAN_X):
        i = r * 4 + c
        g = f'fan{i}'
        n = 32; outer = []; inner = []
        for k in range(n):
            a = 2 * math.pi * k / n + math.pi / 4
            cc, ss = math.cos(a), math.sin(a)
            f = 1.0 / max(abs(cc), abs(ss))
            outer.append(((fx + 48.0 * cc * f) * MM, (zc + 49.5 * ss * f) * MM))
            inner.append(((fx + 45.0 * cc) * MM, (zc + 45.0 * ss) * MM))
        GROUPS.setdefault(g, []).append(H['ring'](f'FanHousing{i}', outer, inner, 'xz', 6.0 * MM, 118.0 * MM, M_black, _scratch()))
        for sx in (-1, 1):
            gx0, gx1 = sorted((fx + sx * 7.0, fx + sx * 47.5))
            perf_uv(bx('FanGrille', gx0, gx1, 0.0, 1.0, z0 + 1.5, z1 - 1.5, M_perf_dk, g), pitch=5.0)
        bx('FanGrilleFrame', fx - 48, fx + 48, -0.5, 6.0, z0, z0 + 2, M_black, g)
        bx('FanGrilleFrameT', fx - 48, fx + 48, -0.5, 6.0, z1 - 2, z1, M_black, g)
        bx('FanHandle', fx - 7.0, fx + 7.0, -3.0, 6.0, z0 + 1, z1 - 1, M_beige, g, bevel=0.8)
        sa('FanHandleGrip', [((fx, -3.2, zc + dz), (12, 0.6, 1.2)) for dz in range(-12, 13, 4)], mat('DGXA100_HandleShade', (0.55, 0.44, 0.30), 0.0, 0.6), g)
        sa('FanStruts', [((fx, 112, zc), (90, 3, 3)), ((fx, 112, zc), (3, 3, 90))], M_black, g)
        cy('FanMotor', 17.0, 12.0, (fx, 106.0, zc), 'y', M_black, g)
        fo = join(g, f'FAN_{i}', root)
        fo['hot_swap'] = 'front (bezel removed)'
        rot = fan_rotor(f'FAN_rotor_{i}', 43.0, 18.0, 30.0, 7, (fx, 60.0, zc), M_black, col)
        reparent(rot, fo); rot['spin_axis'] = 'Y'
        reparent(cy(f'LED_fan_{i}', 1.4, 0.6, (fx + 44.0, -0.8, z1 - 4.5), 'y', M_led_g, None, verts=10), fo)
        fans.append(fo)

# ================================================================ GPU BOARD TRAY (top, slides out the rear)
tray_g = empty('TRAY_gpu', (0.0, D, 140.0), root, col, kind='PLAIN_AXES', size=0.06,
               props={'slide_axis': '+Y', 'slide_travel_m': 0.68, 'access': 'rear',
                      'note': 'GPU board tray: HGX A100 8-GPU baseboard, 8x SXM4 + 6x NVSwitch'})
G = 'gtray'
TY0 = 170.0
BB_Z = 145.0
MOD_Z = BB_Z + 6.6
bx('Pan', -219, 219, TY0, D, 140.0, 142.0, M_steel, G)
for s in (-1, 1):
    x0, x1 = sorted((s * 219.0, s * 217.0))
    bx('Wall', x0, x1, TY0, D, 142.0, 261.5, M_steel, G)
bx('FrontWall', -217, 217, TY0, TY0 + 2, 142.0, 165.0, M_steel, G)
bx('Baseboard', -215, 215, 178, 700, 142.5, BB_Z, M_pcb_bk, G)
GPU_X = (-129.0, -43.0, 43.0, 129.0)
GPU_Y = (308.0, 461.0)
sa('SXM4_Frames', [((x, y + sy * 72.5, BB_Z + 0.3), (82, 1.5, 0.6)) for x in GPU_X for y in GPU_Y for sy in (-1, 1)] +
   [((x + sx * 41.0, y, BB_Z + 0.3), (1.5, 146, 0.6)) for x in GPU_X for y in GPU_Y for sx in (-1, 1)], M_steel_dk, G)
sa('SXM4_Mezz', [((x, y + dy, BB_Z + 1.0), (56, 20, 2.0)) for x in GPU_X for y in GPU_Y for dy in (-35.4, 35.4)], M_black, G)
# side air funnels (trapezoid baffles left/right of the GPU block)
for s in (-1, 1):
    pts = [(s * 172.0, 236.0), (s * 216.0, 196.0), (s * 216.0, 560.0), (s * 172.0, 532.0)]
    if s < 0:
        pts = list(reversed(pts))
    pr('SideFunnel', pts, 'xy', BB_Z, 100.0, M_steel, G)
# 6x NVSwitch heatsinks (copper base + heat pipes + aluminium fin stack)
NVS_X = (143.75, 86.25, 28.75, -28.75, -86.25, -143.75)    # NVSwitch 0..5 (user guide numbering)
for k, x in enumerate(NVS_X):
    bx('NVS_Pkg', x - 20, x + 20, 558, 598, BB_Z, BB_Z + 2.5, M_pcb, G)
    bx('NVS_CuBase', x - 24, x + 24, 552, 604, BB_Z + 2.5, BB_Z + 8.5, M_cu, G)
    sa('NVS_Pipes', [((x + dx, 578, BB_Z + 11), (5, 50, 5)) for dx in (-12, 0, 12)], M_cu, G)
    sa('NVS_Fins', [((x, 556 + 2.2 * j, BB_Z + 40), (50, 0.6, 52)) for j in range(22)], M_alu, G)
    bx('NVS_Top', x - 25, x + 25, 554, 603, BB_Z + 66, BB_Z + 68, M_alu, G)
# board-to-board / PCIe connectors behind the NVSwitches
sa('BB_Connectors', [((x, 660, BB_Z + 9), (26, 70, 18)) for x in [-190 + 34.5 * k for k in range(12)]], M_black, G)
sa('BB_ConnCaps', [((x, 660, BB_Z + 18.6), (22, 64, 1.2)) for x in [-190 + 34.5 * k for k in range(12)]], M_cu, G)
# HGX baseboard power entry (54 V) at both sides
bx('BB_PowerConn_A', -215, -190, 505, 528, BB_Z, BB_Z + 12, M_black, G)
bx('BB_PowerConn_B', 190, 215, 505, 528, BB_Z, BB_Z + 12, M_black, G)
# rear: full-width hex-perforated exhaust panel + centre latches (user guide rear view)
perf_uv(bx('RearPerf', -217, 217, 846.0, 847.2, 143.0, 261.0, M_perf, G), pitch=5.0)
bx('RearDark', -215, 215, 838.0, 839.0, 143.0, 259.0, M_blackmt, G)
sa('RearFrame', [((0, 848, 142.8), (438, 3, 1.6)), ((0, 848, 261.0), (438, 3, 1.6)),
                 ((-218.2, 848, 202), (1.6, 3, 120)), ((218.2, 848, 202), (1.6, 3, 120))], M_steel, G)
for s in (-1, 1):
    x0, x1 = sorted((s * 4.0, s * 22.0))
    bx('Lever', x0, x1, 847, 854, 150.0, 200.0, M_steel, G, bevel=1.0)
    bx('LatchButton', x0 + 2, x1 - 2, 853, 858, 163.0, 177.0, M_latch, G, bevel=2.0)
gtray = join(G, 'GPU_Tray', tray_g)
# A100 SXM4 slots: Rz(+90): module +X -> chassis +Y (wordmark reads front->rear), module +Y -> chassis -X.
for j, y in enumerate(GPU_Y):
    for i, x in enumerate(GPU_X):
        empty(f'SLOT_gpu_{j * 4 + i}', (x, y, MOD_Z), tray_g, col, rot=(0, 0, math.pi / 2), size=0.06,
              props={'module': 'A100_SXM4', 'glb': 'gpu_a100_sxm4.glb'})
for k, x in enumerate(NVS_X):
    empty(f'NVSWITCH_{k}', (x, 578.0, BB_Z + 2.5), tray_g, col, kind='PLAIN_AXES', size=0.02)

# ================================================================ MOTHERBOARD TRAY (middle, slides out the rear)
tray_m = empty('TRAY_mb', (0.0, D, 52.0), root, col, kind='PLAIN_AXES', size=0.06,
               props={'slide_axis': '+Y', 'slide_travel_m': 0.72, 'access': 'rear',
                      'note': 'motherboard tray: 2x AMD EPYC 7742, 32 DIMMs, PCIe switches, 8+1(+1) ConnectX-6'})
G = 'mtray'
MY0 = 125.0
MBZ = 55.6
bx('MBPan', -219, 219, MY0, D, 52.0, 54.0, M_steel, G)
for s in (-1, 1):
    x0, x1 = sorted((s * 219.0, s * 217.0))
    bx('MBWall', x0, x1, MY0, D, 54.0, 134.0, M_steel, G)
bx('MBBoard', -215, 215, MY0 + 4, 842, 54.0, MBZ, M_pcb, G)
CPU_Y = (317.0, 547.0)
for k, yc in enumerate(CPU_Y):
    bx('SP3_Socket', -38, 38, yc - 37, yc + 37, MBZ, MBZ + 4, M_steel_dk, G)
    bx('CPU_HSBase', -40, 40, yc - 55, yc + 55, MBZ + 4, MBZ + 10, M_cu, G)
    sa('CPU_HSFins', [((x, yc, MBZ + 36), (0.6, 108, 52)) for x in [-39 + 2.0 * j for j in range(40)]], M_alu, G)
    sa('CPU_HSPipes', [((x, yc, MBZ + 12), (6, 112, 5)) for x in (-24, -8, 8, 24)], M_cu, G)
    sa('DIMMs', [((s * (49 + 9.5 * d), yc, MBZ + 18), (1.3, 133, 31)) for s in (-1, 1) for d in range(8)], M_pcb, G)
    sa('DIMM_Chips', [((s * (49 + 9.5 * d) + 0.9, yc + 14 * (c - 4), MBZ + 17), (0.6, 10, 11)) for s in (-1, 1) for d in range(8) for c in range(9)], M_black, G)
    sa('DIMM_Slots', [((s * (49 + 9.5 * d), yc, MBZ + 2.5), (6, 146, 5)) for s in (-1, 1) for d in range(8)], M_black, G)
# PCIe switch heatsinks (4 corners at the front) + 2 more mid-board (user guide motherboard tray image)
for (x, y, w, d) in [(s * 167.0, yy, 70.0, 75.0) for s in (-1, 1) for yy in (228.0, 318.0)] + [(s * 167.0, 515.0, 70.0, 95.0) for s in (-1, 1)]:
    bx('PEX_Base', x - w / 2, x + w / 2, y - d / 2, y + d / 2, MBZ, MBZ + 3, M_alu, G)
    sa('PEX_Fins', [((x - w / 2 + 1 + 2.6 * j, y, MBZ + 17), (0.8, d, 28)) for j in range(int(w / 2.6))], M_alu, G)
# 8x ConnectX-6 cluster NICs (4 each side, standing) + centre storage NIC (horizontal)
NIC_X = (-200.0, -175.0, -150.0, -125.0, 125.0, 150.0, 175.0, 200.0)
for x in NIC_X:
    bx('NIC_Riser', x - 4, x + 4, 690, 830, MBZ, MBZ + 10, M_black, G)
    bx('NIC_PCB', x - 0.8, x + 0.8, 664, 842, MBZ + 6, MBZ + 75, M_pcb, G)
    bx('NIC_HS', x + 0.8, x + 10.0, 700, 770, MBZ + 15, MBZ + 65, M_steel_dk, G)
    bx('NIC_Bracket', x - 10, x + 10, 846, 849, 56, 133, M_steel, G)
    bx('NIC_QSFP', x - 8, x + 8, 849, 856, 100, 116, M_steel, G)
    bx('NIC_QSFP_In', x - 6.5, x + 6.5, 855.9, 856.2, 102, 114, M_port, G)
bx('StorNIC_PCB', -70, 70, 700, 842, 112, 113.6, M_pcb, G)
bx('StorNIC_HS', -25, 25, 730, 780, 113.6, 124, M_steel_dk, G)
bx('StorNIC_Bracket', -78, 78, 846, 849, 104, 132, M_steel, G)
for x in (-30.0, 10.0):
    bx('StorNIC_QSFP', x - 15, x + 15, 849, 856, 109, 126, M_steel, G)
    bx('StorNIC_QSFP_In', x - 13, x + 13, 855.9, 856.2, 111, 124, M_port, G)
bx('M2_Boot', 40, 120, 640, 700, MBZ, MBZ + 18, M_steel_dk, G)
bx('MB_PowerConn', -12, 12, 480, 505, MBZ, MBZ + 10, M_black, G)
# rear faceplate + I/O (user guide motherboard connections: BMC, LAN, USB x2, VGA, serial, power/ID)
bx('MBRearPlateL', -219, -103, 846, 849, 54, 134, M_steel, G)
bx('MBRearPlateR', 103, 219, 846, 849, 54, 134, M_steel, G)
perf_uv(bx('MBRearPerf', -103, 103, 846.5, 847.5, 54, 100, M_perf, G), pitch=5.0)
bx('MBRearIOPlate', -100, 100, 847.5, 849, 56, 82, M_steel_dk, G)
for nm, x, z, w, h in [('Serial', 72.0, 68.0, 25.0, 12.5), ('VGA', 35.0, 68.0, 31.0, 12.5), ('RJ45_LAN', -44.0, 68.0, 16.0, 14.0),
                       ('USB0', -62.0, 63.0, 14.0, 6.0), ('USB1', -62.0, 72.0, 14.0, 6.0), ('RJ45_BMC', -82.0, 68.0, 16.0, 14.0)]:
    bx(f'Port_{nm}', x - w / 2, x + w / 2, 845, 851.0, z - h / 2, z + h / 2, M_black if 'RJ45' in nm else M_steel, G)
    bx(f'Port_{nm}_In', x - w / 2 + 1.5, x + w / 2 - 1.5, 850.9, 851.2, z - h / 2 + 1.5, z + h / 2 - 1.5, M_port, G)
for nm, x in (('RearPower', 9.0), ('RearID', -10.0), ('RearBMCReset', -22.0)):
    cy(nm, 3.0, 2.0, (x, 850.5, 68.0), 'y', M_steel_dk, G, verts=16)
for s in (-1, 1):
    x0, x1 = sorted((s * 4.0, s * 22.0))
    bx('MBLever', x0, x1, 849, 855, 86.0, 98.0, M_steel, G, bevel=1.0)
    bx('MBLatchButton', x0 + 2, x1 - 2, 853, 858, 88.0, 96.0, M_latch, G, bevel=2.0)
mtray = join(G, 'MB_Tray', tray_m)
for k, yc in enumerate(CPU_Y):
    empty(f'SLOT_cpu_{k}', (0.0, yc, MBZ), tray_m, col, size=0.04, props={'cpu': 'AMD EPYC 7742 (SP3)'})
for nm, x, m_ in (('LED_power_rear', 9.0, M_led_g), ('LED_id_rear', -10.0, M_led_b)):
    reparent(cy(nm, 1.2, 0.6, (x, 851.6, 75.0), 'y', m_, None, verts=10), tray_m)

# ================================================================ PSUs (6x 3 kW, 3+3, bottom rear row)
PSU_X = (182.0, 110.0, 38.0, -35.0, -107.0, -179.0)      # PSU 0..5 left->right seen from the rear
PSU_Y0 = 530.0
psus = []
for i, xc in enumerate(PSU_X):
    g = f'psu{i}'
    bx('PSU_Body', xc - 35, xc + 35, PSU_Y0, D, 2.0, 47.0, M_steel_dk, g)
    bx('PSU_Face', xc - 35, xc + 35, D - 1.0, D + 1.0, 2.0, 47.0, M_steel_dk, g)
    perf_uv(bx('PSU_Vent', xc - 33, xc - 20, D + 0.9, D + 1.2, 6.0, 44.0, M_perf_dk, g), pitch=4.0)
    perf_uv(bx('PSU_Vent2', xc + 20, xc + 27, D + 0.9, D + 1.2, 6.0, 44.0, M_perf_dk, g), pitch=4.0)
    # IEC C20 inlet (horizontal)
    bx('C20_Body', xc - 17, xc + 17, D - 6.0, D + 3.5, 20.0, 43.0, M_black, g)
    bx('C20_Recess', xc - 14.5, xc + 14.5, D + 3.4, D + 3.7, 22.5, 40.5, M_port, g)
    sa('C20_Pins', [((xc + dx, D + 1.0, z), (6.0, 5.0, 1.6)) for dx, z in ((-7.5, 29.0), (7.5, 29.0))] + [((xc, D + 1.0, 35.0), (1.6, 5.0, 6.0))], M_steel, g)
    bx('PSU_Handle', xc - 22, xc + 18, D + 1.0, D + 8.0, 6.0, 12.0, M_black, g, bevel=1.0)
    bx('PSU_Latch', xc + 28, xc + 33.5, D + 1.0, D + 5.0, 8.0, 42.0, M_latch, g, bevel=1.0)
    po = join(g, f'PSU_{i}', root)
    po['rating'] = '3000 W @ 200-240 V, 16 A'; po['hot_swap'] = 'rear'
    empty(f'SLOT_psu_{i}', (xc, D, 2.0), po, col, size=0.03)
    empty(f'SOCKET_power_in_psu{i}', (xc, D + 3.7, 31.5), po, col, rot=(-math.pi / 2, 0, 0), kind='SINGLE_ARROW', size=0.03,
          props={'connector': 'IEC C20', 'rating_w': 3000})
    reparent(cy(f'LED_psu_{i}', 1.3, 0.6, (xc - 26.0, D + 1.4, 40.0), 'y', M_led_g, None, verts=10), po)
    psus.append(po)

# front console LEDs (power, ID, fault)
reparent(cy('LED_power', 4.2, 0.5, (228.0, -29.1, 203.0), 'y', M_led_g, None, verts=20), chassis)
reparent(cy('LED_id', 4.2, 0.5, (228.0, -29.1, 182.0), 'y', M_led_b, None, verts=20), chassis)
fault = pr('LED_fault', [(224.0, 157.0), (232.0, 157.0), (228.0, 164.5)], 'xz', -29.0, 0.8, M_led_a, None)
reparent(fault, chassis)

# ================================================================ POWER PATHS (flow UVs)
# PSU outputs -> PDB busbar (y=514) -> 54 V risers up both side walls -> HGX baseboard; -> motherboard
BUS_Y, BUS_Z = 516.0, 30.0
for i, xc in enumerate(PSU_X):
    flow_path(f'PWR_psu{i}', [(xc, PSU_Y0 - 0.5, 24.0), (xc, BUS_Y + 5, 24.0), (xc, BUS_Y + 5, BUS_Z)],
              M_cable, col, root, radius=3.5, fillet=4.0, src=f'psu{i}', dst=f'pdb_from_psu{i}')
flow_path('PWR_pdb_bus', [(-196.0, BUS_Y, BUS_Z), (196.0, BUS_Y, BUS_Z)], M_cu, col, root, rect=(4.0, 14.0), fillet=0.0,
          src='pdb_bus', dst='pdb_bus_end')
for tag, s in (('A', -1), ('B', 1)):
    flow_path(f'PWR_gpu_{tag}', [(s * 196.0, BUS_Y, BUS_Z), (s * 214.0, BUS_Y, BUS_Z), (s * 214.0, BUS_Y, BB_Z + 18.0),
                                 (s * 202.0, BUS_Y, BB_Z + 18.0), (s * 202.0, BUS_Y, BB_Z + 12.0)],
              M_cu, col, root, rect=(10.0, 4.0), fillet=6.0, src=f'pdb_gpu_{tag}', dst=f'baseboard_{tag}')
flow_path('PWR_mb', [(0.0, BUS_Y - 2, BUS_Z), (0.0, BUS_Y - 18, BUS_Z), (0.0, 492.0, MBZ + 10.0)], M_cable, col, root,
          radius=4.0, fillet=10.0, src='pdb_mb', dst='motherboard')

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
for o in sorted([o for o in objs if o.type == 'MESH'], key=lambda o: -tri_count([o]))[:10]:
    print('  TRIS', o.name, tri_count([o]))
print('SLOTS', sorted(o.name for o in objs if o.name.startswith(('SLOT_', 'SOCKET_', 'LED_', 'TRAY_', 'PWR_', 'NVSWITCH'))))
for o in objs:
    if o.name.startswith('PWR_'):
        print('  FLOW', o.name, o['flow_u_start'], o['flow_u_end'])

# ================================================================ preview renders with appended A100 modules
a100 = append_collection(BL + '\\gpu_12b_a100_sxm4.blend', 'A100_SXM4')
for o in [o for o in objs if o.name.startswith('SLOT_gpu_')]:
    instance_at(o, a100, col)
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
    'front34': ((-0.70, -1.05, 0.62), (0.0, 0.25, 0.12), 50, None),
    'front': ((0.0, -2.0, 0.132), (0.0, 0.0, 0.132), 85, None),
    'nobezel': ((0.0, -2.0, 0.132), (0.0, 0.0, 0.132), 85, hide(bezel)),
    'rear34': ((0.85, 1.85, 0.62), (0.0, 0.62, 0.11), 50, None),
    'rear': ((0.0, 2.85, 0.132), (0.0, 0.86, 0.132), 85, None),
    'open34': ((-0.62, -0.40, 1.05), (0.0, 0.48, 0.10), 45, hide(lid)),
    'top': ((0.0, 0.47, 1.9), (0.0, 0.4701, 0.0), 50, hide(lid)),
    'trayout': ((0.95, 2.05, 0.95), (0.0, 0.95, 0.12), 45, slide_out(tray_g, 520.0, lid)),
}
render(FILE, {k: v for k, v in views.items() if not only or k in only})
print('DONE')
