"""NVIDIA GeForce RTX 4090 Founders Edition (Oct 2022) - build script.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python <this file>

Reference-derived layout (mm, x from bracket, z from PCIe finger bottom=-12.5):
  shroud 304 x 123 (z 1.5..124.5), 61 thick (y -55..+6)
  silver X frame: centre x=153, triangle bases x=98..208
  front (-Y): fan pod near bracket (fan centre x=62), exposed slanted fins in the
              middle triangles, chevron fin stack in the far pod
  back  (+Y): dark plate + "RTX 4090" near bracket, dark triangles, fan at far end (x=243)
  top edge  : silver pods, exposed fins in the middle with black rail on the +Y side,
              16-pin 12VHPWR pointing straight up (x~190), "GEFORCE RTX" on far pod
"""
import bpy, bmesh, math, mathutils

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']

ROOT = 'RTX4090_FE'
OUT_BLEND = r'C:\laragon\www\scaling-law\blender\gpu_07_rtx4090_fe.blend'
OUT_GLB = r'C:\laragon\www\scaling-law\blender\export\gpu_rtx4090_fe.glb'
OUT_REN = r'C:\laragon\www\scaling-law\blender\renders\rtx4090_fe_{}.png'
FONT_B = r'C:\Windows\Fonts\segoeuib.ttf'
FONT_R = r'C:\Windows\Fonts\segoeui.ttf'

root, col = H['new_card_scene'](ROOT)
M = H['base_materials']()
mat = H['mat']
M['frame'] = mat('RTX40_FrameAlu', (0.31, 0.295, 0.28), 1.0, 0.38)
M['fin'] = mat('RTX40_FinBlack', (0.012, 0.012, 0.013), 0.0, 0.75, spec=0.06)
M['cavity'] = mat('RTX40_Cavity', (0.006, 0.006, 0.007), 0.3, 0.55, spec=0.2)
M['plate'] = mat('RTX40_BackPlate', (0.030, 0.030, 0.030), 0.25, 0.45, spec=0.25)
M['blade'] = mat('RTX40_FanBlade', (0.018, 0.018, 0.020), 0.0, 0.50, spec=0.3)
M['hub'] = mat('RTX40_HubSpun', (0.07, 0.07, 0.072), 0.6, 0.30, aniso=0.6)
M['label'] = mat('RTX40_Label', (0.55, 0.55, 0.56), 0.0, 0.5)
M['led'] = mat('RTX40_LogoLED', (0.75, 0.76, 0.78), 0.0, 0.4, emit=(1, 1, 1), emit_str=0.8)
M['bracket'] = mat('RTX40_Bracket', (0.20, 0.20, 0.20), 1.0, 0.38)
M['void'] = mat('RTX40_Void', (0.002, 0.002, 0.002), 0.0, 1.0, spec=0.0)
M['conn'] = mat('RTX40_ConnPlastic', (0.012, 0.012, 0.013), 0.0, 0.5, spec=0.3)

# ---------------------------------------------------------------- dimensions
XL, XR = 0.0, 0.304
ZB, ZT = 0.0015, 0.1245
ZC = (ZB + ZT) / 2
YF, YB = -0.0550, 0.0060
XC = 0.153
XT0, XT1 = 0.098, 0.208          # triangle base corners (top & bottom)
RIM = 0.0052                     # silver rim width on the faces
FAN_F = (0.062, ZC)              # front fan centre (x, z)
FAN_B = (0.243, ZC)              # back fan centre
FAN_WELL_R = 0.0592


# ---------------------------------------------------------------- 2D helpers
def area2(p):
    return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))


def ccw(p):
    return p if area2(p) > 0 else list(reversed(p))


def offset_convex(pts, d):
    """Inset a convex polygon by d (positive = inward)."""
    p = ccw(pts); n = len(p); lines = []
    for i in range(n):
        a, b = p[i], p[(i + 1) % n]
        dx, dz = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dz)
        nx, nz = -dz / L, dx / L
        lines.append(((a[0] + nx * d, a[1] + nz * d), (dx, dz)))
    out = []
    for i in range(n):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        den = d1[0] * d2[1] - d1[1] * d2[0]
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    return out


def rounded(pts, radii, seg=6):
    """Round each corner of a polygon with its own radius."""
    n = len(pts); out = []
    for i in range(n):
        p = mathutils.Vector(pts[i]); a = mathutils.Vector(pts[i - 1]); b = mathutils.Vector(pts[(i + 1) % n])
        r = radii[i] if isinstance(radii, (list, tuple)) else radii
        if r <= 0:
            out.append(tuple(p)); continue
        u1 = (a - p).normalized(); u2 = (b - p).normalized()
        ang = u1.angle(u2); half = ang / 2
        d = r / math.tan(half)
        bis = (u1 + u2).normalized(); c = p + bis * (r / math.sin(half))
        t1 = p + u1 * d; t2 = p + u2 * d
        a1 = math.atan2(t1.y - c.y, t1.x - c.x); a2 = math.atan2(t2.y - c.y, t2.x - c.x)
        da = a2 - a1
        while da > math.pi: da -= 2 * math.pi
        while da < -math.pi: da += 2 * math.pi
        for k in range(seg + 1):
            aa = a1 + da * k / seg
            out.append((c.x + r * math.cos(aa), c.y + r * math.sin(aa)))
    return out


def clip_seg(p0, p1, poly):
    """Cyrus-Beck: clip segment to convex polygon. Returns (q0, q1) or None."""
    p = ccw(poly); t0, t1 = 0.0, 1.0
    dx, dz = p1[0] - p0[0], p1[1] - p0[1]
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        nx, nz = -(b[1] - a[1]), b[0] - a[0]            # inward normal (CCW)
        num = nx * (p0[0] - a[0]) + nz * (p0[1] - a[1])
        den = nx * dx + nz * dz
        if abs(den) < 1e-12:
            if num < 0: return None
            continue
        t = -num / den
        if den > 0: t0 = max(t0, t)
        else: t1 = min(t1, t)
        if t0 > t1: return None
    return (p0[0] + dx * t0, p0[1] + dz * t0), (p0[0] + dx * t1, p0[1] + dz * t1)


def minus_circle_h(x0, x1, z, c, R):
    """Split horizontal segment [x0,x1] at height z by a circle hole."""
    dzc = z - c[1]
    if abs(dzc) >= R: return [(x0, x1)]
    dx = math.sqrt(R * R - dzc * dzc)
    return [s for s in ((x0, c[0] - dx), (c[0] + dx, x1)) if s[1] - s[0] > 0.0015]


def bm_strip(bm, q0, q1, th, y0, y1):
    """Thin plate whose centre line is q0->q1 in XZ, thickness th, extruded along Y."""
    dx, dz = q1[0] - q0[0], q1[1] - q0[1]; L = math.hypot(dx, dz)
    if L < 0.001: return
    nx, nz = -dz / L * th / 2, dx / L * th / 2
    ring = [(q0[0] + nx, q0[1] + nz), (q1[0] + nx, q1[1] + nz), (q1[0] - nx, q1[1] - nz), (q0[0] - nx, q0[1] - nz)]
    v0 = [bm.verts.new((x, y0, z)) for x, z in ring]
    v1 = [bm.verts.new((x, y1, z)) for x, z in ring]
    bm.faces.new(v0); bm.faces.new(list(reversed(v1)))
    for k in range(4):
        j = (k + 1) % 4
        bm.faces.new((v0[k], v0[j], v1[j], v1[k]))


def cut_mat(obj, cutter, remove=True):
    """Boolean difference that gives the new walls the cutter's material."""
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


def cyl_cutter(name, cx, cz, r, y0, y1, material):
    o = H['cyl'](name, r, abs(y1 - y0), (cx, (y0 + y1) / 2, cz), material, col, verts=64, rot=(math.pi / 2, 0, 0))
    return o


def look(cam, target, up_hint=None):
    d = mathutils.Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


# ---------------------------------------------------------------- pods (silver frame)
L_OUT = [(XL, ZB), (XT0, ZB), (XC + 0.003, ZC), (XT0, ZT), (XL, ZT)]
R_OUT = [(XR, ZB), (XR, ZT), (XT1, ZT), (XC - 0.003, ZC), (XT1, ZB)]
L_POLY = rounded(L_OUT, [0.009, 0.006, 0.003, 0.006, 0.009], 6)
R_POLY = rounded(R_OUT, [0.011, 0.011, 0.006, 0.003, 0.006], 6)

podL = H['prism']('Pod_Left', L_POLY, 'xz', YF, YB - YF, M['frame'], col, parent=root)
podR = H['prism']('Pod_Right', R_POLY, 'xz', YF, YB - YF, M['frame'], col, parent=root)
for o in (podL, podR):
    b = o.modifiers.new('Bevel', 'BEVEL'); b.width = 0.0042; b.segments = 4; b.limit_method = 'ANGLE'
    b.angle_limit = math.radians(50)
    H['apply_all'](o)

L_IN = offset_convex(L_OUT, RIM)
R_IN = offset_convex(R_OUT, RIM)
L_IN_R = rounded(L_IN, [0.005, 0.004, 0.002, 0.004, 0.005], 5)
R_IN_R = rounded(R_IN, [0.007, 0.007, 0.004, 0.002, 0.004], 5)

# front-left: recess + fan well
c = H['prism']('cut', L_IN_R, 'xz', YF - 0.003, 0.003 + 0.0060, M['cavity'], col)
cut_mat(podL, c)
c = cyl_cutter('cut', FAN_F[0], FAN_F[1], FAN_WELL_R, YF - 0.003, YF + 0.0225, M['cavity'])
cut_mat(podL, c)
# back-left: shallow recess for the dark back plate
c = H['prism']('cut', L_IN_R, 'xz', YB - 0.0012, 0.004, M['plate'], col)
cut_mat(podL, c)
# front-right: deep recess for the chevron fin stack
c = H['prism']('cut', R_IN_R, 'xz', YF - 0.003, 0.003 + 0.0100, M['cavity'], col)
cut_mat(podR, c)
# back-right: recess + fan well
c = H['prism']('cut', R_IN_R, 'xz', YB - 0.0050, 0.008, M['cavity'], col)
cut_mat(podR, c)
c = cyl_cutter('cut', FAN_B[0], FAN_B[1], FAN_WELL_R, YB - 0.0225, YB + 0.003, M['cavity'])
cut_mat(podR, c)
# tail end: shallow rectangular recess with a slot (support-bracket mount)
c = H['box']('cut', (0.004, 0.040, 0.034), (XR, -0.0255, 0.094), M['frame'], col)
cut_mat(podR, c)
H['box']('Tail_Slot', (0.0012, 0.016, 0.0016), (XR - 0.0002, -0.0255, 0.058), M['cavity'], col, parent=root)


# ---------------------------------------------------------------- fins
def build_fins():
    bm = bmesh.new()
    # middle triangles: top "/" fins, bottom "\" fins (through the full thickness)
    tri_top = [(XT0 + 0.001, ZT), (XT1 - 0.001, ZT), (XC, ZC + 0.002)]
    tri_bot = [(XT0 + 0.001, ZB), (XC, ZC - 0.002), (XT1 - 0.001, ZB)]
    ang = math.radians(52)
    for tri, sgn in ((tri_top, 1), (tri_bot, -1)):
        d = (math.cos(ang), sgn * math.sin(ang))
        x = XT0 - 0.12
        while x < XT1 + 0.02:
            zc0 = ZC
            p0 = (x - d[0] * 0.2, zc0 - d[1] * 0.2); p1 = (x + d[0] * 0.2, zc0 + d[1] * 0.2)
            s = clip_seg(p0, p1, tri)
            if s: bm_strip(bm, s[0], s[1], 0.0021, YF + 0.0012, YB - 0.0028)
            x += 0.0046
    # front-right chevron stack "<"
    cang = math.radians(38)
    a = XC - 0.06
    while a < XR:
        for sgn in (1, -1):
            p0 = (a, ZC); p1 = (a + math.cos(cang) * 0.3, ZC + sgn * math.sin(cang) * 0.3)
            s = clip_seg(p0, p1, R_IN)
            if s: bm_strip(bm, s[0], s[1], 0.0008, YF + 0.0015, YF + 0.0100)
        a += 0.0030
    # horizontal fins around the fans (front-left recess / back-right recess)
    for poly, fc, y0, y1 in ((L_IN, FAN_F, YF + 0.0032, YF + 0.0060), (R_IN, FAN_B, YB - 0.0050, YB - 0.0024)):
        z = ZB + 0.004
        while z < ZT - 0.003:
            for x0, x1 in minus_circle_h(XL - 0.01, XR + 0.01, z, fc, FAN_WELL_R + 0.0005):
                s = clip_seg((x0, z), (x1, z), poly)
                if s: bm_strip(bm, s[0], s[1], 0.0010, y0, y1)
            z += 0.0030
    # fins seen through the fans (well floors)
    for fc, y0, y1 in ((FAN_F, YF + 0.0200, YF + 0.0226), (FAN_B, YB - 0.0226, YB - 0.0200)):
        z = fc[1] - FAN_WELL_R + 0.002
        while z < fc[1] + FAN_WELL_R:
            dx = math.sqrt(max(FAN_WELL_R ** 2 - (z - fc[1]) ** 2, 0))
            if dx > 0.004: bm_strip(bm, (fc[0] - dx, z), (fc[0] + dx, z), 0.0010, y0, y1)
            z += 0.0030
    return _new_obj('Fins', bm, M['fin'], col, root)


fins = build_fins()

# black back triangles (+Y) - the back cover between the pods
for nm, tri in (('Back_TriTop', [(XT0, ZT), (XT1, ZT), (XC, ZC + 0.002)]),
                 ('Back_TriBot', [(XT0, ZB), (XC, ZC - 0.002), (XT1, ZB)])):
    t = rounded(offset_convex(tri, 0.0012), [0.002, 0.002, 0.004] if nm.endswith('Top') else [0.002, 0.004, 0.002], 4)
    H['prism'](nm, t, 'xz', YB - 0.0030, 0.0026, M['plate'], col, parent=root)

# black rail on the top edge (+Y side of the middle section)
H['box']('Top_Rail', (XT1 - XT0 - 0.004, 0.0105, 0.0045), ((XT0 + XT1) / 2, YB - 0.00525, ZT - 0.0020), M['plate'], col, bevel=0.0012, parent=root)
H['box']('Bot_Rail', (XT1 - XT0 - 0.004, 0.0105, 0.0035), ((XT0 + XT1) / 2, YB - 0.00525, ZB + 0.0015), M['plate'], col, bevel=0.0010, parent=root)

# back dark plate in left pod recess is the cut floor; logo text on it
def place_text(name, body, font, size, mtl, loc, rot):
    return H['text_mesh'](name, body, font, size, mtl, col, root, loc, rot, extrude=0.00018)


yl = YB - 0.0012 + 0.0002
tR = place_text('Back_Text_RTX', 'RTX', FONT_B, 0.0175, M['label'], (0, 0, 0), (-math.pi / 2, 0, 0))
tR.scale = (1.22, 1, 1)
t4 = place_text('Back_Text_4090', '4090', FONT_R, 0.0175, M['label'], (0, 0, 0), (-math.pi / 2, 0, 0))
t4.scale = (1.22, 1, 1)
bpy.context.view_layer.update()
wR, w4, gap = tR.dimensions.x, t4.dimensions.x, 0.0035
print('TEXTDIM', tR.dimensions, t4.dimensions)
x0 = 0.064 - (wR + gap + w4) / 2
tR.location = (x0 + wR / 2, yl, ZC)
t4.location = (x0 + wR + gap + w4 / 2, yl, ZC)

# "GEFORCE RTX" backlit logo on the top edge of the far pod (reads from the front side)
place_text('Top_Text', 'GEFORCE RTX', FONT_B, 0.0088, M['led'], (0.257, (YF + YB) / 2, ZT + 0.00005), (0, 0, 0))

# ---------------------------------------------------------------- 16-pin 12VHPWR (straight up)
PX, PY = 0.190, -0.0104
hz = 0.010
conn = H['box']('Power_16pin', (0.0215, 0.0098, hz), (PX, PY, ZT - hz / 2 + 0.0004), M['conn'], col, bevel=0.0005, parent=root)


def pin_holes():
    for i in range(6):
        for row in (-0.0016, 0.0016):
            yield (PX + (i - 2.5) * 0.0030, PY - 0.0010 + row, ZT + 0.0004), (0.0024, 0.0024, 0.009)
    yield (PX - 0.0035, PY + 0.0034, ZT + 0.0004), (0.0110, 0.0012, 0.006)   # sense pins slot


holes = H['slat_array']('cut', pin_holes, M['cavity'], col)
cut_mat(conn, holes)
c = H['box']('cut', (0.0225, 0.0106, 0.016), (PX, PY, ZT - 0.006), M['fin'], col)
cut_mat(fins, c)
H['sockets'](root, col, power_in=(PX, PY, ZT + 0.002), pcie=(0.081, 0.0008, -0.0085))

# ---------------------------------------------------------------- fans
def build_fan(name, centre, outward):
    """outward=-1: front (-Y) fan, +1: back (+Y) fan. Spin axis = empty's local Z."""
    cx, cz = centre
    yc = (YF + 0.0130) if outward < 0 else (YB - 0.0130)
    e = bpy.data.objects.new(name, None); e.empty_display_type = 'CIRCLE'; e.empty_display_size = 0.058
    col.objects.link(e); e.parent = root
    e.location = (cx, yc, cz)
    e.rotation_euler = (math.pi / 2 if outward < 0 else -math.pi / 2, 0, 0)
    mirror = -1 if outward < 0 else 1      # back fan = same fan seen from its exhaust side
    nb, rh, rt = 7, 0.0185, 0.0566
    bm = bmesh.new()
    NR, NS = 7, 6
    for b in range(nb):
        phb = b * 2 * math.pi / nb
        grid = []
        for i in range(NR):
            t = i / (NR - 1); r = rh + (rt - rh) * t
            span = 0.62 + 0.20 * t
            phc = phb + 0.55 * t ** 1.25
            pitch = 0.0085 * (1 - 0.45 * t)
            row = []
            for j in range(NS):
                s = j / (NS - 1)
                th = phc + (s - 0.5) * span
                z = (s - 0.5) * pitch - 0.0010 * math.sin(math.pi * s)
                row.append(bm.verts.new((mirror * r * math.cos(th), r * math.sin(th), z)))
            grid.append(row)
        for i in range(NR - 1):
            for j in range(NS - 1):
                bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    bl = _new_obj(name + '_Blades', bm, M['blade'], col, e)
    so = bl.modifiers.new('Solid', 'SOLIDIFY'); so.thickness = 0.0013; so.offset = 0
    H['apply_all'](bl)
    H['cyl'](name + '_Hub', 0.0195, 0.0110, (0, 0, -0.0003), M['blade'], col, verts=48, bevel=0.0008, parent=e)
    H['cyl'](name + '_Cap', 0.0170, 0.0008, (0, 0, 0.0055), M['hub'], col, verts=48, parent=e)
    ro = [(0.0582 * math.cos(a), 0.0582 * math.sin(a)) for a in [k * 2 * math.pi / 64 for k in range(64)]]
    ri = [(0.0565 * math.cos(a), 0.0565 * math.sin(a)) for a in [k * 2 * math.pi / 64 for k in range(64)]]
    H['ring'](name + '_Ring', ro, ri, 'xy', -0.0045, 0.0085, M['blade'], col, parent=e)
    return e


build_fan('Front_Fan', FAN_F, -1)
build_fan('Back_Fan', FAN_B, +1)

# ---------------------------------------------------------------- PCB + PCIe
H['box']('PCB', (0.190, 0.0016, 0.085), (0.003 + 0.095, 0.0008, -0.0005 + 0.0425), M['pcb'], col, parent=root)
H['pcie_edge'](root, col, M, x0=0.040)

# ---------------------------------------------------------------- bracket (3-slot)
BX, BT = -0.0010, 0.0010
BY0, BY1 = -0.0575, 0.0035
BZ0, BZ1 = -0.0030, 0.0985
br = H['box']('Bracket', (BT, BY1 - BY0, BZ1 - BZ0), (BX, (BY0 + BY1) / 2, (BZ0 + BZ1) / 2), M['bracket'], col, parent=root)
PORT_Z = [0.0145, 0.0375, 0.0605, 0.0835]          # HDMI lowest (next to PCIe), then 3x DP
PORT_Y = -0.0042


def bracket_holes():
    for k, z in enumerate(PORT_Z):
        if k == 0:
            yield (BX, PORT_Y, z), (0.004, 0.0062, 0.0150)
        else:
            yield (BX, PORT_Y, z), (0.004, 0.0060, 0.0168)
        yield (BX, -0.0228, z), (0.004, 0.0250, 0.0190)        # vent window


cut_mat(br, H['slat_array']('cut', bracket_holes, M['bracket'], col))
H['box']('Bracket_Tab', (0.0100, BY1 - BY0, BT), (BX - 0.0050, (BY0 + BY1) / 2, BZ1), M['bracket'], col, parent=root)
H['box']('Bracket_Tongue', (BT, 0.0070, 0.0180), (BX, -0.0060, BZ0 - 0.0090), M['bracket'], col, parent=root)


def vent_slats():
    for z in PORT_Z:
        zz = z - 0.0090
        while zz < z + 0.0090:
            yield (0.0035, -0.0228, zz), (0.0060, 0.0250, 0.0006)
            zz += 0.0016


H['slat_array']('Bracket_VentFins', vent_slats, M['fin'], col, root)
c = H['box']('cut', (0.0160, 0.0262, 0.0935), (0.0, -0.0228, 0.0490), M['void'], col)
cut_mat(podL, c)


def ports():
    for k, z in enumerate(PORT_Z):
        hz_ = 0.0150 if k == 0 else 0.0168
        yield (0.0050, PORT_Y, z), (0.0090, 0.0062, hz_)


H['slat_array']('Port_Shells', ports, M['steel'], col, root)


def port_inner():
    for k, z in enumerate(PORT_Z):
        hz_ = 0.0150 if k == 0 else 0.0168
        yield (0.0039, PORT_Y, z), (0.0086, 0.0048, hz_ - 0.0014)


H['slat_array']('Port_Inner', port_inner, M['port'], col, root)


def port_tongues():
    for k, z in enumerate(PORT_Z):
        yield (0.0038, PORT_Y + 0.0006, z), (0.0084, 0.0013, 0.0110)


H['slat_array']('Port_Tongues', port_tongues, M['plastic'], col, root)

# ---------------------------------------------------------------- tidy: parent check
for o in col.objects:
    if o is not root and o.parent is None:
        o.parent = root

# ---------------------------------------------------------------- save / export
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
tris = H['export_glb'](ROOT, OUT_GLB)
print('TRIS', tris)

# ---------------------------------------------------------------- renders
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.resolution_percentage = 100
studio = H['coll']('Studio')
views = {
    'front':   ((0.152, -0.95, 0.063), (0.152, 0.0, 0.056), 85),
    'back':    ((0.152, 0.95, 0.063), (0.152, 0.0, 0.056), 85),
    'top':     ((0.152, -0.06, 0.85), (0.152, -0.0245, 0.0), 85),
    'threeq':  ((-0.22, -0.46, 0.34), (0.145, -0.025, 0.045), 50),
    'back34':  ((0.52, 0.44, 0.33), (0.150, -0.020, 0.045), 50),
    'bracket': ((-0.40, -0.16, 0.10), (0.0, -0.025, 0.050), 60),
    'bracketface': ((-0.45, -0.026, 0.056), (0.0, -0.026, 0.056), 85),
    'topdet':  ((0.25, -0.17, 0.30), (0.200, -0.020, 0.115), 70),
}
import sys
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
    cam.data.lens = lens
    cam.data.clip_start = 0.01
    cam.location = pos; look(cam, tgt)
    sc.camera = cam
    sc.render.filepath = OUT_REN.format(nm)
    bpy.ops.render.render(write_still=True)
sc.camera = bpy.data.objects['Cam_threeq'] if bpy.data.objects.get('Cam_threeq') else sc.camera
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print('DONE')
