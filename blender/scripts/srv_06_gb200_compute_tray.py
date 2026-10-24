"""NVIDIA GB200 NVL72 compute tray (1U, 2025) - 2x GB200 superchip boards, 4 B200 + 2 Grace.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python srv_06_gb200_compute_tray.py

Conventions (rack-mount, brief phase 2): metres, Z up, front panel in XZ at y=0 facing -Y, depth toward +Y,
origin = bottom-front-centre. Standard: 19" EIA, 1U = 44.45 mm (NVIDIA MGX NVL72 rack).
Body 438 W x 43.2 H x 875 D mm; champagne bezel ears to 482.6 mm and handles 22 mm proud of the panel.
Front I/O laid out from the STH GTC-2024 close-up (2x OSFP CX-7 | 4x E1.S | BMC module | 2x OSFP CX-7 | BF-3).
Rear: busbar clip (centre), 4 NVLink connectors, 2 coolant UQDs (supply left, return right).
Export: no GPU boards - SLOT_superchip_0/1 (board 1 mirrored in X with scale -1, as in the phase-1 report).
"""
import bpy, math, os
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\nvl72_lib.py', encoding='utf-8').read())

ROOT = 'srv_06_gb200_compute_tray'
root, col = H['new_card_scene'](ROOT)
M = nv_materials()
box, cyl, sa = H['box'], H['cyl'], H['slat_array']

W, HT, D = 0.440, 0.0432, 0.875
HW = W / 2
PZ0, PZ1 = 0.0080, 0.0425            # visible front panel band (above the handle bar)
QZ = 0.022                           # rear QD / clip height

# ------------------------------------------------------------------ chassis
box('Chassis_Floor', (W, D, 0.0010), (0, D / 2, 0.0005), M['sheet'], col, parent=root)
for s in (-1, 1):
    box(f'Chassis_Side_{"L" if s < 0 else "R"}', (0.0010, D, HT - 0.001), (s * (HW - 0.0005), D / 2, HT / 2), M['sheet'], col, parent=root)
box('Chassis_Rear', (W, 0.0015, HT - 0.001), (0, D - 0.00075, HT / 2), M['sheet'], col, parent=root)
box('Lid_Front', (W, 0.420, 0.0010), (0, 0.210, HT - 0.0005), M['sheet'], col, parent=root)
lid_r = box('Lid_Rear', (W, D - 0.420, 0.0010), (0, 0.420 + (D - 0.420) / 2, HT - 0.0005), M['sheet'], col, parent=root)
sa('Lid_Screws', lambda: (((x, y, HT + 0.0002), (0.004, 0.004, 0.0004)) for x in (-0.2, -0.07, 0.07, 0.2) for y in (0.05, 0.41)),
   M['steel'], col, root)
box('Front_Panel', (0.412, 0.0020, PZ1 - PZ0 + 0.004), (0, 0.0010, (PZ0 + PZ1) / 2), M['panel'], col, parent=root)
grille('Front_Grille', -0.206, 0.206, PZ0, PZ1, -0.0002, M['grille'], col, root, pitch=0.0022)

# ------------------------------------------------------------------ champagne bezel (ears + split handle bar)
for s in (-1, 1):
    box(f'Bezel_Ear_{"L" if s < 0 else "R"}', (0.0293, 0.030, HT - 0.001), (s * (0.2413 - 0.01465), -0.007, HT / 2),
        M['gold'], col, bevel=0.0035, segs=3, parent=root)
    box(f'Bezel_Bar_{"L" if s < 0 else "R"}', (0.2110, 0.0080, 0.0065), (s * (0.0010 + 0.1055), -0.018, 0.0045),
        M['gold'], col, bevel=0.0020, segs=2, parent=root)
    box(f'Bezel_Bar_Post_{"L" if s < 0 else "R"}', (0.0060, 0.016, 0.0050), (s * 0.0045, -0.010, 0.0040), M['gold_dk'], col, parent=root)

# ------------------------------------------------------------------ front ports
frames, holes, darks = [], [], []


def port(x, z, w, h, depth=0.004, inner=None):
    frames.append(((x, -0.0012 + depth / 2 - 0.002, z), (w + 0.0016, depth, h + 0.0016)))
    holes.append(((x, -0.0033, z), (w, 0.0006, h)))


# OSFP cages (CX-7, single port each, stacked) - left and centre-right
for x in (-0.157, 0.061):
    for z in (0.0158, 0.0318):
        port(x, z, 0.0225, 0.0130)
        frames.append(((x, 0.032, z), (0.0225, 0.064, 0.0130)))          # cage body behind the panel
# E1.S carriers (4, vertical)
for i in range(4):
    x = -0.1255 + i * 0.0115
    darks.append(((x, -0.0010, 0.0250), (0.0098, 0.0030, 0.0310)))
    frames.append(((x, -0.0026, 0.0350), (0.0060, 0.0010, 0.0045)))     # latch
box('E1S_Cage', (0.050, 0.130, 0.036), (-0.108, 0.067, 0.022), M['sheet'], col, parent=root)
# centre BMC / DC-SCM module plate
box('BMC_Plate', (0.066, 0.0016, 0.0280), (-0.012, -0.0010, 0.0255), M['module'], col, bevel=0.0006, parent=root)
port(-0.036, 0.0270, 0.0160, 0.0135)       # RJ45 BMC
port(0.012, 0.0270, 0.0160, 0.0135)        # RJ45 (BF-3 BMC)
port(-0.0195, 0.0270, 0.0090, 0.0035)      # USB-C
port(-0.0055, 0.0270, 0.0075, 0.0050)      # mini-DP
# BlueField-3: RJ45 + 2x QSFP112
port(0.110, 0.0230, 0.0160, 0.0135)
for x in (0.137, 0.162):
    port(x, 0.0230, 0.0190, 0.0090)
    frames.append(((x, 0.030, 0.023), (0.0190, 0.058, 0.0090)))
sa('Port_Frames', lambda: iter(frames), M['steel'], col, root)
sa('Port_Holes', lambda: iter(holes), M['rack_hole'], col, root)
sa('E1S_Carriers', lambda: iter(darks), M['black_mt'], col, root)
# RJ45 link LEDs are part of the frames; status LEDs are separate (game-driven)
for nm, x, mc in (('LED_power', 0.080, 'led_g'), ('LED_status', 0.085, 'led_b'), ('LED_fault', 0.090, 'led_a')):
    box(nm, (0.0022, 0.0012, 0.0022), (x, -0.0008, 0.0385), M[mc], col, parent=root)
H['text_mesh']('Label_Tray', 'GB200', FONT, 0.0040, M['label'], col, root, (0.185, -0.0004, 0.0390), (math.pi / 2, 0, 0), extrude=0.0001)

# ------------------------------------------------------------------ front-zone internals
for x in (-0.157, 0.061):                   # CX-7 NIC cards (2 levels)
    for z in (0.0060, 0.0225):
        box(f'NIC_{x:+.3f}_{z:.3f}', (0.060, 0.110, 0.0016), (x + 0.012, 0.115, z), M['pcb_g'], col, parent=root)
        box(f'NIC_HS_{x:+.3f}_{z:.3f}', (0.030, 0.030, 0.0080), (x + 0.012, 0.130, z + 0.0048), M['alu'], col, parent=root)
box('BF3_Card', (0.105, 0.165, 0.0016), (0.140, 0.095, 0.0055), M['pcb_g'], col, parent=root)
box('BF3_Heatsink', (0.050, 0.060, 0.0180), (0.140, 0.120, 0.0153), M['fin_dark'], col, parent=root)
box('BMC_Board', (0.075, 0.120, 0.0016), (-0.012, 0.064, 0.0080), M['pcb_g'], col, parent=root)
box('M2_Boot', (0.022, 0.080, 0.0030), (0.015, 0.200, 0.0060), M['pcb_g'], col, parent=root)
box('Front_Bulkhead', (W - 0.002, 0.0010, 0.034), (0, 0.250, 0.019), M['sheet'], col, parent=root)
# fan wall: 8x 40x40x56 mm
fans, hubs = [], []
for i in range(8):
    x = -0.175 + i * 0.050
    fans.append(((x, 0.328, 0.0215), (0.040, 0.056, 0.040)))
fw = sa('Fan_Frames', lambda: iter(fans), M['plastic'], col, root)
for i in range(8):
    x = -0.175 + i * 0.050
    hubs.append(cyl(f'Fan_Hub_{i}', 0.0175, 0.057, (x, 0.328, 0.0215), M['black_mt'], col, verts=20, rot=(math.pi / 2, 0, 0), parent=root))
merge('Fan_Hubs', hubs)
box('Fan_Bracket', (W - 0.002, 0.004, 0.0015), (0, 0.358, 0.0420), M['sheet'], col, parent=root)

# ------------------------------------------------------------------ superchip slots + standoffs
BX, BY, BZ = 0.099, 0.645, 0.008
s0 = slot('SLOT_superchip_0', (-BX, BY, BZ), col, root, size=0.05)
s1 = slot('SLOT_superchip_1', (BX, BY, BZ), col, root, scale=(-1, 1, 1), size=0.05)
so = []
for sx in (-1, 1):
    for u in (-0.085, 0.085):
        for v in (-0.120, 0.0, 0.120):
            so.append(((sx * BX + u, BY + v, 0.0045), (0.005, 0.005, 0.007)))
sa('Board_Standoffs', lambda: iter(so), M['tin'], col, root)


def board_pt(p, mirror):
    x, y, z = p
    return ((BX if mirror else -BX) + (-x if mirror else x), BY + y, BZ + z)


# board socket world positions (phase-1 GB200_Superchip report / blend)
B_IN = [board_pt((-0.030, -0.1655, 0.015), m) for m in (0, 1)]
B_OUT = [board_pt((0.030, -0.1655, 0.015), m) for m in (0, 1)]
B_PWR = [board_pt((-0.1175, -0.012, 0.0058), m) for m in (0, 1)]

# ------------------------------------------------------------------ rear: NVLink connectors (4) + flyover cables
NVX = [-BX - 0.0365, -BX + 0.035, BX - 0.035, BX + 0.0365]
for i, x in enumerate(NVX):
    box(f'NVLink_Rear_{i}', (0.052, 0.034, 0.026), (x, D - 0.006, 0.018), M['plastic'], col, bevel=0.0010, parent=root)
    box(f'NVLink_Rear_{i}_Face', (0.040, 0.0010, 0.016), (x, D + 0.0112, 0.018), M['port'], col, parent=root)
    for s in (-1, 1):
        cyl(f'NVLink_Rear_{i}_Pin{s}', 0.0018, 0.012, (x + s * 0.0225, D + 0.016, 0.018), M['steel'], col, verts=12,
            rot=(math.pi / 2, 0, 0), parent=root)
    box(f'NVLink_Flyover_{i}', (0.040, 0.066, 0.0035), (x, 0.826, 0.030), M['black_mt'], col, bevel=0.0010, parent=root)
    slot(f'SOCKET_nvlink_{i}', (x, D + 0.022, 0.018), col, root, rot=(-math.pi / 2, 0, 0), size=0.02, kind='SINGLE_ARROW')

# ------------------------------------------------------------------ power: busbar clip -> PDB -> board cables
box('Busbar_Clip_Housing', (0.046, 0.030, 0.030), (0, D + 0.012, QZ), M['black_st'], col, bevel=0.0015, parent=root)
for s in (-1, 1):
    box(f'Busbar_Clip_Finger{s}', (0.004, 0.026, 0.024), (s * 0.0065, D + 0.036, QZ), M['tin'], col, bevel=0.0008, parent=root)
clip, u_pdb = flow_box('Power_1_ClipBar', (0, D + 0.040, QZ), (0, 0.800, QZ), 0.010, 0.006, M['busbar'], col, root, u0=0.0)
box('PDB_Board', (0.060, 0.050, 0.0016), (0, 0.800, 0.006), M['pcb_g'], col, parent=root)
box('PDB_Block', (0.050, 0.030, 0.016), (0, 0.800, 0.015), M['black_st'], col, bevel=0.001, parent=root)
pw_paths = []
for k in (0, 1):
    s = -1 if k == 0 else 1
    bx, by, bz = B_PWR[k]
    ctrl = [(s * 0.024, 0.795, 0.024), (s * 0.060, 0.842, 0.0375), (s * 0.150, 0.844, 0.0375), (s * 0.208, 0.830, 0.0370),
            (s * 0.2135, 0.760, 0.0360), (s * 0.2140, 0.670, 0.0300), (bx - s * 0.002, by + 0.004, bz + 0.016), (bx - s * 0.0005, by + 0.001, bz + 0.004), (bx, by, bz)]
    o, ue = tube(f'Power_2_Cable_{k}', ctrl, 0.0028, M['cable_red'], col, root, u0=u_pdb)
    pw_paths.append(o)
    slot(f'SOCKET_power_out_board{k}', (bx, by, bz), col, root, rot=(0, -math.pi / 2 if k == 0 else math.pi / 2, 0), size=0.02,
         kind='SINGLE_ARROW')
slot('SOCKET_power_in', (0, D + 0.049, QZ), col, root, rot=(-math.pi / 2, 0, 0), size=0.03, kind='SINGLE_ARROW')

# ------------------------------------------------------------------ coolant: rear UQDs, splitter, hoses to the board QDs
QX = 0.200
for s, tag, mc in ((-1, 'in', 'qd_blue'), (1, 'out', 'qd_red')):
    x = s * QX
    cyl(f'UQD_{tag}_Body', 0.0080, 0.050, (x, D, QZ), M['brass'], col, verts=24, rot=(math.pi / 2, 0, 0), bevel=0.0006, parent=root)
    cyl(f'UQD_{tag}_Collar', 0.0094, 0.008, (x, D + 0.016, QZ), M[mc], col, verts=24, rot=(math.pi / 2, 0, 0), parent=root)
    cyl(f'UQD_{tag}_Nose', 0.0055, 0.010, (x, D + 0.030, QZ), M['steel'], col, verts=20, rot=(math.pi / 2, 0, 0), parent=root)
    cyl(f'UQD_{tag}_Flange', 0.0130, 0.0025, (x, D - 0.0025, QZ), M['steel'], col, verts=6, rot=(math.pi / 2, 0, 0), parent=root)
    slot(f'SOCKET_coolant_{tag}', (x, D + 0.035, QZ), col, root, rot=(-math.pi / 2, 0, 0), size=0.03, kind='SINGLE_ARROW')
# female couplers on the board QD noses
CPL = 0.020
for k in (0, 1):
    for p, mc, nm in ((B_IN[k], 'qd_blue', 'in'), (B_OUT[k], 'qd_red', 'out')):
        cyl(f'Board{k}_Coupler_{nm}', 0.0082, CPL, (p[0], p[1] - CPL / 2, p[2]), M['steel'], col, verts=20, rot=(math.pi / 2, 0, 0), parent=root)
        cyl(f'Board{k}_Coupler_{nm}_Ring', 0.0088, 0.004, (p[0], p[1] - 0.006, p[2]), M[mc], col, verts=20, rot=(math.pi / 2, 0, 0), parent=root)
# tees
for s, nm in ((-1, 'Supply'), (1, 'Return')):
    box(f'Hose_Tee_{nm}', (0.016, 0.016, 0.012), (s * 0.160, 0.440, 0.030), M['stainless'], col, bevel=0.0015, parent=root)
HR = 0.0045
flow = []
yb = B_IN[0][1] - CPL          # hose end = coupler back
# supply trunk: rear UQD in -> tee
o, u_s = tube('Coolant_1_Supply_Trunk', [(-QX, D - 0.025, QZ), (-QX, D - 0.045, QZ + 0.004), (-0.207, 0.80, 0.034), (-0.207, 0.53, 0.034),
                                        (-0.196, 0.460, 0.032), (-0.168, 0.440, 0.030)], HR, M['hose'], col, root, u0=0.0); flow.append(o)
o, _ = tube('Coolant_2_Supply_Board0', [(-0.152, 0.440, 0.030), (-0.136, 0.446, 0.028), (B_IN[0][0], 0.452, 0.025), (B_IN[0][0], yb, B_IN[0][2])],
            HR, M['hose'], col, root, u0=u_s); flow.append(o)
o, _ = tube('Coolant_2_Supply_Board1', [(-0.160, 0.432, 0.030), (-0.120, 0.426, 0.0345), (0.100, 0.426, 0.0345), (B_IN[1][0], 0.440, 0.029),
                                       (B_IN[1][0], yb, B_IN[1][2])], HR, M['hose'], col, root, u0=u_s); flow.append(o)
o, u_r0 = tube('Coolant_3_Return_Board0', [(B_OUT[0][0], yb, B_OUT[0][2]), (B_OUT[0][0], 0.440, 0.028), (-0.040, 0.414, 0.0305),
                                          (0.120, 0.414, 0.0305), (0.160, 0.432, 0.030)], HR, M['hose'], col, root, u0=0.0); flow.append(o)
o, u_r1 = tube('Coolant_3_Return_Board1', [(B_OUT[1][0], yb, B_OUT[1][2]), (B_OUT[1][0] + 0.004, 0.444, 0.028), (0.130, 0.440, 0.030),
                                          (0.152, 0.440, 0.030)], HR, M['hose'], col, root, u0=0.0); flow.append(o)
o, _ = tube('Coolant_4_Return_Trunk', [(0.168, 0.440, 0.030), (0.196, 0.460, 0.032), (0.207, 0.53, 0.034), (0.207, 0.80, 0.034),
                                      (QX, D - 0.045, QZ + 0.004), (QX, D - 0.025, QZ)], HR, M['hose'], col, root, u0=max(u_r0, u_r1)); flow.append(o)
for k in (0, 1):
    slot(f'SOCKET_coolant_out_board{k}', B_IN[k], col, root, rot=(math.pi / 2, 0, 0), size=0.02, kind='SINGLE_ARROW')
    slot(f'SOCKET_coolant_in_board{k}', B_OUT[k], col, root, rot=(math.pi / 2, 0, 0), size=0.02, kind='SINGLE_ARROW')
for o in flow + pw_paths + [clip]:
    print('FLOW', o.name, round(o['flow_u_start'], 4), round(o['flow_u_end'], 4))

root['standard'] = '19in EIA, 1U = 44.45 mm (NVIDIA MGX NVL72 rack)'
root['size_mm'] = '440 x 43.2 x 875 (body), 482.6 wide at the bezel ears'
root['tdp_w'] = 6300

# ------------------------------------------------------------------ finalize + export
finalize_modifiers(root)
objs = tree(root)
print('TRIS tray', tri_count(objs))
print('BBOX', bbox(objs))
glb = BASE + r'\export\srv_06_gb200_compute_tray.glb'
H['export_glb'](ROOT, glb)
print('GLB', os.path.getsize(glb))

# ------------------------------------------------------------------ previews with the phase-1 boards appended
prev = H['coll']('Preview_Boards')
b0 = append_tree(BASE + r'\gpu_14b_gb200_superchip.blend', 'GB200_Superchip')
b1 = dup_tree(b0, b0.users_collection[0])
bpy.context.view_layer.update()
b0.matrix_world = s0.matrix_world.copy(); b1.matrix_world = s1.matrix_world.copy()
b0.name = 'PREVIEW_Superchip_0'; b1.name = 'PREVIEW_Superchip_1'
bpy.context.view_layer.update()
print('TRIS boards', tri_count(tree(b0)) * 2)

stage(3.2, target=(0, 0.45, 0), floor_z=-0.0005, floor_scale=4)
R = BASE + r'\renders\srv_06_gb200_compute_tray_'
lid_r.hide_render = True
cam_view(R + '34.png', (-0.75, -0.55, 0.62), (0, 0.42, 0.0), lens=40)
cam = bpy.data.objects['Camera']; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.98
cam.location = (0, 0.44, 1.5); cam.rotation_euler = (0, 0, math.pi / 2); render(R + 'top.png')
cam_view(R + 'rear34.png', (0.55, 1.45, 0.40), (0.0, 0.70, 0.02), lens=40)
cam_view(R + 'front.png', (0, -0.6, 0.022), (0, 0, 0.022), ortho=0.50)
cam_view(R + 'front_close.png', (-0.06, -0.30, 0.09), (-0.06, 0, 0.022), lens=50)
lid_r.hide_render = False
cam_view(R + 'closed34.png', (-0.75, -0.55, 0.62), (0, 0.42, 0.0), lens=40)
bpy.ops.wm.save_as_mainfile(filepath=BASE + r'\srv_06_gb200_compute_tray.blend')
print('DONE')
