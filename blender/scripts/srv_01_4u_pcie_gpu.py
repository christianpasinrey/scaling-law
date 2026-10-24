"""4U 8x PCIe GPU server (2017-2023) - modelled on the Supermicro SuperServer SYS-4029GP-TRT
(chassis CSE-418GTS-R4000BP2, board X11DPG-OT-CPU, dual Xeon Scalable, 8 double-width PCIe GPUs behind a
PCIe-switch daughterboard, 24x 2.5" front bays, 8x 92 mm hot-swap fans mid-chassis, 4x 2000 W PSUs at the rear).

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python C:\\laragon\\www\\scaling-law\\blender\\scripts\\srv_01_4u_pcie_gpu.py
  (env SRV_VIEWS=front,rear,... renders a subset)

Rack-mount convention (BRIEF_SERVERS_RACKS.md): metres, Z up, origin bottom-front-centre, front panel in the XZ plane
at y=0 facing -Y, depth toward +Y. EIA 19" rack: ears 482.6 mm, body 437 mm, 4U = 177.8 mm, depth 737 mm.

Layout (Supermicro product photos front/rear/top/angle via Broadberry + IT Creations):
  front:  24x 2.5" bays (3 cages of 8) in the lower ~80 mm, perforated intake grille above, control panel on the
          left ear (power button + status LEDs), SUPERMICRO badge on the right ear, handles on both ears.
  y 0.18-0.27: fan wall, 2 rows x 4 fans 92 mm.
  y 0.28-0.44: CPU board, 2 sockets with passive 2U heatsinks, 12 DIMMs per CPU, DIMMs parallel to airflow.
  y 0.44-0.74: PCIe switch daughterboard on top of the 4 PSUs; GPUs stand vertically (PCB vertical, fingers down),
          4 left + 4 right, brackets at the rear; middle 5 slot positions = 2x x8 + 1x x4 + blanks.
  rear:   21 slot positions over 4 PSUs (2+2) with the rear I/O between them.
"""
import bpy, bmesh, math, mathutils, os

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']

BASE = r'C:\laragon\www\scaling-law\blender'
FILE = 'srv_01_4u_pcie_gpu'
ROOT = 'SRV_4U_PCIe_GPU'
FONT_BOLD = r'C:\Windows\Fonts\arialbd.ttf'
FONT_BLACK = r'C:\Windows\Fonts\ariblk.ttf'
V = mathutils.Vector

root, col = H['new_card_scene'](ROOT)
root.empty_display_size = 0.2
M = H['base_materials']()
mat = H['mat']
CH = mat('SRV_ChassisSteel', (0.48, 0.49, 0.50), 0.85, 0.36)
CH_IN = mat('SRV_ChassisInner', (0.36, 0.37, 0.38), 0.8, 0.45)
BLK = mat('SRV_BlackPowder', (0.012, 0.012, 0.013), 0.1, 0.55, spec=0.3)
HOLE = mat('SRV_Hole', (0.002, 0.002, 0.002), 0.0, 1.0, spec=0.0)
PCB_MB = mat('SRV_PCB_Board', (0.012, 0.045, 0.040), 0.0, 0.45)
PCB_GB = mat('SRV_PCB_GPUBoard', (0.020, 0.090, 0.035), 0.0, 0.42)
PCB_DIMM = mat('SRV_PCB_DIMM', (0.015, 0.085, 0.030), 0.0, 0.45)
CHIP = mat('SRV_Chip', (0.010, 0.010, 0.011), 0.0, 0.35)
YEL = mat('SRV_YellowLabel', (0.80, 0.62, 0.05), 0.0, 0.5)
WHITE = mat('SRV_WhitePlastic', (0.75, 0.75, 0.72), 0.0, 0.45)
RED = mat('SRV_RedLatch', (0.60, 0.08, 0.07), 0.0, 0.45)
PINK = mat('SRV_PSULatch', (0.78, 0.20, 0.32), 0.0, 0.45)
BLUE = mat('SRV_BluePort', (0.02, 0.10, 0.45), 0.0, 0.45)
COPPER = mat('SRV_Copper', (0.86, 0.45, 0.26), 1.0, 0.30)
CABLE = mat('SRV_PowerCable', (0.020, 0.020, 0.022), 0.0, 0.55, spec=0.3)
PSU_FACE = mat('SRV_PSUFace', (0.30, 0.31, 0.32), 0.9, 0.35)
LED_G = mat('SRV_LED_Green', (0.1, 1.0, 0.25), 0.0, 0.3, emit=(0.1, 1.0, 0.25), emit_str=6.0)
LED_B = mat('SRV_LED_Blue', (0.1, 0.35, 1.0), 0.0, 0.3, emit=(0.1, 0.35, 1.0), emit_str=6.0)
LED_A = mat('SRV_LED_Amber', (1.0, 0.45, 0.05), 0.0, 0.3, emit=(1.0, 0.45, 0.05), emit_str=6.0)
TXT = mat('SRV_BadgeText', (0.75, 0.75, 0.76), 0.6, 0.35)
TXT_RED = mat('SRV_BadgeRed', (0.70, 0.04, 0.04), 0.0, 0.4)

# ---------------------------------------------------------------- dimensions (Supermicro spec page)
W2 = 0.437 / 2        # body half width
EAR = 0.4826 / 2      # ear outer half width
D = 0.737             # depth
HT = 0.1778           # 4U
T = 0.0010            # sheet thickness
P = 0.02032           # PCIe slot pitch
NPOS = 21             # rear slot positions: 8 + 5 + 8 (rear photo)
X0 = -NPOS * P / 2
Y_BR = 0.722          # card x=0 plane; bracket plate at +3 mm, tab tip at D-1 mm
Z_PSU0, Z_PSU1 = 0.002, 0.042           # 1U PSU modules (40 mm)
Z_GB0, Z_GB1 = 0.0440, 0.0456           # PCIe switch daughterboard
ZS = Z_GB1 + 0.0155   # card z=0 (finger bottom -12.5 mm sits 3 mm above the board)
Z_MB0, Z_MB1 = 0.0060, 0.0076           # CPU board
Y_FAN = (0.180, 0.230)                  # fan rows (front face of each 38 mm fan)
Z_FANC = 0.126
CPU = [(-0.112, 0.349), (0.082, 0.349)]
PSU_X = [-0.172, -0.096, 0.096, 0.172]
PSU_W, PSU_Y0 = 0.0735, 0.472
GPU_POS = [0, 2, 4, 6, 13, 15, 17, 19]  # first slot position of each double-width GPU
NIC_POS = [(9, 8), (10, 8), (11, 4)]    # (position, lanes)
A100_PWR = V((0.276, -0.014, 0.072))     # A100 PCIe SOCKET_power_in in card space
BUS_Y, BUS_Z = 0.428, 0.036


def B(name, mn, mx, m, parent=None, bevel=0.0):
    c = [(a + b) / 2 for a, b in zip(mn, mx)]
    s = [b - a for a, b in zip(mn, mx)]
    return H['box'](name, s, c, m, col, bevel=bevel, parent=parent or root)


def boxes(name, items, m, parent=None):
    def gen():
        for mn, mx in items:
            yield [(a + b) / 2 for a, b in zip(mn, mx)], [b - a for a, b in zip(mn, mx)]
    return H['slat_array'](name, gen, m, col, parent or root)


def empty(name, loc, rot=(0, 0, 0), kind='ARROWS', size=0.03, **props):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind; e.empty_display_size = size
    e.location = loc; e.rotation_euler = rot
    col.objects.link(e); e.parent = root
    for k, v in props.items():
        e[k] = v
    return e


def join(name, objs):
    for o in objs:
        H['apply_all'](o)
    bpy.context.view_layer.update()   # matrix_world of freshly rotated objects is stale until an update
    with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs, object=objs[0]):
        bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


Mt = mathutils.Matrix


def mboxes(name, mats, m, parent=None):
    """Unit cubes transformed by full 4x4 matrices (rotated parts), merged into one mesh.
    (hw.box bakes the location into the mesh, so rotating its object would orbit the world origin.)"""
    bm = bmesh.new()
    for mx in mats:
        bmesh.ops.create_cube(bm, size=1, matrix=mx)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(m)
    col.objects.link(o); o.parent = parent or root
    return o


def circle(r, n, cx=0.0, cy=0.0, a0=0.0):
    return [(cx + r * math.cos(a0 + 2 * math.pi * k / n), cy + r * math.sin(a0 + 2 * math.pi * k / n)) for k in range(n)]


def square_loop(h, n):
    """n points on a square of half side h, same angular order as circle(r, n)."""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        c, s = math.cos(a), math.sin(a)
        f = h / max(abs(c), abs(s))
        pts.append((c * f, s * f))
    return pts


# ---------------------------------------------------------------- flow sweep (power paths)
def fillet(pts, r, seg=6):
    pts = [V(p) for p in pts]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        d1 = (p0 - p1).normalized(); d2 = (p2 - p1).normalized()
        ang = d1.angle(d2)
        if ang > math.pi - 1e-3:
            out.append(p1); continue
        t = r / math.tan(ang / 2)
        t = min(t, 0.45 * (p0 - p1).length, 0.45 * (p2 - p1).length)
        a, b = p1 + d1 * t, p1 + d2 * t
        for k in range(seg + 1):
            s = k / seg
            out.append((1 - s) ** 2 * a + 2 * (1 - s) * s * p1 + s * s * b)
    out.append(pts[-1])
    return out


def flow_sweep(name, pts, profile, m, u0=0.0, r=0.006, parent=None, kind='power'):
    """Sweep a closed 2D profile along a filleted polyline. UV u = u0 + metres along the path (continuous),
    v = 0..1 around the profile. Custom props flow_u_start/flow_u_end for the pulse shader."""
    path = fillet(pts, r)
    n = len(profile)
    tans = []
    for i in range(len(path)):
        a = path[max(i - 1, 0)]; b = path[min(i + 1, len(path) - 1)]
        tans.append((b - a).normalized())
    up = V((0, 0, 1)) if abs(tans[0].z) < 0.9 else V((1, 0, 0))
    nrm = (up - tans[0] * up.dot(tans[0])).normalized()
    bm = bmesh.new(); rings = []; us = []; s = 0.0
    for i, p in enumerate(path):
        if i:
            s += (p - path[i - 1]).length
            q = tans[i - 1].rotation_difference(tans[i])
            nrm = (q @ nrm); nrm = (nrm - tans[i] * nrm.dot(tans[i])).normalized()
        bi = tans[i].cross(nrm)
        rings.append([bm.verts.new(p + nrm * pa + bi * pb) for pa, pb in profile])
        us.append(u0 + s)
    uv = bm.loops.layers.uv.new('UVMap')
    for i in range(len(path) - 1):
        for k in range(n):
            j = (k + 1) % n
            f = bm.faces.new((rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]))
            vk, vj = k / n, (k + 1) / n
            for loop, (uu, vv) in zip(f.loops, ((us[i], vk), (us[i], vj), (us[i + 1], vj), (us[i + 1], vk))):
                loop[uv].uv = (uu, vv)
    for ring_, uu in ((list(reversed(rings[0])), us[0]), (rings[-1], us[-1])):
        f = bm.faces.new(ring_)
        for loop in f.loops:
            loop[uv].uv = (uu, 0.5)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(m)
    col.objects.link(o); o.parent = parent or root
    o['flow_u_start'] = round(u0, 5); o['flow_u_end'] = round(u0 + s, 5); o['flow_kind'] = kind
    return o, u0 + s


def tube(r, n=8):
    return circle(r, n)


def rect(w, h):
    return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]


# ================================================================= CHASSIS
B('Chassis_Floor', (-W2, 0, 0), (W2, D, T), CH)
B('Chassis_Side_L', (-W2, 0, 0), (-W2 + T, D, HT - T), CH)
B('Chassis_Side_R', (W2 - T, 0, 0), (W2, D, HT - T), CH)
# fixed front top cover with the pressed round dimples of the photos
cov = [((-W2, 0.0, HT - T), (W2, 0.185, HT))]
B('Chassis_TopCover', (-W2, 0.0, HT - T), (W2, 0.185, HT), CH)
dimples = []
for x in (-0.15, -0.05, 0.05, 0.15):
    for y in (0.05, 0.14):
        dimples.append(H['cyl']('Dimple', 0.0075, 0.0006, (x + (0.02 if y > 0.1 else 0), y, HT + 0.0002), CH_IN, col, verts=20, parent=root))
join('Chassis_TopCover_Dimples', dimples)
# side-wall rails toward the rear (lid slides over them)
B('Chassis_LidRail_L', (-W2 + T, 0.185, HT - 0.012), (-W2 + 0.004, D, HT - T), CH_IN)
B('Chassis_LidRail_R', (W2 - 0.004, 0.185, HT - 0.012), (W2 - T, D, HT - T), CH_IN)

# ---------------------------------------------------------------- lid (removable)
lid_items = [((-W2 - 0.0006, 0.1855, HT - T), (W2 + 0.0006, D, HT)),
             ((-W2 - 0.0016, 0.1855, HT - 0.020), (-W2 - 0.0006, D, HT)),
             ((W2 + 0.0006, 0.1855, HT - 0.020), (W2 + 0.0016, D, HT)),
             ((-W2 - 0.0006, D - T, HT - 0.006), (W2 + 0.0006, D, HT))]
lid = boxes('Lid', lid_items, CH)
B('Lid_Latch', (-0.035, 0.205, HT), (0.035, 0.228, HT + 0.0012), BLK, parent=lid, bevel=0.0005)
B('Lid_LatchButton', (-0.012, 0.209, HT + 0.0012), (0.012, 0.224, HT + 0.0020), CH_IN, parent=lid)
B('Lid_Label', (0.06, 0.30, HT), (0.17, 0.36, HT + 0.0002), WHITE, parent=lid)
H['text_mesh']('Lid_Label_Text', 'CAUTION  HOT SWAP FANS', FONT_BOLD, 0.0055, BLK, col, lid, (0.115, 0.33, HT + 0.00025), (0, 0, 0))
# lid rib pattern (pressed stiffeners)
B('Lid_Rib', (-0.20, 0.45, HT), (0.20, 0.455, HT + 0.0006), CH_IN, parent=lid)

# ================================================================= FRONT
# ears + handles
for side, sx in (('L', -1), ('R', 1)):
    x_in, x_out = sx * W2, sx * EAR
    B('Ear_%s' % side, (min(x_in, x_out), -0.0025, 0.0), (max(x_in, x_out), 0.006, HT), CH)
    xc = sx * (W2 + EAR) / 2
    hz0, hz1 = 0.088, 0.168
    hb = [((xc - 0.004, -0.030, hz0), (xc + 0.004, -0.024, hz1)),
          ((xc - 0.004, -0.030, hz1 - 0.008), (xc + 0.004, -0.0025, hz1)),
          ((xc - 0.004, -0.030, hz0), (xc + 0.004, -0.0025, hz0 + 0.008))]
    hnd = boxes('Handle_%s' % side, hb, M['alu'])
    hnd.modifiers.new('Bevel', 'BEVEL').width = 0.0015
# front frame strips (silver chassis edges around the bays/grille)
fr = [((-W2, -0.001, HT - 0.006), (W2, 0.004, HT)),          # top lip
      ((-W2, -0.001, 0.083), (W2, 0.004, 0.088)),            # bays/grille divider
      ((-W2, -0.001, 0.0), (W2, 0.004, 0.004)),               # bottom lip
      ((-W2, -0.001, 0.0), (-0.2115, 0.004, HT)),
      ((0.2115, -0.001, 0.0), (W2, 0.004, HT))]
for i in (1, 2):
    xd = -0.2115 + i * 0.141
    fr.append(((xd - 0.0015, -0.001, 0.088), (xd + 0.0015, 0.004, HT - 0.006)))
boxes('Front_Frame', fr, CH)

# intake grille: dark backing + bar grid (3 panels)
B('Front_Grille_Backing', (-0.2115, 0.010, 0.088), (0.2115, 0.012, HT - 0.006), HOLE)
gb = []
for i in range(3):
    xa = -0.2115 + i * 0.141 + 0.0015; xb = xa + 0.141 - 0.003
    zc0, zc1 = 0.090, HT - 0.008
    gb += [((xa, 0.0, zc0), (xb, 0.0025, zc0 + 0.004)), ((xa, 0.0, zc1 - 0.004), (xb, 0.0025, zc1)),
           ((xa, 0.0, zc0), (xa + 0.004, 0.0025, zc1)), ((xb - 0.004, 0.0, zc0), (xb, 0.0025, zc1))]
    nx = 12
    for k in range(1, nx):
        x = xa + (xb - xa) * k / nx
        gb.append(((x - 0.0016, 0.0, zc0), (x + 0.0016, 0.0025, zc1)))
    nz = 7
    for k in range(1, nz):
        z = zc0 + (zc1 - zc0) * k / nz
        gb.append(((xa, 0.0, z - 0.0017), (xb, 0.0025, z + 0.0017)))
boxes('Front_Grille', gb, BLK)

# drive bays: 3 cages x 8 vertical 2.5" carriers
B('Drive_Cage_Inner', (-0.2115, 0.004, 0.004), (0.2115, 0.006, 0.083), HOLE)
B('Drive_Cage_Top', (-0.2115, 0.0, 0.0835), (0.2115, 0.130, 0.0855), CH_IN)
B('Drive_Backplane', (-0.2115, 0.128, 0.004), (0.2115, 0.1296, 0.083), PCB_MB)
carr, tabs = [], []
pitch = 0.141 / 8
for c in range(3):
    for k in range(8):
        i = c * 8 + k
        xc = -0.2115 + c * 0.141 + (k + 0.5) * pitch
        x0, x1 = xc - 0.0080, xc + 0.0080
        carr += [((x0, -0.0015, 0.074), (x1, 0.003, 0.0815)),        # top cap
                 ((x0, -0.0015, 0.006), (x0 + 0.0015, 0.003, 0.0815)),
                 ((x1 - 0.0015, -0.0015, 0.006), (x1, 0.003, 0.0815)),
                 ((x0, -0.0015, 0.021), (x1, 0.003, 0.0235))]
        for z in [0.026 + 0.0042 * j for j in range(11)]:
            carr.append(((x0, -0.0008, z), (x1, 0.002, z + 0.0016)))
        tabs.append(((x0 + 0.0012, -0.0030, 0.0065), (x1 - 0.0012, 0.003, 0.0205)))
        led = B('LED_drive_%02d' % i, (xc - 0.0018, -0.0021, 0.0770), (xc + 0.0018, -0.0013, 0.0795), LED_B if k % 2 else LED_G)
        led['led_role'] = 'drive_activity'
        empty('SLOT_drive_%02d' % i, (xc, 0.0, 0.006), kind='CUBE', size=0.005, slot_type='2.5in_bay')
boxes('Drive_Carriers', carr, BLK)
boxes('Drive_Latches', tabs, RED)

# control panel (left ear): power button + status LEDs
xcp = -(W2 + EAR) / 2
B('CtrlPanel_Plate', (xcp - 0.0085, -0.0035, 0.008), (xcp + 0.0085, -0.0025, 0.080), BLK)
H['cyl']('Btn_Power', 0.0045, 0.002, (xcp, -0.0045, 0.068), RED, col, verts=24, rot=(math.pi / 2, 0, 0), parent=root)
H['cyl']('Btn_UID', 0.0028, 0.0016, (xcp, -0.0042, 0.016), BLUE, col, verts=16, rot=(math.pi / 2, 0, 0), parent=root)
for i, (nm, m_) in enumerate((('power', LED_G), ('hdd', LED_B), ('nic1', LED_G), ('nic2', LED_G), ('info', LED_A))):
    z = 0.054 - i * 0.0072
    o = B('LED_%s' % nm, (xcp - 0.0020, -0.0042, z - 0.0013), (xcp + 0.0020, -0.0034, z + 0.0013), m_)
    o['led_role'] = nm
# SUPERMICRO badge on the right ear (reads top to bottom)
xb = (W2 + EAR) / 2
B('Badge_Plate', (xb - 0.0075, -0.0034, 0.006), (xb + 0.0075, -0.0025, 0.080), M['black_gl'])
H['text_mesh']('Badge_Text', 'SUPERMICR', FONT_BLACK, 0.0072, TXT, col, root, (xb, -0.0036, 0.046), (math.pi / 2, math.pi / 2, 0))
H['cyl']('Badge_Dot', 0.0022, 0.0004, (xb, -0.0036, 0.0105), TXT_RED, col, verts=16, rot=(math.pi / 2, 0, 0), parent=root)

# ================================================================= FAN WALL (2 rows x 4 fans 92 mm)
fan_objs, hub_objs, blade_m, strut_m = [], [], [], []
fan_cases = []
for row, yf in enumerate(Y_FAN):
    for k in range(4):
        xc = -0.15 + k * 0.10
        fr_ = H['ring']('FanFrame', [(xc + a, Z_FANC + b) for a, b in square_loop(0.046, 32)],
                        [(xc + a, Z_FANC + b) for a, b in circle(0.0445, 32)], 'xz', yf, 0.038, BLK, col, parent=root)
        fan_objs.append(fr_)
        hub = H['cyl']('FanHub', 0.019, 0.026, (xc, yf + 0.019, Z_FANC), BLK, col, verts=24, rot=(math.pi / 2, 0, 0), parent=root)
        hub_objs.append(hub)
        # struts on the outlet side
        for a in (0.5, 2.6, 4.7):
            ca, sa = math.cos(a), math.sin(a)
            strut_m.append(Mt.Translation((xc + ca * 0.032, yf + 0.0365, Z_FANC + sa * 0.032)) @ Mt.Rotation(-a, 4, 'Y') @ Mt.Diagonal((0.026, 0.003, 0.003, 1)))
        # 7 blades as thin twisted plates (merged later)
        for bi in range(7):
            a = 2 * math.pi * bi / 7
            blade_m.append(Mt.Translation((xc + math.cos(a) * 0.0315, yf + 0.019, Z_FANC + math.sin(a) * 0.0315)) @
                           Mt.Rotation(-a, 4, 'Y') @ Mt.Rotation(0.55, 4, 'X') @ Mt.Diagonal((0.025, 0.0012, 0.016, 1)))
        # hot-swap module top: cap with handle + yellow label
        fan_cases.append(((xc - 0.048, yf - 0.002, Z_FANC + 0.046), (xc + 0.048, yf + 0.040, Z_FANC + 0.049)))
        B('FanLabel', (xc - 0.012, yf + 0.006, Z_FANC + 0.049), (xc + 0.012, yf + 0.030, Z_FANC + 0.0494), YEL)
for o in fan_objs + hub_objs:
    H['apply_all'](o)
fan_objs.append(mboxes('Fan_Struts', strut_m, BLK))
fans = join('Fan_Frames', fan_objs + hub_objs)
blades = mboxes('Fan_Blades', blade_m, M['plastic'])
blades['spin_axis'] = 'Y'
labels = [o for o in col.objects if o.name.startswith('FanLabel')]
join('Fan_Labels', labels)
boxes('Fan_Module_Caps', fan_cases, BLK)
# fan cage bulkheads: perforated plate below fans, rails
B('FanCage_Bulkhead', (-W2 + T, 0.270, T), (W2 - T, 0.2712, Z_FANC - 0.047), CH_IN)
slits = []
for k in range(16):
    for j in range(3):
        x = -0.195 + k * 0.026
        slits.append(((x, 0.2690, 0.012 + j * 0.022), (x + 0.018, 0.2700, 0.026 + j * 0.022)))
boxes('FanCage_Slits', slits, HOLE)
B('FanCage_Shelf', (-W2 + T, Y_FAN[0] - 0.004, Z_FANC - 0.048), (W2 - T, Y_FAN[1] + 0.042, Z_FANC - 0.046), CH_IN)

# ================================================================= CPU BOARD (X11DPG-OT-CPU)
B('MB_PCB', (-W2 + 0.002, 0.278, Z_MB0), (W2 - 0.002, 0.440, Z_MB1), PCB_MB)
B('MB_PCB_RearIO', (-0.055, 0.440, Z_MB0), (0.055, 0.735, Z_MB1), PCB_MB)
slots, dimm_pcb, dimm_chips, latches = [], [], [], []
DY0, DY1 = 0.278, 0.420
for ci, (cx, cy) in enumerate(CPU):
    # socket frame + passive 2U heatsink (fins parallel to airflow)
    B('CPU%d_Socket' % ci, (cx - 0.040, cy - 0.050, Z_MB1), (cx + 0.040, cy + 0.050, Z_MB1 + 0.005), BLK)
    B('CPU%d_HS_Base' % ci, (cx - 0.039, cy - 0.054, Z_MB1 + 0.005), (cx + 0.039, cy + 0.054, Z_MB1 + 0.012), M['alu'])
    fins = [((cx - 0.039 + k * 0.0019, cy - 0.054, Z_MB1 + 0.012), (cx - 0.039 + k * 0.0019 + 0.0004, cy + 0.054, Z_MB1 + 0.064))
            for k in range(42)]
    fins.append(((cx - 0.039, cy - 0.054, Z_MB1 + 0.0635), (cx + 0.040, cy - 0.050, Z_MB1 + 0.064)))
    boxes('CPU%d_HS_Fins' % ci, fins, M['alu'])
    for sx in (-1, 1):
        for sy in (-1, 1):
            H['cyl']('CPU%d_HS_Screw' % ci, 0.0035, 0.008, (cx + sx * 0.033, cy + sy * 0.047, Z_MB1 + 0.066), CH_IN, col, verts=12, parent=root)
    B('CPU%d_HS_Label' % ci, (cx - 0.015, cy - 0.020, Z_MB1 + 0.0640), (cx + 0.015, cy + 0.020, Z_MB1 + 0.0645), CH_IN)
    empty('SLOT_cpu_%d' % ci, (cx, cy, Z_MB1), kind='CUBE', size=0.02, slot_type='LGA3647')
    # 6 DIMMs each side
    for sx in (-1, 1):
        for j in range(6):
            x = cx + sx * (0.046 + j * 0.0080)
            slots.append(((x - 0.0030, DY0, Z_MB1), (x + 0.0030, DY1, Z_MB1 + 0.008)))
            dimm_pcb.append(((x - 0.0006, DY0 + 0.004, Z_MB1 + 0.003), (x + 0.0006, DY1 - 0.004, Z_MB1 + 0.034)))
            for s in (-1, 1):
                dimm_chips.append(((x + s * 0.0006 - (0.0012 if s < 0 else 0), DY0 + 0.010, Z_MB1 + 0.012),
                                   (x + s * 0.0006 + (0.0012 if s > 0 else 0), DY1 - 0.010, Z_MB1 + 0.026)))
            for y in (DY0, DY1 - 0.006):
                latches.append(((x - 0.0032, y, Z_MB1), (x + 0.0032, y + 0.006, Z_MB1 + 0.017)))
    # VRM chokes behind the socket
    for k in range(6):
        B('VRM', (cx - 0.030 + k * 0.010, 0.410, Z_MB1), (cx - 0.023 + k * 0.010, 0.418, Z_MB1 + 0.006), CHIP)
boxes('DIMM_Slots', slots, BLK)
boxes('DIMM_PCBs', dimm_pcb, PCB_DIMM)
boxes('DIMM_Chips', dimm_chips, CHIP)
boxes('DIMM_Latches', latches, WHITE)
join('MB_VRM', [o for o in col.objects if o.name.startswith('VRM')])
join('CPU_HS_Screws', [o for o in col.objects if o.name.startswith('CPU0_HS_Screw') or o.name.startswith('CPU1_HS_Screw')])

# ================================================================= PCIe SWITCH DAUGHTERBOARD + GPU BAY
B('GB_PCB', (-W2 + 0.002, 0.440, Z_GB0), (W2 - 0.002, Y_BR + 0.002, Z_GB1), PCB_GB)
B('GB_Standoffs', (-0.058, 0.445, Z_PSU1), (-0.056, 0.70, Z_GB0), CH_IN)
B('GB_Standoffs_R', (0.056, 0.445, Z_PSU1), (0.058, 0.70, Z_GB0), CH_IN)


def pcb_x(pos, width_slots):
    """x of the card PCB plane (card y=0) for a card whose bracket starts at slot position pos."""
    return X0 + (pos + width_slots) * P - 0.0035


conn = []
for g, pos in enumerate(GPU_POS):
    xp = pcb_x(pos, 2)
    conn.append(((xp - 0.0030, Y_BR - 0.1135, Z_GB1), (xp + 0.0046, Y_BR - 0.0235, Z_GB1 + 0.011)))
    empty('SLOT_gpu_%d' % g, (xp, Y_BR, ZS), (0, 0, -math.pi / 2), size=0.05,
          slot_type='pcie_x16_double_width', bank='left' if g < 4 else 'right', root_complex=g // 4)
for k, (pos, lanes) in enumerate(NIC_POS):
    xp = pcb_x(pos, 1)
    ln = {8: 0.056, 4: 0.039}[lanes]
    conn.append(((xp - 0.0030, Y_BR - 0.0235 - ln, Z_GB1), (xp + 0.0046, Y_BR - 0.0235, Z_GB1 + 0.011)))
    empty('SLOT_nic_%d' % k, (xp, Y_BR, ZS), (0, 0, -math.pi / 2), size=0.03, slot_type='pcie_x%d' % lanes)
boxes('GB_PCIe_Slots', conn, BLK)
# PCIe switch heatsink with the yellow label of the photos (middle, in front of the NIC slots)
B('GB_Switch_HS_Base', (-0.046, 0.462, Z_GB1), (0.046, 0.552, Z_GB1 + 0.004), M['alu'])
boxes('GB_Switch_HS_Fins', [((-0.046 + k * 0.0023, 0.462, Z_GB1 + 0.004), (-0.046 + k * 0.0023 + 0.0005, 0.552, Z_GB1 + 0.022)) for k in range(40)], M['alu'])
B('GB_Switch_Label', (-0.040, 0.470, Z_GB1 + 0.022), (0.040, 0.545, Z_GB1 + 0.0224), YEL)
H['text_mesh']('GB_Switch_Text', 'PCIe SWITCH  DO NOT REMOVE', FONT_BOLD, 0.0045, BLK, col, root, (0.0, 0.5075, Z_GB1 + 0.0226), (0, 0, 0))
# GPU retention crossbar over the card ends
B('GPU_RetentionBar', (-W2 + T, Y_BR - 0.2745, HT - 0.0065), (W2 - T, Y_BR - 0.2655, HT - T), CH_IN)
for g, pos in enumerate(GPU_POS):
    xp = pcb_x(pos, 2)
    B('GPU_Guide_%d' % g, (xp - 0.030, Y_BR - 0.2745, HT - 0.010), (xp - 0.006, Y_BR - 0.2655, HT - 0.0065), BLK)
join('GPU_Guides', [o for o in col.objects if o.name.startswith('GPU_Guide_')])

# ================================================================= REAR
# slot area frame: sill, tab ledge, dividers, vented top strip
Z_TAB = ZS + 0.1085
rear = [((-W2, Y_BR + 0.0035, Z_PSU1), (W2, D, Z_PSU1 + 0.008)),                 # sill
        ((-W2, Y_BR + 0.0035, Z_TAB - 0.005), (W2, D, Z_TAB - 0.0001)),          # tab ledge
        ((-W2, D - T, Z_TAB), (W2, D, HT - T))]                                  # top strip plate
for pos in [0, 2, 4, 6, 8, 13, 15, 17, 19, 21]:
    x = X0 + pos * P
    rear.append(((x - 0.0008, Y_BR + 0.0035, Z_PSU1), (x + 0.0008, D, Z_TAB)))
for pos in range(9, 13):
    x = X0 + pos * P
    rear.append(((x - 0.0006, Y_BR + 0.0035, Z_PSU1), (x + 0.0006, D, Z_TAB)))
boxes('Rear_SlotFrame', rear, CH)
vent = []
for k in range(40):
    x = -0.205 + k * 0.0104
    vent.append(((x, D - T - 0.0003, Z_TAB + 0.0015), (x + 0.0062, D + 0.0001, HT - 0.0035)))
boxes('Rear_TopVents', vent, HOLE)


def blank_bracket(name, xa, xb, perf_rows):
    items = [((xa, Y_BR + 0.0026, ZS - 0.0085), (xb, Y_BR + 0.0034, Z_TAB)),
             ((xa, Y_BR + 0.0026, Z_TAB - 0.0009), (xb, D - 0.0012, Z_TAB))]
    o = boxes(name, items, CH)
    holes = []
    for r_ in range(perf_rows):
        z = ZS + 0.004 + r_ * 0.0068
        nx = max(1, int((xb - xa - 0.004) / 0.0062))
        for c in range(nx):
            x = xa + 0.003 + c * 0.0062
            holes.append(((x, Y_BR + 0.0035, z), (x + 0.0042, Y_BR + 0.0037, z + 0.0046)))
    h = boxes(name + '_Perf', holes, HOLE, parent=o)
    return o


for g, pos in enumerate(GPU_POS):
    b = blank_bracket('BLANK_gpu_%d' % g, X0 + pos * P + 0.0006, X0 + (pos + 2) * P - 0.0006, 13)
    b['blank_for'] = 'SLOT_gpu_%d' % g
for pos in range(8, 13):
    nic = next((k for k, (p_, _) in enumerate(NIC_POS) if p_ == pos), None)
    nm = 'BLANK_nic_%d' % nic if nic is not None else 'Rear_SlotCover_%d' % pos
    b = blank_bracket(nm, X0 + pos * P + 0.0006, X0 + (pos + 1) * P - 0.0006, 13)
    if nic is not None:
        b['blank_for'] = 'SLOT_nic_%d' % nic

# rear I/O between the PSU pairs
B('RearIO_Shield', (-0.0575, D - 0.0012, Z_PSU0), (0.0575, D, Z_PSU1), CH)
io_items, io_holes, io_blue = [], [], []
for z in (0.008, 0.0215):                       # USB 3.0 x2 (stacked)
    io_holes.append(((-0.050, D - 0.002, z), (-0.0365, D + 0.0002, z + 0.0058)))
    io_blue.append(((-0.0485, D - 0.0019, z + 0.0016), (-0.038, D + 0.0003, z + 0.0034)))
io_holes.append(((-0.050, D - 0.002, 0.031), (-0.0365, D + 0.0002, 0.0425)))   # IPMI RJ45
for x in (-0.030, -0.012):                       # 2x 10GBase-T
    io_holes.append(((x, D - 0.002, 0.008), (x + 0.0158, D + 0.0002, 0.0215)))
    io_items.append(((x - 0.0006, D - 0.0004, 0.0074), (x + 0.0164, D + 0.0008, 0.0221)))
io_items.append(((-0.0506, D - 0.0004, 0.0304), (-0.0359, D + 0.0008, 0.0431)))
io_blue.append(((0.010, D - 0.0004, 0.010), (0.041, D + 0.0012, 0.0225)))      # VGA
io_holes.append(((0.0135, D + 0.0008, 0.0128), (0.0375, D + 0.0014, 0.0197)))
for z in (0.027, 0.036):                        # 2 more USB
    io_holes.append(((0.012, D - 0.002, z), (0.0255, D + 0.0002, z + 0.0058)))
# laid out as seen from behind (USB at the far left, VGA at the right): mirror x
mir = lambda items: [((-b[0], a[1], a[2]), (-a[0], b[1], b[2])) for a, b in items]
boxes('RearIO_PortShells', mir(io_items), M['steel'])
boxes('RearIO_PortHoles', mir(io_holes), HOLE)
boxes('RearIO_Blue', mir(io_blue), BLUE)
for i, (nm, z) in enumerate((('lan1', 0.019), ('lan2', 0.019))):
    x = (-0.030, -0.012)[i]
    o = B('LED_%s' % nm, (-x - 0.0035, D + 0.0008, z + 0.0005), (-x - 0.0010, D + 0.0012, z + 0.0020), LED_G)
    o['led_role'] = nm
o = B('LED_uid_rear', (-0.052, D, 0.035), (-0.046, D + 0.0012, 0.041), LED_B); o['led_role'] = 'uid'

# ---------------------------------------------------------------- PSUs (4x 2000 W, 1U modules, 2+2)
psu_bodies, psu_faces, psu_handles, psu_latches, grille, inlets, holes_ = [], [], [], [], [], [], []
pins, psu_bars = [], []
for k, px in enumerate(PSU_X):
    x0, x1 = px - PSU_W / 2, px + PSU_W / 2
    psu_bodies.append(((x0 + 0.0005, PSU_Y0, Z_PSU0), (x1 - 0.0005, D - 0.003, Z_PSU1)))
    psu_faces.append(((x0, D - 0.003, Z_PSU0), (x1, D, Z_PSU1)))
    # fan (left half): dark disc + concentric rings
    fx, fz = px + 0.019, 0.022      # seen from behind: fan left, inlet, latch right
    H['cyl']('PSUFanHole', 0.0175, 0.001, (fx, D + 0.0002, fz), HOLE, col, verts=32, rot=(math.pi / 2, 0, 0), parent=root)
    for rr in (0.0060, 0.0110, 0.0165):
        grille.append(H['ring']('PSUGrille', circle(rr, 28, fx, fz), circle(rr - 0.0009, 28, fx, fz), 'xz', D + 0.0008, 0.0006, M['steel'], col, parent=root))
    for a in (0.0, math.pi / 2):
        psu_bars.append(Mt.Translation((fx, D + 0.0011, fz)) @ Mt.Rotation(a, 4, 'Y') @ Mt.Diagonal((0.035, 0.0006, 0.0009, 1)))
    # C20 inlet
    ix, iz = px - 0.011, 0.022
    inlets.append(((ix - 0.0125, D, iz - 0.0105), (ix + 0.0125, D + 0.003, iz + 0.0085)))
    holes_.append(((ix - 0.0105, D + 0.0028, iz - 0.0085), (ix + 0.0105, D + 0.0031, iz + 0.0065)))
    pins += [((ix - 0.0075, D + 0.0005, iz - 0.0002), (ix - 0.0015, D + 0.0029, iz + 0.0012)),
             ((ix + 0.0015, D + 0.0005, iz - 0.0002), (ix + 0.0075, D + 0.0029, iz + 0.0012)),
             ((ix - 0.0007, D + 0.0005, iz - 0.0072), (ix + 0.0007, D + 0.0029, iz - 0.0022))]
    empty('SOCKET_power_in_%d' % k, (ix, D + 0.003, iz), (-math.pi / 2, 0, 0), kind='SINGLE_ARROW', size=0.03,
          connector='IEC60320_C20', psu=k)
    empty('SLOT_psu_%d' % k, (px, D, Z_PSU0), size=0.03, slot_type='psu_1u_2000w')
    # handle + latch
    psu_handles += [((px - 0.026, D, 0.0345), (px - 0.002, D + 0.008, 0.0375)),
                    ((px - 0.026, D, 0.0040), (px - 0.002, D + 0.008, 0.0070))]
    psu_latches.append(((x0 + 0.0015, D, 0.006), (x0 + 0.0065, D + 0.006, 0.036)))
    o = B('LED_psu_%d' % k, (px + 0.001, D, 0.0045), (px + 0.0045, D + 0.0008, 0.0070), LED_G)
    o['led_role'] = 'psu'
boxes('PSU_Bodies', psu_bodies, PSU_FACE)
boxes('PSU_Faces', psu_faces, PSU_FACE)
boxes('PSU_Handles', psu_handles, BLK)
boxes('PSU_Latches', psu_latches, PINK)
boxes('PSU_Inlets', inlets, BLK)
boxes('PSU_InletHoles', holes_, HOLE)
boxes('PSU_InletPins', pins, M['steel'])
grille.append(mboxes('PSU_GrilleBars', psu_bars, M['steel']))
join('PSU_FanGrilles', grille)
join('PSU_FanHoles', [o for o in col.objects if o.name.startswith('PSUFanHole')])

# ================================================================= POWER DISTRIBUTION (flow paths)
# PSU output -> 12 V busbar (copper) under the daughterboard front edge -> 8-pin cables -> GPU power connectors;
# CPU VRM feeds as board traces.
BUS = rect(0.003, 0.008)
psu_len = {}
for k, px in enumerate(PSU_X):
    _, u1 = flow_sweep('PWR_psu_%d' % k, [(px, PSU_Y0, 0.022), (px, BUS_Y, 0.022), (px, BUS_Y, BUS_Z - 0.004)],
                       [(b, a) for a, b in rect(0.012, 0.002)], COPPER, 0.0, r=0.006)
    psu_len[k] = u1
B('PDB_Connectors', (-0.21, PSU_Y0 - 0.006, Z_PSU0 + 0.004), (-0.058, PSU_Y0, Z_PSU1 - 0.004), BLK)
B('PDB_Connectors_R', (0.058, PSU_Y0 - 0.006, Z_PSU0 + 0.004), (0.21, PSU_Y0, Z_PSU1 - 0.004), BLK)
u_bus0 = max(psu_len.values())
bus_start = {'L': -0.060, 'R': 0.060}
for side, sx in (('L', -1), ('R', 1)):
    flow_sweep('PWR_bus_%s' % side, [(sx * 0.060, BUS_Y, BUS_Z), (sx * 0.212, BUS_Y, BUS_Z)], BUS, COPPER, u_bus0)
# GPU 8-pin cables
plugs = []
for g, pos in enumerate(GPU_POS):
    xp = pcb_x(pos, 2)
    sock = V((xp, Y_BR, ZS)) + V((A100_PWR.y, -A100_PWR.x, A100_PWR.z))   # card -> world (rot z -90)
    xc = sock.x
    u0 = u_bus0 + abs(xc - bus_start['L' if xc < 0 else 'R'])
    plug_y = sock.y - 0.012
    flow_sweep('PWR_gpu_%d' % g, [(xc, BUS_Y, BUS_Z + 0.004), (xc, BUS_Y, sock.z), (xc, plug_y, sock.z)],
               tube(0.0035), CABLE, u0, r=0.005)
    plugs.append(((xc - 0.0045, plug_y, sock.z - 0.0095), (xc + 0.0045, sock.y - 0.0005, sock.z + 0.0095)))
    empty('SOCKET_power_out_gpu_%d' % g, tuple(sock), (-math.pi / 2, 0, 0), kind='SINGLE_ARROW', size=0.02,
          connector='8pin_EPS12V', slot='SLOT_gpu_%d' % g)
boxes('PWR_gpu_Plugs', plugs, BLK)
# CPU VRM feeds as flat board traces
for ci, (cx, cy) in enumerate(CPU):
    u0 = u_bus0 + abs(cx - bus_start['L' if cx < 0 else 'R'])
    flow_sweep('PWR_cpu_%d' % ci, [(cx, BUS_Y, BUS_Z - 0.004), (cx, BUS_Y, Z_MB1 + 0.0004), (cx, 0.419, Z_MB1 + 0.0004)],
               [(b, a) for a, b in rect(0.016, 0.0008)], COPPER, u0, r=0.004)

for o in root.children_recursive:
    if o.type == 'MESH' and o.modifiers:
        H['apply_all'](o)

# ================================================================= SAVE / EXPORT (no GPUs)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BASE, FILE + '.blend'))
objs = [root] + list(root.children_recursive)
bpy.ops.object.select_all(action='DESELECT')
for o in objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = root
dg = bpy.context.evaluated_depsgraph_get(); tris = 0
for o in objs:
    if o.type == 'MESH':
        e = o.evaluated_get(dg); me = e.to_mesh(); me.calc_loop_triangles(); tris += len(me.loop_triangles); e.to_mesh_clear()
glb = os.path.join(BASE, 'export', FILE + '.glb')
bpy.ops.export_scene.gltf(filepath=glb, use_selection=True, export_apply=True, export_extras=True)
print('TRIANGLES', tris, 'GLB_BYTES', os.path.getsize(glb))
lid_tris = len(lid.data.polygons)
print('SLOTS', sorted(o.name for o in objs if o.type == 'EMPTY' and (o.name.startswith('SLOT_') or o.name.startswith('SOCKET_'))))

# ================================================================= PREVIEW: append GPUs into every slot
def load_card(path, cname):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = [cname]
    c = dst.collections[0]
    bpy.context.scene.collection.children.link(c)
    return c


def place_card(c, rname, slot, tag):
    src_root = bpy.data.objects[rname]
    mapping = {}
    for o in [src_root] + list(src_root.children_recursive):
        n = o.copy(); n.name = '%s_%s_%s' % (tag, slot.name, o.name)
        c.objects.link(n); mapping[o] = n
    for o, n in mapping.items():
        if o.parent in mapping:
            n.parent = mapping[o.parent]
    mapping[src_root].parent = None
    mapping[src_root].matrix_world = slot.matrix_world.copy()
    return list(mapping.values())


bpy.context.view_layer.update()
prev = bpy.data.collections.new('Preview_GPUs'); bpy.context.scene.collection.children.link(prev)
ca = load_card(os.path.join(BASE, 'gpu_06_a100_pcie.blend'), 'A100_PCIe')
ca.hide_render = True; ca.hide_viewport = True
cv = load_card(os.path.join(BASE, 'gpu_03_tesla_v100_pcie.blend'), 'TeslaV100_PCIe')
cv.hide_render = True; cv.hide_viewport = True
gpu_sets = {'a100': [], 'v100': []}
for g in range(8):
    slot = bpy.data.objects['SLOT_gpu_%d' % g]
    gpu_sets['a100'] += place_card(prev, 'A100_PCIe', slot, 'A')
    gpu_sets['v100'] += place_card(prev, 'TeslaV100_PCIe', slot, 'V')


def show(gpus=None, lid_on=True, blanks=None):
    for k, lst in gpu_sets.items():
        for o in lst:
            o.hide_render = (k != gpus)
    for o in [lid] + list(lid.children_recursive):
        o.hide_render = not lid_on
    for o in col.objects:
        if o.name.startswith('BLANK_gpu_'):
            hide = gpus is not None if blanks is None else not blanks
            o.hide_render = hide
            for ch in o.children:
                ch.hide_render = hide


# ---------------------------------------------------------------- studio (template is sized for a 30 cm card)
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.render.image_settings.file_format = 'PNG'
CTR = V((0.0, D / 2, HT / 2))
fl = bpy.data.objects.get('Floor')
if fl:
    fl.location = (0.0, D / 2, -0.0004); fl.scale = (fl.scale[0] * 8, fl.scale[1] * 8, fl.scale[2])
for nm, loc in (('Key', (0.35, -0.55, 1.45)), ('Fill', (-1.30, -0.05, 0.45)), ('Rim', (1.20, 1.45, 1.00))):
    l = bpy.data.objects.get(nm)
    if l:
        l.location = loc
        l.data.energy *= 9.0
        if hasattr(l.data, 'size'):
            l.data.size *= 3.0
        l.rotation_euler = (V(CTR) - V(loc)).to_track_quat('-Z', 'Y').to_euler()


def cam(name, loc, target, lens=50, ortho=None):
    c = bpy.data.objects.get(name)
    if not c:
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.data.collections['Studio'].objects.link(c)
    c.location = loc
    c.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.data.lens = lens; c.data.clip_start = 0.01; c.data.clip_end = 50
    if ortho:
        c.data.type = 'ORTHO'; c.data.ortho_scale = ortho
    return c


views = {
    # name: (camera, gpus, lid, world rotation)
    'front': (cam('R_front', (0.0, -1.55, 0.30), (0.0, 0.0, 0.085), 75), 'a100', True, 0.0),
    'rear': (cam('R_rear', (0.0, D + 1.55, 0.30), (0.0, D, 0.085), 75), 'a100', True, math.pi),
    '34_closed': (cam('R_34c', (-0.95, -1.05, 0.80), (0.0, 0.33, 0.07), 50), 'a100', True, 0.0),
    '34_open': (cam('R_34o', (0.80, -0.75, 1.05), (0.0, 0.40, 0.06), 45), 'a100', False, 0.0),
    'top_open': (cam('R_top', (0.0, D / 2, 2.0), (0.0, D / 2, 0.0), 50, ortho=0.86), 'a100', False, 0.0),
    'rear_34': (cam('R_rear34', (0.85, D + 0.95, 0.70), (0.0, D - 0.05, 0.07), 45), 'a100', True, math.pi),
    'power_detail': (cam('R_pwr', (-0.30, 0.16, 0.42), (-0.10, 0.45, 0.10), 35), 'a100', False, 0.0),
    'v100_open': (cam('R_v100', (-0.75, -0.55, 1.00), (0.0, 0.42, 0.06), 45), 'v100', False, 0.0),
    'ears': (cam('R_ears', (0.12, -0.42, 0.10), (0.20, 0.0, 0.05), 55), 'a100', True, 0.0),
    'nogpu_open': (cam('R_nogpu', (0.70, D + 0.55, 0.95), (0.0, 0.45, 0.06), 45), None, False, math.pi),
}
bpy.data.objects['R_top'].rotation_euler = (0, 0, math.pi / 2)   # front at the left, like the Supermicro top view
only = os.environ.get('SRV_VIEWS')
for k, (c, gpus, lid_on, wr) in views.items():
    if only and k not in only.split(','):
        continue
    show(gpus, lid_on)
    sc.camera = c
    mp = next((n for n in sc.world.node_tree.nodes if n.type == 'MAPPING'), None)
    if mp:
        mp.inputs['Rotation'].default_value[2] = wr
    sc.render.filepath = os.path.join(BASE, 'renders', '%s_%s.png' % (FILE, k))
    bpy.ops.render.render(write_still=True)
print('DONE')
