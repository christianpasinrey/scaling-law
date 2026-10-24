"""NVIDIA L40S (Ada Lovelace, 48 GB GDDR6, 2023) - passive dual-slot FHFL datacenter card.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python gpu_09_l40s.py

Reference: PNY product shots (front / back / left / right / 3qtr) of NVIDIA-L40S:
  - front (-Y): champagne-gold U-shroud, plain face, finely fluted rounded top + bottom edges,
    small notch in the bottom edge just past the PCIe latch tab
  - top: gold fluted band on the front half, black strip on the back half with the NVIDIA logo
    near the power end, two small connectors next to the bracket
  - back (+Y): flat black backplate, 10 screws (5 top / 5 bottom)
  - bracket: silver full-height bracket, 4x DisplayPort column (PCB side) + screwed window
    showing the horizontal black heatsink fins
  - power end: gold-framed fin opening (front side) + black end cap with 16-pin 12V-2x6
    connector at the top, two vent slots
"""
import bpy, bmesh, math, mathutils, os, sys

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']

ROOT = 'L40S'
BASE = r'C:\laragon\www\scaling-law\blender'
BLEND = os.path.join(BASE, 'gpu_09_l40s.blend')
GLB = os.path.join(BASE, 'export', 'gpu_l40s.glb')
RENDERS = os.path.join(BASE, 'renders')
FONT = r'C:\Windows\Fonts\arialbd.ttf'
DO_RENDER = '--norender' not in sys.argv

root, col = H['new_card_scene'](ROOT)
M = H['base_materials']()
mat = H['mat']
GOLD = mat('HW_L40S_Gold', (0.86, 0.64, 0.37), 1.0, 0.36, aniso=0.3)
GOLD_IN = mat('HW_L40S_GoldInner', (0.40, 0.31, 0.19), 1.0, 0.5)
BLACK = mat('HW_L40S_Black', (0.005, 0.005, 0.006), 0.0, 0.62, spec=0.12)
VENT = mat('HW_L40S_Vent', (0.001, 0.001, 0.001), 0.0, 1.0, spec=0.02)
FINS = mat('HW_L40S_Fins', (0.004, 0.004, 0.005), 0.0, 0.5, spec=0.12)
BRACKET = mat('HW_L40S_Bracket', (0.52, 0.52, 0.53), 1.0, 0.42)
SCREW = mat('HW_L40S_Screw', (0.03, 0.03, 0.032), 0.8, 0.3)
SCREW_S = mat('HW_ScrewSilver', (0.6, 0.6, 0.62), 1.0, 0.3)
LABEL = mat('HW_LabelWhite', (0.75, 0.76, 0.78), 0.0, 0.6)

# ---------------------------------------------------------------- dimensions
L = 0.267            # shroud length (x)
ZT = 0.097           # shroud top
ZB = 0.0             # shroud bottom
YF = -0.0355         # front face
YB = 0.0045          # back face (backplate)
YS = -0.0118         # split gold U-shroud / black body
R = 0.0042           # radius of the fluted edges
X0_PCIE = 0.042      # PCIe key start
NOTCH = (0.149, 0.165, 0.0035)   # bottom-edge notch x0, x1, depth


def notch_z(x):
    x0, x1, d = NOTCH
    ramp = 0.0018
    if x <= x0 - ramp or x >= x1 + ramp:
        return 0.0
    if x < x0:
        t = (x - (x0 - ramp)) / ramp
    elif x > x1:
        t = ((x1 + ramp) - x) / ramp
    else:
        t = 1.0
    return d * (0.5 - 0.5 * math.cos(math.pi * t))


# ---------------------------------------------------------------- gold fluted bands
def fluted_band(name, top):
    """Rounded, finely fluted edge band of the U-shroud (top or bottom).
    Profile in YZ: quarter arc from the front face to the flat, then flat to YS; shell 0.8 mm."""
    s = 1 if top else -1
    zc = (ZT - R) if top else (ZB + R)
    yc = YF + R
    outer = []
    for k in range(6):
        a = math.pi - (math.pi / 2) * k / 5          # 180deg (front) -> 90deg (up)
        n = (math.cos(a), s * math.sin(a))
        outer.append(((yc + R * n[0], zc + s * R * math.sin(a)), n))
    outer.append(((YS, ZT if top else ZB), (0.0, s)))
    t = 0.0008
    inner = [(YS, (ZT - t) if top else (ZB + t)), (yc, (ZT - t) if top else (ZB + t)),
             (YF + t, zc)]
    pitch = 0.0006
    n_sec = int(L / pitch)
    bm = bmesh.new(); rings = []
    for i in range(n_sec + 1):
        x = min(L, i * pitch)
        dz = notch_z(x) if not top else 0.0
        amp = 0.00032 if (i % 2 == 0 and 0 < i < n_sec) else 0.0
        pts = []
        for j, ((py, pz), nn) in enumerate(outer):
            f = 0.6 if j == 0 else 1.0
            pts.append((py + nn[0] * amp * f, pz + nn[1] * amp * f + dz))
        for py, pz in inner:
            pts.append((py, pz + dz))
        rings.append([bm.verts.new((x, py, pz)) for py, pz in pts])
    n = len(rings[0])
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(n):
            j = (k + 1) % n
            bm.faces.new((a[k], a[j], b[j], b[k]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = False
    o = bpy.data.objects.new(name, me); me.materials.append(GOLD)
    col.objects.link(o); o.parent = root
    return o


fluted_band('Shroud_Top', True)
fluted_band('Shroud_Bottom', False)

# front face plate (between the two arcs)
face = H['box']('Shroud_Face', (L, 0.0010, ZT - ZB - 2 * R + 0.0006),
                (L / 2, YF + 0.0005, (ZT + ZB) / 2), GOLD, col, parent=root)
nc = H['box']('cut', (NOTCH[1] - NOTCH[0] + 0.004, 0.01, 0.02),
              ((NOTCH[0] + NOTCH[1]) / 2, YF, ZB + R - 0.01 + NOTCH[2] + 0.0003), GOLD, col)
H['cut'](face, nc)

# inner liner of the U so the ends read as a frame (dark gold)
H['box']('Shroud_Liner', (L - 0.001, 0.0006, ZT - ZB - 0.004), (L / 2, YF + 0.0013, (ZT + ZB) / 2),
         GOLD_IN, col, parent=root)

# ---------------------------------------------------------------- heatsink fins (horizontal)
def fins():
    n = 21
    z0, z1 = ZB + 0.0050, ZT - 0.0050
    for i in range(n):
        z = z0 + (z1 - z0) * i / (n - 1)
        yield (L / 2, (YF + 0.0020 + YS) / 2, z), (L - 0.0016, YS - YF - 0.0020, 0.00045)
H['slat_array']('Heatsink_Fins', fins, FINS, col, root)
H['box']('Heatsink_Base', (L - 0.002, 0.0012, ZT - ZB - 0.003), (L / 2, YS - 0.0004, (ZT + ZB) / 2),
         FINS, col, parent=root)

# ---------------------------------------------------------------- black body / backplate
body = H['box']('Body_Black', (L, YB - YS, ZT - ZB), (L / 2, (YB + YS) / 2, (ZT + ZB) / 2),
                BLACK, col, bevel=0.0005, parent=root)
nc = H['box']('cut', (NOTCH[1] - NOTCH[0], 0.03, 0.01),
              ((NOTCH[0] + NOTCH[1]) / 2, (YB + YS) / 2, ZB - 0.005 + NOTCH[2]), BLACK, col)
H['cut'](body, nc)
# the notch flanks are rounded in the photo: two small cylinders blend it
for xx in (NOTCH[0], NOTCH[1]):
    c = H['cyl']('cut', NOTCH[2], 0.03, (xx, (YB + YS) / 2, ZB), BLACK, col, verts=16, rot=(math.pi / 2, 0, 0))
    H['cut'](body, c)

# backplate screws (5 top, 5 bottom) measured on the PNY back shot
for i, (xs, zs) in enumerate([(0.0085, ZT - 0.0035), (0.075, ZT - 0.0035), (0.132, ZT - 0.0035),
                              (0.189, ZT - 0.0035), (0.247, ZT - 0.0035),
                              (0.018, ZB + 0.0042), (0.075, ZB + 0.0042), (0.132, ZB + 0.0042),
                              (0.189, ZB + 0.0042), (0.246, ZB + 0.0042)]):
    H['cyl'](f'Back_Screw_{i}', 0.0012, 0.0005, (xs, YB + 0.00015, zs), SCREW, col, verts=12,
             rot=(math.pi / 2, 0, 0), parent=root)
    H['box'](f'Back_Screw_{i}_Slot', (0.0012, 0.0002, 0.0003), (xs, YB + 0.0004, zs), M['port'], col,
             parent=root).rotation_euler = (0, math.radians(45), 0)

# ---------------------------------------------------------------- PCB + PCIe
pcb = H['box']('PCB', (0.258, 0.0016, 0.0950), (0.004 + 0.129, 0.0008, 0.0465), M['pcb'], col, parent=root)
nc = H['box']('cut', (NOTCH[1] - NOTCH[0], 0.01, 0.01), ((NOTCH[0] + NOTCH[1]) / 2, 0.0008, -0.0050 + NOTCH[2]), BLACK, col)
H['cut'](pcb, nc)
H['pcie_edge'](root, col, M, x0=X0_PCIE)
x_end = X0_PCIE + 0.0935
# latch tab with hook right after the fingers
tab = H['box']('PCB_LatchTab', (NOTCH[0] - x_end, 0.0016, 0.0080), ((x_end + NOTCH[0]) / 2, 0.0008, -0.0040),
               M['pcb'], col, parent=root)
hk = H['box']('cut', (0.0040, 0.01, 0.0040), (x_end + 0.0045, 0.0008, -0.0080), BLACK, col)
H['cut'](tab, hk)

# ---------------------------------------------------------------- bracket (silver, 4x DP + fin window)
BX = -0.0030; BT = 0.0009
br = H['box']('Bracket', (BT, 0.0400, 0.1020), (BX, -0.0170, 0.0610), BRACKET, col, parent=root)  # z 0.010..0.112
lower = H['box']('Bracket_Lower', (BT, 0.0310, 0.0160), (BX, -0.0185, 0.0020), BRACKET, col, parent=root)  # z -0.006..0.010
H['box']('Bracket_Tab', (0.0110, 0.0190, BT), (BX - 0.0055 + BT / 2, -0.0080, 0.1120), BRACKET, col, parent=root)
H['box']('Bracket_ProngA', (BT, 0.0150, 0.0100), (BX, -0.0120, -0.0110), BRACKET, col, parent=root)
H['box']('Bracket_ProngB', (BT, 0.0090, 0.0100), (BX, -0.0290, -0.0110), BRACKET, col, parent=root)

DP_Y = -0.0052
DP_Z = [0.0950, 0.0745, 0.0540, 0.0335]
DW, DH, CH = 0.0068, 0.0165, 0.0020
for i, zc in enumerate(DP_Z):
    pts = [(DP_Y - DW / 2, zc - DH / 2), (DP_Y + DW / 2, zc - DH / 2), (DP_Y + DW / 2, zc + DH / 2 - CH),
           (DP_Y + DW / 2 - CH, zc + DH / 2), (DP_Y - DW / 2, zc + DH / 2)]
    c = H['prism']('cut', pts, 'yz', BX - 0.003, 0.006, BRACKET, col)
    H['cut'](br, c)
    # connector: steel shell, dark cavity, plastic tongue
    pts_s = [(y + (0.0003 if y > DP_Y else -0.0003), z + (0.0003 if z > zc else -0.0003)) for y, z in pts]
    H['prism'](f'DP_{i}_Shell', pts_s, 'yz', BX + 0.0006, 0.0100, M['steel'], col, parent=root)
    H['prism'](f'DP_{i}_Cavity', [(y + (-0.0003 if y > DP_Y else 0.0003), z + (-0.0003 if z > zc else 0.0003)) for y, z in pts],
               'yz', BX + 0.0005, 0.0100, M['port'], col, parent=root)
    H['box'](f'DP_{i}_Tongue', (0.0060, 0.0015, 0.0120), (BX + 0.0045, DP_Y + 0.0012, zc), M['plastic'], col, parent=root)

WY0, WY1, WZ0, WZ1 = -0.0338, -0.0128, 0.0230, 0.1065
c = H['box']('cut', (0.006, WY1 - WY0, WZ1 - WZ0), (BX, (WY0 + WY1) / 2, (WZ0 + WZ1) / 2), BRACKET, col)
H['cut'](br, c)
fw = 0.0016
outer = [(WY0 - fw, WZ0 - fw), (WY1 + fw, WZ0 - fw), (WY1 + fw, WZ1 + fw), (WY0 - fw, WZ1 + fw)]
inner = [(WY0, WZ0), (WY1, WZ0), (WY1, WZ1), (WY0, WZ1)]
H['ring']('Bracket_WindowFrame', outer, inner, 'yz', BX - BT / 2 - 0.0005, 0.0005, BRACKET, col, parent=root)
for yy in (WY0 - 0.0002, WY1 + 0.0002):
    for zz in (WZ0 - 0.0002, WZ1 + 0.0002):
        H['cyl']('Bracket_Screw', 0.0013, 0.0008, (BX - BT / 2 - 0.0009, yy, zz), SCREW_S, col, verts=12,
                 rot=(0, math.pi / 2, 0), parent=root)
# window fins: the polished heatsink fins run all the way to the bracket
def wfins():
    n = 24
    for i in range(n):
        z = WZ0 + 0.0015 + (WZ1 - WZ0 - 0.003) * i / (n - 1)
        yield (BX + 0.0020, (WY0 + WY1) / 2, z), (0.0030, WY1 - WY0 + 0.001, 0.0006)
H['slat_array']('Bracket_Fins', wfins, FINS, col, root)
H['box']('Bracket_FinBack', (0.0006, WY1 - WY0 + 0.002, WZ1 - WZ0 + 0.002), (BX + 0.0036, (WY0 + WY1) / 2, (WZ0 + WZ1) / 2),
         M['port'], col, parent=root)

# ---------------------------------------------------------------- top connectors near the bracket
for i, (xc, w) in enumerate(((0.0150, 0.0130), (0.0330, 0.0090))):
    H['box'](f'Top_Conn_{i}', (w, 0.0075, 0.0030), (xc, -0.0060, ZT + 0.0003), M['plastic'], col, bevel=0.0003, parent=root)
    H['box'](f'Top_Conn_{i}_Hole', (w - 0.0025, 0.0045, 0.0004), (xc, -0.0060, ZT + 0.0017), M['port'], col, parent=root)

# ---------------------------------------------------------------- power end (black cap + 16-pin)
XE = L
# 12V-2x6 (16-pin): 2 columns x 6 rows of 3 mm pitch power pins + 4 sense pins, vertical
CY0, CY1, CZ0, CZ1 = -0.0105, -0.0025, 0.0730, 0.0935
H['box']('Power_16pin', (0.0060, CY1 - CY0, CZ1 - CZ0), (XE - 0.0015, (CY0 + CY1) / 2, (CZ0 + CZ1) / 2),
         M['plastic'], col, bevel=0.0003, parent=root)
def pins():
    for r in range(6):
        for cc in range(2):
            yield (XE + 0.00155, CY0 + 0.0020 + cc * 0.0030, CZ0 + 0.0022 + r * 0.0030), (0.0002, 0.0022, 0.0022)
    for r in range(4):
        yield (XE + 0.00155, CY1 - 0.0011, CZ0 + 0.0040 + r * 0.0035), (0.0002, 0.0010, 0.0014)
H['slat_array']('Power_16pin_Holes', pins, VENT, col, root)
H['box']('Power_16pin_Latch', (0.0012, 0.0030, 0.0040), (XE + 0.0016, CY1 + 0.0012, (CZ0 + CZ1) / 2), M['plastic'], col, parent=root)
# vent slots + screws on the black end cap
for i, (z0, z1) in enumerate(((0.0420, 0.0690), (0.0130, 0.0380))):
    H['box'](f'EndCap_Vent_{i}', (0.0003, 0.0070, z1 - z0), (XE + 0.0001, -0.0058, (z0 + z1) / 2), VENT, col, parent=root)
for i, zz in enumerate((0.0400, 0.0090)):
    H['cyl'](f'EndCap_Screw_{i}', 0.0011, 0.0004, (XE + 0.0002, -0.0058, zz), SCREW, col, verts=12,
             rot=(0, math.pi / 2, 0), parent=root)

# ---------------------------------------------------------------- top branding
txt = H['text_mesh']('Top_NVIDIA', 'NVIDIA', FONT, 0.0050, LABEL, col, root,
                     (0.2440, -0.0032, ZT + 0.0001), (0, 0, 0), extrude=0.0)
# stylised NVIDIA eye mark left of the wordmark
eye = H['box']('Top_NVIDIA_Eye', (0.0042, 0.0036, 0.0002), (0.2310, -0.0034, ZT + 0.0001), LABEL, col, parent=root)
H['cyl']('Top_NVIDIA_EyeIris', 0.0011, 0.0003, (0.2318, -0.0034, ZT + 0.0002), BLACK, col, verts=16, parent=root)

# ---------------------------------------------------------------- sockets
H['sockets'](root, col, power_in=(XE + 0.0020, (CY0 + CY1) / 2, (CZ0 + CZ1) / 2),
             pcie=(X0_PCIE + 0.0475, 0.0008, -0.0085))

# cleanup stray cutters (named 'cut') and apply modifiers
for o in list(col.objects):
    if o.name.startswith('cut'):
        bpy.data.objects.remove(o, do_unlink=True)
for o in root.children_recursive:
    if o.type == 'MESH' and o.modifiers:
        H['apply_all'](o)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
tris = H['export_glb'](ROOT, GLB)
print(f'L40S TRIS {tris}  GLB {os.path.getsize(GLB)} bytes')

# ---------------------------------------------------------------- renders
if DO_RENDER:
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.render.resolution_percentage = 100
    try:
        sc.eevee.taa_render_samples = 48
    except Exception:
        pass
    cam = bpy.data.objects['Camera']
    C = mathutils.Vector((0.132, -0.016, 0.046))
    views = {
        'front':   ((0.132, -0.60, 0.050), C, 50),
        'back':    ((0.132, 0.60, 0.050), C, 50),
        'top':     ((0.132, -0.016, 0.62), C, 50),
        '34':      ((-0.17, -0.42, 0.30), C, 50),
        'bracket': ((-0.42, -0.12, 0.10), mathutils.Vector((0.0, -0.016, 0.048)), 55),
        'power':   ((0.62, -0.12, 0.13), mathutils.Vector((0.267, -0.016, 0.048)), 55),
        'top34':   ((-0.08, -0.20, 0.30), mathutils.Vector((0.09, -0.016, 0.09)), 45),
    }
    only = [a.split('=', 1)[1] for a in sys.argv if a.startswith('--views=')]
    only = only[0].split(',') if only else list(views)
    for name in only:
        loc, tgt, lens = views[name]
        cam.location = loc
        d = tgt - mathutils.Vector(loc)
        up = 'Y'
        if name == 'top':
            cam.rotation_euler = (0, 0, 0)
        else:
            cam.rotation_euler = d.to_track_quat('-Z', up).to_euler()
        cam.data.type = 'PERSP'; cam.data.lens = lens
        sc.camera = cam
        sc.render.filepath = os.path.join(RENDERS, f'l40s_{name}.png')
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sc.render.filepath)
