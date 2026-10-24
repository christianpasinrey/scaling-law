"""NVIDIA GeForce RTX 5090 Founders Edition (Jan 2025) - build script.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python <this file>

Reference-derived layout (mm, bracket at x=0, PCIe fingers down, fans toward -Y):
  body 304 x ~120 x 40 (2-slot), double flow-through: two 7-blade fans on the
  front, two exposed vertical fin stacks on the back, both inside rounded
  "pentagon" panels whose diagonals form the FE X at x=152.
  Top edge: gunmetal end caps (GEFORCE RTX on the far cap, once per half),
  a lower centre section with two LED slits and the angled 12V-2x6 connector
  pocket (front half) and an exposed fin channel (back half).
  Bracket: solid (no vents), port plate with HDMI (bottom) + 3x DP.
"""
import bpy, bmesh, math, mathutils, os

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']
V = mathutils.Vector

BASE = r'C:\laragon\www\scaling-law\blender'
ROOT = 'RTX5090_FE'
FONT = r'C:\Windows\Fonts\bahnschrift.ttf'

root, col = H['new_card_scene'](ROOT)
M = H['base_materials']()
mat = H['mat']
GUN = mat('R50_Gunmetal', (0.050, 0.052, 0.058), 0.85, 0.48)
FACE = mat('R50_FaceDark', (0.020, 0.021, 0.024), 0.5, 0.55, spec=0.3)
FLOOR = mat('R50_WellFloor', (0.022, 0.023, 0.026), 0.5, 0.5, spec=0.3)
FIN = mat('R50_Fins', (0.022, 0.022, 0.025), 0.75, 0.42, spec=0.4)
BLADE = mat('R50_Blade', (0.016, 0.017, 0.019), 0.0, 0.55, spec=0.28)
HUB = mat('R50_Hub', (0.20, 0.205, 0.22), 0.9, 0.30, aniso=0.5)
LED = mat('R50_LED', (0.85, 0.87, 0.9), 0.0, 0.4, emit=(1.0, 1.0, 1.0), emit_str=4.0)
TXT_TOP = mat('R50_TextTop', (0.55, 0.57, 0.60), 0.2, 0.45, emit=(0.75, 0.78, 0.82), emit_str=0.6)
TXT_BACK = mat('R50_TextBack', (0.30, 0.31, 0.33), 0.8, 0.35)
BRACKET = mat('R50_Bracket', (0.050, 0.053, 0.060), 0.8, 0.42)
CORE = M['port']

# ---------------------------------------------------------------- dimensions
L = 0.304                      # length
ZB, ZT = 0.004, 0.124          # body bottom / top (fingers stick out below ZB)
ZC = (ZB + ZT) / 2
XC = L / 2                     # centre of the X
YF, YB = -0.0215, 0.0185       # front (fan) face / back (fin) face -> 40 mm, 2 slots
YF_IN, YB_IN = -0.0015, 0.0025  # inner faces of the two halves (seam between)
CAP_A, CAP_B = 0.098, 0.206    # gunmetal end caps end/start on the top edge
W2 = 0.0012 * math.sqrt(2)     # X band half width projected on X
FAN_R = 0.0570                 # circular fan opening
FAN_X = (0.0615, L - 0.0615)


# ------------------------------------------------------------ local helpers
def rpoly(pts, radii, seg=6):
    """Round the corners of a convex 2D polygon. radii: one per vertex."""
    out = []
    n = len(pts)
    for i in range(n):
        p, v, q = V(pts[i - 1]), V(pts[i]), V(pts[(i + 1) % n])
        r = radii[i]
        a, b = (p - v), (q - v)
        la, lb = a.length, b.length
        a.normalize(); b.normalize()
        th = math.acos(max(-1.0, min(1.0, a.dot(b))))
        if r <= 0 or th > math.pi - 1e-3:
            out.append(tuple(v)); continue
        d = min(r / math.tan(th / 2), la * 0.49, lb * 0.49)
        r = d * math.tan(th / 2)
        t1, t2 = v + a * d, v + b * d
        bis = (a + b).normalized()
        c = v + bis * (r / math.sin(th / 2))
        a1 = math.atan2(t1.y - c.y, t1.x - c.x)
        a2 = math.atan2(t2.y - c.y, t2.x - c.x)
        da = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
        for k in range(seg + 1):
            ang = a1 + da * k / seg
            out.append((c.x + r * math.cos(ang), c.y + r * math.sin(ang)))
    return out


def span_at(poly, axis, val):
    """Intersection interval of a convex polygon (pts (x,z)) with the line coord[axis]=val."""
    o = 1 - axis
    hits = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        if (p[axis] - val) * (q[axis] - val) <= 0 and p[axis] != q[axis]:
            t = (val - p[axis]) / (q[axis] - p[axis])
            hits.append(p[o] + t * (q[o] - p[o]))
    if len(hits) < 2:
        return None
    return min(hits), max(hits)


def pentagon(side, e, rr_out, rr_diag, rr_tip):
    """Panel bounded by the outer frame (inset e) and the two X diagonals (inset by the band)."""
    xo = e if side < 0 else L - e
    dz = ZC - (ZB + e)
    xa = XC + side * (dz + W2)
    xt = XC + side * W2
    pts = [(xo, ZB + e), (xa, ZB + e), (xt, ZC), (xa, ZT - e), (xo, ZT - e)]
    return rpoly(pts, [rr_out, rr_diag, rr_tip, rr_diag, rr_out], seg=6)


def triangle(top, e, rr_base, rr_apex):
    zb = ZT - e if top else ZB + e
    s = abs(ZC - zb) - W2
    apex = ZC + (W2 if top else -W2)
    return rpoly([(XC - s, zb), (XC + s, zb), (XC, apex)], [rr_base, rr_base, rr_apex], seg=5)


def ybox(name, x0, x1, y0, y1, z0, z1, m, bevel=0.0, segs=2):
    return H['box'](name, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
                    m, col, bevel=bevel, segs=segs, parent=root)


def cutter_box(x0, x1, y0, y1, z0, z1):
    o = H['box']('_cut', (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), CORE, col)
    return o


def cut_many(targets, cutter):
    for t in targets:
        H['cut'](t, cutter, remove_cutter=False)
    bpy.data.objects.remove(cutter, do_unlink=True)


def text_on(name, body, size, center, d, u, m, extrude=0.00015):
    """Flat text whose reading direction is d and letter-up is u (normal = d x u)."""
    d, u = V(d).normalized(), V(u).normalized()
    n = d.cross(u)
    rot = mathutils.Matrix((d, u, n)).transposed().to_euler()
    return H['text_mesh'](name, body, FONT, size, m, col, root, center, rot, extrude=extrude)


def ring_xz(name, cx, cz, r_out, r_in, y0, depth, m, n=64):
    o = [(cx + r_out * math.cos(2 * math.pi * k / n), cz + r_out * math.sin(2 * math.pi * k / n)) for k in range(n)]
    i = [(cx + r_in * math.cos(2 * math.pi * k / n), cz + r_in * math.sin(2 * math.pi * k / n)) for k in range(n)]
    return H['ring'](name, o, i, 'xz', y0, depth, m, col, parent=root)


def fan(prefix, cx, cz, y_front, spin=1):
    """7 broad swept blades + hub; blades sit between y_front and y_front+pitch."""
    nb, r0, r1 = 7, 0.0185, 0.0545
    nr, nc, thick, pitch = 7, 6, 0.0008, 0.0048
    bm = bmesh.new()
    for b in range(nb):
        base = 2 * math.pi * b / nb
        top, bot = [], []
        for i in range(nr + 1):
            t = i / nr
            r = r0 + (r1 - r0) * t
            width = math.radians(38 + 11 * t)          # angular chord, wider at the tip
            sweep = spin * math.radians(32) * t ** 1.3  # blades curve as they go out
            rowt, rowb = [], []
            for j in range(nc + 1):
                s = j / nc
                ang = base + sweep + spin * width * s
                y = y_front + pitch * s * (0.75 + 0.25 * t)
                x, z = cx + r * math.cos(ang), cz + r * math.sin(ang)
                rowt.append(bm.verts.new((x, y, z)))
                rowb.append(bm.verts.new((x, y + thick, z)))
            top.append(rowt); bot.append(rowb)
        for i in range(nr):
            for j in range(nc):
                bm.faces.new((top[i][j], top[i][j + 1], top[i + 1][j + 1], top[i + 1][j]))
                bm.faces.new((bot[i][j], bot[i + 1][j], bot[i + 1][j + 1], bot[i][j + 1]))
        for i in range(nr):          # leading / trailing edges
            bm.faces.new((top[i][0], top[i + 1][0], bot[i + 1][0], bot[i][0]))
            bm.faces.new((top[i][nc], bot[i][nc], bot[i + 1][nc], top[i + 1][nc]))
        for j in range(nc):          # root / tip
            bm.faces.new((top[0][j], bot[0][j], bot[0][j + 1], top[0][j + 1]))
            bm.faces.new((top[nr][j], top[nr][j + 1], bot[nr][j + 1], bot[nr][j]))
    blades = _new_obj(prefix + '_Blades', bm, BLADE, col, root)
    hub_d = 0.0085
    hub = H['cyl'](prefix + '_Hub', 0.0190, hub_d, (cx, y_front - 0.0015 + hub_d / 2, cz), HUB, col,
                   verts=48, rot=(math.pi / 2, 0, 0), bevel=0.0014, parent=root)
    H['apply_all'](hub)
    return blades, hub


# ---------------------------------------------------------------- body halves
FRONT_PENTA = [pentagon(-1, 0.0025, 0.010, 0.006, 0.004), pentagon(1, 0.0025, 0.010, 0.006, 0.004)]
BACK_PENTA = [pentagon(-1, 0.0025, 0.013, 0.007, 0.004), pentagon(1, 0.0025, 0.013, 0.007, 0.004)]

f_cap1 = ybox('Front_Cap_Bracket', 0.0, CAP_A, YF, YF_IN, ZB, ZT, GUN, bevel=0.007, segs=6)
f_cap2 = ybox('Front_Cap_End', CAP_B, L, YF, YF_IN, ZB, ZT, GUN, bevel=0.007, segs=6)
f_mid = ybox('Front_Centre', 0.06, L - 0.06, YF + 0.0001, YF_IN, ZB + 0.002, ZT - 0.002, GUN, bevel=0.0015, segs=2)
b_cap1 = ybox('Back_Cap_Bracket', 0.0, CAP_A, YB_IN, YB, ZB, ZT, GUN, bevel=0.007, segs=6)
b_cap2 = ybox('Back_Cap_End', CAP_B, L, YB_IN, YB, ZB, ZT, GUN, bevel=0.007, segs=6)
b_mid = ybox('Back_Centre', 0.06, L - 0.06, YB_IN, YB - 0.0001, ZB + 0.002, ZT - 0.002, GUN, bevel=0.0015, segs=2)
core = ybox('Core_Seam', 0.0015, L - 0.0015, YF_IN - 0.001, YB_IN + 0.001, ZB + 0.0015, ZT - 0.0015, M['black_mt'])
FRONT = [f_cap1, f_cap2, f_mid]
BACK = [b_cap1, b_cap2, b_mid]

# front: shallow pentagon recess, then deep circular fan wells
for k, poly in enumerate(FRONT_PENTA):
    c = H['prism']('_cut', poly, 'xz', YF - 0.01, 0.01 + 0.003, CORE, col)
    cut_many(FRONT, c)
    H['prism'](f'Front_WellFloor_{k}', poly, 'xz', YF + 0.003, -0.0003, FLOOR, col, parent=root)
floors = [o for o in col.objects if o.name.startswith('Front_WellFloor')]
for k, fx in enumerate(FAN_X):
    c = H['cyl']('_cut', FAN_R, 0.03, (fx, YF_IN - 0.002 - 0.015, ZC), CORE, col, verts=96, rot=(math.pi / 2, 0, 0))
    cut_many(FRONT + floors, c)
    ring_xz(f'Front_FanRing_{k}', fx, ZC, FAN_R + 0.0009, FAN_R - 0.0002, YF + 0.0004, 0.006, GUN)

# back: deep pentagon recesses for the exposed fin stacks
for poly in BACK_PENTA:
    c = H['prism']('_cut', poly, 'xz', 0.005, 0.03, CORE, col)
    cut_many(BACK, c)

# top / bottom centre: LED slits + connector pocket (front half), fin channels (back half)
for zt, lit in ((ZT - 0.002, True), (ZB + 0.002, False)):
    for yc in (-0.0145, -0.0098):
        z0, z1 = (zt - 0.003, zt + 0.01) if lit else (zt - 0.01, zt + 0.003)
        cut_many([f_mid], cutter_box(0.106, 0.176, yc - 0.0008, yc + 0.0008, z0, z1))
        if lit:
            ybox('LED_Slit', 0.1065, 0.1755, yc - 0.0006, yc + 0.0006, zt - 0.0026, zt - 0.0016, LED)
    z0, z1 = (zt - 0.008, zt + 0.01) if lit else (zt - 0.01, zt + 0.008)
    cut_many([b_mid], cutter_box(CAP_A + 0.002, CAP_B - 0.002, YB_IN - 0.001, YB + 0.01, z0, z1))
cut_many([f_mid], cutter_box(0.1795, 0.2005, -0.0200, -0.0025, ZT - 0.017, ZT + 0.01))

# ---------------------------------------------------------------- fins
def front_fins():
    for fx in FAN_X:
        z = ZC - FAN_R + 0.0012
        while z < ZC + FAN_R - 0.001:
            h = math.sqrt(max(FAN_R ** 2 - (z - ZC) ** 2, 0)) - 0.0004
            if h > 0.002:
                yield (fx, -0.0072, z), (2 * h, 0.0074, 0.0005)
            z += 0.0021


def back_fins():
    for poly in BACK_PENTA:
        xs = [p[0] for p in poly]
        x = min(xs) + 0.0008
        while x < max(xs) - 0.0005:
            s = span_at(poly, 0, x)
            if s and s[1] - s[0] > 0.002:
                yield (x, (0.005 + YB - 0.0016) / 2, (s[0] + s[1]) / 2), (0.00045, YB - 0.0016 - 0.005, s[1] - s[0] - 0.0002)
            x += 0.00145


def channel_fins():
    for zc in (ZT - 0.0055, ZB + 0.0055):
        x = CAP_A + 0.003
        while x < CAP_B - 0.002:
            yield (x, (YB_IN + YB - 0.0008) / 2, zc), (0.0005, YB - 0.0008 - YB_IN, 0.0066)
            x += 0.0019


H['slat_array']('Front_Fins', front_fins, FIN, col, root)
H['slat_array']('Back_Fins', back_fins, FIN, col, root)
H['slat_array']('Edge_Fins', channel_fins, FIN, col, root)

# ---------------------------------------------------------------- face panels
for top in (False, True):
    tri = triangle(top, 0.0035, 0.004, 0.0025)
    H['prism']('Front_Tri_' + ('Top' if top else 'Bot'), tri, 'xz', YF + 0.0002, -0.0005, FACE, col, parent=root)
    H['prism']('Back_Tri_' + ('Top' if top else 'Bot'), tri, 'xz', YB - 0.0002, 0.0005, FACE, col, parent=root)

# ---------------------------------------------------------------- fans
for k, fx in enumerate(FAN_X):
    fan(f'Fan_{k}', fx, ZC, YF + 0.0045, spin=-1)

# ---------------------------------------------------------------- 12V-2x6 connector (angled toward +X)
TILT = math.radians(25)
CON_LOC = (0.1900, -0.0112, ZT - 0.0095)
con = ybox('Power_12V2x6', -0.0042, 0.0042, -0.0080, 0.0080, -0.0065, 0.0060, M['plastic'], bevel=0.0004)
con.location = CON_LOC; con.rotation_euler = (0, TILT, 0)


def con_holes():
    for xr in (-0.0021, 0.0021):
        for i in range(6):
            yield (xr, -0.0065 + i * 0.0026, 0.0058), (0.0017, 0.0019, 0.0006)


holes = H['slat_array']('Power_12V2x6_Pins', con_holes, CORE, col, root)
holes.location = CON_LOC; holes.rotation_euler = (0, TILT, 0)

# ---------------------------------------------------------------- top-edge branding
text_on('Top_Logo_Front', 'GEFORCE RTX', 0.0062, (0.2555, -0.0115, ZT + 0.00005), (1, 0, 0), (0, 1, 0), TXT_TOP)
text_on('Top_Logo_Back', 'GEFORCE RTX', 0.0050, (0.2555, 0.0100, ZT + 0.00005), (-1, 0, 0), (0, -1, 0), TXT_TOP)
# back plate "RTX 5090": along the bracket-side diagonal of the top triangle, reads with the card upside down
s2 = 1 / math.sqrt(2)
text_on('Back_Model', 'RTX 5090', 0.0068, (0.1190, YB + 0.0004, 0.1035), (s2, 0, -s2), (-s2, 0, -s2), TXT_BACK)

# ---------------------------------------------------------------- end face details
for z in (0.035, 0.093):
    H['cyl']('End_Screw', 0.0011, 0.0006, (L + 0.0001, -0.0115, z), M['black_st'], col, verts=16, rot=(0, math.pi / 2, 0), parent=root)
ybox('End_Label', L - 0.0002, L + 0.0002, 0.0060, 0.0150, 0.030, 0.098, FACE)

# ---------------------------------------------------------------- PCIe + daughterboard
H['pcie_edge'](root, col, M, x0=0.045)
ybox('PCIe_Board', 0.040, 0.150, 0.0, 0.0016, -0.0005, ZB + 0.001, M['pcb'])
ybox('PCIe_Hook', 0.1395, 0.1505, 0.0, 0.0016, -0.0040, 0.0, M['pcb'])

# ---------------------------------------------------------------- bracket (solid, port plate)
BX, BT = -0.0030, 0.0009
BY0, BY1 = YF, YB
br = ybox('Bracket', BX - BT / 2, BX + BT / 2, BY0, BY1, -0.0040, 0.1165, BRACKET)
for yc in (-0.0115, 0.0085):
    ybox('Bracket_Tongue', BX - BT / 2, BX + BT / 2, yc - 0.0037, yc + 0.0037, -0.0145, -0.0035, BRACKET)
ybox('Bracket_Tab', BX - 0.0110, BX + BT / 2, -0.0115, 0.0085, 0.1165 - BT, 0.1165, BRACKET)
plate = ybox('Port_Plate', BX - BT / 2 - 0.0008, BX - BT / 2, -0.0176, 0.0146, 0.0140, 0.1120, BRACKET, bevel=0.0003)
for y in (-0.0158, 0.0128):
    for z in (0.0165, 0.1095):
        H['cyl']('Plate_Screw', 0.0012, 0.0005, (BX - BT / 2 - 0.0010, y, z), M['black_st'], col, verts=16,
                 rot=(0, math.pi / 2, 0), parent=root)
PORT_Y = 0.0030


def port_outline(kind, zc, lz, ly, inset=0.0):
    """(y, z) outline, long axis along Z. HDMI: both front-side corners chamfered; DP: one corner."""
    y0, y1 = PORT_Y - ly / 2 + inset, PORT_Y + ly / 2 - inset
    z0, z1 = zc - lz / 2 + inset, zc + lz / 2 - inset
    c = 0.0016
    if kind == 'HDMI':
        return [(y1, z0), (y1, z1), (y0 + c, z1), (y0, z1 - c), (y0, z0 + c), (y0 + c, z0)]
    return [(y1, z0), (y1, z1), (y0, z1), (y0, z0 + c), (y0 + c, z0)]


PORTS = [('HDMI', 0.0300, 0.0145, 0.0058), ('DP', 0.0525, 0.0160, 0.0050), ('DP', 0.0750, 0.0160, 0.0050), ('DP', 0.0975, 0.0160, 0.0050)]
for i, (kind, zc, lz, ly) in enumerate(PORTS):
    c = H['prism']('_cut', port_outline(kind, zc, lz + 0.0008, ly + 0.0008), 'yz', BX - 0.01, 0.02, CORE, col)
    cut_many([br, plate], c)
    outer = port_outline(kind, zc, lz, ly)
    inner = port_outline(kind, zc, lz, ly, inset=0.0005)
    H['ring'](f'Port_{i}_{kind}_Shell', outer, inner, 'yz', BX - BT / 2 - 0.0006, 0.0066, M['steel'], col, parent=root)
    H['prism'](f'Port_{i}_{kind}_Back', inner, 'yz', BX + 0.0040, 0.0004, M['port'], col, parent=root)
    ybox(f'Port_{i}_{kind}_Tongue', BX - BT / 2 + 0.0004, BX + 0.004, PORT_Y - 0.0007, PORT_Y + 0.0007, zc - lz / 2 + 0.0015, zc + lz / 2 - 0.0015, M['port'])

# ---------------------------------------------------------------- sockets
H['sockets'](root, col, power_in=(CON_LOC[0] + 0.0025, CON_LOC[1], ZT - 0.003), pcie=(0.0910, 0.0008, -0.0085))

# smooth shading with sharp edges kept (rounded caps, hubs, fan rings)
def smooth(o, deg=35):
    H['apply_all'](o)
    o.data.shade_smooth()
    o.data.set_sharp_from_angle(angle=math.radians(deg))


for o in list(col.objects):
    if o.type == 'MESH' and (o.name.startswith(('Front_Cap', 'Back_Cap', 'Front_Centre', 'Back_Centre', 'Front_FanRing')) or o.name.endswith('_Hub')):
        smooth(o)

# leftover cutters (safety)
for o in list(col.objects):
    if o.name.startswith('_cut'):
        bpy.data.objects.remove(o, do_unlink=True)

# ---------------------------------------------------------------- save / export
os.makedirs(os.path.join(BASE, 'export'), exist_ok=True)
os.makedirs(os.path.join(BASE, 'renders'), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BASE, 'gpu_10_rtx5090_fe.blend'))
tris = H['export_glb'](ROOT, os.path.join(BASE, 'export', 'gpu_rtx5090_fe.glb'))
print('TRIANGLES', tris)

# ---------------------------------------------------------------- preview renders
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
studio = H['coll']('Studio')


def shot(view, loc, target, lens):
    cd = bpy.data.cameras.new('CAM_' + view); cd.lens = lens; cd.clip_start = 0.01
    cam = bpy.data.objects.new('CAM_' + view, cd); studio.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (V(target) - V(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.filepath = os.path.join(BASE, 'renders', f'rtx5090_fe_{view}.png')
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)


ONLY = os.environ.get('R50_VIEWS')
VIEWS = [
    ('front', (XC, -0.62, ZC), (XC, 0, ZC), 55),
    ('back', (XC, 0.62, ZC), (XC, 0, ZC), 55),
    ('top', (XC, -0.16, 0.55), (XC, 0, ZT), 50),
    ('34', (-0.20, -0.50, 0.28), (0.15, 0, 0.055), 60),
    ('bracket', (-0.42, -0.12, 0.12), (0, -0.002, 0.055), 55),
    ('back34', (0.50, 0.42, 0.25), (0.15, 0, 0.055), 60),
]
for v in VIEWS:
    if not ONLY or v[0] in ONLY.split(','):
        shot(*v)
sc.camera = bpy.data.objects.get('Camera')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BASE, 'gpu_10_rtx5090_fe.blend'))
print('DONE')
