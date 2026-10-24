"""Garage rig 1 (game start, 2017): ATX mid-tower deep-learning workstation, 2x GTX 1080 Ti.

Case modelled on the NZXT H440 (2014-2017 "New Edition"; black with red accents):
  220 W x 475 H x 510 D mm incl. feet, 7 slots, PSU shroud with NZXT plate, cable cover panel,
  3x120 mm front fans + 1x140 mm rear fan, tinted acrylic window, top-front I/O notch.
Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python <this file> [-- view ...]

World frame (room item): origin = floor, centre of footprint; front panel faces -Y, window side -X,
motherboard tray on +X, Z up.
Card pose (derived from gpu_01_gtx1080ti_fe.blend): card X (length, bracket at 0) -> world -Y,
card Y (PCB normal, cooler at -Y) -> world +Z, card Z (height, fingers down) -> world -X.
"""
import bpy, math, mathutils, sys

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\garage_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']
G = bpy.app.driver_namespace['GL']
V = mathutils.Vector

ROOT = 'Rig01_Tower2017'
OUT_BLEND = r'C:\laragon\www\scaling-law\blender\rig_01_tower_2017.blend'
OUT_GLB = r'C:\laragon\www\scaling-law\blender\export\rig_01_tower_2017.glb'
OUT_REN = r'C:\laragon\www\scaling-law\blender\renders\rig_01_tower_2017_{}.png'
FONT_B = r'C:\Windows\Fonts\segoeuib.ttf'
FONT_LOGO = r'C:\Windows\Fonts\bahnschrift.ttf'

root, col = H['new_card_scene'](ROOT)
M = H['base_materials']()
G['garage_materials'](M, accent=(0.60, 0.015, 0.02))
mat = H['mat']
M['case'] = mat('T1_CaseBlack', (0.012, 0.012, 0.013), 0.35, 0.42, spec=0.4)
M['case_in'] = mat('T1_InteriorBlack', (0.010, 0.010, 0.011), 0.2, 0.6, spec=0.3)
M['glass'] = mat('T1_AcrylicTint', (0.03, 0.03, 0.035), 0.0, 0.04, alpha=0.22)
M['mesh'] = mat('T1_FilterMesh', (0.004, 0.004, 0.004), 0.0, 0.9, spec=0.05)
M['logo'] = mat('T1_LogoSilver', (0.80, 0.80, 0.82), 0.9, 0.25)
M['psu_body'] = mat('T1_PSUBlack', (0.015, 0.015, 0.016), 0.5, 0.45)
box, cyl, cut = H['box'], H['cyl'], H['cut']
basis = G['basis']

# ---------------------------------------------------------------- key dimensions (m)
X0, X1 = -0.110, 0.110
YF, YR = -0.255, 0.255
ZB, ZT = 0.012, 0.475           # body bottom (on 12 mm feet) / top
SK = 0.0012                     # panel thickness
TRAY_X = 0.0850                 # tray front face
BOARD_X = TRAY_X - 0.0064 - 0.0016   # PCB component surface (6.4 mm standoffs)
BOARD_REAR_Y, BOARD_BOT_Z = 0.236, 0.135
SHROUD_Z = 0.1045
CARD_Y0 = 0.2495                # card origin (bracket x=0) in world Y
CARD_X0 = BOARD_X - 0.0024 - 0.0085   # card z=0 plane in world X (finger bottom z=-0.0085 sits 2.4 mm over the PCB)
GPU_POS = (2, 5)                # expansion positions of the two x16 slots used
X16_START = BOARD_REAR_Y - (CARD_Y0 - 0.026) - 0.0015

# ---------------------------------------------------------------- shell
box('Case_Bottom', (X1 - X0, YR - YF, SK), (0, 0, ZB + SK / 2), M['case'], col, parent=root)
box('Case_PanelRight', (SK, YR - YF, ZT - ZB), (X1 - SK / 2, 0, (ZB + ZT) / 2), M['case'], col, parent=root)
left = box('Case_PanelLeft', (SK, YR - YF, ZT - ZB), (X0 + SK / 2, 0, (ZB + ZT) / 2), M['case'], col, parent=root)
WIN = (-0.083, 0.207, 0.040, 0.406)   # window y0, y1, z0, z1 (measured off the side photo)
c = box('cutter', (0.02, WIN[1] - WIN[0], WIN[3] - WIN[2]), (X0, (WIN[0] + WIN[1]) / 2, (WIN[2] + WIN[3]) / 2), M['case'], col)
cut(left, c)
box('Case_Window', (0.0006, WIN[1] - WIN[0] + 0.012, WIN[3] - WIN[2] + 0.012),
    (X0 + SK + 0.0004, (WIN[0] + WIN[1]) / 2, (WIN[2] + WIN[3]) / 2), M['glass'], col, parent=root)
# window rubber gasket
box_g = G['box_array']
box_g('Case_WindowGasket', [((X0 + 0.0003, (WIN[0] + WIN[1]) / 2, WIN[2] - 0.0015), (0.0008, WIN[1] - WIN[0] + 0.006, 0.003)),
                            ((X0 + 0.0003, (WIN[0] + WIN[1]) / 2, WIN[3] + 0.0015), (0.0008, WIN[1] - WIN[0] + 0.006, 0.003)),
                            ((X0 + 0.0003, WIN[0] - 0.0015, (WIN[2] + WIN[3]) / 2), (0.0008, 0.003, WIN[3] - WIN[2] + 0.006)),
                            ((X0 + 0.0003, WIN[1] + 0.0015, (WIN[2] + WIN[3]) / 2), (0.0008, 0.003, WIN[3] - WIN[2] + 0.006))],
      M['rubber'], col, root)

# top panel + top-front I/O notch (chamfer between the side panels)
CH_Y = -0.215
box('Case_Top', (X1 - X0, YR - CH_Y, SK), (0, (YR + CH_Y) / 2, ZT - SK / 2), M['case'], col, parent=root)
ang = math.atan2(0.020, 0.040)
ch_len = math.hypot(0.040, 0.020)
# built at the origin then rotated/moved: hw.box bakes its location into the mesh in 5.2
chamfer = box('Case_TopChamfer', (X1 - X0 - 2 * SK, ch_len, SK), (0, 0, 0), M['case'], col, parent=root)
chamfer.rotation_euler = (ang, 0, 0)
chamfer.location = (0, (YF + CH_Y) / 2, ZT - 0.010 - SK / 2)
# top side vent strips (mesh)
box_g('Case_TopVents', [((sx * 0.1005, 0.020, ZT + 0.0001), (0.009, 0.420, 0.0004)) for sx in (-1, 1)], M['mesh'], col, root)
# front panel with intake gaps on both sides
box('Case_Front', (0.208, 0.003, 0.452 - 0.014), (0, YF + 0.0015, (0.014 + 0.452) / 2), M['case'], col, bevel=0.0008, parent=root)
box_g('Case_FrontIntake', [((sx * 0.1062, YF + 0.004, (0.014 + 0.452) / 2), (0.0045, 0.002, 0.452 - 0.020)) for sx in (-1, 1)], M['mesh'], col, root)
box_g('Case_Accent', [((0, YF + 0.0012, 0.4535), (0.218, 0.0024, 0.003)),
                      ((X0 - 0.0002, YF + 0.003, (ZB + 0.455) / 2), (0.0006, 0.004, 0.455 - ZB)),
                      ((X1 + 0.0002, YF + 0.003, (ZB + 0.455) / 2), (0.0006, 0.004, 0.455 - ZB))], M['accent'], col, root)
# top I/O on the chamfer: local frame x across, y up the slope, z = outward normal
io = G['frame_empty']('TopIO', col, root, (0, (YF + CH_Y) / 2, ZT - 0.010), basis((1, 0, 0), (0, math.cos(ang), math.sin(ang))))
ports = [((-0.060 + i * 0.016, 0, 0.0004), (0.0125, 0.0055, 0.002)) for i in range(4)]
box_g('IO_USBShells', ports, M['steel'], col, io)
box_g('IO_USBTongues', [((-0.060 + i * 0.016, 0, 0.0012), (0.010, 0.0016, 0.0008)) for i in range(4)],
      M['usb'], col, io)
G['cyl_array']('IO_Audio', [((0.012 + i * 0.012, 0, 0.0002), 0.0028, 0.0012, 'z') for i in range(2)], M['port'], col, io, segs=16)
cyl('IO_PowerButton', 0.0075, 0.0025, (0.075, 0, 0.0010), M['case'], col, verts=32, parent=io)
led_ring = H['ring']('LED_power', [(0.0095 * math.cos(2 * math.pi * k / 32) + 0.075, 0.0095 * math.sin(2 * math.pi * k / 32)) for k in range(32)],
                     [(0.0078 * math.cos(2 * math.pi * k / 32) + 0.075, 0.0078 * math.sin(2 * math.pi * k / 32)) for k in range(32)],
                     'xy', 0.0, 0.0006, M['led_w'], col, parent=io)
box('LED_hdd', (0.003, 0.0015, 0.0006), (0.052, 0, 0.0003), M['led_w'], col, parent=io)
# feet
box_g('Case_Feet', [((sx * 0.080, sy * 0.205, ZB / 2), (0.040, 0.070, ZB)) for sx in (-1, 1) for sy in (-1, 1)], M['rubber'], col, root)

# rear panel with apertures
rear = box('Case_Rear', (X1 - X0 - 2 * SK, SK, ZT - ZB - SK), (0, YR - SK / 2, (ZB + ZT) / 2), M['case'], col, parent=root)
IO_X0, IO_X1 = BOARD_X - 0.0445, BOARD_X + 0.001
IO_Z0, IO_Z1 = BOARD_BOT_Z + 0.305 - 0.162, BOARD_BOT_Z + 0.305 - 0.003
cut(rear, box('cutter', (IO_X1 - IO_X0, 0.02, IO_Z1 - IO_Z0), ((IO_X0 + IO_X1) / 2, YR, (IO_Z0 + IO_Z1) / 2), M['case'], col))
SL_X0, SL_X1 = CARD_X0 - 0.1085, CARD_X0 + 0.0035
slot_z = {k: BOARD_BOT_Z + G['slot_y'](k) for k in range(1, 8)}
SL_Z0, SL_Z1 = slot_z[7] - 0.0178, slot_z[1] + 0.0030
cut(rear, box('cutter', (SL_X1 - SL_X0, 0.02, SL_Z1 - SL_Z0), ((SL_X0 + SL_X1) / 2, YR, (SL_Z0 + SL_Z1) / 2), M['case'], col))
FAN_R = (-0.036, 0.367)        # rear 140 mm fan centre (x, z)
cut(rear, cyl('cutter', 0.066, 0.02, (FAN_R[0], YR, FAN_R[1]), M['case'], col, verts=48, rot=(math.pi / 2, 0, 0)))
PSU_X, PSU_W, PSU_H, PSU_L = -0.005, 0.150, 0.086, 0.150
PSU_Z = ZB + SK + 0.0013
cut(rear, box('cutter', (PSU_W + 0.002, 0.02, PSU_H + 0.002), (PSU_X, YR, PSU_Z + PSU_H / 2), M['case'], col))
# rear fan grille rings
for k, r in enumerate((0.064, 0.048, 0.032, 0.016)):
    n = 40
    H['ring'](f'Case_RearGrille{k}', [(r * math.cos(2 * math.pi * i / n) + FAN_R[0], r * math.sin(2 * math.pi * i / n) + FAN_R[1]) for i in range(n)],
              [((r - 0.002) * math.cos(2 * math.pi * i / n) + FAN_R[0], (r - 0.002) * math.sin(2 * math.pi * i / n) + FAN_R[1]) for i in range(n)],
              'xz', YR - SK, SK, M['case'], col, parent=root)
box_g('Case_RearGrilleBars', [((FAN_R[0], YR - SK / 2, FAN_R[1]), (0.130, SK, 0.003)), ((FAN_R[0], YR - SK / 2, FAN_R[1]), (0.003, SK, 0.130))], M['case'], col, root)
# I/O shield
shield = box('Case_IOShield', (IO_X1 - IO_X0, 0.0008, IO_Z1 - IO_Z0), ((IO_X0 + IO_X1) / 2, YR - 0.0004, (IO_Z0 + IO_Z1) / 2), M['steel'], col, parent=root)
# slot area: separators + vented covers on the unused positions
used = set()
for k in GPU_POS:
    used |= {k, k + 1}
sep = []
for k in range(1, 8):
    sep.append((((SL_X0 + SL_X1) / 2, YR - 0.002, slot_z[k] + 0.0030 + 0.0006), (SL_X1 - SL_X0, 0.004, 0.0012)))
box_g('Case_SlotSeparators', sep, M['case'], col, root)
covers = [(((SL_X0 + SL_X1) / 2, YR - 0.0025, slot_z[k] - 0.0074), (SL_X1 - SL_X0 - 0.004, 0.0009, 0.0185)) for k in range(1, 8) if k not in used]
box_g('Case_SlotCovers', covers, M['steel'], col, root)
vents = []
for k in range(1, 8):
    if k in used:
        continue
    for i in range(9):
        vents.append(((SL_X0 + 0.012 + i * 0.010, YR - 0.0019, slot_z[k] - 0.0074), (0.006, 0.0004, 0.010)))
box_g('Case_SlotCoverVents', vents, M['port'], col, root)
box_g('Case_SlotScrews', [((SL_X1 + 0.006, YR + 0.0008, slot_z[k] - 0.002), (0.006, 0.002, 0.006)) for k in range(1, 8)], M['steel'], col, root)
box('Case_SlotRail', (0.012, 0.012, SL_Z1 - SL_Z0 + 0.010), (SL_X1 + 0.006, YR - 0.006, (SL_Z0 + SL_Z1) / 2), M['case'], col, parent=root)

# ---------------------------------------------------------------- interior structure
box('Tray', (0.0016, YR - (-0.071), 0.470 - 0.105), (TRAY_X + 0.0008, (YR + -0.071) / 2, (0.105 + 0.470) / 2), M['case_in'], col, parent=root)
box_g('Tray_Grommets', [((TRAY_X - 0.0003, -0.040, z), (0.0016, 0.022, 0.060)) for z in (0.170, 0.290, 0.410)] +
      [((TRAY_X - 0.0003, 0.190, 0.4585), (0.0016, 0.060, 0.012))], M['rubber'], col, root)
box('CableCover', (0.002, -0.071 - (-0.236), 0.470 - SHROUD_Z), (0.079, (-0.071 + -0.236) / 2, (0.470 + SHROUD_Z) / 2), M['case_in'], col, parent=root)
box_g('CableCover_Slots', [((0.0778, y, z), (0.0006, 0.012, 0.012)) for y in (-0.195, -0.115) for z in (0.150, 0.230, 0.310, 0.390, 0.450)], M['port'], col, root)
# PSU shroud
box('Shroud_Top', (TRAY_X - (-0.101), YR - (-0.222), 0.0015), ((TRAY_X - 0.101) / 2, (YR - 0.222) / 2, SHROUD_Z - 0.00075), M['case_in'], col, parent=root)
box('Shroud_Side', (0.0015, YR - (-0.222), SHROUD_Z - ZB), (-0.101, (YR - 0.222) / 2, (SHROUD_Z + ZB) / 2), M['case_in'], col, parent=root)
box('Shroud_Plate', (0.0008, 0.240, 0.060), (-0.1019, -0.030, 0.060), M['accent'], col, bevel=0.0003, parent=root)
G['text_at']('Shroud_Logo', 'NZXT', FONT_LOGO, 0.040, M['logo'], col, root, (-0.1026, -0.030, 0.0600), (0, -1, 0), (0, 0, 1), extrude=0.0003)
box('Shroud_CableHole', (0.032, 0.040, 0.0004), (0.066, -0.040, SHROUD_Z + 0.0002), M['port'], col, parent=root)
box('Shroud_CableHole2', (0.016, 0.050, 0.0004), (0.076, 0.060, SHROUD_Z + 0.0002), M['port'], col, parent=root)
# front fan bracket rails
box_g('FrontFanRails', [((sx * 0.066, YF + 0.0185, 0.235), (0.006, 0.012, 0.400)) for sx in (-1, 1)], M['case_in'], col, root)

# ---------------------------------------------------------------- fans
for i, z in enumerate((0.110, 0.235, 0.360)):
    G['fan'](f'Fan_Front{i}', col, root, M, 0.120, 0.025, 7, loc=(0.0, -0.2245 - 0.0125 + 0.0, z), rot3=basis((-1, 0, 0), (0, 0, 1)))
G['fan']('Fan_Rear', col, root, M, 0.140, 0.025, 7, loc=(FAN_R[0], YR - SK - 0.0135, FAN_R[1]), rot3=basis((-1, 0, 0), (0, 0, 1)))

# ---------------------------------------------------------------- PSU + motherboard
psu_e, P = G['psu'](
    'PSU', col, root, M, loc=(PSU_X, YR - 0.0015, PSU_Z), rot3=basis((-1, 0, 0), (0, -1, 0)), length=PSU_L,
    brand='EVGA', model='SUPERNOVA 1000 G3', font_b=FONT_B, ports=8)
mb_e, MB = G['motherboard'](
    'Motherboard', col, root, M, loc=(BOARD_X, BOARD_REAR_Y, BOARD_BOT_Z), rot3=basis((0, -1, 0), (0, 0, 1)),
    slot_types=('x1', 'x16', 'x1', 'x1', 'x16', 'x1', 'x16'), cooler='tower', x16_start=X16_START)
cyl_s = [((TRAY_X - 0.0032, BOARD_REAR_Y - x, BOARD_BOT_Z + y), 0.0028, 0.0064, 'x') for x, y in
         ((0.006, 0.010), (0.006, 0.295), (0.163, 0.010), (0.163, 0.295), (0.238, 0.010), (0.238, 0.295), (0.163, 0.155), (0.006, 0.155))]
G['cyl_array']('Motherboard_Standoffs', cyl_s, M['gold'], col, root, segs=8)

# ---------------------------------------------------------------- GPU slots (exported as empties)
card_rot = basis((0, -1, 0), (0, 0, 1))
slots = []
for i, k in enumerate(GPU_POS):
    z_conn = slot_z[k]
    s = G['marker'](f'SLOT_gpu_{i}', col, root, (CARD_X0, CARD_Y0, z_conn - 0.0008), card_rot, size=0.05)
    s['pcie_position'] = k
    s['card_frame'] = 'phase-1 card frame: X length from bracket, Y PCB normal (cooler -Y), Z height'
    slots.append(s)

# ---------------------------------------------------------------- power: sockets + flow cables
def sock(name, p, d):
    """Socket empty at p whose +Z points along d (flow direction out of the source / into the load)."""
    q = V(d).to_track_quat('Z', 'Y').to_matrix()
    e = G['marker'](name, col, root, p, q, kind='SINGLE_ARROW', size=0.03)
    return e


sock('SOCKET_power_in', P['inlet'], (0, 1, 0))
ports_w = [root.matrix_world.inverted() @ p for p in P['ports']]
out_dir = V((0, -1, 0))
cables = []


def cable(name, pts, r=0.0048, flat=0.55, mat_=None):
    o = G['flow_cable'](name, pts, r, mat_ or M['cable'], col, root, sides=8, flat=flat)
    cables.append(o)
    return o


for i, k in enumerate(GPU_POS):
    z0 = slot_z[k] - 0.0008
    tgt = V((CARD_X0 - 0.1105, CARD_Y0 - 0.236, z0 - 0.0095))      # card SOCKET_power_in mapped to world
    zs = tgt.z
    p = ports_w[i]
    pts = [p, p + out_dir * 0.020, V((0.050 - 0.012 * i, 0.010, 0.070)), V((0.066 - 0.006 * i, -0.038, 0.100)),
           V((0.066 - 0.006 * i, -0.042, 0.130)), V((0.064 - 0.006 * i, -0.042, zs - 0.020)),
           V((0.020, -0.040, zs)), V((-0.060, -0.034, zs)), V((-0.074, -0.004, zs)),
           V((-0.066, tgt.y, zs)), tgt]
    cable(f'Cable_GPU_{i}', pts)
    sock(f'SOCKET_power_out_gpu_{i}', tgt, (1, 0, 0))
    # plug housings (8-pin + 6-pin side by side along the card edge)
    box_g(f'Plug_GPU_{i}', [((tgt.x - 0.007, tgt.y - 0.006, zs), (0.014, 0.0105, 0.0085)),
                            ((tgt.x - 0.007, tgt.y + 0.006, zs), (0.014, 0.0080, 0.0085))], M['plastic'], col, root)

t24 = V(MB['atx24'])
p = ports_w[4]
cable('Cable_ATX24', [p, p + out_dir * 0.020, V((0.040, 0.010, 0.065)), V((0.072, -0.050, 0.100)), V((0.072, -0.052, 0.150)),
                      V((0.068, -0.048, 0.300)), V((0.050, -0.022, t24.z)), V((0.047, t24.y - 0.002, t24.z)), t24], r=0.011, flat=0.40)
sock('SOCKET_power_out_mobo', t24, (1, 0, 0))
box('Plug_ATX24', (0.016, 0.012, 0.052), (t24.x - 0.008, t24.y, t24.z), M['plastic'], col, parent=root)
t8 = V(MB['eps8'])
p = ports_w[5]
cable('Cable_EPS8', [p, p + out_dir * 0.020, V((0.060, 0.070, 0.060)), V((0.096, 0.060, 0.095)), V((0.097, 0.090, 0.250)),
                     V((0.097, 0.170, 0.440)), V((0.080, 0.190, 0.4585)), V((0.066, t8.y, t8.z + 0.012)), t8], r=0.0050, flat=0.6)
sock('SOCKET_power_out_cpu', t8, (1, 0, 0))
box('Plug_EPS8', (0.016, 0.020, 0.010), (t8.x - 0.008, t8.y, t8.z), M['plastic'], col, parent=root)

# ---------------------------------------------------------------- tidy, save, export
for o in col.objects:
    if o is not root and o.parent is None:
        o.parent = root
# window pane / glass must not hide the interior in the game: keep it, flagged
bpy.data.objects['Case_Window']['transparent'] = True
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
tris = H['export_glb'](ROOT, OUT_GLB)
# re-export with extras so flow_u_start / flow_u_end / flow_kind reach the game (selection left by export_glb)
bpy.ops.export_scene.gltf(filepath=OUT_GLB, use_selection=True, export_apply=True, export_extras=True)
print('TRIS', tris)
for c_ in cables:
    print('CABLE', c_.name, c_['flow_u_end'])
for s in slots:
    print('SLOT', s.name, tuple(round(v, 4) for v in s.matrix_world.translation), tuple(round(math.degrees(a), 2) for a in s.matrix_world.to_euler()))
for o in root.children_recursive:
    if o.name.startswith('SOCKET'):
        print('SOCK', o.name, tuple(round(v, 4) for v in o.matrix_world.translation))

# ---------------------------------------------------------------- previews (with appended cards)
only = None
if '--' in sys.argv:
    a = sys.argv[sys.argv.index('--') + 1:]
    only = set(a) if a else None
G['append_cards'](slots)
G['setup_studio'](2.2, (0.0, 0.0, 0.24))
views = {
    'threeq':  ((-0.95, -1.05, 0.70), (0.0, 0.0, 0.225), 45),
    'side':    ((-1.45, 0.0, 0.25), (0.0, 0.0, 0.24), 50),
    'front':   ((0.45, -1.25, 0.55), (0.0, 0.0, 0.23), 45),
    'rear':    ((0.55, 1.20, 0.55), (0.0, 0.1, 0.23), 45),
}
G['render_views'](views, OUT_REN, only)
# interior views: side panel off
for nm in ('Case_PanelLeft', 'Case_Window', 'Case_WindowGasket'):
    bpy.data.objects[nm].hide_render = True
G['render_views']({
    'open':    ((-1.00, -0.55, 0.55), (0.0, 0.03, 0.26), 45),
    'opendet': ((-0.55, -0.30, 0.42), (0.0, 0.08, 0.25), 38),
}, OUT_REN, only)
print('DONE')
