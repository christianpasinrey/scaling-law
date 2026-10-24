"""MSI GeForce RTX 4070 Ti SUPER 16G VENTUS 3X (Jan 2024) - build script.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python <this file> [-- view ...]

References: MSI datasheet + gallery product shots (front/back ortho, bracket), Lowyat review photos
(top edge with 16-pin + "msi" plate, bracket, backplate 3/4). Measured px -> mm (front 0.403 mm/px,
back 0.395 mm/px, bracket face = x 0, PCIe finger bottom = z -12.5):
  card 308 x 120 x 50 mm (MSI datasheet, SUPER OC)
  front (-Y): silver face plate, thin black frame, 3 wells R48.5 at x 55.2 / 155.7 / 256.0, z 54.9
              black trapezoid notches top & bottom between fans, black block bottom-left
              (identical to the non-SUPER RTX 4070 Ti VENTUS 3X)
  fans      : TORX FAN 4.0, 10 forward-curved blades (clockwise sweep seen from the front),
              black hub cap with silver rim + "msi"
  top edge  : black band "GEFORCE RTX" (x 20..100), silver/black "msi" plate (x 106..152),
              16-pin 12V-2x6 pins-up at x 162.5 right after the plate, exposed fins + heat pipes
  back (+Y) : brushed black backplate, nickel X retention bracket with PCB window (x 94, z 47),
              "GEFORCE RTX" along the bracket end, notch over the 16-pin, slanted flow-through
              cut-outs over the tail (x > 183) with a solid diagonal band carrying "msi"
  bracket   : 2-slot nickel bracket, hexagon vent mesh, HDMI (lowest, next to PCIe) + 3x DP above
"""
import bpy, bmesh, math, mathutils, sys

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']

ROOT = 'MSI_RTX4070TiSuper_Ventus3X'
OUT_BLEND = r'C:\laragon\www\scaling-law\blender\gpu_15_msi_rtx4070ti_ventus3x.blend'
OUT_GLB = r'C:\laragon\www\scaling-law\blender\export\gpu_msi_rtx4070ti_ventus3x.glb'
OUT_REN = r'C:\laragon\www\scaling-law\blender\renders\msi_4070ti_{}.png'
FONT_B = r'C:\Windows\Fonts\segoeuib.ttf'
FONT_BI = r'C:\Windows\Fonts\seguibli.ttf'

root, col = H['new_card_scene'](ROOT)
M = H['base_materials']()
mat = H['mat']
M['silver'] = mat('MSI_SilverFace', (0.46, 0.47, 0.49), 0.85, 0.30, aniso=0.3)
M['body'] = mat('MSI_ShroudBlack', (0.005, 0.005, 0.0055), 0.0, 0.50, spec=0.25)
M['blade'] = mat('MSI_FanBlade', (0.006, 0.006, 0.007), 0.0, 0.42, spec=0.30)
M['cap'] = mat('MSI_HubCap', (0.012, 0.012, 0.013), 0.2, 0.32, spec=0.4)
M['white'] = mat('MSI_PrintWhite', (0.80, 0.80, 0.81), 0.0, 0.40)
M['grey'] = mat('MSI_PrintGrey', (0.22, 0.22, 0.23), 0.3, 0.40)
M['plate'] = mat('MSI_BackPlate', (0.012, 0.012, 0.013), 0.5, 0.42, aniso=0.5)
M['gloss'] = mat('MSI_GlossBlack', (0.006, 0.006, 0.007), 0.3, 0.16)
M['fin'] = mat('MSI_Fins', (0.22, 0.22, 0.23), 0.9, 0.38)
M['pipe'] = mat('MSI_HeatPipe', (0.36, 0.30, 0.26), 1.0, 0.35)
M['xbr'] = mat('MSI_XBracket', (0.28, 0.28, 0.29), 1.0, 0.32, aniso=0.4)
M['copper'] = mat('MSI_Copper', (0.80, 0.42, 0.25), 1.0, 0.35)
M['cavity'] = mat('MSI_Cavity', (0.005, 0.005, 0.006), 0.2, 0.6, spec=0.2)
M['bracket'] = mat('MSI_Bracket', (0.62, 0.62, 0.64), 1.0, 0.30)
M['conn'] = mat('MSI_ConnPlastic', (0.012, 0.012, 0.013), 0.0, 0.5, spec=0.3)
M['comp'] = mat('MSI_Component', (0.35, 0.28, 0.18), 0.6, 0.4)

# ---------------------------------------------------------------- dimensions (m)
XL, XR = 0.0030, 0.3080          # shroud length (bracket face at x 0)
ZB, ZT = -0.0007, 0.1072         # shroud bottom / top
YF = -0.0440                     # front of the silver face (50 mm total thickness)
YBODY0, YBODY1 = -0.0430, -0.0285  # black shroud body (fan side)
YBP0, YBP1 = 0.0045, 0.0060      # backplate
FANS = [(0.0552, 0.0549), (0.1557, 0.0549), (0.2560, 0.0549)]
WELL_R = 0.0485
PCB_END = 0.1800
PX = 0.1625                      # 16-pin connector centre x


# ---------------------------------------------------------------- helpers
def rounded(pts, radii, seg=6):
    n = len(pts); out = []
    for i in range(n):
        p = mathutils.Vector(pts[i]); a = mathutils.Vector(pts[i - 1]); b = mathutils.Vector(pts[(i + 1) % n])
        r = radii[i] if isinstance(radii, (list, tuple)) else radii
        if r <= 0:
            out.append(tuple(p)); continue
        u1 = (a - p).normalized(); u2 = (b - p).normalized()
        half = u1.angle(u2) / 2
        d = r / math.tan(half)
        c = p + (u1 + u2).normalized() * (r / math.sin(half))
        t1 = p + u1 * d; t2 = p + u2 * d
        a1 = math.atan2(t1.y - c.y, t1.x - c.x); a2 = math.atan2(t2.y - c.y, t2.x - c.x)
        da = a2 - a1
        while da > math.pi: da -= 2 * math.pi
        while da < -math.pi: da += 2 * math.pi
        for k in range(seg + 1):
            aa = a1 + da * k / seg
            out.append((c.x + r * math.cos(aa), c.y + r * math.sin(aa)))
    return out


def inset(pts, d):
    """Shrink a convex polygon towards its centroid by roughly d."""
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    out = []
    for x, y in pts:
        L = math.hypot(x - cx, y - cy)
        out.append((x - (x - cx) / L * d, y - (y - cy) / L * d))
    return out


def new_obj(name, bm, material, parent=root):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(material); col.objects.link(o)
    if parent: o.parent = parent
    return o


def bm_strip(bm, q0, q1, th, y0, y1):
    """Flat band whose centre line is q0->q1 in XZ (width th), extruded along Y."""
    dx, dz = q1[0] - q0[0], q1[1] - q0[1]; L = math.hypot(dx, dz)
    if L < 1e-5: return
    nx, nz = -dz / L * th / 2, dx / L * th / 2
    ring = [(q0[0] + nx, q0[1] + nz), (q1[0] + nx, q1[1] + nz), (q1[0] - nx, q1[1] - nz), (q0[0] - nx, q0[1] - nz)]
    v0 = [bm.verts.new((x, y0, z)) for x, z in ring]
    v1 = [bm.verts.new((x, y1, z)) for x, z in ring]
    bm.faces.new(v0); bm.faces.new(list(reversed(v1)))
    for k in range(4):
        j = (k + 1) % 4
        bm.faces.new((v0[k], v0[j], v1[j], v1[k]))


def cut_mat(obj, cutter, remove=True):
    """Boolean difference; new walls get the cutter's material."""
    H['apply_all'](obj)
    for m in cutter.data.materials:
        if m and m.name not in [x.name for x in obj.data.materials if x]:
            obj.data.materials.append(m)
    mod = obj.modifiers.new('Cut', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'; mod.solver = 'EXACT'; mod.object = cutter
    try:
        mod.material_mode = 'TRANSFER'
    except Exception:
        pass
    H['apply_all'](obj)
    if remove:
        bpy.data.objects.remove(cutter, do_unlink=True)
    return obj


def cone_y(name, cx, cz, r_front, r_back, y_front, y_back, material, verts=72):
    """Truncated cone along Y (radius r_front at y_front, r_back at y_back)."""
    bm = bmesh.new()
    f = [bm.verts.new((cx + r_front * math.cos(2 * math.pi * k / verts), y_front, cz + r_front * math.sin(2 * math.pi * k / verts))) for k in range(verts)]
    b = [bm.verts.new((cx + r_back * math.cos(2 * math.pi * k / verts), y_back, cz + r_back * math.sin(2 * math.pi * k / verts))) for k in range(verts)]
    bm.faces.new(f); bm.faces.new(list(reversed(b)))
    for k in range(verts):
        j = (k + 1) % verts
        bm.faces.new((f[k], f[j], b[j], b[k]))
    return new_obj(name, bm, material, parent=None)


def text(name, body, font, size, mtl, loc, rotm, length=None, parent=root, extrude=0.00015, shear=0.0):
    """Text whose local +X (reading), +Y (letter up), +Z (normal) map to the columns of rotm."""
    rot = mathutils.Matrix(rotm).to_euler() if not isinstance(rotm[0], (int, float)) else rotm
    t = H['text_mesh'](name, body, font, size, mtl, col, parent, loc, rot, extrude=extrude, shear=shear)
    if length:
        bpy.context.view_layer.update()
        s = length / t.dimensions.x
        t.scale = (s, s, 1)
    return t


def look(cam, target):
    d = mathutils.Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


# ---------------------------------------------------------------- shroud body (black)
BODY = rounded([(XL, ZB), (XR, ZB), (XR, ZT), (XL, ZT)], [0.003, 0.008, 0.010, 0.006], 6)
body = H['prism']('Shroud_Body', BODY, 'xz', YBODY0, YBODY1 - YBODY0, M['body'], col, parent=root)
b = body.modifiers.new('Bevel', 'BEVEL'); b.width = 0.0022; b.segments = 2; b.limit_method = 'ANGLE'
H['apply_all'](body)
for i, (fx, fz) in enumerate(FANS):
    c = H['cyl']('cut', WELL_R, 0.030, (fx, YBODY0, fz), M['cavity'], col, verts=72, rot=(math.pi / 2, 0, 0))
    cut_mat(body, c)

# ---------------------------------------------------------------- silver face plate
SIL = rounded([(0.0050, 0.0033), (0.3050, 0.0033), (0.3050, 0.1060), (0.0050, 0.1060)], [0.003, 0.007, 0.009, 0.006], 6)
sil = H['prism']('Shroud_SilverFace', SIL, 'xz', YF, 0.0022, M['silver'], col, parent=root)
b = sil.modifiers.new('Bevel', 'BEVEL'); b.width = 0.0008; b.segments = 2; b.limit_method = 'ANGLE'
H['apply_all'](sil)
for fx, fz in FANS:
    cut_mat(sil, cone_y('cut', fx, fz, 0.0512, 0.0482, YF - 0.0004, YF + 0.0026, M['silver']))
# black notches between the fans (top & bottom) and the black block bottom-left
for xm in ((FANS[0][0] + FANS[1][0]) / 2, (FANS[1][0] + FANS[2][0]) / 2):
    top = [(xm - 0.0140, 0.1080), (xm - 0.0100, 0.1012), (xm + 0.0100, 0.1012), (xm + 0.0140, 0.1080)]
    bot = [(xm - 0.0180, 0.0010), (xm + 0.0180, 0.0010), (xm + 0.0140, 0.0082), (xm - 0.0140, 0.0082)]
    for poly in (top, bot):
        cut_mat(sil, H['prism']('cut', poly, 'xz', YF - 0.002, 0.006, M['body'], col))
cut_mat(sil, H['box']('cut', (0.019, 0.006, 0.014), (0.0115, YF + 0.001, 0.0040), M['body'], col))
# black fan-frame lip inside each well (dark ring between the silver chamfer and the blade tips)
for i, (fx, fz) in enumerate(FANS):
    ro_ = [(fx + 0.0484 * math.cos(2 * math.pi * k / 72), fz + 0.0484 * math.sin(2 * math.pi * k / 72)) for k in range(72)]
    ri_ = [(fx + 0.0466 * math.cos(2 * math.pi * k / 72), fz + 0.0466 * math.sin(2 * math.pi * k / 72)) for k in range(72)]
    H['ring']('Fan_Frame_%d' % (i + 1), ro_, ri_, 'xz', YBODY0 + 0.0002, 0.0050, M['body'], col, parent=root)


# ---------------------------------------------------------------- heatsink fin stack (vertical fins)
def fins():
    x = 0.0080
    while x < 0.3035:
        y0, y1 = YBODY1 - 0.0002, -0.0028
        if PX - 0.0125 < x < PX + 0.0125:
            y1 = -0.0128
        elif x > PCB_END:
            y1 = YBP0 - 0.0004
        yield (x, (y0 + y1) / 2, 0.0530), (0.00035, y1 - y0, 0.1020)
        x += 0.0021


H['slat_array']('Fin_Stack', fins, M['fin'], col, root)
H['box']('Fin_Base', (PCB_END - 0.010, 0.0012, 0.098), (0.010 + (PCB_END - 0.010) / 2, -0.0026, 0.0505), M['cavity'], col, parent=root)


def pipe(name, x0, x1, y, z, r=0.0029, down=-1):
    H['cyl'](name, r, x1 - x0, ((x0 + x1) / 2, y, z), M['pipe'], col, verts=16, rot=(0, math.pi / 2, 0), parent=root)
    for xe in (x0, x1):
        H['cyl'](name + '_End', r, 0.010, (xe, y, z + down * 0.005), M['pipe'], col, verts=16, parent=root)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=r, location=(xe, y, z))
        s = bpy.context.active_object; s.name = name + '_Bend'; s.data.materials.append(M['pipe'])
        for c in list(s.users_collection): c.objects.unlink(s)
        col.objects.link(s); s.parent = root


pipe('HeatPipe_T1', 0.046, 0.140, -0.0110, 0.1028)
pipe('HeatPipe_T2', 0.040, 0.146, -0.0172, 0.1030)
pipe('HeatPipe_T3', 0.052, 0.134, -0.0234, 0.1028)
pipe('HeatPipe_B1', 0.028, 0.112, -0.0130, 0.0032, down=1)
pipe('HeatPipe_B2', 0.036, 0.104, -0.0200, 0.0030, down=1)

H['box']('Tail_Cap', (0.0025, YBP0 - YBODY1, 0.103), (0.3060, (YBODY1 + YBP0) / 2, 0.0530), M['body'], col, bevel=0.0006, parent=root)

# ---------------------------------------------------------------- top edge branding
YT = (YBODY0 + YBODY1) / 2
text('Top_Text_GeForceRTX', 'GEFORCE RTX', FONT_B, 0.0090, M['white'], (0.0600, YT, ZT + 0.00002), (0, 0, 0), length=0.0780)
MSI_PLATE = [(0.1060, YT), (0.1110, -0.0426), (0.1470, -0.0426), (0.1520, YT), (0.1470, -0.0290), (0.1110, -0.0290)]
H['prism']('Top_MsiPlate', MSI_PLATE, 'xy', ZT - 0.0003, 0.0013, M['silver'], col, parent=root, bevel=0.0003)
H['prism']('Top_MsiPlateInset', inset(MSI_PLATE, 0.0018), 'xy', ZT + 0.0010, 0.0002, M['gloss'], col, parent=root)
text('Top_Text_msi', 'msi', FONT_BI, 0.0110, M['white'], (0.1290, YT, ZT + 0.00125), (0, 0, 0), length=0.0190)

# ---------------------------------------------------------------- PCB, PCIe, 16-pin
H['box']('PCB', (PCB_END - 0.0020, 0.0016, 0.0987), (0.0020 + (PCB_END - 0.0020) / 2, 0.0008, -0.0002 + 0.0987 / 2), M['pcb'], col, parent=root)
H['pcie_edge'](root, col, M, x0=0.040)

PZ0, PZ1 = 0.0880, 0.1018
conn = H['box']('Power_16pin', (0.0192, 0.0096, PZ1 - PZ0), (PX, -0.0058, (PZ0 + PZ1) / 2), M['conn'], col, bevel=0.0004, parent=root)


def pin_holes():
    for i in range(6):
        for row in (-0.0017, 0.0017):
            yield (PX + (i - 2.5) * 0.0030, -0.0068 + row, PZ1), (0.0023, 0.0023, 0.008)
    yield (PX, -0.0017, PZ1), (0.0120, 0.0011, 0.005)     # sense-pin row


cut_mat(conn, H['slat_array']('cut', pin_holes, M['cavity'], col))
H['sockets'](root, col, power_in=(PX, -0.0058, PZ1 + 0.002), pcie=(0.0878, 0.0008, -0.0085))

# ---------------------------------------------------------------- backplate (+Y)
K = 0.0003954


def B(u, v):
    """back reference shot (crop px) -> (x, z) metres"""
    return ((u - 33) * K, (v - 75) * K)


BPL = rounded([(0.0015, 0.0000), (XR, 0.0000), (XR, 0.1068), (0.0015, 0.1068)], [0.001, 0.002, 0.003, 0.001], 4)
bp = H['prism']('BackPlate', BPL, 'xz', YBP0, YBP1 - YBP0, M['plate'], col, parent=root)
CX, CZ = 0.0940, 0.0470
SCREWS_X = [(-0.0338, -0.0297), (0.0338, -0.0297), (-0.0338, 0.0297), (0.0338, 0.0297)]
OCT = [(CX + 0.0330 * math.cos(math.radians(22.5 + 45 * k)), CZ + 0.0330 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
cut_mat(bp, H['prism']('cut', OCT, 'xz', YBP0 - 0.001, 0.003, M['cavity'], col))
for dx, dz in SCREWS_X:
    L = math.hypot(dx, dz) + 0.0085; ang = math.atan2(dz, dx)
    arm = H['box']('cut', (L, 0.003, 0.0190), (CX + math.cos(ang) * L / 2, YBP0 + 0.0005, CZ + math.sin(ang) * L / 2), M['cavity'], col)
    arm.rotation_euler = (0, -ang, 0)
    cut_mat(bp, arm)
# notch over the 16-pin connector
cut_mat(bp, H['box']('cut', (0.0200, 0.006, 0.0160), (PX + 0.0004, YBP0, 0.1030), M['cavity'], col))
# slanted flow-through cut-outs over the tail
VENTS = [
    [(497.3, 236.7), (497.3, 189.3), (578.7, 95), (594, 95), (594, 106.7), (516.7, 236.7)],
    [(615, 171.7), (615, 136), (648.3, 95), (681.7, 95)],
    [(603.3, 255), (603.3, 221.7), (696.7, 95), (741.7, 95)],
    [(565, 326.7), (595, 326.7), (623.3, 290), (623.3, 260)],
    [(663.3, 321.7), (693.3, 321.7), (770, 233.3), (770, 206.7)],
    [(715, 321.7), (743.3, 321.7), (770, 290), (770, 260)],
    [(772, 171.7), (772, 140), (793.3, 117), (793.3, 150)],
    [(772, 231.7), (772, 196.7), (793.3, 173), (793.3, 208.3)],
    [(772, 305), (772, 260), (793.3, 234), (793.3, 276.7)],
]
for quad in VENTS:
    cut_mat(bp, H['prism']('cut', [B(u, v) for u, v in quad], 'xz', YBP0 - 0.001, 0.003, M['cavity'], col))

# retention X-bracket (nickel) + PCB window detail
OCT_O = [(CX + 0.0270 * math.cos(math.radians(22.5 + 45 * k)), CZ + 0.0270 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
OCT_I = [(CX + 0.0200 * math.cos(math.radians(22.5 + 45 * k)), CZ + 0.0200 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
H['ring']('XBracket_Ring', OCT_O, OCT_I, 'xz', 0.0030, 0.0040, M['xbr'], col, parent=root)
OCT_R = [(CX + 0.0207 * math.cos(math.radians(22.5 + 45 * k)), CZ + 0.0207 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
OCT_R2 = [(CX + 0.0190 * math.cos(math.radians(22.5 + 45 * k)), CZ + 0.0190 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
H['ring']('XBracket_WindowRim', OCT_R, OCT_R2, 'xz', 0.0024, 0.0048, M['bracket'], col, parent=root)


def xarms():
    bm = bmesh.new()
    for dx, dz in SCREWS_X:
        bm_strip(bm, (CX + dx * 0.55, CZ + dz * 0.55), (CX + dx * 1.10, CZ + dz * 1.10), 0.0110, 0.0030, 0.0068)
    return new_obj('XBracket_Arms', bm, M['xbr'])


xarms()
BP_SCREWS = [(114, 80), (455, 117), (607, 101), (787, 101), (114, 325), (287, 330), (392, 330), (607, 331), (787, 331)]
for i, (dx, dz) in enumerate(SCREWS_X):
    H['cyl']('XScrew_Washer_%d' % i, 0.0036, 0.0004, (CX + dx, 0.0069, CZ + dz), M['copper'], col, verts=20, rot=(math.pi / 2, 0, 0), parent=root)
    H['cyl']('XScrew_%d' % i, 0.0027, 0.0012, (CX + dx, 0.0075, CZ + dz), M['steel'], col, verts=16, rot=(math.pi / 2, 0, 0), parent=root)
for i, (u, v) in enumerate(BP_SCREWS):
    sx, sz = B(u, v)
    H['cyl']('Screw_%02d' % i, 0.0024, 0.0008, (sx, YBP1 + 0.0004, sz), M['steel'], col, verts=16, rot=(math.pi / 2, 0, 0), parent=root)


def pcb_parts():
    import random
    rnd = random.Random(4070)
    for _ in range(26):
        x = CX + rnd.uniform(-0.016, 0.016); z = CZ + rnd.uniform(-0.016, 0.016)
        yield (x, 0.0019, z), (rnd.choice((0.0012, 0.0020, 0.0030)), 0.0006, rnd.choice((0.0008, 0.0012, 0.0020)))
    for x, z in ((CX + 0.004, CZ + 0.008), (CX + 0.004, CZ - 0.002), (CX + 0.004, CZ - 0.010)):
        yield (x, 0.0020, z), (0.0050, 0.0008, 0.0070)


H['slat_array']('PCB_BackParts', pcb_parts, M['comp'], col, root)

# printed / gloss graphics on the backplate
YP0, YP1 = YBP1, YBP1 + 0.00020


def paths(name, segs, material, y0=YP0, y1=YP1):
    bm = bmesh.new()
    for pts, w in segs:
        P = [B(u, v) for u, v in pts]
        for a, c in zip(P[:-1], P[1:]):
            bm_strip(bm, a, c, w * K, y0, y1)
    return new_obj(name, bm, material)


paths('Back_GlossLines', [
    ([(40, 108), (100, 190)], 4),
    ([(103, 187), (117, 210), (117, 265), (150, 300), (330, 300)], 6),
], M['gloss'])
H['prism']('Back_GlossPanel', [B(u, v) for u, v in [(487, 325), (487, 240), (505, 218), (543, 218), (543, 310), (530, 325)]],
           'xz', YP0 - 0.00005, 0.00015, M['gloss'], col, parent=root)

# "GEFORCE RTX" along the bracket end: reads toward -Z, letter tops toward -X, facing +Y
ROT_GF = ((0, -1, 0), (0, 0, 1), (-1, 0, 0))
gx, gz = B(85, 212)
text('Back_Text_GeForceRTX', 'GEFORCE RTX', FONT_B, 0.0150, M['white'], (gx, YP1 + 0.0001, gz), ROT_GF, length=0.0930)
# "msi" on the solid diagonal band: reads up-right at ~50 deg toward +X/-Z
a = math.radians(50)
r_ = (math.cos(a), 0, -math.sin(a)); u_ = (-math.sin(a), 0, -math.cos(a)); n_ = (0, 1, 0)
ROT_MSI = tuple(tuple(v[i] for v in (r_, u_, n_)) for i in range(3))
mx, mz = B(695, 250)
text('Back_Text_msi', 'msi', FONT_BI, 0.0200, M['white'], (mx, YP1 + 0.0001, mz), ROT_MSI, length=0.0400)


# ---------------------------------------------------------------- fans (TORX FAN 4.0)
def build_fan(name, centre):
    cx, cz = centre
    e = bpy.data.objects.new(name, None); e.empty_display_type = 'CIRCLE'; e.empty_display_size = 0.046
    col.objects.link(e); e.parent = root
    e.location = (cx, -0.0362, cz)
    e.rotation_euler = (math.pi / 2, 0, 0)          # local +Z -> -Y (out of the front)
    nb, rh, rt = 10, 0.0150, 0.0450
    bm = bmesh.new(); NR, NS = 10, 7
    tips = []
    for bi in range(nb):
        phb = bi * 2 * math.pi / nb
        grid = []
        for i in range(NR):
            t = i / (NR - 1); r = rh + (rt - rh) * t
            span = 0.42 + 0.22 * t
            phc = phb - 1.05 * t ** 1.15                  # clockwise sweep seen from the front
            pitch = 0.0080 * (1 - 0.40 * t)
            row = []
            for j in range(NS):
                s = j / (NS - 1)
                th = phc + (s - 0.5) * span
                z = (s - 0.5) * pitch + 0.0012 * math.sin(math.pi * s)
                row.append(bm.verts.new((r * math.cos(th), r * math.sin(th), z)))
            grid.append(row)
        for i in range(NR - 1):
            for j in range(NS - 1):
                bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
        tips.append(phb - 1.05)
    bl = new_obj(name + '_Blades', bm, M['blade'], e)
    so = bl.modifiers.new('Solid', 'SOLIDIFY'); so.thickness = 0.0012; so.offset = 0
    H['apply_all'](bl)
    for pl in bl.data.polygons: pl.use_smooth = True
    # TORX 4.0: blade tips linked in pairs by a thin outer arc
    bm = bmesh.new()
    for bi in range(0, nb, 2):
        a0 = tips[bi] + 0.28; a1 = tips[bi] - 2 * math.pi / nb - 0.28
        n = 8; ro, ri = rt + 0.0004, rt - 0.0010
        vo0 = []; vi0 = []; vo1 = []; vi1 = []
        for k in range(n + 1):
            aa = a0 + (a1 - a0) * k / n
            for lst, rr, zz in ((vo0, ro, -0.0016), (vi0, ri, -0.0016), (vo1, ro, 0.0016), (vi1, ri, 0.0016)):
                lst.append(bm.verts.new((rr * math.cos(aa), rr * math.sin(aa), zz)))
        for k in range(n):
            bm.faces.new((vo0[k], vo0[k + 1], vo1[k + 1], vo1[k]))
            bm.faces.new((vi0[k], vi1[k], vi1[k + 1], vi0[k + 1]))
            bm.faces.new((vo1[k], vo1[k + 1], vi1[k + 1], vi1[k]))
            bm.faces.new((vo0[k], vi0[k], vi0[k + 1], vo0[k + 1]))
        bm.faces.new((vo0[0], vo1[0], vi1[0], vi0[0])); bm.faces.new((vo0[n], vi0[n], vi1[n], vo1[n]))
    new_obj(name + '_TipLinks', bm, M['blade'], e)
    H['cyl'](name + '_Hub', rh + 0.0005, 0.0100, (0, 0, 0.0005), M['blade'], col, verts=40, bevel=0.0006, parent=e)
    H['cyl'](name + '_Cap', 0.0153, 0.0008, (0, 0, 0.0059), M['cap'], col, verts=40, parent=e)
    ro_ = [(0.0157 * math.cos(2 * math.pi * k / 40), 0.0157 * math.sin(2 * math.pi * k / 40)) for k in range(40)]
    ri_ = [(0.0147 * math.cos(2 * math.pi * k / 40), 0.0147 * math.sin(2 * math.pi * k / 40)) for k in range(40)]
    H['ring'](name + '_CapRim', ro_, ri_, 'xy', 0.0050, 0.0016, M['silver'], col, parent=e)

    def marks():
        for sy in (-1, 1):
            yield (0, sy * 0.0105, 0.00635), (0.0110, 0.0006, 0.0002)
            for sx in (-1, 1):
                yield (sx * 0.0068, sy * 0.0094, 0.00635), (0.0030, 0.0005, 0.0002)
    H['slat_array'](name + '_CapMarks', marks, M['grey'], col, e)
    text(name + '_Logo', 'msi', FONT_BI, 0.0100, M['white'], (0, 0, 0.00635), (0, 0, 0), length=0.0185, parent=e)
    return e


for i, fc in enumerate(FANS):
    build_fan('Fan_%d' % (i + 1), fc)

# ---------------------------------------------------------------- bracket (2-slot, hex mesh)
BX, BT = -0.0005, 0.0010
BY0, BY1 = -0.0390, 0.0022
BZ0, BZ1 = -0.0030, 0.0906
br = H['box']('Bracket', (BT, BY1 - BY0, BZ1 - BZ0), (BX, (BY0 + BY1) / 2, (BZ0 + BZ1) / 2), M['bracket'], col, parent=root)
PORTS = [(0.0108, 'HDMI'), (0.0325, 'DP'), (0.0537, 'DP'), (0.0748, 'DP')]
PORT_Y = -0.0058


def port_holes():
    for z, kind in PORTS:
        yield (BX, PORT_Y, z), (0.004, 0.0062 if kind == 'DP' else 0.0058, 0.0168 if kind == 'DP' else 0.0152)


def hex_cutter():
    bm = bmesh.new(); rr = 0.00235; pitch = 0.0049
    zc, col_i = 0.0040, 0
    while zc < 0.0860:
        yc = -0.0352 + (0.00245 if col_i % 2 else 0)
        while yc < -0.0108:
            pts = [(yc + rr * math.cos(math.radians(60 * k)), zc + rr * math.sin(math.radians(60 * k))) for k in range(6)]
            v0 = [bm.verts.new((BX - 0.003, y, z)) for y, z in pts]
            v1 = [bm.verts.new((BX + 0.003, y, z)) for y, z in pts]
            bm.faces.new(v0); bm.faces.new(list(reversed(v1)))
            for k in range(6):
                j = (k + 1) % 6
                bm.faces.new((v0[k], v0[j], v1[j], v1[k]))
            yc += pitch
        zc += pitch * 0.866; col_i += 1
    return new_obj('cut', bm, M['bracket'], parent=None)


cut_mat(br, H['slat_array']('cut', port_holes, M['bracket'], col))
cut_mat(br, hex_cutter())
H['box']('Bracket_Tab', (0.0100, BY1 - BY0, BT), (BX - 0.0050, (BY0 + BY1) / 2, BZ1), M['bracket'], col, parent=root)
H['box']('Bracket_Tongue', (BT, 0.0070, 0.0180), (BX, -0.0055, BZ0 - 0.0090), M['bracket'], col, parent=root)


def port_shell():
    for z, kind in PORTS:
        hz = 0.0168 if kind == 'DP' else 0.0152
        yield (0.0065, PORT_Y, z), (0.0100, 0.0062 if kind == 'DP' else 0.0058, hz)


def port_inner():
    for z, kind in PORTS:
        hz = 0.0168 if kind == 'DP' else 0.0152
        yield (0.0062, PORT_Y, z), (0.0100, 0.0050, hz - 0.0012)


def port_tongue():
    for z, kind in PORTS:
        yield (0.0050, PORT_Y + 0.0006, z), (0.0084, 0.0012, 0.0110)


H['slat_array']('Port_Shells', port_shell, M['steel'], col, root)
H['slat_array']('Port_Inner', port_inner, M['port'], col, root)
H['slat_array']('Port_Tongues', port_tongue, M['plastic'], col, root)

# ---------------------------------------------------------------- tidy / save / export
for o in col.objects:
    if o is not root and o.parent is None:
        o.parent = root

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
tris = H['export_glb'](ROOT, OUT_GLB)
print('TRIS', tris)

# ---------------------------------------------------------------- renders
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.resolution_percentage = 100
studio = H['coll']('Studio')
views = {
    'front':   ((0.155, -0.95, 0.050), (0.155, 0.0, 0.050), 85),
    'back':    ((0.155, 0.95, 0.050), (0.155, 0.0, 0.050), 85),
    'top':     ((0.155, -0.02, 0.85), (0.155, -0.0195, 0.0), 85),
    'threeq':  ((-0.22, -0.46, 0.34), (0.150, -0.020, 0.045), 50),
    'back34':  ((0.52, 0.44, 0.33), (0.150, -0.020, 0.045), 50),
    'bracket': ((-0.42, -0.20, 0.12), (0.0, -0.020, 0.045), 60),
    'topdet':  ((0.22, -0.20, 0.30), (0.150, -0.020, 0.100), 70),
}
only = None
if '--' in sys.argv:
    a = sys.argv[sys.argv.index('--') + 1:]
    only = set(a) if a else None
for nm, (pos, tgt, lens) in views.items():
    if only and nm not in only:
        continue
    cn = 'Cam_' + nm
    cam = bpy.data.objects.get(cn)
    if not cam:
        cam = bpy.data.objects.new(cn, bpy.data.cameras.new(cn)); studio.objects.link(cam)
    cam.data.lens = lens; cam.data.clip_start = 0.01
    cam.location = pos; look(cam, tgt)
    sc.camera = cam
    sc.render.filepath = OUT_REN.format(nm)
    bpy.ops.render.render(write_still=True)
if bpy.data.objects.get('Cam_threeq'):
    sc.camera = bpy.data.objects['Cam_threeq']
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print('DONE')
