"""NVIDIA H100 PCIe 80 GB (2022) - passive dual-slot FHFL card.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python C:\\laragon\\www\\scaling-law\\blender\\scripts\\gpu_08_h100_pcie.py

References (see report): NVIDIA product brief PB-11133-001 (dimension drawing, end view, NVLink top view),
IT Creations / Lenovo / Puget product photos (front, top edge, power end, back, bracket).
The H100 NVL (94 GB) uses the identical champagne shroud, so this model also stands in for it.

Axes (hw.py): bracket at x~0, card grows +X, Z up, PCIe finger bottom ~ -0.0125,
PCB at y in [0, 0.0016], front (shroud) toward -Y, backplate toward +Y.
"""
import bpy, bmesh, math, mathutils, os

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']

BASE = r'C:\laragon\www\scaling-law\blender'
ROOT = 'H100_PCIe'
FONT_BLACK = r'C:\Windows\Fonts\ariblk.ttf'
FONT_REG = r'C:\Windows\Fonts\arial.ttf'
FONT_BOLD = r'C:\Windows\Fonts\arialbd.ttf'

root, col = H['new_card_scene'](ROOT)
M = H['base_materials']()
mat = H['mat']
GOLD = mat('HW_H100Champagne', (0.64, 0.47, 0.26), 0.75, 0.45)
GOLD_RIB = mat('HW_H100ChampagneRib', (0.54, 0.39, 0.21), 0.75, 0.50)
GOLD_IN = mat('HW_H100ChampagneInner', (0.30, 0.225, 0.14), 1.0, 0.55)
BLACK = mat('HW_H100Black', (0.005, 0.005, 0.0055), 0.0, 0.80, spec=0.04)
CAP = mat('HW_H100CapBlack', (0.002, 0.002, 0.0025), 0.0, 0.42, spec=0.22)
PCB = mat('HW_H100PCB', (0.008, 0.009, 0.008), 0.0, 0.70, spec=0.08)
BACKPL = mat('HW_H100BackPlate', (0.006, 0.006, 0.0065), 0.0, 0.75, spec=0.06)
FINS = mat('HW_H100Fins', (0.004, 0.004, 0.0045), 0.0, 0.70, spec=0.08)
PORT = mat('HW_H100Port', (0.002, 0.002, 0.002), 0.0, 1.0, spec=0.0)
PLASTIC = mat('HW_H100Plastic', (0.006, 0.006, 0.0065), 0.0, 0.60, spec=0.12)
BRACKET = mat('HW_H100Bracket', (0.09, 0.083, 0.076), 1.0, 0.30)
PRINT_GOLD = mat('HW_H100PrintGold', (0.28, 0.20, 0.10), 0.0, 0.55, spec=0.2)
PRINT_GREY = mat('HW_H100PrintGrey', (0.07, 0.07, 0.075), 0.0, 0.55)
LABEL = mat('HW_H100LabelGrey', (0.035, 0.036, 0.040), 0.0, 0.40, spec=0.45)
LABEL_TXT = mat('HW_H100LabelText', (0.20, 0.20, 0.21), 0.0, 0.55)
SCREW = mat('HW_H100Screw', (0.30, 0.30, 0.31), 1.0, 0.35)

# ---------------------------------------------------------------- dimensions
L = 0.2677             # shroud length without bracket (brief: 267.70 mm)
Z_TOP = 0.0987         # 111.15 mm above finger bottom (-0.0125)
Z_NEAR = 0.0043        # shroud bottom over the PCIe connector (recessed by 3.55 mm)
Z_FAR = 0.0008         # shroud bottom beyond the step (13.25 mm above finger bottom)
X_STEP = 0.150         # step position (photos: ~56-62 % of length from bracket)
Y_FRONT = -0.0355      # front face
Y_GOLD = -0.0105       # gold shroud / black frame boundary (photos: gold ~64 % of thickness)
Y_BACK = 0.0036        # back plate outer face
WALL = 0.0015
RIB_H = 0.0008
RIB_P = 0.00216        # rib pitch measured on the top-edge photo


def boxes(name, items, material, parent=root):
    """items: list of (min(x,y,z), max(x,y,z)) boxes merged into one mesh."""
    def gen():
        for a, b in items:
            c = tuple((a[i] + b[i]) / 2 for i in range(3)); s = tuple(b[i] - a[i] for i in range(3))
            yield c, s
    return H['slat_array'](name, gen, material, col, parent)


def look_rot(local_x, local_y):
    lx = mathutils.Vector(local_x).normalized(); ly = mathutils.Vector(local_y).normalized(); lz = lx.cross(ly)
    m = mathutils.Matrix((lx, ly, lz)).transposed()
    return m.to_euler()


ROT_TOP = (0, 0, 0)                                  # on the top edge: reads +X, letters up +Y
ROT_BACK = look_rot((0, 0, -1), (-1, 0, 0))          # on the back plate: reads -Z, letters toward bracket
ROT_END = look_rot((0, 1, 0), (0, 0, 1))             # on the far end face (normal +X)


def text_mesh_lo(name, body, font, size, material, loc, rot, extrude=0.0, res=3):
    """Like hw.text_mesh but with low curve resolution (tiny print stays cheap)."""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.size = size; cu.extrude = extrude; cu.resolution_u = res
    t = bpy.data.objects.new(name, cu); col.objects.link(t); cu.materials.append(material)
    bpy.context.view_layer.objects.active = t
    bpy.ops.object.select_all(action='DESELECT'); t.select_set(True)
    bpy.ops.object.convert(target='MESH')
    t.parent = root; t.matrix_parent_inverse.identity()
    t.location = loc; t.rotation_euler = rot
    return t


def text(name, body, size, material, loc, rot, font=FONT_BOLD, extrude=0.0, fit_w=None, fit_h=None, res=3):
    t = text_mesh_lo(name, body, font, size, material, loc, rot, extrude=extrude, res=res)
    if fit_w or fit_h:
        d = t.dimensions
        sx = fit_w / d.x if fit_w else 1.0
        sy = fit_h / d.y if fit_h else sx
        if not fit_w:
            sx = sy
        t.scale = (sx, sy, 1)
    return t


# ---------------------------------------------------------------- gold shroud (extrusion along Y)
gold = boxes('Shroud_Gold', [
    # front wall: two pieces abutting at the step
    ((0.0, Y_FRONT, Z_NEAR), (X_STEP, Y_FRONT + WALL, Z_TOP - RIB_H)),
    ((X_STEP, Y_FRONT, Z_FAR), (L, Y_FRONT + WALL, Z_TOP - RIB_H)),
    # top wall
    ((0.0, Y_FRONT + WALL, Z_TOP - RIB_H - WALL), (L, Y_GOLD, Z_TOP - RIB_H)),
    # bottom walls (far one is thick so the step face is closed)
    ((0.0, Y_FRONT + WALL, Z_NEAR), (X_STEP, Y_GOLD, Z_NEAR + WALL)),
    ((X_STEP, Y_FRONT + WALL, Z_FAR), (L, Y_GOLD, Z_NEAR + WALL)),
], GOLD)
gold.data.materials.append(GOLD_IN)


def _mk_obj(name, bm, material, smooth=True):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(material)
    col.objects.link(o); o.parent = root
    for p in me.polygons:
        p.use_smooth = smooth and len(p.vertices) == 4
    return o


def ribs(name, spans, z_base, sign, y0, y1, w=0.00178, h=RIB_H, seg=6):
    """Rounded ridges running along Y, repeating along X; sign +1 = up (top edge), -1 = down."""
    bm = bmesh.new()
    for xa, xb in spans:
        n = int((xb - xa) // RIB_P)
        off = xa + ((xb - xa) - n * RIB_P) / 2 + RIB_P / 2
        for i in range(n):
            xc = off + i * RIB_P
            prof = []
            for k in range(seg + 1):
                a = math.pi * k / seg
                prof.append((xc + (w / 2) * math.cos(a), z_base + sign * h * math.sin(a) ** 0.6))
            v0 = [bm.verts.new((x, y0, z)) for x, z in prof]
            v1 = [bm.verts.new((x, y1, z)) for x, z in prof]
            for k in range(seg):
                bm.faces.new((v0[k], v0[k + 1], v1[k + 1], v1[k]))
            bm.faces.new(v0); bm.faces.new(list(reversed(v1)))
    return _mk_obj(name, bm, GOLD_RIB)


ribs('Shroud_Ribs_Top', [(0.0, L)], Z_TOP - RIB_H, +1, Y_FRONT, Y_GOLD)
rb_near = ribs('Shroud_Ribs_Bottom_Near', [(0.0, X_STEP)], Z_NEAR, -1, Y_FRONT, Y_GOLD, h=RIB_H * 0.9)
rb_far = ribs('Shroud_Ribs_Bottom_Far', [(X_STEP, L)], Z_FAR, -1, Y_FRONT, Y_GOLD, h=RIB_H * 0.9)

# heatsink fins (horizontal plates, visible through the bracket vent and at the far end)
FIN_P = 0.0043
fins = []
z = Z_NEAR + WALL + 0.0028
while z < Z_TOP - RIB_H - WALL - 0.002:
    fins.append(((0.0006, Y_FRONT + WALL, z - 0.00028), (L - 0.0008, Y_GOLD, z + 0.00028)))
    z += FIN_P
boxes('Heatsink_Fins', fins, FINS)
# heatsink base plate (dark) behind the fins
boxes('Heatsink_Base', [((0.0006, Y_GOLD - 0.0012, Z_NEAR + WALL), (L - 0.0008, Y_GOLD, Z_TOP - RIB_H - WALL))], FINS)

# ---------------------------------------------------------------- black frame, PCB, back plate
boxes('Frame_Black', [
    ((0.0, Y_GOLD, Z_NEAR), (X_STEP, 0.0, Z_TOP)),
    ((X_STEP, Y_GOLD, Z_FAR), (L, 0.0, Z_TOP)),
], BLACK)
H['box']('PCB', (L - 0.002, 0.0016, Z_TOP - 0.0012 - 0.0003), (L / 2, 0.0008, (Z_TOP - 0.0012 + 0.0003) / 2), PCB, col, parent=root)
boxes('BackPlate', [
    ((0.0, 0.0016, Z_NEAR), (X_STEP, Y_BACK, Z_TOP - 0.0010)),
    ((X_STEP, 0.0016, Z_FAR), (L, Y_BACK, Z_TOP - 0.0010)),
], BACKPL)
# black top rail closing the PCB / back plate edge (one continuous matte strip as on the card)
boxes('Frame_TopRail', [((0.0, 0.0, Z_TOP - 0.0010), (L, Y_BACK, Z_TOP))], BLACK)
X0_PCIE = 0.0525   # key centre 59.05 mm from bracket face (brief Fig. 3)
H['pcie_edge'](root, col, dict(M, pcb=PCB), x0=X0_PCIE)

# ---------------------------------------------------------------- top edge: NVLink caps + printing
BRK = -0.0009      # outer face of the bracket plate (268.60 - 267.70)
caps = []
for a, b in ((0.0132, 0.0620), (0.0696, 0.1180), (0.1250, 0.1740)):
    caps.append(((BRK + a, -0.0041, Z_TOP), (BRK + b, Y_BACK - 0.0002, Z_TOP + 0.0004)))
boxes('NVLink_Caps', caps, CAP)
for i, (a, b) in enumerate(((0.0132, 0.0620), (0.0696, 0.1180), (0.1250, 0.1740))):
    text('Top_NVLINK_%d' % i, 'NVLINK', 0.0018, PRINT_GREY, (BRK + (a + b) / 2, -0.0073, Z_TOP + 0.00002), ROT_TOP,
         font=FONT_REG, fit_w=0.0072)
text('Top_H100', 'H100', 0.0026, PRINT_GOLD, (BRK + 0.0068, -0.0016, Z_TOP + 0.00002), ROT_TOP, font=FONT_REG, fit_w=0.0058)
text('Top_NVIDIA', 'NVIDIA', 0.005, PRINT_GOLD, (0.2494, -0.0046, Z_TOP + 0.00002), ROT_TOP, font=FONT_BLACK,
     fit_w=0.0205, fit_h=0.0048)
# NVIDIA eye badge: beige square with a dark eye cut-out
EX, EY = 0.2342, -0.0046
H['box']('Top_Eye_Badge', (0.0070, 0.0058, 0.00012), (EX, EY, Z_TOP + 0.00006), PRINT_GOLD, col, parent=root)


def ellipse(cx, cy, rx, ry, n=28):
    return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n)]


H['ring']('Top_Eye_Ring', ellipse(EX - 0.0006, EY, 0.0026, 0.0017), ellipse(EX - 0.0006, EY, 0.0019, 0.0011),
          'xy', Z_TOP + 0.00012, 0.00004, BLACK, col, parent=root)
H['prism']('Top_Eye_Pupil', ellipse(EX - 0.0004, EY, 0.0007, 0.0007, 16), 'xy', Z_TOP + 0.00012, 0.00004, BLACK, col, parent=root)
H['box']('Top_Eye_Cut', (0.0016, 0.0058, 0.00004), (EX - 0.0035 + 0.0008, EY, Z_TOP + 0.00014), BLACK, col, parent=root)

# ---------------------------------------------------------------- far end: 16-pin power + recess
CZ0, CZ1 = 0.0778, 0.0957          # connector body along Z (brief end view)
CY0, CY1 = -0.0098, -0.0006
H['box']('Power_16pin', (0.0090, CY1 - CY0, CZ1 - CZ0), (L + 0.0004 - 0.0045, (CY0 + CY1) / 2, (CZ0 + CZ1) / 2), PLASTIC, col, parent=root)
H['box']('Power_16pin_Latch', (0.0030, 0.0012, 0.0050), (L - 0.0012, CY0 - 0.0006, (CZ0 + CZ1) / 2), PLASTIC, col, parent=root)


def pin_holes():
    for r in range(6):
        zc = CZ0 + 0.0015 + 0.0015 + r * 0.0030
        for yc in (-0.0083, -0.0053):
            yield (L + 0.00045, yc, zc), (0.0002, 0.0022, 0.0022)
    for r in range(4):
        zc = (CZ0 + CZ1) / 2 + (r - 1.5) * 0.0025
        yield (L + 0.00045, -0.0026, zc), (0.0002, 0.0011, 0.0012)


H['slat_array']('Power_16pin_Holes', pin_holes, PORT, col, root)
H['box']('End_Recess', (0.0002, 0.0072, 0.040), (L + 0.0001, -0.0058, 0.040), PORT, col, parent=root)
for i, zc in enumerate((0.022, 0.058)):
    H['cyl']('End_Insert_%d' % i, 0.0017, 0.0004, (L + 0.0002, -0.0058, zc), SCREW, col, verts=16, rot=(0, math.pi / 2, 0), parent=root)
    H['cyl']('End_Insert_Hole_%d' % i, 0.0009, 0.0004, (L + 0.0004, -0.0058, zc), PORT, col, verts=12, rot=(0, math.pi / 2, 0), parent=root)

# ---------------------------------------------------------------- back plate details
for i, (xc, zc) in enumerate(((0.0070, 0.0949), (0.0070, 0.0134), (0.2600, 0.0949), (0.2600, 0.0110))):
    H['cyl']('Back_Screw_%d' % i, 0.0019, 0.0006, (xc, Y_BACK + 0.0003, zc), SCREW, col, verts=20, rot=(math.pi / 2, 0, 0), parent=root)
    H['box']('Back_Screw_%d_Slot' % i, (0.0022, 0.0002, 0.0005), (xc, Y_BACK + 0.00065, zc), PORT, col, parent=root)
H['box']('Back_Label', (0.0090, 0.0001, 0.0250), (0.0072, Y_BACK + 0.00005, 0.0730), LABEL, col, parent=root)
H['box']('Back_Label2', (0.0050, 0.0001, 0.0135), (0.0150, Y_BACK + 0.00005, 0.0782), LABEL, col, parent=root)
for i, (s, xc, zc) in enumerate((('MODEL: P1010', 0.0040, 0.0790), ('NVIDIA CORP', 0.0062, 0.0794),
                                   ('900-21010-0300-030', 0.0084, 0.0760), ('SANTA CLARA  MADE IN CHINA', 0.0106, 0.0730))):
    text('Back_Text_%d' % i, s, 0.0012, LABEL_TXT, (xc, Y_BACK + 0.00012, zc), ROT_BACK, font=FONT_REG, res=2)
text('Back_Text_PN', '699-21010-0200-600', 0.0011, LABEL_TXT, (0.0140, Y_BACK + 0.00012, 0.0782), ROT_BACK, font=FONT_REG, res=2)
text('Back_Text_VB', 'VBIOS 96.00.30.00.01', 0.0010, LABEL_TXT, (0.0160, Y_BACK + 0.00012, 0.0782), ROT_BACK, font=FONT_REG, res=2)

# ---------------------------------------------------------------- bracket (FHFL, vented)
BX0, BX1 = BRK, 0.0
Z_TAB = 0.0924      # 104.86 mm above finger bottom (brief Fig. 3)
Z_BOT = -0.0081
plate = H['prism']('Bracket', [(-0.0370, Z_BOT), (-0.0030, Z_BOT), (0.0030, -0.0010), (0.0030, Z_TAB), (-0.0370, Z_TAB)],
                   'yz', BX0, BX1 - BX0, BRACKET, col, parent=root)
WIN = (-0.0335, -0.0115, 0.0085, 0.0875)  # y0, y1, z0, z1
cutter = H['box']('Bracket_WinCut', (0.01, WIN[1] - WIN[0], WIN[3] - WIN[2]), (BX0, (WIN[0] + WIN[1]) / 2, (WIN[2] + WIN[3]) / 2), BRACKET, col)
H['cut'](plate, cutter)
H['prism']('Bracket_Tongue', [(-0.0100, Z_BOT + 0.0005), (-0.0020, Z_BOT + 0.0005), (-0.0030, -0.0262), (-0.0090, -0.0262)],
           'yz', BX0, BX1 - BX0, BRACKET, col, parent=root)
# tab (bent outward, toward -X) with two edge notches and a screw hole
tab_items = []
segs = [(-0.0355, -0.0250, -0.0120), (-0.0250, -0.0231, -0.0092), (-0.0231, -0.0222, -0.0120),
        (-0.0176, -0.0043, -0.0120), (-0.0043, -0.0024, -0.0092), (-0.0024, 0.0030, -0.0120)]
for y0, y1, x0 in segs:
    tab_items.append(((x0, y0, Z_TAB - 0.0009), (BX0, y1, Z_TAB)))
# screw hole (y -0.0222..-0.0176, x -0.0087..-0.0045) left open between two bars
tab_items.append(((-0.0120, -0.0222, Z_TAB - 0.0009), (-0.0087, -0.0176, Z_TAB)))
tab_items.append(((-0.0045, -0.0222, Z_TAB - 0.0009), (BX0, -0.0176, Z_TAB)))
tab = boxes('Bracket_Tab', tab_items, BRACKET)
# vent frame (raised plate with 4 screws) and the outer window edge
ring_out = [(-0.0366, 0.0044), (-0.0084, 0.0044), (-0.0084, 0.0916), (-0.0366, 0.0916)]
ring_in = [(WIN[0], WIN[2]), (WIN[1], WIN[2]), (WIN[1], WIN[3]), (WIN[0], WIN[3])]
H['ring']('Bracket_VentFrame', ring_out, ring_in, 'yz', BX0, -0.0008, BRACKET, col, parent=root)
for i, (yc, zc) in enumerate(((-0.0351, 0.0061), (-0.0351, 0.0899), (-0.0099, 0.0061), (-0.0099, 0.0899))):
    H['cyl']('Bracket_Screw_%d' % i, 0.0013, 0.0007, (BX0 - 0.0008 - 0.00035, yc, zc), BRACKET, col, verts=16, rot=(0, math.pi / 2, 0), parent=root)
    H['box']('Bracket_Screw_%d_Torx' % i, (0.0002, 0.0012, 0.0005), (BX0 - 0.0008 - 0.0008, yc, zc), PORT, col, parent=root)

# ---------------------------------------------------------------- sockets
H['sockets'](root, col, power_in=(L + 0.0006, (CY0 + CY1) / 2, (CZ0 + CZ1) / 2), pcie=(X0_PCIE + 0.047, 0.0008, -0.0085))

for o in root.children_recursive:
    if o.type == 'MESH':
        H['apply_all'](o)

# ---------------------------------------------------------------- save / export / renders
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BASE, 'gpu_08_h100_pcie.blend'))
tris = H['export_glb'](ROOT, os.path.join(BASE, 'export', 'gpu_h100_pcie.glb'))
print('TRIANGLES', tris)

sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.render.image_settings.file_format = 'PNG'


def cam(name, loc, target, lens=50, ortho=None):
    c = bpy.data.objects.get(name)
    if not c:
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.data.collections['Studio'].objects.link(c)
    c.location = loc
    c.rotation_euler = (mathutils.Vector(target) - mathutils.Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    c.data.lens = lens; c.data.clip_start = 0.005
    if ortho:
        c.data.type = 'ORTHO'; c.data.ortho_scale = ortho
    return c


C = (0.134, -0.016, 0.045)
views = {
    'front': cam('R_front', (0.134, -0.72, 0.20), (0.134, 0, 0.046), 60),
    'back': cam('R_back', (0.134, 0.72, 0.20), (0.134, 0, 0.046), 60),
    'top': cam('R_top', (0.134, -0.12, 0.62), (0.134, -0.016, 0.098), 60),
    '34': cam('R_34', (-0.20, -0.50, 0.28), C, 55),
    'bracket': cam('R_bracket', (-0.30, -0.22, 0.13), (0.0, -0.017, 0.045), 70),
    'power': cam('R_power', (0.52, -0.16, 0.20), (0.262, -0.010, 0.075), 70),
    'detail_top': cam('R_detail_top', (0.06, -0.20, 0.22), (0.09, -0.005, 0.097), 60),
}
only = os.environ.get('H100_VIEWS')
for k, c in views.items():
    if only and k not in only.split(','):
        continue
    sc.camera = c
    mp = next((n for n in sc.world.node_tree.nodes if n.type == 'MAPPING'), None)
    if mp:   # the glossy floor mirrors the HDRI; turn the studio for the back view so it stays neutral
        mp.inputs['Rotation'].default_value[2] = math.pi if k == 'back' else 0.0
    sc.render.filepath = os.path.join(BASE, 'renders', 'h100_pcie_%s.png' % k)
    bpy.ops.render.render(write_still=True)
print('DONE')
