"""NVIDIA RTX PRO 6000 Blackwell Workstation Edition (96 GB GDDR7, 600 W, 2025).

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python <this file>

Dual-slot, double flow-through cooler (both fans on the front face), all-black
"pro" colour scheme, X-shaped frame with glossy black centre triangles, 4x DP 2.1b
in a single column on a solid black bracket, 12V-2x6 on the top edge.
References: StorageReview review photos (front / back / top / bracket) and the
NVIDIA RTX PRO Blackwell Quick Start Guide drawings (bracket + power connector).
"""
import bpy, bmesh, math, mathutils, os

BASE = r'C:\laragon\www\scaling-law\blender'
exec(open(os.path.join(BASE, 'lib', 'hw.py'), encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']

ROOT = 'RTXPRO6000_Blackwell'
FONT = r'C:\Windows\Fonts\arialbd.ttf'
FONT_W = r'C:\Windows\Fonts\bahnschrift.ttf'
root, col = H['new_card_scene'](ROOT)
M = H['base_materials']()

# ---------------------------------------------------------------- materials
mat = H['mat']
M_FRAME = mat('PRO_FrameBlack', (0.009, 0.009, 0.010), 0.1, 0.5, spec=0.18)
M_ARM = mat('PRO_FrameEdge', (0.06, 0.062, 0.066), 0.95, 0.24)
M_GLOSS = mat('PRO_GlossBlack', (0.0008, 0.0008, 0.001), 0.0, 0.10, spec=0.25)
M_FIN = mat('PRO_Fins', (0.012, 0.012, 0.013), 0.7, 0.42, spec=0.3)
M_RECESS = mat('PRO_Recess', (0.002, 0.002, 0.002), 0.0, 0.9, spec=0.05)
M_BLADE = mat('PRO_Blade', (0.011, 0.011, 0.012), 0.0, 0.55, spec=0.25)
M_HUB = mat('PRO_HubSpun', (0.16, 0.16, 0.165), 0.9, 0.32, aniso=0.6)
M_TEXT = mat('PRO_TextChampagne', (0.62, 0.58, 0.50), 0.9, 0.3)
M_LOGO = mat('PRO_TextGrey', (0.30, 0.30, 0.30), 0.6, 0.45)
M_CHROME = mat('PRO_Chrome', (0.75, 0.75, 0.77), 1.0, 0.12)
M_BRACKET = mat('PRO_BracketBlack', (0.015, 0.015, 0.016), 0.6, 0.45, spec=0.35)
M_CONN = mat('PRO_ConnPlastic', (0.006, 0.006, 0.0065), 0.0, 0.6, spec=0.2)

# ---------------------------------------------------------------- dimensions
X0, X1 = 0.0, 0.302            # body length (304 mm incl. bracket)
Z0, Z1 = 0.001, 0.127          # body height ~126 mm (137 mm incl. PCIe fingers)
YF, YB = -0.0355, 0.0035       # front (fans) / back faces: 39 mm, dual slot
XC, ZC = (X0 + X1) / 2, (Z0 + Z1) / 2
FAN_X = (0.062, 0.240)
FAN_R = 0.0535                 # well radius (fans ~105 mm)


def mcut(obj, cutter, solver='MANIFOLD'):
    """Boolean difference with the Manifold solver (EXACT empties this bevelled body in 5.2)."""
    H['apply_all'](obj)
    m = obj.modifiers.new('Cut', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.solver = solver; m.object = cutter
    H['apply_all'](obj)
    bpy.data.objects.remove(cutter, do_unlink=True)
    if len(obj.data.polygons) == 0:
        raise RuntimeError('boolean emptied ' + obj.name)
    return obj


def round_poly(pts, radii, seg=6):
    """Round the corners of a convex polygon (list of (a,b)); radii per vertex."""
    out = []
    n = len(pts)
    for i in range(n):
        P = mathutils.Vector(pts[i]); A = mathutils.Vector(pts[i - 1]); B = mathutils.Vector(pts[(i + 1) % n])
        r = radii[i] if isinstance(radii, (list, tuple)) else radii
        u1 = (A - P).normalized(); u2 = (B - P).normalized()
        phi = math.acos(max(-1.0, min(1.0, u1.dot(u2))))
        if r <= 0 or phi > math.pi - 1e-3:
            out.append(tuple(P)); continue
        t = r / math.tan(phi / 2)
        bis = (u1 + u2).normalized()
        C = P + bis * (r / math.sin(phi / 2))
        T1 = P + u1 * t; T2 = P + u2 * t
        a1 = math.atan2(T1.y - C.y, T1.x - C.x); a2 = math.atan2(T2.y - C.y, T2.x - C.x)
        da = a2 - a1
        while da > math.pi: da -= 2 * math.pi
        while da < -math.pi: da += 2 * math.pi
        for k in range(seg + 1):
            a = a1 + da * k / seg
            out.append((C.x + r * math.cos(a), C.y + r * math.sin(a)))
    return out


def circle(cx, cz, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * k / n), cz + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def text_oriented(name, body, font, size, material, loc, d, t, extrude=0.00015, scale=(1, 1, 1)):
    """Text whose reading direction is d and letter-up is t (world vectors); normal = d x t."""
    d = mathutils.Vector(d).normalized(); t = mathutils.Vector(t).normalized(); n = d.cross(t)
    rot = mathutils.Matrix((d, t, n)).transposed().to_euler()
    return H['text_mesh'](name, body, font, size, material, col, root, loc, rot, extrude=extrude, scale=scale)


# ---------------------------------------------------------------- face layout
RIM = 0.0042
XA = 0.093          # where the X arm meets the top / bottom rim (panel side)
XT = XC - 0.0045    # panel tip x (panels nearly touch in the middle)
AW = 0.0042         # raised arm width
PANEL_L = [(X0 + RIM, Z0 + RIM), (XA, Z0 + RIM), (XT, ZC), (XA, Z1 - RIM), (X0 + RIM, Z1 - RIM)]
PANEL_L_R = [0.0085, 0.006, 0.0055, 0.006, 0.0085]


def mirror_x(pts):
    return [(2 * XC - a, b) for a, b in reversed(pts)]


def mirror_z(pts):
    return [(a, 2 * ZC - b) for a, b in reversed(pts)]


PANEL_R = mirror_x(PANEL_L); PANEL_R_R = list(reversed(PANEL_L_R))
# top triangle: edge parallel to the panel's upper slanted edge, offset by the arm width
ex, ez = XT - XA, ZC - (Z1 - RIM)
L = math.hypot(ex, ez); nx, nz = -ez / L, ex / L          # normal pointing "up/right" from the panel edge
if nx < 0: nx, nz = -nx, -nz
ox, oz = XA + nx * AW, (Z1 - RIM) + nz * AW               # point on the offset line
ZT_TOP = Z1 - 0.0028
x_at_top = ox + (ZT_TOP - oz) * ex / ez
z_at_c = oz + (XC - ox) * ez / ex
TRI_T = [(x_at_top, ZT_TOP), (XC, z_at_c), (2 * XC - x_at_top, ZT_TOP)]
TRI_T = [(x_at_top, ZT_TOP), (2 * XC - x_at_top, ZT_TOP), (XC, z_at_c)]
TRI_T_R = [0.002, 0.002, 0.0055]
TRI_B = mirror_z(TRI_T); TRI_B_R = list(reversed(TRI_T_R))
print('LAYOUT tri top', [tuple(round(v, 4) for v in p) for p in TRI_T])


def panel_zrange(x, poly):
    """z-range of the convex polygon at abscissa x (unrounded polygon)."""
    zs = []
    n = len(poly)
    for i in range(n):
        (a0, b0), (a1, b1) = poly[i], poly[(i + 1) % n]
        if (a0 - x) * (a1 - x) <= 0 and a0 != a1:
            zs.append(b0 + (x - a0) * (b1 - b0) / (a1 - a0))
    return (min(zs), max(zs)) if len(zs) >= 2 else None


# ---------------------------------------------------------------- body shell
body_outline = round_poly([(X0, Z0), (X1, Z0), (X1, Z1), (X0, Z1)], 0.011, seg=8)
body = H['prism']('Body', body_outline, 'xz', YF, YB - YF, M_FRAME, col, parent=root, bevel=0.0026)
H["apply_all"](body); print("BODY0", len(body.data.polygons))


def cutter_prism(name, pts, y0, depth):
    return H['prism'](name, pts, 'xz', y0, depth, M_RECESS, col)


REC_P = 0.0016   # panel recess depth
REC_T = 0.0010   # triangle recess depth
faces = {'Front': (YF, 1), 'Back': (YB, -1)}
for side, (yface, s) in faces.items():
    # s = +1: face at YF, recess toward +Y ; s = -1: face at YB, recess toward -Y
    for nm, pts, rr, dep in (('PanelL', PANEL_L, PANEL_L_R, REC_P), ('PanelR', PANEL_R, PANEL_R_R, REC_P),
                             ('TriT', TRI_T, TRI_T_R, REC_T), ('TriB', TRI_B, TRI_B_R, REC_T)):
        poly = round_poly(pts, rr, seg=6)
        c = cutter_prism(f'{side}_{nm}_Cut', poly, yface - s * 0.002, s * (dep + 0.002))
        mcut(body, c); print("CUT", nm, side, len(body.data.polygons))
        # glossy plate at the bottom of each triangle recess
        if nm.startswith('Tri'):
            H['prism'](f'{side}_{nm}_Gloss', poly, 'xz', yface + s * dep - s * 0.0003, s * 0.0003, M_GLOSS, col, parent=root)
        else:
            fl = H['prism'](f'{side}_{nm}_Floor', poly, 'xz', yface + s * dep - s * 0.0002, s * 0.0002, M_RECESS, col, parent=root)
            if side == 'Front':
                fx = FAN_X[0] if nm == 'PanelL' else FAN_X[1]
                mcut(fl, H['cyl']('FloorHole', FAN_R + 0.0001, 0.01, (fx, yface, ZC), M_RECESS, col, verts=64, rot=(math.pi / 2, 0, 0)))

# fan wells (front only), real depth so the blades sit inside
WELL_D = 0.021
for i, fx in enumerate(FAN_X):
    c = H['cyl'](f'Well{i}_Cut', FAN_R, WELL_D + 0.004, (fx, YF + WELL_D / 2 - 0.002, ZC), M_RECESS, col, verts=64, rot=(math.pi / 2, 0, 0))
    mcut(body, c)
    H['cyl'](f'Fan{i}_WellFloor', FAN_R - 0.0002, 0.0004, (fx, YF + WELL_D - 0.0002, ZC), M_RECESS, col, verts=64,
             rot=(math.pi / 2, 0, 0), parent=root)
    # raised lip ring around the well
    H['ring'](f'Fan{i}_Lip', circle(fx, ZC, FAN_R + 0.0012, 64), circle(fx, ZC, FAN_R - 0.0001, 64), 'xz',
              YF - 0.0004, 0.0030, M_ARM, col, parent=root)

# top-edge centre: glossy channel with chrome rails + 12V-2x6 recess
TOP_X0, TOP_X1 = 0.099, 0.203
c = H['box']('TopChannel_Cut', (TOP_X1 - TOP_X0, 0.0285, 0.004), ((TOP_X0 + TOP_X1) / 2, -0.016, Z1 + 0.0008), M_RECESS, col)
mcut(body, c)
CON_X = 0.188
c = H['box']('Conn_Cut', (0.0135, 0.0225, 0.020), (CON_X, -0.016, Z1 - 0.0085), M_RECESS, col)
mcut(body, c)
# glossy floor of the channel (split around the connector opening)
gx0, gx1 = CON_X - 0.0068, CON_X + 0.0068
H['box']('Top_Gloss_A', (gx0 - TOP_X0, 0.0285, 0.0004), ((TOP_X0 + gx0) / 2, -0.016, Z1 - 0.0012 - 0.0002), M_GLOSS, col, parent=root)
H['box']('Top_Gloss_B', (TOP_X1 - gx1, 0.0285, 0.0004), ((gx1 + TOP_X1) / 2, -0.016, Z1 - 0.0012 - 0.0002), M_GLOSS, col, parent=root)
for k, yy in enumerate((-0.0310, -0.0010)):
    H['box'](f'Top_Rail{k}', (TOP_X1 - TOP_X0 + 0.002, 0.0012, 0.0016), ((TOP_X0 + TOP_X1) / 2, yy, Z1 - 0.0004), M_CHROME, col,
             parent=root, bevel=0.0004)

# ---------------------------------------------------------------- fin ridges
FIN_P, FIN_W, FIN_H = 0.0019, 0.0008, 0.0013


def ridges(poly, yfloor, s, holes=()):
    """Vertical ridges (along Z) clipped to a convex polygon, skipping circular holes."""
    xs0 = min(p[0] for p in poly) + 0.0015; xs1 = max(p[0] for p in poly) - 0.0015
    x = xs0
    while x <= xs1:
        zr = panel_zrange(x, poly)
        if zr:
            z0, z1 = zr[0] + 0.0012, zr[1] - 0.0012
            segs = [(z0, z1)]
            for (hx, hz, hr) in holes:
                if abs(x - hx) < hr:
                    dz = math.sqrt(hr * hr - (x - hx) ** 2)
                    new = []
                    for a, b in segs:
                        if b <= hz - dz or a >= hz + dz:
                            new.append((a, b)); continue
                        if a < hz - dz: new.append((a, hz - dz))
                        if b > hz + dz: new.append((hz + dz, b))
                    segs = new
            for a, b in segs:
                if b - a > 0.0015:
                    yield (x, yfloor - s * FIN_H / 2, (a + b) / 2), (FIN_W, FIN_H, b - a)
        x += FIN_P


for side, (yface, s) in faces.items():
    yfloor = yface + s * REC_P
    for nm, poly, fx in (('L', PANEL_L, FAN_X[0]), ('R', PANEL_R, FAN_X[1])):
        holes = [(fx, ZC, FAN_R + 0.0014)] if side == 'Front' else []
        H['slat_array'](f'{side}_Fins{nm}', lambda poly=poly, yfloor=yfloor, s=s, holes=holes: ridges(poly, yfloor, s, holes),
                        M_FIN, col, root)

# fins visible at the bottom of each fan well (flow-through stack)
for i, fx in enumerate(FAN_X):
    poly = circle(fx, ZC, FAN_R - 0.0008, 48)
    yfl = YF + WELL_D - 0.0004

    def well_fins(poly=poly, yfl=yfl):
        for (c, sz) in ridges(poly, yfl, 1):
            c = (c[0], yfl - 0.0012, c[2]); sz = (sz[0], 0.0024, sz[2])
            yield c, sz
    H['slat_array'](f'Fan{i}_StackFins', well_fins, M_FIN, col, root)

# ---------------------------------------------------------------- fans
N_BLADE = 7
R_HUB, R_TIP = 0.0190, 0.0518


def blade_mesh(name, theta0, ycen):
    bm = bmesh.new()
    NR, NC = 8, 6
    grid = []
    for i in range(NR + 1):
        u = i / NR
        r = R_HUB - 0.0006 + (R_TIP - R_HUB + 0.0006) * u
        thc = theta0 - 0.62 * u ** 1.15            # swept: tips trail clockwise (front view)
        hw = 0.25 + 0.11 * u                         # angular half-width grows toward the tip
        row = []
        for j in range(NC + 1):
            v = j / NC
            th = thc - hw + 2 * hw * v
            # camber/pitch: leading edge (v=1) toward the face, trailing edge deeper
            y = ycen + (0.5 - v) * (0.0048 + 0.0030 * u) - 0.0012 * math.sin(math.pi * v)
            row.append(bm.verts.new((r * math.cos(th), y, r * math.sin(th))))
        grid.append(row)
    for i in range(NR):
        for j in range(NC):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); col.objects.link(o); me.materials.append(M_BLADE)
    sol = o.modifiers.new('Solid', 'SOLIDIFY'); sol.thickness = 0.0009; sol.offset = 0
    H['apply_all'](o)
    return o


for i, fx in enumerate(FAN_X):
    fan = bpy.data.objects.new(f'Fan{i}', None); fan.empty_display_type = 'CIRCLE'; fan.empty_display_size = 0.05
    col.objects.link(fan); fan.parent = root; fan.location = (fx, 0, ZC)
    blades = []
    for b in range(N_BLADE):
        blades.append(blade_mesh(f'Fan{i}_Blade{b}', 2 * math.pi * b / N_BLADE + 0.3, YF + 0.0105))
    # merge blades into one object
    with bpy.context.temp_override(active_object=blades[0], selected_editable_objects=blades, object=blades[0]):
        bpy.ops.object.join()
    bl = blades[0]; bl.name = f'Fan{i}_Blades'; bl.parent = fan
    hub = H['cyl'](f'Fan{i}_HubBody', R_HUB + 0.0004, 0.014, (0, YF + 0.0125, 0), M_BLADE, col, verts=48,
                   rot=(math.pi / 2, 0, 0), parent=fan)
    hub.location = (0, YF + 0.0125, 0)
    cap = H['cyl'](f'Fan{i}_Cap', R_HUB - 0.0008, 0.0010, (0, YF + 0.0050, 0), M_HUB, col, verts=48,
                   rot=(math.pi / 2, 0, 0), parent=fan, bevel=0.0003)
    cap.location = (0, YF + 0.0050, 0)
    # rotor outer ring tying the blade tips together (double flow-through fan, see NVIDIA exploded view)
    H['ring'](f'Fan{i}_RotorRing', circle(0, 0, R_TIP + 0.0011, 64), circle(0, 0, R_TIP - 0.0002, 64), 'xz',
              YF + 0.0060, 0.0090, M_BLADE, col, parent=fan)
    capr = H['ring'](f'Fan{i}_CapRing', circle(0, 0, R_HUB + 0.0004, 48), circle(0, 0, R_HUB - 0.0008, 48), 'xz',
                     YF + 0.0048, 0.0010, M_ARM, col, parent=fan)

# ---------------------------------------------------------------- 12V-2x6 connector
CY, CZT = -0.016, Z1 - 0.0016
conn = H['box']('Power_12V2x6', (0.0096, 0.0196, 0.012), (CON_X, CY, CZT - 0.006), M_CONN, col, parent=root, bevel=0.0004)


def conn_holes():
    for row in range(2):
        for k in range(6):
            yield (CON_X - 0.0015 + 0.0030 * row - 0.0008, CY - 0.0075 + 0.0030 * k, CZT + 0.00005), (0.0022, 0.0022, 0.0002)
    for k in range(4):      # sideband / sense pins
        yield (CON_X + 0.0034, CY - 0.0045 + 0.0030 * k, CZT + 0.00005), (0.0011, 0.0011, 0.0002)


H['slat_array']('Power_12V2x6_Holes', conn_holes, M['port'], col, root)
H['box']('Power_12V2x6_Latch', (0.0014, 0.005, 0.003), (CON_X - 0.0054, CY, CZT - 0.002), M_CONN, col, parent=root)

# ---------------------------------------------------------------- texts / logos
# back: "RTX PRO 6000" along the left arm of the top triangle, readable with the card
# flipped (PCIe up, bracket left) exactly as in the StorageReview back photo.
ang = math.atan2(abs(ez), abs(ex))
d = (math.cos(ang), 0, -math.sin(ang))           # runs from the top edge toward the centre crossing
t = (-math.sin(ang), 0, -math.cos(ang))
tx, tz = 0.127, 0.103
text_oriented('Back_Text', 'RTX PRO 6000', FONT, 0.0052, M_TEXT, (tx, YB - REC_T + 0.00045, tz), d, t, extrude=0.0001)
# front: tiny "RTX PRO 6000" on the lower triangle near the left arm
d2 = (math.cos(ang), 0, math.sin(ang)); t2 = (-math.sin(ang), 0, math.cos(ang))
text_oriented('Front_Text', 'RTX PRO 6000', FONT, 0.0022, M_LOGO, (0.122, YF + REC_T - 0.00045, 0.016), d2, t2, extrude=0.0001)
# top edge: NVIDIA eye + wordmark near the far end, reads +X with letter-up toward the back (+Y)
text_oriented('Top_Logo_Text', 'NVIDIA', FONT_W, 0.0062, M_LOGO, (0.268, -0.0165, Z1 + 0.0001), (1, 0, 0), (0, 1, 0),
              extrude=0.0001, scale=(1.25, 1, 1))
eye = H['ring']('Top_Logo_Eye', [(0.2405, -0.0195), (0.2475, -0.0195), (0.2475, -0.0135), (0.2405, -0.0135)],
                [(0.2413, -0.0187), (0.2467, -0.0187), (0.2467, -0.0143), (0.2413, -0.0143)], 'xy', Z1, 0.0002, M_LOGO, col, parent=root)
H['cyl']('Top_Logo_EyeDot', 0.0016, 0.0002, (0.2440, -0.0165, Z1 + 0.0001), M_LOGO, col, verts=20, parent=root)

# ---------------------------------------------------------------- bracket (solid, black, 4x DP in one column)
BX, BT = -0.0030, 0.0009
br = H['box']('Bracket', (BT, 0.0400, 0.1180), (BX, -0.0170, 0.0530), M_BRACKET, col, parent=root)
H['box']('Bracket_Tab', (0.0110, 0.0190, BT), (BX - 0.0055 + BT / 2, -0.0080, 0.1120), M_BRACKET, col, parent=root)
H['box']('Bracket_Tongue', (BT, 0.0080, 0.0120), (BX, -0.0060, -0.0100), M_BRACKET, col, parent=root)
H['box']('Bracket_Tongue2', (BT, 0.0060, 0.0070), (BX, -0.0290, -0.0080), M_BRACKET, col, parent=root)
PX = BX - BT / 2 - 0.0005
H['box']('Bracket_PortPlate', (0.0010, 0.0330, 0.0930), (PX, -0.0188, 0.0625), M_BRACKET, col, parent=root, bevel=0.0003)
for k, (yy, zz) in enumerate(((-0.0045, 0.0200), (-0.0330, 0.0200), (-0.0045, 0.1050), (-0.0330, 0.1050))):
    H['cyl'](f'Bracket_Screw{k}', 0.0014, 0.0008, (PX - 0.0007, yy, zz), M['black_st'], col, verts=16,
             rot=(0, math.pi / 2, 0), parent=root)
# DisplayPort 2.1b x4: long axis along Z, chamfered corners on the -Y side
DP_Y = -0.0128


def dp_outline(yc, zc, w=0.0160, h=0.0050, ch=0.0016, grow=0.0):
    w += 2 * grow; h += 2 * grow
    y0, y1, z0, z1 = yc - h / 2, yc + h / 2, zc - w / 2, zc + w / 2
    return [(y1, z0), (y1, z1), (y0 + ch, z1), (y0, z1 - ch), (y0, z0 + ch), (y0 + ch, z0)]


for k, zz in enumerate((0.0290, 0.0510, 0.0730, 0.0950)):
    shell = H['prism'](f'DP{k}_Shell', dp_outline(DP_Y, zz, grow=0.0004), 'yz', PX - 0.0009, 0.0060, M['steel'], col, parent=root)
    inner = H['prism'](f'DP{k}_Inner', dp_outline(DP_Y, zz), 'yz', PX - 0.0011, 0.0050, M['port'], col, parent=root)
    H['box'](f'DP{k}_Tongue', (0.0020, 0.0012, 0.0118), (PX - 0.0001, DP_Y + 0.0006, zz), M_CONN, col, parent=root)
# regulatory label strip (dark, as on the photo)
H['box']('Bracket_Label', (0.0002, 0.0090, 0.0400), (PX - 0.0006, -0.0275, 0.0560), M['plastic'], col, parent=root)

# rear-end brace mount (integrated GPU support bracket mounting)
H['box']('Brace_Plate', (0.0010, 0.0045, 0.0750), (X1 + 0.0005, 0.0005, 0.0660), M_BRACKET, col, parent=root)
tab = H['box']('Brace_Tab', (0.0080, 0.0050, 0.0010), (X1 + 0.0040, 0.0005, 0.1030), M_BRACKET, col, parent=root)
mcut(tab, H['cyl']('Brace_Hole', 0.0012, 0.004, (X1 + 0.0055, 0.0005, 0.1030), M_RECESS, col, verts=16))

# ---------------------------------------------------------------- PCIe, sockets
H['pcie_edge'](root, col, M, x0=0.040)
H['sockets'](root, col, power_in=(CON_X, CY, Z1 + 0.0005), pcie=(0.081, 0.0008, -0.0085))

# stray cutters: make sure nothing un-parented remains in the card collection
for o in list(col.objects):
    if o.parent is None and o is not root:
        print('REMOVING stray', o.name)
        bpy.data.objects.remove(o, do_unlink=True)

# smooth shading by angle (rounded corners, rings, hubs) while keeping hard 90-degree edges
meshes = [o for o in col.objects if o.type == 'MESH']
with bpy.context.temp_override(selected_editable_objects=meshes, selected_objects=meshes, active_object=meshes[0], object=meshes[0]):
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))

# ---------------------------------------------------------------- save / export
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BASE, 'gpu_11_rtx_pro_6000_blackwell.blend'))
os.makedirs(os.path.join(BASE, 'export'), exist_ok=True)
tris = H['export_glb'](ROOT, os.path.join(BASE, 'export', 'gpu_rtx_pro_6000_blackwell.glb'))
print('TRIANGLES', tris)

# ---------------------------------------------------------------- renders
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
cam = sc.camera
floor = bpy.data.objects.get('Floor')


def shoot(view, loc, target, lens=50, up=(0, 0, 1), hide_floor=False):
    cam.location = loc
    dvec = mathutils.Vector(target) - mathutils.Vector(loc)
    cam.rotation_euler = dvec.to_track_quat('-Z', 'Y' if up == (0, 0, 1) else 'Z').to_euler()
    if up != (0, 0, 1):
        q = dvec.to_track_quat('-Z', 'Y')
        cam.rotation_euler = q.to_euler()
    cam.data.lens = lens
    if floor:
        floor.hide_render = hide_floor
    sc.render.filepath = os.path.join(BASE, 'renders', f'rtx_pro_6000_{view}.png')
    bpy.ops.render.render(write_still=True)


views = os.environ.get('VIEWS', 'front,back,top,threequarter,bracket').split(',')
C = (0.151, -0.016, 0.063)
if 'front' in views:
    shoot('front', (0.151, -0.62, 0.075), C, lens=50)
if 'back' in views:
    shoot('back', (0.151, 0.60, 0.075), C, lens=50)
if 'top' in views:
    shoot('top', (0.20, -0.17, 0.40), (0.17, -0.016, 0.12), lens=45)
if 'threequarter' in views:
    shoot('threequarter', (-0.17, -0.40, 0.30), (0.155, -0.01, 0.055), lens=45)
if 'bracket' in views:
    shoot('bracket', (-0.40, -0.14, 0.11), (0.0, -0.016, 0.06), lens=45)
if 'end' in views:
    shoot('end', (0.62, 0.12, 0.20), (0.30, -0.016, 0.07), lens=45)
print('DONE')
