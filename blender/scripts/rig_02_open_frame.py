"""Garage rig 2 (2018-2019): open-air aluminium multi-GPU frame, 6 cards on PCIe risers.

Modelled on the generic 6/8-GPU "Veddha-style" stackable frames sold 2017-2019
(listing size 640 x 365 x 380 mm, 20x20 mm aluminium extrusion, ATX board + 2 PSUs on the
lower deck, cards standing on USB-riser boards with their brackets screwed to the top front rail,
4x120 mm fans pushing air along the cards).
Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python <this file> [-- view ...]

World frame (room item): origin = floor, centre of the footprint; card brackets / front rail at -Y,
fans at +Y, PSU AC inlets at +X, Z up.
Card pose: card X (length, bracket at 0) -> world +Y, card Y (PCB normal, cooler at -Y) -> world -X,
card Z (height, fingers down) -> world +Z  (= rotation Z +90 deg).
"""
import bpy, math, mathutils, sys

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\garage_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']
G = bpy.app.driver_namespace['GL']
V = mathutils.Vector

ROOT = 'Rig02_OpenFrame'
OUT_BLEND = r'C:\laragon\www\scaling-law\blender\rig_02_open_frame.blend'
OUT_GLB = r'C:\laragon\www\scaling-law\blender\export\rig_02_open_frame.glb'
OUT_REN = r'C:\laragon\www\scaling-law\blender\renders\rig_02_open_frame_{}.png'
FONT_B = r'C:\Windows\Fonts\segoeuib.ttf'

root, col = H['new_card_scene'](ROOT)
M = H['base_materials']()
G['garage_materials'](M, accent=(0.75, 0.55, 0.02))
mat = H['mat']
M['ext'] = mat('F2_ExtrusionAlu', (0.70, 0.71, 0.73), 1.0, 0.38, aniso=0.3)
M['groove'] = mat('F2_ExtrusionGroove', (0.10, 0.10, 0.11), 1.0, 0.5)
M['bracket'] = mat('F2_BracketBlack', (0.02, 0.02, 0.022), 0.6, 0.45)
M['riser'] = mat('F2_RiserPCB', (0.02, 0.06, 0.20), 0.0, 0.45)
box, cyl = H['box'], H['cyl']
basis, box_g = G['basis'], G['box_array']

# ---------------------------------------------------------------- dimensions (m)
FL, FW, FH, E = 0.640, 0.365, 0.380, 0.020
PX, PY = FL / 2 - E / 2, FW / 2 - E / 2           # post centres
MID_Z = 0.243                                      # riser-rail level (centre)
TOP_Z = FH - E / 2
N_GPU = 6
PITCH = 0.085
CARD_X = [-0.235 + PITCH * i for i in range(N_GPU)]   # card PCB plane (card y=0)
CARD_Y0 = -0.157                                       # bracket (card x=0)
RISER_PCB_Z = MID_Z + E / 2 + 0.003                    # riser PCB bottom (3 mm standoffs)
RISER_TOP = RISER_PCB_Z + 0.0016
CARD_Z0 = RISER_TOP + 0.0024 + 0.0085                  # finger bottom 2.4 mm over the riser PCB
DECK_Z = E                                             # deck rails top
BOARD_Z = DECK_Z + 0.0064 + 0.0016                     # PCB top surface

# ---------------------------------------------------------------- frame (merged extrusions)
bars = []


def bar(p0, p1):
    bars.append((V(p0), V(p1)))


for sx in (-1, 1):
    for sy in (-1, 1):
        bar((sx * PX, sy * PY, 0), (sx * PX, sy * PY, FH))                         # posts
for z in (E / 2, MID_Z, TOP_Z):
    for sx in (-1, 1):
        bar((sx * PX, -PY + E / 2, z), (sx * PX, PY - E / 2, z))                    # side bars (Y)
for z in (E / 2, TOP_Z):
    for sy in (-1, 1):
        bar((-PX + E / 2, sy * PY, z), (PX - E / 2, sy * PY, z))                    # front/back rails (X)
bar((-PX + E / 2, PY, MID_Z), (PX - E / 2, PY, MID_Z))                              # rear mid rail (fan bar)
RISER_RAIL_Y = CARD_Y0 + 0.070
bar((-PX + E / 2, RISER_RAIL_Y, MID_Z), (PX - E / 2, RISER_RAIL_Y, MID_Z))          # riser rail
bar((-PX + E / 2, 0.100, MID_Z), (PX - E / 2, 0.100, MID_Z))                        # card tail support
for y in (-0.085, 0.120):
    bar((-PX + E / 2, y, E / 2), (PX - E / 2, y, E / 2))                            # deck rails


def ext_items():
    for a, b in bars:
        c = (a + b) / 2; d = b - a
        ax = max(range(3), key=lambda i: abs(d[i]))
        s = [E, E, E]; s[ax] = abs(d[ax])
        yield tuple(c), tuple(s)


def groove_items():
    for a, b in bars:
        c = (a + b) / 2; d = b - a
        ax = max(range(3), key=lambda i: abs(d[i]))
        L = abs(d[ax]) - 0.004
        for o in range(3):
            if o == ax:
                continue
            for sgn in (-1, 1):
                cc = list(c); cc[o] += sgn * (E / 2 + 0.0001)
                s = [0.0062, 0.0062, 0.0062]; s[ax] = L; s[o] = 0.0004
                yield tuple(cc), tuple(s)


box_g('Frame_Extrusions', list(ext_items()), M['ext'], col, root)
box_g('Frame_Grooves', list(groove_items()), M['groove'], col, root)
# corner brackets (black cast L-brackets at the post joints)
cb = []
for sx in (-1, 1):
    for sy in (-1, 1):
        for z in (E, MID_Z + E / 2, TOP_Z - E / 2):
            cb.append(((sx * (PX - 0.018), sy * PY, z + (0.008 if z != TOP_Z - E / 2 else -0.008)), (0.016, 0.021, 0.016)))
box_g('Frame_CornerBrackets', cb, M['bracket'], col, root)
box_g('Frame_Feet', [((sx * PX, sy * PY, -0.0) , (0.030, 0.030, 0.001)) for sx in (-1, 1) for sy in (-1, 1)], M['rubber'], col, root)

# ---------------------------------------------------------------- lower deck: motherboard + 2 PSUs
mb_e, MB = G['motherboard'](
    'Motherboard', col, root, M, loc=(-0.300, 0.140, BOARD_Z), rot3=basis((0, -1, 0), (1, 0, 0)),
    slot_types=('x1', 'x16', 'x1', 'x1', 'x16', 'x1', 'x16'), cooler='stock')
G['cyl_array']('Motherboard_Standoffs', [((x, y, DECK_Z + 0.0032), 0.0028, 0.0064, 'z') for x in (-0.290, -0.150, -0.005) for y in (-0.085, 0.120)],
               M['gold'], col, root, segs=8)
PSU_L = 0.200
psus = []
for j, yc in enumerate((-0.085, 0.085)):
    e, P = G['psu'](f'PSU_{j}', col, root, M, loc=(0.300, yc, DECK_Z), rot3=basis((0, 1, 0), (-1, 0, 0)),
                    length=PSU_L, brand='EVGA', model='SUPERNOVA 1600 G2', font_b=FONT_B, ports=8)
    psus.append(P)

# ---------------------------------------------------------------- risers + USB adapters
riser_pcb, riser_slot, riser_6p, riser_usb, riser_caps, leds = [], [], [], [], [], []
for i, x in enumerate(CARD_X):
    riser_pcb.append(((x - 0.007, CARD_Y0 + 0.075, RISER_PCB_Z + 0.0008), (0.046, 0.110, 0.0016)))
    riser_slot.append(((x - 0.0008, CARD_Y0 + 0.0245 + 0.04575, RISER_TOP + 0.0056), (0.0084, 0.0915, 0.0112)))
    riser_6p.append(((x - 0.020, -0.040, RISER_TOP + 0.0065), (0.009, 0.014, 0.013)))
    riser_usb.append(((x - 0.020, -0.130, RISER_TOP + 0.0035), (0.013, 0.014, 0.0065)))
    riser_caps += [((x - 0.026, y, RISER_TOP + 0.004), 0.003, 0.008, 'z') for y in (-0.105, -0.080)]
    leds.append(box(f'LED_riser_{i}', (0.003, 0.002, 0.0012), (x - 0.012, -0.060, RISER_TOP + 0.0006), M['led_b'], col, parent=root))
box_g('Riser_PCBs', riser_pcb, M['riser'], col, root)
box_g('Riser_x16Slots', riser_slot, M['plastic'], col, root)
box_g('Riser_6pin', riser_6p, M['plastic'], col, root)
box_g('Riser_USB', riser_usb, M['usb'], col, root)
G['cyl_array']('Riser_Caps', riser_caps, M['cap'], col, root, segs=10)
G['cyl_array']('Riser_Standoffs', [((x - 0.007 + dx, RISER_RAIL_Y, MID_Z + E / 2 + 0.0015), 0.0025, 0.003, 'z') for x in CARD_X for dx in (-0.015, 0.015)],
               M['steel'], col, root, segs=8)
adapters = []; adapter_top = []
for i in range(N_GPU):
    k = i + 1
    xs = -0.300 + G['slot_y'](k)
    adapters.append(((xs, 0.115, BOARD_Z + 0.0112 + 0.010), (0.0016, 0.024, 0.020)))
    adapter_top.append(V((xs, 0.115, BOARD_Z + 0.0112 + 0.026)))
box_g('USBAdapter_PCBs', adapters, M['riser'], col, root)
box_g('USBAdapter_Ports', [(tuple(p - V((0, 0, 0.003))), (0.0065, 0.013, 0.012)) for p in adapter_top], M['usb'], col, root)

# ---------------------------------------------------------------- fans on the rear rail
for i, xf in enumerate((-0.195, -0.065, 0.065, 0.195)):
    G['fan'](f'Fan_{i}', col, root, M, 0.120, 0.025, 7, loc=(xf, PY - E / 2 - 0.0125 - 0.0005, 0.305), rot3=basis((1, 0, 0), (0, 0, 1)))
box_g('Fan_Clips', [((xf, PY - E / 2 - 0.004, z), (0.030, 0.008, 0.012)) for xf in (-0.195, -0.065, 0.065, 0.195) for z in (0.362, 0.249)], M['bracket'], col, root)
# frame power button
box('Frame_PowerSwitch', (0.020, 0.012, 0.010), (-0.250, -PY - E / 2 - 0.006, TOP_Z), M['plastic'], col, parent=root)
cyl('Frame_PowerButton', 0.0045, 0.004, (-0.250, -PY - E / 2 - 0.0125, TOP_Z), M['plastic'], col, verts=24, rot=(math.pi / 2, 0, 0), parent=root)
H['ring']('LED_power', [(0.0058 * math.cos(2 * math.pi * k / 24) - 0.250, 0.0058 * math.sin(2 * math.pi * k / 24) + TOP_Z) for k in range(24)],
          [(0.0047 * math.cos(2 * math.pi * k / 24) - 0.250, 0.0047 * math.sin(2 * math.pi * k / 24) + TOP_Z) for k in range(24)],
          'xz', -PY - E / 2 - 0.0125, 0.0006, M['led_b'], col, parent=root)

# ---------------------------------------------------------------- GPU slots
card_rot = basis((0, 1, 0), (-1, 0, 0))
slots = []
for i, x in enumerate(CARD_X):
    s = G['marker'](f'SLOT_gpu_{i}', col, root, (x, CARD_Y0, CARD_Z0), card_rot, size=0.05)
    s['card_frame'] = 'phase-1 card frame: X length from bracket, Y PCB normal (cooler -Y), Z height'
    slots.append(s)


# ---------------------------------------------------------------- power: sockets + flow cables
def sock(name, p, d):
    q = V(d).to_track_quat('Z', 'Y').to_matrix()
    return G['marker'](name, col, root, p, q, kind='SINGLE_ARROW', size=0.03)


cables = []


def cable(name, pts, r=0.0042, flat=0.6, m=None, kind='power'):
    o = G['flow_cable'](name, pts, r, m or M['cable'], col, root, sides=8, flat=flat)
    o['flow_kind'] = kind
    cables.append(o)
    return o


for j, P in enumerate(psus):
    sock(f'SOCKET_power_in_{j}', P['inlet'], (-1, 0, 0))
OUT = V((-1, 0, 0))
plugs = []
for i, x in enumerate(CARD_X):
    P = psus[0 if i < 3 else 1]
    p = P['ports'][i % 3]
    tgt = V((x - CARD_POWER_IN.y, CARD_Y0 + CARD_POWER_IN.x, CARD_Z0 + CARD_POWER_IN.z))
    cx = tgt.x
    cable(f'Cable_GPU_{i}', [p, p + OUT * 0.020, V((0.060, p.y * 0.6 + 0.04, 0.110)), V((cx, 0.125, 0.200)),
                             V((cx, 0.126, 0.360)), V((cx, 0.104, 0.408)), V((cx, tgt.y + 0.002, 0.396)), tgt])
    sock(f'SOCKET_power_out_gpu_{i}', tgt, (0, 0, -1))
    plugs += [((cx, tgt.y - 0.006, tgt.z + 0.007), (0.0085, 0.0105, 0.014)), ((cx, tgt.y + 0.006, tgt.z + 0.007), (0.0085, 0.008, 0.014))]
    # riser power (6-pin) dropping between the cards
    p = P['ports'][4 + i % 3]
    rx = x - 0.020
    rt = V((rx, -0.040, RISER_TOP + 0.013 + 0.008))
    cable(f'Cable_Riser_{i}', [p, p + OUT * 0.020, V((0.050, p.y * 0.6 + 0.02, 0.130)), V((rx, 0.124, 0.200)), V((rx, 0.124, 0.330)),
                               V((rx, 0.060, 0.338)), V((rx, -0.022, 0.318)), V((rx, -0.040, rt.z + 0.010)), rt], r=0.0036)
    sock(f'SOCKET_power_out_riser_{i}', rt, (0, 0, -1))
    plugs.append(((rx, -0.040, rt.z), (0.0105, 0.016, 0.016)))
    # USB 3.0 data cable: motherboard x1 adapter -> riser board
    a = adapter_top[i]
    ue = V((rx, -0.139, RISER_TOP + 0.0035))
    cable(f'Data_USB_riser_{i}', [a, a + V((0, 0, 0.030)), V((a.x * 0.6 + rx * 0.4, 0.000, 0.150)), V((rx, -0.165, 0.200)),
                                  V((rx, -0.162, 0.248)), V((rx, -0.150, ue.z)), ue], r=0.0024, flat=1.0, m=M['usb'], kind='data')
t24 = V(MB['atx24']); p = psus[0]['ports'][3]
cable('Cable_ATX24', [p, p + OUT * 0.020, V((0.000, -0.105, 0.100)), V((-0.085, -0.098, 0.080)), V((t24.x, t24.y, t24.z + 0.022)), t24], r=0.010, flat=0.4)
sock('SOCKET_power_out_mobo', t24, (0, 0, -1))
plugs.append(((t24.x, t24.y, t24.z + 0.006), (0.054, 0.012, 0.014)))
t8 = V(MB['eps8']); p = psus[0]['ports'][7]
cable('Cable_EPS8', [p, p + OUT * 0.020, V((0.040, 0.040, 0.110)), V((0.000, 0.095, 0.080)), V((t8.x, t8.y, t8.z + 0.020)), t8], r=0.0045)
sock('SOCKET_power_out_cpu', t8, (0, 0, -1))
plugs.append(((t8.x, t8.y, t8.z + 0.006), (0.012, 0.021, 0.014)))
box_g('Plugs', plugs, M['plastic'], col, root)

# ---------------------------------------------------------------- tidy, save, export
for o in col.objects:
    if o is not root and o.parent is None:
        o.parent = root
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
G['setup_studio'](2.6, (0.0, 0.0, 0.19))
views = {
    'threeq':  ((-1.05, -1.25, 0.85), (0.0, 0.0, 0.18), 42),
    'front':   ((0.0, -1.55, 0.42), (0.0, 0.0, 0.19), 45),
    'back34':  ((1.10, 1.05, 0.80), (0.0, 0.0, 0.17), 42),
    'top':     ((0.0, -0.25, 1.65), (0.0, 0.0, 0.15), 40),
    'riser':   ((-0.46, -0.52, 0.42), (-0.12, -0.08, 0.25), 40),
    'deck':    ((0.75, -0.55, 0.35), (-0.05, 0.0, 0.08), 40),
}
G['render_views'](views, OUT_REN, only)
print('DONE')
