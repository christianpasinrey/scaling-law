"""NVIDIA NVLink Switch tray for GB200 NVL72 (1U, 2025) - 2x NVLink 5 switch ASICs, 144 NVLink ports.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python srv_07_nvl72_switch_tray.py

Conventions: metres, Z up, front panel XZ at y=0 facing -Y, depth +Y, origin bottom-front-centre.
19" EIA, 1U = 44.45 mm. Body 440 x 43.2 x 875 mm, champagne bezel ears to 482.6 mm (same family as srv_06).
Layout from STH GTC-2024 photos (front: dual RJ45 mgmt, RJ45 RS-232 console, USB-A, LED column + 2 buttons,
perforated grille; inside: 2 switch ASICs mid-rear with teal twinax flyovers to the rear NVLink connector row,
6 fans, PDB modules fed by red/black cables from the centre busbar clip, brass UQDs in the rear corners).
Production trays are liquid cooled: copper cold plates on both ASICs in series (supply left, return right).
"""
import bpy, math, os
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\nvl72_lib.py', encoding='utf-8').read())

ROOT = 'srv_07_nvl72_switch_tray'
root, col = H['new_card_scene'](ROOT)
M = nv_materials()
box, cyl, sa = H['box'], H['cyl'], H['slat_array']

W, HT, D = 0.440, 0.0432, 0.875
HW = W / 2
PZ0, PZ1 = 0.0080, 0.0425
QZ = 0.022

# ------------------------------------------------------------------ chassis + bezel
box('Chassis_Floor', (W, D, 0.0010), (0, D / 2, 0.0005), M['sheet'], col, parent=root)
for s in (-1, 1):
    box(f'Chassis_Side_{"L" if s < 0 else "R"}', (0.0010, D, HT - 0.001), (s * (HW - 0.0005), D / 2, HT / 2), M['sheet'], col, parent=root)
box('Chassis_Rear', (W, 0.0015, HT - 0.001), (0, D - 0.00075, HT / 2), M['sheet'], col, parent=root)
box('Lid_Front', (W, 0.330, 0.0010), (0, 0.165, HT - 0.0005), M['sheet'], col, parent=root)
lid_r = box('Lid_Rear', (W, D - 0.330, 0.0010), (0, 0.330 + (D - 0.330) / 2, HT - 0.0005), M['sheet'], col, parent=root)
sa('Lid_Screws', lambda: (((x, y, HT + 0.0002), (0.004, 0.004, 0.0004)) for x in (-0.2, -0.07, 0.07, 0.2) for y in (0.05, 0.32)),
   M['steel'], col, root)
box('Front_Panel', (0.412, 0.0020, PZ1 - PZ0 + 0.004), (0, 0.0010, (PZ0 + PZ1) / 2), M['panel'], col, parent=root)
grille('Front_Grille', -0.082, 0.206, PZ0, PZ1, -0.0002, M['grille'], col, root, pitch=0.0022)
box('Mgmt_Plate', (0.124, 0.0012, PZ1 - PZ0), (-0.144, -0.0004, (PZ0 + PZ1) / 2), M['panel'], col, parent=root)
for s in (-1, 1):
    box(f'Bezel_Ear_{"L" if s < 0 else "R"}', (0.0293, 0.030, HT - 0.001), (s * (0.2413 - 0.01465), -0.007, HT / 2),
        M['gold'], col, bevel=0.0035, segs=3, parent=root)
    box(f'Bezel_Bar_{"L" if s < 0 else "R"}', (0.2110, 0.0080, 0.0065), (s * (0.0010 + 0.1055), -0.018, 0.0045),
        M['gold'], col, bevel=0.0020, segs=2, parent=root)
    box(f'Bezel_Bar_Post_{"L" if s < 0 else "R"}', (0.0060, 0.016, 0.0050), (s * 0.0045, -0.010, 0.0040), M['gold_dk'], col, parent=root)

# ------------------------------------------------------------------ front management I/O
frames, holes = [], []


def port(x, z, w, h, depth=0.004):
    frames.append(((x, -0.0012, z), (w + 0.0016, depth, h + 0.0016)))
    holes.append(((x, -0.0033, z), (w, 0.0006, h)))


port(-0.180, 0.0178, 0.0160, 0.0135); port(-0.180, 0.0318, 0.0160, 0.0135)   # dual mgmt RJ45 (stacked)
port(-0.156, 0.0255, 0.0160, 0.0135)                                         # RJ45 RS-232 console (115200)
port(-0.139, 0.0255, 0.0060, 0.0130)                                         # USB-A (vertical)
sa('Port_Frames', lambda: iter(frames), M['steel'], col, root)
sa('Port_Holes', lambda: iter(holes), M['rack_hole'], col, root)
for i, (nm, mc) in enumerate((('LED_power', 'led_g'), ('LED_status', 'led_b'), ('LED_fault', 'led_a'), ('LED_uid', 'led_w'))):
    box(nm, (0.0020, 0.0012, 0.0020), (-0.124, -0.0010, 0.0370 - i * 0.0062), M[mc], col, parent=root)
for i, z in enumerate((0.0330, 0.0200)):
    cyl(f'Button_{i}', 0.0024, 0.0020, (-0.112, -0.0010, z), M['black_gl'], col, verts=16, rot=(math.pi / 2, 0, 0), parent=root)
H['text_mesh']('Label_Tray', 'NVLINK SWITCH', FONT, 0.0034, M['label'], col, root, (0.170, -0.0004, 0.0390), (math.pi / 2, 0, 0), extrude=0.0001)

# ------------------------------------------------------------------ front internals: mgmt board, PDB, fans
box('Mgmt_Board', (0.120, 0.150, 0.0016), (-0.140, 0.080, 0.006), M['pcb_g'], col, parent=root)
box('Mgmt_CPU_HS', (0.035, 0.035, 0.012), (-0.120, 0.120, 0.0128), M['fin_dark'], col, parent=root)
for s in (-1, 1):
    box(f'PDB_Module_{s}', (0.045, 0.040, 0.022), (s * 0.030, 0.375, 0.012), M['black_st'], col, bevel=0.001, parent=root)
fans, hubs = [], []
FX = [-0.175, -0.130, -0.022, 0.022, 0.130, 0.175]
for i, x in enumerate(FX):
    fans.append(((x, 0.440, 0.0215), (0.040, 0.056, 0.040)))
    hubs.append(cyl(f'Fan_Hub_{i}', 0.0175, 0.057, (x, 0.440, 0.0215), M['black_mt'], col, verts=20, rot=(math.pi / 2, 0, 0), parent=root))
sa('Fan_Frames', lambda: iter(fans), M['plastic'], col, root)
merge('Fan_Hubs', hubs)
box('Fan_Bracket', (W - 0.002, 0.004, 0.0015), (0, 0.470, 0.0420), M['sheet'], col, parent=root)

# ------------------------------------------------------------------ switch ASICs, spreader plate, cold plates
box('Switch_Board', (0.400, 0.330, 0.0020), (0, 0.660, 0.006), M['pcb_g'], col, parent=root)
box('Stiffener_Plate', (0.390, 0.250, 0.0020), (0, 0.640, 0.0080), M['anod'], col, bevel=0.0008, parent=root)
ASIC = [(-0.075, 0.625), (0.075, 0.625)]
for i, (x, y) in enumerate(ASIC):
    box(f'ASIC{i}_Substrate', (0.075, 0.075, 0.0016), (x, y, 0.0098), M['substrate'], col, bevel=0.0003, parent=root)
    box(f'ASIC{i}_Lid', (0.058, 0.058, 0.0030), (x, y, 0.0121), M['nickel'], col, bevel=0.0006, parent=root)
    box(f'ColdPlate{i}_Base', (0.068, 0.068, 0.0030), (x, y, 0.0151), M['copper'], col, bevel=0.0006, parent=root)
    box(f'ColdPlate{i}_Body', (0.054, 0.054, 0.0060), (x, y, 0.0196), M['copper'], col, bevel=0.0016, parent=root)
    box(f'ColdPlate{i}_Cap', (0.044, 0.044, 0.0012), (x, y, 0.0232), M['copper_dk'], col, bevel=0.0005, parent=root)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f'ColdPlate{i}_Screw{sx}{sy}', 0.0030, 0.0030, (x + sx * 0.029, y + sy * 0.029, 0.0181), M['black_st'], col, verts=16, parent=root)
    for j in range(3):                                          # flyover connector clusters on the substrate edge
        box(f'ASIC{i}_Flyover_{j}', (0.016, 0.010, 0.0060), (x - 0.020 + j * 0.020, y + 0.045, 0.0120), M['plastic'], col, parent=root)
# ------------------------------------------------------------------ rear NVLink connector row + teal twinax flyovers
NVX = [-0.170, -0.130, -0.090, -0.050, 0.050, 0.090, 0.130, 0.170]
for i, x in enumerate(NVX):
    box(f'NVLink_Rear_{i}', (0.036, 0.030, 0.026), (x, D - 0.008, 0.018), M['plastic'], col, bevel=0.0008, parent=root)
    box(f'NVLink_Rear_{i}_Face', (0.028, 0.0010, 0.016), (x, D + 0.0073, 0.018), M['port'], col, parent=root)
    slot(f'SOCKET_nvlink_{i}', (x, D + 0.012, 0.018), col, root, rot=(-math.pi / 2, 0, 0), size=0.02, kind='SINGLE_ARROW')
teal = []
for i, x in enumerate(NVX):
    a = 0 if x < 0 else 1
    ax, ay = ASIC[a]
    for k in (-1, 1):
        sx = ax - 0.020 + (i % 4) * 0.0135 + k * 0.003
        o, _ = tube(f'Twinax_{i}_{k}', [(sx, ay + 0.050, 0.0150), (sx, ay + 0.075, 0.030), ((sx + x) / 2, 0.790, 0.034),
                                       (x + k * 0.006, D - 0.040, 0.026), (x + k * 0.006, D - 0.023, 0.018)],
                    0.0024, M['teal'], col, root, res=6, ring=8)
        teal.append(o)
merge('Twinax_Flyovers', teal)

# ------------------------------------------------------------------ power: busbar clip -> PDB modules (flow UV)
box('Busbar_Clip_Housing', (0.046, 0.030, 0.030), (0, D + 0.012, QZ), M['black_st'], col, bevel=0.0015, parent=root)
for s in (-1, 1):
    box(f'Busbar_Clip_Finger{s}', (0.004, 0.026, 0.024), (s * 0.0065, D + 0.036, QZ), M['tin'], col, bevel=0.0008, parent=root)
clip, u_c = flow_box('Power_1_ClipBar', (0, D + 0.040, QZ), (0, D - 0.030, QZ), 0.010, 0.006, M['busbar'], col, root, u0=0.0)
pw = []
for k, (s, mc) in enumerate(((-1, 'cable_red'), (1, 'black_mt'))):
    o, _ = tube(f'Power_2_Cable_{k}', [(s * 0.004, D - 0.030, QZ), (s * 0.006, 0.780, 0.032), (s * 0.008, 0.560, 0.034),
                                       (s * 0.012, 0.470, 0.030), (s * 0.030, 0.397, 0.020)], 0.0034, M[mc], col, root, u0=u_c)
    pw.append(o)
slot('SOCKET_power_in', (0, D + 0.049, QZ), col, root, rot=(-math.pi / 2, 0, 0), size=0.03, kind='SINGLE_ARROW')

# ------------------------------------------------------------------ coolant: brass UQDs (rear corners) -> ASIC0 -> ASIC1 -> out
QX = 0.200
for s, tag, mc in ((-1, 'in', 'qd_blue'), (1, 'out', 'qd_red')):
    x = s * QX
    cyl(f'UQD_{tag}_Body', 0.0080, 0.050, (x, D, QZ), M['brass'], col, verts=24, rot=(math.pi / 2, 0, 0), bevel=0.0006, parent=root)
    cyl(f'UQD_{tag}_Collar', 0.0094, 0.008, (x, D + 0.016, QZ), M[mc], col, verts=24, rot=(math.pi / 2, 0, 0), parent=root)
    cyl(f'UQD_{tag}_Nose', 0.0055, 0.010, (x, D + 0.030, QZ), M['steel'], col, verts=20, rot=(math.pi / 2, 0, 0), parent=root)
    cyl(f'UQD_{tag}_Flange', 0.0130, 0.0025, (x, D - 0.0025, QZ), M['steel'], col, verts=6, rot=(math.pi / 2, 0, 0), parent=root)
    slot(f'SOCKET_coolant_{tag}', (x, D + 0.035, QZ), col, root, rot=(-math.pi / 2, 0, 0), size=0.03, kind='SINGLE_ARROW')
PZ = 0.0262
ports = {}
for i, (x, y) in enumerate(ASIC):
    for nm, px in (('in', x - 0.016), ('out', x + 0.016)):
        cyl(f'ColdPlate{i}_Fitting_{nm}', 0.0050, 0.0040, (px, y - 0.012, 0.0258), M['steel'], col, verts=6, parent=root)
        ports[(i, nm)] = (px, y - 0.012, 0.0278)
HR = 0.0040
flow = []
p = ports[(0, 'in')]
o, u = tube('Coolant_1_In_ASIC0', [(-QX, D - 0.025, QZ), (-QX, D - 0.050, QZ + 0.006), (-0.205, 0.700, 0.034), (-0.200, 0.540, 0.034),
                                   (p[0] - 0.010, 0.560, 0.034), (p[0], p[1] - 0.004, 0.033), (p[0], p[1], p[2])], HR, M['hose'], col, root, u0=0.0)
flow.append(o)
u += 0.08                                  # through cold plate 0
a, b = ports[(0, 'out')], ports[(1, 'in')]
o, u = tube('Coolant_2_ASIC0_ASIC1', [a, (a[0], a[1] - 0.006, 0.034), (0.0, 0.585, 0.0365), (b[0], b[1] - 0.006, 0.034), b],
            0.0032, M['copper'], col, root, u0=u); flow.append(o)
u += 0.08                                  # through cold plate 1
p = ports[(1, 'out')]
o, u = tube('Coolant_3_ASIC1_Out', [(p[0], p[1], p[2]), (p[0], p[1] - 0.004, 0.033), (p[0] + 0.010, 0.560, 0.034), (0.200, 0.540, 0.034),
                                    (0.205, 0.700, 0.034), (QX, D - 0.050, QZ + 0.006), (QX, D - 0.025, QZ)], HR, M['hose'], col, root, u0=u)
flow.append(o)
for o in flow + pw + [clip]:
    print('FLOW', o.name, round(o['flow_u_start'], 4), round(o['flow_u_end'], 4))

root['standard'] = '19in EIA, 1U = 44.45 mm (NVIDIA MGX NVL72 rack)'
root['size_mm'] = '440 x 43.2 x 875 (body), 482.6 wide at the bezel ears'
root['nvlink'] = '2x NVLink 5 switch ASIC, 72 ports each, 57.6 Tbps full duplex per tray'

finalize_modifiers(root)
objs = tree(root)
print('TRIS tray', tri_count(objs))
print('BBOX', bbox(objs))
glb = BASE + r'\export\srv_07_nvl72_switch_tray.glb'
H['export_glb'](ROOT, glb)
print('GLB', os.path.getsize(glb))

stage(3.2, target=(0, 0.45, 0), floor_z=-0.0005, floor_scale=4)
R = BASE + r'\renders\srv_07_nvl72_switch_tray_'
lid_r.hide_render = True
cam_view(R + '34.png', (-0.75, -0.55, 0.62), (0, 0.42, 0.0), lens=40)
cam = bpy.data.objects['Camera']; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.98
cam.location = (0, 0.44, 1.5); cam.rotation_euler = (0, 0, math.pi / 2); render(R + 'top.png')
cam_view(R + 'rear34.png', (0.55, 1.45, 0.40), (0.0, 0.70, 0.02), lens=40)
cam_view(R + 'front.png', (0, -0.6, 0.022), (0, 0, 0.022), ortho=0.50)
lid_r.hide_render = False
cam_view(R + 'closed34.png', (-0.75, -0.55, 0.62), (0, 0.42, 0.0), lens=40)
bpy.ops.wm.save_as_mainfile(filepath=BASE + r'\srv_07_nvl72_switch_tray.blend')
print('DONE')
