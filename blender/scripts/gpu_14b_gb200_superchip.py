"""NVIDIA GB200 Grace Blackwell Superchip board ("Bianca", 2024-2025) as in a GB200 NVL72 compute tray.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python gpu_14b_gb200_superchip.py

Conventions: metres, board flat (PCB bottom at z=0, parts toward +Z), origin = board centre.
  +Y = GPU end (NVLink backplane connectors -> rack spine / tray rear)
  -Y = Grace / I/O end (coolant quick-disconnects, toward the tray front manifold)
Footprint (rectified from STH Computex-2024 photo, scale from NVIDIA DGX tray top view):
  PCB 200 x 285 x 2.4 mm. NVLink connectors overhang +Y edge by ~8 mm, quick-disconnects
  overhang -Y edge by ~31 mm, power cable stubs overhang -X by ~8 mm.
  Max height z = ~33 mm (hoses) -> fits a 1U tray. Two boards side by side across the 1U
  tray width (mirrored in X for the right-hand board), GPU end toward the rear.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector

BASE = r'C:\laragon\www\scaling-law\blender'
exec(open(BASE + r'\lib\hw.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']
exec(open(BASE + r'\scripts\blackwell_common.py', encoding='utf-8').read())

ROOT = 'GB200_Superchip'
root, col = H['new_card_scene'](ROOT)
M = H['base_materials'](); M.update(extra_materials())
box, cyl, sa = H['box'], H['cyl'], H['slat_array']

BW, BL, T = 0.200, 0.285, 0.0024


def P(u, v):
    """photo mm (u from left, v from GPU-end edge) -> model metres."""
    return (u / 1000.0 - BW / 2, BL / 2 - v / 1000.0)


def join(name, objs):
    for o in objs:
        H['apply_all'](o)
    with bpy.context.temp_override(active_object=objs[0], object=objs[0], selected_objects=objs, selected_editable_objects=objs):
        bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


def reparent(o, parent):
    bpy.context.view_layer.update()
    mw = o.matrix_world.copy(); o.parent = parent
    o.matrix_parent_inverse = parent.matrix_world.inverted(); o.matrix_world = mw


# ---------------------------------------------------------------- PCB
box('PCB', (BW, BL, T), (0, 0, T / 2), M['pcb_board'], col, bevel=0.0004, parent=root)

# GPU packages (B200, lidded) ------------------------------------------------
GPU = [(-0.0465, 0.0815), (0.0465, 0.0815)]
GL, GH = 0.072, 0.077
LID_G = T + 0.0055
for i, (x, y) in enumerate(GPU):
    box(f'GPU{i}_Substrate', (GL + 0.002, GH + 0.002, 0.0016), (x, y, T + 0.0008), M['substrate'], col, bevel=0.0003, parent=root)
    box(f'GPU{i}_Lid', (GL, GH, LID_G - T - 0.0016), (x, y, (T + 0.0016 + LID_G) / 2), M['nickel'], col, bevel=0.0007, parent=root)
    H['text_mesh'](f'GPU{i}_Text', 'NVIDIA', FONT_LOGO, 0.0115, M['black_mt'], col, root,
                   (x - 0.002, y + 0.006, LID_G + 0.00002), (0, 0, math.pi / 2), extrude=0.00002, scale=(1.18, 1, 1))
    box(f'GPU{i}_Logo', (0.0105, 0.0120, 0.00004), (x - 0.002, y - 0.024, LID_G + 0.00002), M['black_mt'], col, parent=root)
    cyl(f'GPU{i}_Logo_Eye', 0.0030, 0.00006, (x - 0.002, y - 0.0245, LID_G + 0.00003), M['nickel'], col, verts=24, parent=root)
    cyl(f'GPU{i}_Logo_Pupil', 0.0015, 0.00008, (x - 0.002, y - 0.0245, LID_G + 0.00004), M['black_mt'], col, verts=16, parent=root)

# Grace CPU ------------------------------------------------------------------
CPU = (0.0010, -0.0125)
CL, CH = 0.064, 0.070
LID_C = T + 0.0045
box('Grace_Substrate', (CL + 0.003, CH + 0.003, 0.0012), (CPU[0], CPU[1], T + 0.0006), M['substrate'], col, bevel=0.0003, parent=root)
box('Grace_Lid', (CL, CH, LID_C - T - 0.0012), (CPU[0], CPU[1], (T + 0.0012 + LID_C) / 2), M['nickel'], col, bevel=0.0007, parent=root)
for k, (txt, dy, sz) in enumerate((('NVIDIA', 0.012, 0.0080), ('GRACE', 0.001, 0.0058), ('TH500  2405', -0.009, 0.0040))):
    H['text_mesh'](f'Grace_Text_{k}', txt, FONT_LOGO if k < 2 else FONT, sz, M['black_mt'], col, root,
                   (CPU[0] + 0.002, CPU[1] + dy, LID_C + 0.00002), (0, 0, 0), extrude=0.00002)
# LPDDR5X: 2 blocks of 2 x 4 packages either side of Grace
lp = []
for u0 in (42.0, 135.0):
    for c in range(2):
        for r in range(4):
            x, y = P(u0 + 6.0 + c * 13.0, 133.0 + r * 16.0)
            lp.append(((x, y, T + 0.0005), (0.0115, 0.0145, 0.0010)))
sa('LPDDR5X', lambda: iter(lp), M['mold'], col, root)
sa('LPDDR5X_Marks', lambda: (((c[0] - 0.003, c[1] + 0.005, T + 0.00102), (0.0012, 0.0012, 0.00004)) for c, s in lp), M['print'], col, root)

# VRM chokes and power stages ------------------------------------------------
ch = []
for i in range(12):                               # outer columns along both long edges (GPU zone)
    for u in (7.0, 193.0):
        ch.append((P(u, 26 + i * 8.6), (0.0075, 0.0070, 0.0050)))
for i in range(9):                                # two columns between the GPUs
    for u in (95.5, 104.5):
        ch.append((P(u, 30 + i * 8.8), (0.0075, 0.0070, 0.0050)))
for i in range(19):                               # row under the GPUs
    u = 19 + i * 8.6
    if 84 < u < 116:
        continue
    for v in (106.0, 115.0):
        ch.append((P(u, v), (0.0075, 0.0068, 0.0050)))
for i in range(7):                                # row under Grace
    ch.append((P(73 + i * 9.2, 195.5), (0.0078, 0.0068, 0.0050)))
sa('VRM_Chokes', lambda: (((x, y, T + s[2] / 2), s) for (x, y), s in ch), M['choke'], col, root)
sa('VRM_Choke_Pads', lambda: (((x, y + s[1] / 2 + 0.0004, T + 0.0003), (s[0] * 0.7, 0.0010, 0.0006)) for (x, y), s in ch), M['tin'], col, root)
# dense power-stage / cap strip along the long edges (fine gold/tin dots seen in photos)
sa('Edge_Cap_Strips', lambda: (((P(u, 0)[0], BL / 2 - (22 + j * 1.6) / 1000, T + 0.00025), (0.0012, 0.0008, 0.0005))
                               for u in (1.8, 13.0, 187.0, 198.2) for j in range(70)), M['tin'], col, root)

# NVLink backplane connectors at the GPU end (overhang the edge) ---------------
for i, x in enumerate((-0.0365, 0.0350)):
    y = BL / 2 - 0.0020
    box(f'NVLink_Conn{i}_Body', (0.060, 0.020, 0.0110), (x, y, T + 0.0055), M['plastic'], col, bevel=0.0006, parent=root)
    for s in (-1, 1):
        box(f'NVLink_Conn{i}_Tower{s}', (0.0135, 0.0175, 0.0100), (x + s * 0.0215, y + 0.0005, T + 0.0110 + 0.0050), M['plastic'], col, bevel=0.0012, parent=root)
        box(f'NVLink_Conn{i}_Slot{s}', (0.0070, 0.0040, 0.0006), (x + s * 0.0215, y + 0.0040, T + 0.0211), M['port'], col, parent=root)
    box(f'NVLink_Conn{i}_Rib', (0.028, 0.0050, 0.0030), (x, y + 0.0060, T + 0.0125), M['black_st'], col, parent=root)
    cyl(f'NVLink_Conn{i}_Screw', 0.0012, 0.003, (x, y + 0.006, T + 0.0150), M['steel'], col, verts=12, parent=root)
    sa(f'NVLink_Conn{i}_Pins', lambda x=x, y=y: (((x + (k - 23) * 0.00115, y - 0.0115, T + 0.0006), (0.0005, 0.003, 0.0010))
                                               for k in range(47)), M['gold'], col, root)

# Gold power-lug pads (corner pairs and mid pairs) ---------------------------
pads = [(8, 6), (8, 16.5), (192, 6), (192, 16.5), (9, 149), (9, 160), (190, 149), (190, 160)]
for i, (u, v) in enumerate(pads):
    x, y = P(u, v)
    box(f'PowerPad_{i}', (0.0140, 0.0095, 0.00012), (x, y, T + 0.00006), M['gold'], col, parent=root)
    cyl(f'PowerPad_Hole_{i}', 0.0021, 0.0003, (x, y, T + 0.00015), M['port'], col, verts=16, parent=root)

# mounting holes (tinned rings) -----------------------------------------------
holes = [(13, 22), (98, 22), (102, 22), (187, 22), (17, 104), (84, 104), (116, 104), (183, 104), (36, 4.5), (164, 4.5),
         (64, 121), (136, 121), (64, 190), (136, 190), (4, 30), (196, 30), (4, 190), (196, 190), (20, 210), (180, 210),
         (100, 215), (45, 236), (155, 236), (30, 266), (70, 280), (130, 280), (170, 266), (100, 282)]
for i, (u, v) in enumerate(holes):
    x, y = P(u, v)
    cyl(f'MountHole_{i}', 0.0034, 0.00016, (x, y, T + 0.00008), M['tin'], col, verts=20, parent=root)
    cyl(f'MountHole_Bore_{i}', 0.0016, 0.0002, (x, y, T + 0.00012), M['port'], col, verts=16, parent=root)

# I/O end: copper-finned blocks, cable connectors, headers --------------------
for i, v in enumerate((228.5, 259.5)):
    x, y = P(104.5, v)
    box(f'IO_Block{i}_Frame', (0.0290, 0.0265, 0.0045), (x, y, T + 0.00225), M['plastic'], col, bevel=0.0004, parent=root)
    sa(f'IO_Block{i}_Fins', lambda x=x, y=y: (((x, y - 0.0105 + k * 0.0015, T + 0.0045), (0.0240, 0.0008, 0.0020)) for k in range(15)),
       M['copper'], col, root)
conns = [(20, 172, 235, 0.0075), (168.5, 172, 205, 0.0070), (168.5, 208, 236, 0.0070), (186, 172, 215, 0.0072), (186, 221, 240, 0.0072),
         (183, 246, 266, 0.0070)]
for i, (u, v0, v1, w) in enumerate(conns):
    x, y = P(u, (v0 + v1) / 2)
    box(f'Cable_Conn_{i}', (w, (v1 - v0) / 1000, 0.0085), (x, y, T + 0.00425), M['plastic'], col, bevel=0.0004, parent=root)
    box(f'Cable_Conn_{i}_Slot', (w * 0.45, (v1 - v0) / 1000 - 0.003, 0.0004), (x, y, T + 0.0086), M['port'], col, parent=root)
hdr = [35, 50, 65, 135, 150, 165]
for i, u in enumerate(hdr):
    x, y = P(u, 280.5)
    box(f'Header_{i}', (0.0100, 0.0065, 0.0070), (x, y, T + 0.0035), M['plastic'], col, bevel=0.0003, parent=root)
    sa(f'Header_{i}_Holes', lambda x=x, y=y: (((x - 0.0034 + c * 0.0023, y + rr * 0.0024 - 0.0012, T + 0.0071), (0.0014, 0.0014, 0.0002))
                                              for c in range(4) for rr in range(2)), M['port'], col, root)
x, y = P(20, 158)
box('Debug_Header', (0.0045, 0.012, 0.0060), (x + 0.003, y - 0.004, T + 0.0030), M['plastic'], col, parent=root)
# silkscreen
x, y = P(158, 203)
H['text_mesh']('Silk_NVIDIA', 'NVIDIA', FONT_LOGO, 0.0050, M['print'], col, root, (x, y, T + 0.00002), (0, 0, 0), extrude=0.00002)
H['text_mesh']('Silk_Config', 'GB200  CONFIG1', FONT, 0.0022, M['print'], col, root, (x, y - 0.0055, T + 0.00002), (0, 0, 0), extrude=0.00002)


# SMD scatter in the I/O / control zone ---------------------------------------
def keepout(u, v):
    zones = [(60, 145, 118, 200), (90, 120, 214, 275), (14, 26, 168, 240), (160, 192, 168, 270), (28, 172, 274, 285),
             (0, 18, 140, 168), (182, 200, 140, 168)]
    return any(a <= u <= b and c <= v <= d for a, b, c, d in zones)


def smd():
    rnd = random.Random(42)
    n = 0
    while n < 420:
        u = rnd.uniform(3, 197); v = rnd.uniform(122, 283)
        if keepout(u, v):
            continue
        n += 1
        x, y = P(u, v)
        if rnd.random() < 0.35:
            caps.append(((x, y, T + 0.0003), (0.0010, 0.0005, 0.0006)))
            continue
        w, h = rnd.choice(((0.0010, 0.0005), (0.0010, 0.0005), (0.0016, 0.0008), (0.0020, 0.0012), (0.0030, 0.0016), (0.0040, 0.0040)))
        if rnd.random() < 0.5:
            w, h = h, w
        yield (x, y, T + 0.0003), (w, h, 0.0006 if w < 0.004 else 0.0010)


caps = []
sa('SMD_Parts', smd, M['smd'], col, root)
sa('SMD_Caps', lambda: iter(caps), M['smd_cap'], col, root)

# ---------------------------------------------------------------- cooling loop (child empty)
cool = bpy.data.objects.new('CoolingLoop', None); cool.empty_display_type = 'CUBE'; cool.empty_display_size = 0.01
col.objects.link(cool); cool.parent = root
PORT_H = 0.0060


def cold_plate(name, cx, cy, base_wh, top_wh, z0, ports):
    """Brazed copper cold plate: base, body, lid, port fittings, 4 spring screws. returns fitting top z."""
    bw, bh = base_wh; tw, th = top_wh
    box(name + '_Base', (bw, bh, 0.0030), (cx, cy, z0 + 0.0015), M['copper'], col, bevel=0.0006, parent=cool)
    box(name + '_Body', (tw, th, 0.0050), (cx, cy, z0 + 0.0055), M['copper'], col, bevel=0.0018, parent=cool)
    box(name + '_Cap', (tw - 0.010, th - 0.010, 0.0016), (cx, cy, z0 + 0.0088), M['copper_dk'], col, bevel=0.0007, parent=cool)
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        px, py = cx + sx * (bw / 2 - 0.0045), cy + sy * (bh / 2 - 0.0045)
        cyl(f'{name}_Spring{k}', 0.0026, 0.0045, (px, py, z0 + 0.0030 + 0.00225), M['steel'], col, verts=16, parent=cool)
        cyl(f'{name}_Screw{k}', 0.0030, 0.0016, (px, py, z0 + 0.0075 + 0.0008), M['black_st'], col, verts=20, bevel=0.0004, parent=cool)
    zt = z0 + 0.0080
    for k, (px, py) in enumerate(ports):
        cyl(f'{name}_Fitting{k}', 0.0058, 0.0025, (px, py, zt + 0.00125), M['steel'], col, verts=6, parent=cool)
        cyl(f'{name}_Barb{k}', 0.0042, PORT_H - 0.0025, (px, py, zt + 0.0025 + (PORT_H - 0.0025) / 2), M['steel'], col, verts=24, parent=cool)
    return zt + PORT_H


G0_IN, G0_OUT = (GPU[0][0], GPU[0][1] - 0.026), (GPU[0][0], GPU[0][1] + 0.026)
G1_IN, G1_OUT = (GPU[1][0], GPU[1][1] + 0.026), (GPU[1][0], GPU[1][1] - 0.026)
C_IN, C_OUT = (CPU[0] - 0.016, CPU[1] - 0.026), (CPU[0] - 0.016, CPU[1] + 0.026)
zg = cold_plate('ColdPlate_GPU0', GPU[0][0], GPU[0][1], (0.084, 0.088), (0.068, 0.070), LID_G, (G0_IN, G0_OUT))
cold_plate('ColdPlate_GPU1', GPU[1][0], GPU[1][1], (0.084, 0.088), (0.068, 0.070), LID_G, (G1_IN, G1_OUT))
zc = cold_plate('ColdPlate_CPU', CPU[0], CPU[1], (0.072, 0.078), (0.058, 0.064), LID_C, (C_IN, C_OUT))

# quick-disconnect pair on a bracket at the -Y edge
QZ = 0.0150
QD = [(-0.030, 'in', 'qd_blue'), (0.030, 'out', 'qd_red')]
box('QD_Bracket', (0.088, 0.0080, QZ + 0.0060 - T), (0, -BL / 2 + 0.0060, (T + QZ + 0.0060) / 2), M['anod'], col, bevel=0.0005, parent=cool)
for x, tag, mc in QD:
    y0 = -BL / 2 + 0.0100
    cyl(f'QD_{tag}_Body', 0.0072, 0.024, (x, y0 - 0.012, QZ), M['steel'], col, verts=28, rot=(math.pi / 2, 0, 0), bevel=0.0005, parent=cool)
    cyl(f'QD_{tag}_Collar', 0.0080, 0.0070, (x, y0 - 0.0175, QZ), M[mc], col, verts=28, rot=(math.pi / 2, 0, 0), bevel=0.0006, parent=cool)
    cyl(f'QD_{tag}_Nose', 0.0052, 0.0085, (x, y0 - 0.0282, QZ), M['steel'], col, verts=24, rot=(math.pi / 2, 0, 0), parent=cool)
    cyl(f'QD_{tag}_Valve', 0.0030, 0.0010, (x, y0 - 0.0325, QZ), M['port'], col, verts=20, rot=(math.pi / 2, 0, 0), parent=cool)
    cyl(f'QD_{tag}_Hex', 0.0085, 0.0040, (x, y0 + 0.0005, QZ), M['steel'], col, verts=6, rot=(math.pi / 2, 0, 0), parent=cool)
    cyl(f'QD_{tag}_HoseBarb', 0.0050, 0.0080, (x, y0 + 0.0060, QZ), M['steel'], col, verts=20, rot=(math.pi / 2, 0, 0), parent=cool)

QD_TIP_Y = -BL / 2 + 0.0100 - 0.0330
QD_BACK_Y = -BL / 2 + 0.0100 + 0.0100

# tubes (flow order, continuous UV u in metres)
u = 0.0
PATH = []
o, u = tube('Coolant_1_Hose_In', [(-0.030, QD_BACK_Y, QZ), (-0.030, QD_BACK_Y + 0.010, QZ + 0.002), (-0.026, -0.098, 0.0255),
                                   (-0.018, -0.060, 0.0270), (C_IN[0], C_IN[1] - 0.004, zc + 0.0030), (C_IN[0], C_IN[1], zc)],
            0.0046, M['hose'], col, cool, u0=u); PATH.append(o)
u += 0.060   # through the Grace cold plate
o, u = tube('Coolant_2_Pipe_CPU_GPU0', [(C_OUT[0], C_OUT[1], zc), (C_OUT[0], C_OUT[1] + 0.003, zc + 0.0030),
                                         (-0.030, 0.034, 0.0265), (G0_IN[0], G0_IN[1] - 0.004, zg + 0.0030), (G0_IN[0], G0_IN[1], zg)],
            0.0036, M['copper'], col, cool, u0=u); PATH.append(o)
u += 0.055   # through GPU0 cold plate
o, u = tube('Coolant_3_Pipe_GPU0_GPU1', [(G0_OUT[0], G0_OUT[1], zg), (G0_OUT[0] + 0.002, G0_OUT[1] + 0.004, zg + 0.0030),
                                          (0.0, 0.118, 0.0275), (G1_IN[0] - 0.002, G1_IN[1] + 0.004, zg + 0.0030), (G1_IN[0], G1_IN[1], zg)],
            0.0036, M['copper'], col, cool, u0=u); PATH.append(o)
u += 0.055   # through GPU1 cold plate
o, u = tube('Coolant_4_Hose_Out', [(G1_OUT[0], G1_OUT[1], zg), (G1_OUT[0], G1_OUT[1] - 0.004, zg + 0.0030), (0.066, 0.020, 0.0280),
                                    (0.074, -0.040, 0.0280), (0.060, -0.098, 0.0255), (0.030, QD_BACK_Y + 0.010, QZ + 0.002), (0.030, QD_BACK_Y, QZ)],
            0.0046, M['hose'], col, cool, u0=u); PATH.append(o)
FLOW_LEN = u
for o in PATH:
    uv = o.data.uv_layers['UVMap'].data
    us = [d.uv[0] for d in uv]; vs = [d.uv[1] for d in uv]
    print('UV', o.name, round(min(us), 4), round(max(us), 4), round(min(vs), 3), round(max(vs), 3), len(o.data.polygons))
# hose clamps / ferrules at hose ends
for o in (PATH[0], PATH[3]):
    pass
for k, (x, y, z, rot) in enumerate(((-0.030, QD_BACK_Y + 0.003, QZ, (math.pi / 2, 0, 0)), (0.030, QD_BACK_Y + 0.003, QZ, (math.pi / 2, 0, 0)),
                                    (C_IN[0], C_IN[1], zc + 0.0015, (0, 0, 0)), (G1_OUT[0], G1_OUT[1], zg + 0.0015, (0, 0, 0)))):
    cyl(f'Hose_Ferrule_{k}', 0.0056, 0.0050, (x, y, z), M['steel'], col, verts=24, rot=rot, parent=cool)

# ---------------------------------------------------------------- power input: cable lugs on the mid-left gold pads
PWR = []
for k, (v, mc) in enumerate(((149, 'cable_red'), (160, 'black_mt'))):
    x, y = P(9, v)
    box(f'Power_Lug_{k}', (0.0130, 0.0075, 0.0018), (x, y, T + 0.0009 + 0.00012), M['tin'], col, bevel=0.0004, parent=root)
    cyl(f'Power_Lug_Nut_{k}', 0.0030, 0.0028, (x, y, T + 0.0032), M['steel'], col, verts=6, parent=root)
    box(f'Power_Lug_Barrel_{k}', (0.0080, 0.0058, 0.0050), (x - 0.0095, y, T + 0.0032), M['tin'], col, bevel=0.0010, parent=root)
    o, _ = tube(f'Power_Cable_{k}', [(x - 0.0135, y, T + 0.0032), (x - 0.0200, y, T + 0.0034), (x - 0.0260, y, T + 0.0034)],
                0.0029, M[mc], col, root)
    cyl(f'Power_Cable_End_{k}', 0.0029, 0.0008, (x - 0.0262, y, T + 0.0034), M[mc], col, verts=16, rot=(0, math.pi / 2, 0), parent=root)
x, y = P(9, 154.5)
empty('SOCKET_power_in', (x - 0.0265, y, T + 0.0034), col, root, size=0.02, rot=(0, -math.pi / 2, 0))

# ---------------------------------------------------------------- coolant sockets
empty('SOCKET_coolant_in', (-0.030, QD_TIP_Y, QZ), col, root, size=0.02, rot=(math.pi / 2, 0, 0))
empty('SOCKET_coolant_out', (0.030, QD_TIP_Y, QZ), col, root, size=0.02, rot=(math.pi / 2, 0, 0))
root['coolant_flow_length_m'] = FLOW_LEN
root['footprint_pcb_mm'] = '200 x 285 x 2.4'

# ---------------------------------------------------------------- finalize
for o in [root] + list(root.children_recursive):
    if o.type == 'MESH':
        H['apply_all'](o)
objs = [root] + list(root.children_recursive)
cool_objs = [cool] + list(cool.children_recursive)
print('TRIS total', tri_count(objs), 'cooling', tri_count(cool_objs), 'flow_len', FLOW_LEN)
mins = [min((o.matrix_world @ Vector(c))[i] for o in objs if o.type == 'MESH' for c in o.bound_box) for i in range(3)]
maxs = [max((o.matrix_world @ Vector(c))[i] for o in objs if o.type == 'MESH' for c in o.bound_box) for i in range(3)]
print('BBOX', [round(v, 4) for v in mins], [round(v, 4) for v in maxs])
glb = BASE + r'\export\gpu_gb200_superchip.glb'
H['export_glb'](ROOT, glb)
print('GLB', os.path.getsize(glb))

setup_render()
cam = bpy.data.objects['Camera']
R = BASE + r'\renders\gb200_superchip_'


def vis(obj_list, show):
    for o in obj_list:
        o.hide_render = not show; o.hide_viewport = not show


look_at(cam, (-0.30, -0.44, 0.36), (0, -0.01, 0.0), lens=50); render(R + '34.png')
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.40
cam.location = (0, -0.012, 0.6); cam.rotation_euler = (0, 0, math.pi / 2); render(R + 'top.png')
look_at(cam, (-0.56, -0.03, 0.25), (0, -0.01, 0.008), lens=50); render(R + 'side.png')
look_at(cam, (0.14, -0.30, 0.13), (0.0, -0.11, 0.012), lens=50); render(R + 'qd_close.png')
vis(cool_objs, False)
look_at(cam, (-0.30, -0.44, 0.36), (0, -0.01, 0.0), lens=50); render(R + 'bare.png')
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.40
cam.location = (0, -0.012, 0.6); cam.rotation_euler = (0, 0, math.pi / 2); render(R + 'bare_top.png')
vis(objs, True)
look_at(cam, (-0.30, -0.44, 0.36), (0, -0.01, 0.0), lens=50)
bpy.ops.wm.save_as_mainfile(filepath=BASE + r'\gpu_14b_gb200_superchip.blend')
print('DONE')
