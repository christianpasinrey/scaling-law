"""NVIDIA H100 SXM5 module (2022) + HGX air-cooled heatsink.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python gpu_13a_h100_sxm5.py

Conventions (SXM modules): metres, module lies flat, board top surface = XY plane at z=0,
heatsink toward +Z, X = long side (150 mm), Y = short side (79 mm), origin = module centre.

Library mode: gpu_13b_h200_sxm.py sets SXM_LIBRARY_MODE = True before exec'ing this file and then
calls build(cfg) with its own cfg (H200 shares every piece of geometry; only data differs).

Reference photos (measured px -> mm):
  - ServeTheHome via TechPowerUp, bare H100 SXM5 top (lbCSMI0dZgMTohTw.jpg): board 1090x575 px ->
    7.27 px/mm, centre px (685, 472).  Bottom (lbS55OJTj4bx3EQj.jpg): 8.6 px/mm, centre (720, 459).
  - ServeTheHome HGX H200 photos (Supermicro SYS-821GE-TNHR, ASRock Rack 6U8X-EGS2): heatsink top
    plate, label shelf, copper captive screws, 2-tier fin stack (low full-footprint block + tall
    heat-pipe tower), 8 modules at ~82 mm pitch along Y.
"""
import bpy, bmesh, math, mathutils, random, os

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']

MM = 0.001
FONT_BLACK = r'C:\Windows\Fonts\ariblk.ttf'
FONT_BOLD = r'C:\Windows\Fonts\arialbd.ttf'
FONT_REG = r'C:\Windows\Fonts\arial.ttf'
FONT_MONO = r'C:\Windows\Fonts\consola.ttf'

BLEND_DIR = r'C:\laragon\www\scaling-law\blender'

CFG_H100 = dict(
    root='H100_SXM5',
    blend=os.path.join(BLEND_DIR, 'gpu_13a_h100_sxm5.blend'),
    glb=os.path.join(BLEND_DIR, 'export', 'gpu_h100_sxm5.glb'),
    render_prefix='h100_sxm5',
    # die top marking, read off the bare-module photo
    die_lines=['NVIDIA', 'T TW  2153A1', 'U8A603.L06'],
    pcb_pn='180-1G520-DAAF-B01',
    label_top='H100 SXM5 80GB HBM3',
    label_fru='',
    label_sn='S/N: 1650222000000',
)

# board
BL, BW, BT = 150.0, 79.0, 2.4          # mm


def m(*v):
    return tuple(x * MM for x in v)


def top_px(px, py):
    """Bare-module top photo pixel -> board mm."""
    return ((px - 685) / 7.27, -(py - 472) / 7.27)


def bot_px(px, py):
    """Bare-module bottom photo pixel -> board mm (module flipped about its long X axis)."""
    return ((px - 720) / 8.6, (py - 459) / 8.6)


# ---------------------------------------------------------------- helpers (local, hw.py untouched)
def mats():
    M = H['base_materials']()
    mt = H['mat']
    M.update(
        pcb=mt('SXM_PCB', (0.008, 0.009, 0.009), 0.0, 0.42, spec=0.3),
        copper=mt('SXM_Copper', (0.93, 0.50, 0.30), 1.0, 0.30),
        copper_ring=mt('SXM_CopperPad', (0.85, 0.48, 0.32), 0.9, 0.38),
        inductor=mt('SXM_Inductor', (0.045, 0.045, 0.043), 0.4, 0.5),
        silicon=mt('SXM_Silicon', (0.006, 0.007, 0.010), 0.85, 0.04),
        substrate=mt('SXM_Substrate', (0.015, 0.045, 0.050), 0.0, 0.45),
        stiffener=mt('SXM_Stiffener', (0.42, 0.41, 0.37), 1.0, 0.42),
        greenpcb=mt('SXM_GreenPCB', (0.06, 0.24, 0.08), 0.0, 0.4),
        cap=mt('SXM_Cap', (0.50, 0.38, 0.24), 0.2, 0.5),
        silk=mt('SXM_Silk', (0.75, 0.75, 0.73), 0.0, 0.6),
        champagne=mt('SXM_Champagne', (0.46, 0.36, 0.23), 0.85, 0.45),
        smoke=mt('SXM_SmokeClear', (0.012, 0.016, 0.018), 0.0, 0.06, alpha=0.72),
        label=mt('SXM_LabelBlack', (0.004, 0.004, 0.005), 0.0, 0.55, spec=0.2),
        label_white=mt('SXM_LabelWhite', (0.85, 0.85, 0.85), 0.0, 0.5),
        fin_tower=mt('SXM_FinTower', (0.20, 0.20, 0.21), 0.85, 0.38),
        nickel=mt('SXM_Nickel', (0.72, 0.70, 0.66), 1.0, 0.3),
        mezz=mt('SXM_MezzBlack', (0.02, 0.02, 0.022), 0.0, 0.75),
    )
    return M


def mesh_obj(name, bm, material, col, parent, recalc=True):
    if recalc:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    me.materials.append(material)
    col.objects.link(o)
    o.parent = parent
    return o


def bm_box(bm, c, s):
    bmesh.ops.create_cube(bm, size=1, matrix=mathutils.Matrix.Translation(c) @ mathutils.Matrix.Diagonal((*s, 1)))


def bm_quad_down(bm, c, s):
    """Single quad facing -Z (2 tris) for underside passives."""
    x, y, z = c; hx, hy = s[0] / 2, s[1] / 2
    v = [bm.verts.new(p) for p in ((x - hx, y - hy, z), (x - hx, y + hy, z), (x + hx, y + hy, z), (x + hx, y - hy, z))]
    bm.faces.new(v)


def ribbon(bm, pts, w, z0, h):
    """Thick polyline (x,y in metres) as per-segment boxes rotated along the segment."""
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0) + w * 0.6
        a = math.atan2(y1 - y0, x1 - x0)
        M = (mathutils.Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, z0 + h / 2)) @
             mathutils.Matrix.Rotation(a, 4, 'Z') @ mathutils.Matrix.Diagonal((L, w, h, 1)))
        bmesh.ops.create_cube(bm, size=1, matrix=M)


def annuli(name, centers, r_out, r_in, z, h, material, col, parent, seg=20):
    bm = bmesh.new()
    for cx, cy in centers:
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            ca, sa = math.cos(a), math.sin(a)
            ring.append([bm.verts.new((cx + r * ca, cy + r * sa, zz)) for r, zz in
                         ((r_out, z), (r_in, z), (r_out, z + h), (r_in, z + h))])
        for k in range(seg):
            a, b = ring[k], ring[(k + 1) % seg]
            bm.faces.new((a[2], b[2], b[3], a[3]))  # top
            bm.faces.new((a[0], a[1], b[1], b[0]))  # bottom
            bm.faces.new((a[0], b[0], b[2], a[2]))  # outer
            bm.faces.new((a[1], a[3], b[3], b[1]))  # inner
    return mesh_obj(name, bm, material, col, parent)


def fit_text(o, w=None, h=None):
    """Re-centre a converted text mesh on its origin and scale it to w x h (metres, local axes)."""
    vs = [v.co for v in o.data.vertices]
    mn = mathutils.Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    mx = mathutils.Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    c = (mn + mx) / 2
    c.z = mn.z
    o.data.transform(mathutils.Matrix.Translation(-c))
    dx, dy = mx.x - mn.x, mx.y - mn.y
    sx = (w / dx) if w else None
    sy = (h / dy) if h else None
    if sx is None: sx = sy
    if sy is None: sy = sx
    o.scale = (sx, sy, 1)
    return o


def text(name, body, font, size, material, col, parent, loc, rot_z=0.0, w=None, h=None, extrude=0.0, res=2):
    """Low-poly text: curve resolution `res`, flat unless extruded; centred and fitted to w x h."""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.size = size; cu.extrude = extrude; cu.resolution_u = res
    t = bpy.data.objects.new(name, cu)
    col.objects.link(t)
    cu.materials.append(material)
    with bpy.context.temp_override(active_object=t, object=t, selected_objects=[t], selected_editable_objects=[t]):
        bpy.ops.object.convert(target='MESH')
    t.parent = parent
    t.location = loc; t.rotation_euler = (0, 0, rot_z)
    fit_text(t, w, h)
    return t


def join(objs, name):
    objs = [o for o in objs if o and o.type == 'MESH']
    for o in objs:
        H['apply_all'](o)
    a = objs[0]
    with bpy.context.temp_override(active_object=a, object=a, selected_objects=objs, selected_editable_objects=objs):
        bpy.ops.object.join()
    a.name = name; a.data.name = name
    return a


# ---------------------------------------------------------------- module
def build_module(cfg, root, col, M):
    P = []  # parts to join
    box = lambda n, s, c, mt, bev=0.0: P.append(H['box'](n, m(*s), m(*c), mt, col, bevel=bev * MM, parent=root)) or P[-1]
    rnd = random.Random(1652)

    # PCB with 8 mounting holes (4 corner pairs, measured off the photo)
    pcb = H['box']('PCB', m(BL, BW, BT), m(0, 0, -BT / 2), M['pcb'], col, bevel=0.35 * MM, parent=root)
    hole_px = [(365, 215), (415, 215), (945, 215), (1000, 215), (365, 725), (415, 725), (945, 725), (1000, 725)]
    holes = [top_px(*p) for p in hole_px]
    hc = bmesh.new()
    for x, y in holes:
        bmesh.ops.create_cone(hc, cap_ends=True, segments=20, radius1=1.6 * MM, radius2=1.6 * MM, depth=8 * MM,
                              matrix=mathutils.Matrix.Translation(m(x, y, -1)))
    cutter = mesh_obj('HoleCutter', hc, M['pcb'], col, None)
    H['cut'](pcb, cutter)
    P.append(pcb)
    # copper keep-out rings with via stitching look (top + bottom)
    P.append(annuli('HolePads_T', [m(x, y)[:2] for x, y in holes], 3.7 * MM, 1.6 * MM, 0, 0.04 * MM, M['copper_ring'], col, root))
    P.append(annuli('HolePads_B', [m(x, y)[:2] for x, y in holes], 3.7 * MM, 1.6 * MM, -BT - 0.04 * MM, 0.04 * MM, M['copper_ring'], col, root))

    occupied = []  # (x0,y0,x1,y1) mm on top side

    def occ(cx, cy, sx, sy, pad=0.6):
        occupied.append((cx - sx / 2 - pad, cy - sy / 2 - pad, cx + sx / 2 + pad, cy + sy / 2 + pad))

    for x, y in holes:
        occ(x, y, 8, 8)

    # ---- GH100 package: substrate, stiffener ring, interposer, die, 6 HBM stacks
    pcx, pcy = -1.4, -0.3
    box('Pkg_Substrate', (56.4, 58.0, 1.1), (pcx, pcy, 0.55), M['substrate'], 0.2)
    occ(pcx, pcy, 56.4, 58.0, 0.3)
    so = [(pcx - 28.2, pcy - 29.0), (pcx + 28.2, pcy - 29.0), (pcx + 28.2, pcy + 29.0), (pcx - 28.2, pcy + 29.0)]
    si = [(pcx - 23.4, pcy - 26.7), (pcx + 23.4, pcy - 26.7), (pcx + 23.4, pcy + 26.7), (pcx - 23.4, pcy + 26.7)]
    P.append(H['ring']('Pkg_Stiffener', [m(*p)[:2] for p in so], [m(*p)[:2] for p in si], 'xy', 1.1 * MM, 0.9 * MM,
                       M['stiffener'], col, parent=root))
    box('Pkg_Interposer', (40.5, 47.0, 0.5), (pcx, pcy, 1.35), M['substrate'])
    # underfill / mould border
    box('Pkg_Mould', (40.0, 46.4, 0.95), (pcx, pcy, 1.6 + 0.475 - 0.0), M['black_mt'])
    box('GH100_Die', (39.2, 25.6, 0.12), (pcx, pcy, 2.6), M['silicon'])
    for i, dx in enumerate((-13.1, 0.0, 13.1)):
        for j, dy in enumerate((18.1, -18.1)):
            box(f'HBM_{i}{j}', (12.6, 9.8, 0.12), (pcx + dx, pcy + dy, 2.6), M['silicon'])
    # die marking (reads top->bottom in the photo: rotated -90 deg about Z)
    lines = cfg['die_lines']
    text('Die_Mark0', lines[0], FONT_BOLD, 0.006, M['silk'], col, root, m(pcx + 6.5, pcy, 2.70), -math.pi / 2, w=18 * MM, h=4.0 * MM)
    for k, ln in enumerate(lines[1:]):
        text(f'Die_Mark{k + 1}', ln, FONT_MONO, 0.003, M['silk'], col, root, m(pcx + 0.5 - k * 4.2, pcy, 2.70), -math.pi / 2, w=15 * MM, h=2.4 * MM)
    if cfg.get('pcb_pn'):
        text('PCB_PN', cfg['pcb_pn'], FONT_REG, 0.0015, M['silk'], col, root, m(28.6, 6.0, 0.05), -math.pi / 2, w=17 * MM)

    # ---- VRM: 31 inductors (grey) each with a power stage (black QFN)
    ind_px = ([(270, y) for y in (220, 290, 365, 440, 515)] + [(385, y) for y in (295, 370, 445, 520)] +
              [(535, 220), (595, 220), (765, 220), (825, 220)] + [(530, 725), (590, 725), (760, 725), (820, 725)] +
              [(1035, y) for y in (300, 375, 455, 535, 615, 690)] + [(1150, y) for y in (288, 360, 432, 506, 580, 654, 726)] +
              [(1095, 224)])
    stage_off = {}
    bmI = bmesh.new(); bmS = bmesh.new()
    for px, py in ind_px:
        x, y = top_px(px, py)
        sx, sy = (8.0, 9.4)
        bm_box(bmI, m(x, y, 3.0), m(sx, sy, 6.0)); occ(x, y, sx, sy)
        if px < 470:
            st = (x + 7.6, y)
        elif px > 880:
            st = (x - 7.6, y)
        elif py < 472:
            st = (x, y - 7.6)
        else:
            st = (x, y + 7.6)
        bm_box(bmS, m(st[0], st[1], 0.45), m(5.0, 6.0, 0.9)); occ(*st, 5.0, 6.0)
    I = mesh_obj('VRM_Inductors', bmI, M['inductor'], col, root); P.append(I)
    bv = I.modifiers.new('Bevel', 'BEVEL'); bv.width = 0.45 * MM; bv.segments = 1; bv.limit_method = 'ANGLE'
    P.append(mesh_obj('VRM_Stages', bmS, M['black_gl'], col, root))
    # inductor top silk marks (tiny white text block faked as thin lighter bars)
    bmT = bmesh.new()
    for px, py in ind_px:
        x, y = top_px(px, py)
        for k in range(3):
            bm_box(bmT, m(x - 2.0 + k * 2.0, y, 6.02), m(0.5, 3.6, 0.04))
    P.append(mesh_obj('VRM_Marks', bmT, M['silk'], col, root))

    # polymer caps '470' and small MOSFETs
    bmC = bmesh.new()
    for px, py in [(437, 340), (437, 410), (437, 520), (920, 355), (920, 420)]:
        x, y = top_px(px, py)
        bm_box(bmC, m(x, y, 0.95), m(4.2, 7.0, 1.9)); occ(x, y, 4.2, 7.0)
    for px in (345, 415):
        for py in (575, 610, 645):
            x, y = top_px(px, py)
            bm_box(bmC, m(x, y, 0.55), m(6.4, 4.0, 1.1)); occ(x, y, 6.4, 4.0)
    for px, py in [(160, 240), (160, 320), (160, 400)]:  # small '2R2' inductors (grey below)
        occ(*top_px(px, py), 4.2, 4.2)
    P.append(mesh_obj('Caps_Polymer', bmC, M['black_gl'], col, root))
    bmL = bmesh.new()
    for px, py in [(160, 240), (160, 320), (160, 400)]:
        x, y = top_px(px, py)
        bm_box(bmL, m(x, y, 1.0), m(4.2, 4.2, 2.0))
    x, y = top_px(250, 725)
    bm_box(bmL, m(x, y, 1.4), m(6.2, 5.0, 2.8)); occ(x, y, 6.2, 5.0)
    P.append(mesh_obj('Small_Inductors', bmL, M['inductor'], col, root))

    # green power daughter module (bottom-left in the photo)
    gx0, gy0 = top_px(132, 560); gx1, gy1 = top_px(310, 690)
    gx0 = max(gx0, -BL / 2 + 0.6)
    gcx, gcy, gsx, gsy = (gx0 + gx1) / 2, (gy0 + gy1) / 2, gx1 - gx0, gy0 - gy1
    box('PwrModule_PCB', (gsx, gsy, 1.0), (gcx, gcy, 0.5), M['greenpcb'], 0.15)
    occ(gcx, gcy, gsx, gsy)
    box('PwrModule_Choke', (8.0, 8.0, 4.2), (gx0 + 6.0, gcy + 1.5, 1.0 + 2.1), M['black_mt'], 0.3)
    bmG = bmesh.new()
    for k in range(18):
        bm_box(bmG, m(gx0 + 12 + (k % 6) * 2.3, gy1 + 2.2 + (k // 6) * 4.6, 1.3), m(1.2, 2.2, 0.6))
    P.append(mesh_obj('PwrModule_Parts', bmG, M['cap'], col, root))

    # scattered 0402/0603 passives on the top side (deterministic)
    def free(x, y, sx, sy):
        if abs(x) > BL / 2 - 1.5 or abs(y) > BW / 2 - 1.5:
            return False
        for (a0, b0, a1, b1) in occupied:
            if x + sx / 2 > a0 and x - sx / 2 < a1 and y + sy / 2 > b0 and y - sy / 2 < b1:
                return False
        return True
    bmP = bmesh.new(); bmQ = bmesh.new(); placed = 0
    for _ in range(4000):
        if placed >= 260:
            break
        x = rnd.uniform(-BL / 2, BL / 2); y = rnd.uniform(-BW / 2, BW / 2)
        sx, sy = rnd.choice(((1.0, 0.5), (1.6, 0.8), (0.5, 1.0), (0.8, 1.6), (2.0, 1.25)))
        if free(x, y, sx, sy):
            bm_box(bmP if rnd.random() < 0.7 else bmQ, m(x, y, 0.3), m(sx, sy, 0.6))
            occupied.append((x - sx / 2 - 0.25, y - sy / 2 - 0.25, x + sx / 2 + 0.25, y + sy / 2 + 0.25))
            placed += 1
    P.append(mesh_obj('Passives_Top', bmP, M['cap'], col, root))
    P.append(mesh_obj('Passives_Top_Dark', bmQ, M['black_gl'], col, root))

    # ---- underside: Molex Mirror Mezz connectors (long + short), passives field, markings
    z_b = -BT
    lx0, ly0 = bot_px(935, 205); lx1, ly1 = bot_px(1130, 715)
    sx0, sy0 = bot_px(315, 350); sx1, sy1 = bot_px(510, 580)
    mezz_h = 4.5
    long_c = ((lx0 + lx1) / 2, (ly0 + ly1) / 2, lx1 - lx0, ly1 - ly0)
    short_c = ((sx0 + sx1) / 2, (sy0 + sy1) / 2, sx1 - sx0, sy1 - sy0)
    for nm, (cx, cy, sx, sy) in (('Mezz_Long', long_c), ('Mezz_Short', short_c)):
        box(nm, (sx, sy, mezz_h), (cx, cy, z_b - mezz_h / 2), M['mezz'], 0.5)
        # shallow latch ribs on the long sides (photo: notches every ~1/4)
        bmR = bmesh.new()
        n = 4 if sy > 40 else 2
        for k in range(n):
            yy = cy - sy / 2 + (k + 0.5) * sy / n
            for sgn in (-1, 1):
                bm_box(bmR, m(cx + sgn * (sx / 2 + 0.25), yy, z_b - mezz_h / 2), m(0.5, 2.2, mezz_h * 0.7))
        P.append(mesh_obj(nm + '_Ribs', bmR, M['mezz'], col, root))
        text(nm + '_Brand', 'molex', FONT_BOLD, 0.004, M['black_st'], col, root, m(cx, cy + sy * 0.3, z_b - mezz_h - 0.03), math.pi / 2, w=min(sy * 0.35, 12) * MM)
        o = P[-1] if False else bpy.data.objects[nm + '_Brand']
        o.rotation_euler = (math.pi, 0, -math.pi / 2)  # face -Z, readable from below
        P.append(o)
    bmB = bmesh.new()
    fx0, fy0 = bot_px(555, 290); fx1, fy1 = bot_px(875, 635)
    x = fx0 + 0.8
    while x < fx1 - 0.5:
        y = fy0 + 0.8
        while y < fy1 - 0.5:
            if rnd.random() < 0.85:
                bm_quad_down(bmB, m(x, y, z_b - 0.45), m(1.0, 0.5) if rnd.random() < 0.7 else m(0.5, 1.0))
            y += 1.7
        x += 1.9
    occB = [(lx0 - 1, ly0 - 1, lx1 + 1, ly1 + 1), (sx0 - 1, sy0 - 1, sx1 + 1, sy1 + 1), (fx0, fy0, fx1, fy1)]
    occB += [(hx - 4, hy - 4, hx + 4, hy + 4) for hx, hy in holes]
    placed = 0
    for _ in range(6000):
        if placed >= 520:
            break
        x = rnd.uniform(-BL / 2 + 1.5, BL / 2 - 1.5); y = rnd.uniform(-BW / 2 + 1.5, BW / 2 - 1.5)
        sx, sy = rnd.choice(((1.0, 0.5), (0.5, 1.0), (1.6, 0.8), (0.8, 1.6)))
        if all(not (x + sx / 2 > a0 and x - sx / 2 < a1 and y + sy / 2 > b0 and y - sy / 2 < b1) for a0, b0, a1, b1 in occB):
            bm_quad_down(bmB, m(x, y, z_b - 0.45), m(sx, sy))
            occB.append((x - sx / 2 - 0.3, y - sy / 2 - 0.3, x + sx / 2 + 0.3, y + sy / 2 + 0.3)); placed += 1
    P.append(mesh_obj('Passives_Bottom', bmB, M['cap'], col, root, recalc=False))
    # bottom QFN controllers + DrMOS (black) around the long edges
    bmD = bmesh.new()
    for px, py in [(160, 245), (225, 195), (1290, 215), (1290, 700), (355, 640), (575, 160), (630, 160), (800, 160),
                   (850, 160), (580, 745), (625, 745), (805, 745), (845, 745), (215, 410), (215, 500), (215, 590),
                   (1265, 360), (1265, 430), (1265, 510)]:
        x, y = bot_px(px, py)
        bm_box(bmD, m(x, y, z_b - 0.4), m(4.5, 4.5, 0.8))
    P.append(mesh_obj('Bottom_ICs', bmD, M['black_gl'], col, root))
    for nm, body, (px, py), w in (('Bot_NVIDIA', 'NVIDIA', (515, 640), 9.0), ('Bot_Config', 'CONFIG 5', (535, 460), 9.0)):
        x, y = bot_px(px, py)
        o = text(nm, body, FONT_BOLD, 0.002, M['silk'], col, root, m(x, y, z_b - 0.05), 0, w=w * MM)
        o.rotation_euler = (math.pi, 0, math.pi / 2)
        P.append(o)
    # serial sticker beside the long connector
    x, y = bot_px(905, 545)
    box('Bot_QR', (4.2, 4.2, 0.08), (x, y, z_b - 0.04), M['label_white'])

    # gather text objects created by text() (not appended above)
    for o in list(col.objects):
        if o.parent == root and o.type == 'MESH' and o not in P and o.name.startswith(('Die_Mark', 'PCB_PN')):
            P.append(o)
    return join(P, 'Module')


# ---------------------------------------------------------------- heatsink (HGX H100/H200 air-cooled)
HS_TOP = 118.0          # mm above the board top: plate surface (approx., HGX 4U GPU tray)
TOWER_X = 58.0          # tower half-length (tower shorter than the board; low fin block is full length)
SHELF_Y = -12.0         # tower/plate covers y in [SHELF_Y, BW/2]; label shelf on the -Y side


def build_heatsink(cfg, root, col, M):
    P = []
    box = lambda n, s, c, mt, bev=0.0: P.append(H['box'](n, m(*s), m(*c), mt, col, bevel=bev * MM, parent=root)) or P[-1]
    hw, hl = BW / 2 - 0.5, BL / 2 - 1.0
    # copper pedestal on the GPU package + copper base plate (seen copper-coloured under the low fins)
    box('HS_Pedestal', (44.0, 50.0, 3.4), (-1.4, -0.3, 2.72 + 1.7), M['copper'])
    box('HS_Base', (BL - 4.0, BW - 2.0, 3.5), (0, 0, 6.1 + 1.75), M['copper'], 0.4)
    # spring standoffs at the 8 mounting holes
    bmS = bmesh.new()
    for px, py in [(365, 215), (415, 215), (945, 215), (1000, 215), (365, 725), (415, 725), (945, 725), (1000, 725)]:
        x, y = top_px(px, py)
        bmesh.ops.create_cone(bmS, cap_ends=True, segments=12, radius1=2.6 * MM, radius2=2.6 * MM, depth=6.1 * MM,
                              matrix=mathutils.Matrix.Translation(m(x, y, 3.05)))
    P.append(mesh_obj('HS_Standoffs', bmS, M['black_st'], col, root))

    # low fin block: vertical fins (XZ planes, thin in Y), full module footprint, z 9.6..38
    z0, z1 = 9.6, 38.0

    def low_fins():
        n = 52
        for k in range(n):
            y = -hw + (k + 0.5) * (2 * hw) / n
            yield m(0, y, (z0 + z1) / 2), m(2 * hl, 0.35, z1 - z0)
    P.append(H['slat_array']('HS_LowFins', low_fins, M['fin_dark'], col, root))
    box('HS_MidPlate', (2 * TOWER_X + 2.0, 2 * hw, 1.2), (0, 0, z1 + 0.6), M['fin_dark'])

    # tower: horizontal fins (XY planes stacked in Z) threaded on 6 vertical heat pipes
    t0 = z1 + 1.2
    shelf_lo = 98.0

    def tower_fins():
        z = t0 + 0.6
        while z < HS_TOP - 2.6:
            y_lo = -hw if z < shelf_lo - 0.5 else SHELF_Y
            yield m(0, (y_lo + hw) / 2, z), m(2 * TOWER_X, hw - y_lo, 0.4)
            z += 1.9
    P.append(H['slat_array']('HS_TowerFins', tower_fins, M['fin_tower'], col, root))
    bmP = bmesh.new()
    for x in (-TOWER_X + 5.0, TOWER_X - 5.0):
        for y in (-24.0, 0.0, 24.0):
            ztop = (shelf_lo - 1.0) if y < SHELF_Y else (HS_TOP - 2.2)
            bmesh.ops.create_cone(bmP, cap_ends=True, segments=14, radius1=3.0 * MM, radius2=3.0 * MM,
                                  depth=(ztop - 9.6) * MM, matrix=mathutils.Matrix.Translation(m(x, y, (ztop + 9.6) / 2)))
    P.append(mesh_obj('HS_HeatPipes', bmP, M['copper'], col, root))
    # black sheet-metal corner posts / spine
    for sx in (-1, 1):
        for y0, y1, zt in ((-hw, SHELF_Y, shelf_lo), (SHELF_Y, hw, HS_TOP - 2.0)):
            for yy in (y0 + 1.2, y1 - 1.2):
                box('HS_Post', (2.4, 2.4, zt - t0), (sx * (TOWER_X + 0.2), yy, (zt + t0) / 2), M['black_dc'])
        box('HS_EndRail', (2.0, hw - SHELF_Y, 3.0), (sx * (TOWER_X + 0.2), (SHELF_Y + hw) / 2, HS_TOP - 3.5), M['black_dc'])

    # top plate (champagne) with 4 screws and the NVIDIA logo + wordmark
    py0, py1 = SHELF_Y, hw + 0.5
    pcy = (py0 + py1) / 2
    box('HS_TopPlate', (2 * TOWER_X + 2.0, py1 - py0, 2.0), (0, pcy, HS_TOP - 1.0), M['champagne'], 0.5)
    bmW = bmesh.new()
    for sx in (-1, 1):
        for sy in (py0 + 4.2, py1 - 4.2):
            bmesh.ops.create_cone(bmW, cap_ends=True, segments=16, radius1=2.0 * MM, radius2=1.6 * MM, depth=0.6 * MM,
                                  matrix=mathutils.Matrix.Translation(m(sx * (TOWER_X - 4.5), sy, HS_TOP + 0.3)))
    P.append(mesh_obj('HS_PlateScrews', bmW, M['nickel'], col, root))
    logo_parts(P, col, root, M, cx=-21.2, cy=pcy, W=16.4, Hh=11.2, z=HS_TOP)
    P.append(text('HS_Wordmark', 'NVIDIA', FONT_BLACK, 0.008, M['label'], col, root, m(9.6, pcy, HS_TOP), 0, w=39.0 * MM, h=7.2 * MM, extrude=0.00008, res=3))

    # -Y side: label shelf (black middle + smoked clear end blocks, copper captive screws) and a lower dark bar
    ls0, ls1, ls_top = -27.0, SHELF_Y, 110.0
    box('HS_Shelf_Mid', (62.0, ls1 - ls0, ls_top - shelf_lo), (0, (ls0 + ls1) / 2, (ls_top + shelf_lo) / 2), M['black_mt'])
    for sx in (-1, 1):
        box('HS_Shelf_Clear', (TOWER_X + 1.0 - 31.0, ls1 - ls0, ls_top - shelf_lo),
            (sx * (31.0 + (TOWER_X + 1.0 - 31.0) / 2), (ls0 + ls1) / 2, (ls_top + shelf_lo) / 2), M['smoke'], 0.4)
    db_top = 104.0
    box('HS_DarkBar', (62.0, ls0 + hw, db_top - shelf_lo), (0, (ls0 - hw) / 2, (db_top + shelf_lo) / 2), M['black_mt'])
    for sx in (-1, 1):
        box('HS_DarkBar_Clear', (TOWER_X + 1.0 - 31.0, ls0 + hw, db_top - shelf_lo),
            (sx * (31.0 + (TOWER_X + 1.0 - 31.0) / 2), (ls0 - hw) / 2, (db_top + shelf_lo) / 2), M['smoke'], 0.4)
    bmCS = bmesh.new()
    for sx in (-1, 1):
        for (yy, zt) in (((ls0 + ls1) / 2, ls_top), ((ls0 - hw) / 2, db_top)):
            bmesh.ops.create_cone(bmCS, cap_ends=True, segments=16, radius1=2.6 * MM, radius2=2.0 * MM, depth=2.2 * MM,
                                  matrix=mathutils.Matrix.Translation(m(sx * 36.5, yy, zt + 1.1)))
            # shank visible through the smoked plastic
            bmesh.ops.create_cone(bmCS, cap_ends=True, segments=10, radius1=1.4 * MM, radius2=1.4 * MM, depth=(zt - 9.6) * MM,
                                  matrix=mathutils.Matrix.Translation(m(sx * 36.5, yy, (zt + 9.6) / 2)))
    P.append(mesh_obj('HS_CaptiveScrews', bmCS, M['copper'], col, root))
    # product label sticker (on the shelf top, readable from -Y)
    lcy = (ls0 + ls1) / 2
    box('HS_Label', (60.0, 10.5, 0.1), (0, lcy, ls_top + 0.05), M['label'])
    P.append(text('HS_Label_Prod', cfg['label_top'], FONT_BOLD, 0.002, M['label_white'], col, root, m(-13.0, lcy + 3.2, ls_top + 0.17), 0, h=1.5 * MM))
    if cfg.get('label_fru'):
        P.append(text('HS_Label_FRU', cfg['label_fru'], FONT_REG, 0.002, M['label_white'], col, root, m(-13.0, lcy + 1.0, ls_top + 0.17), 0, h=1.2 * MM))
    P.append(text('HS_Label_NV', 'NVIDIA', FONT_BOLD, 0.002, M['label_white'], col, root, m(14.0, lcy + 3.2, ls_top + 0.17), 0, h=1.3 * MM))
    P.append(text('HS_Label_SN', cfg['label_sn'], FONT_REG, 0.002, M['label_white'], col, root, m(19.0, lcy + 1.0, ls_top + 0.17), 0, h=1.2 * MM))
    rnd = random.Random(141)

    def bars():
        for x0, x1 in ((-26.5, -2.0), (5.0, 27.5)):
            x = x0
            while x < x1:
                w = rnd.choice((0.18, 0.18, 0.3, 0.45))
                yield m(x + w / 2, lcy - 2.4, ls_top + 0.13), m(w, 3.6, 0.04)
                x += w + rnd.choice((0.18, 0.3, 0.45))
    P.append(H['slat_array']('HS_Label_Barcode', bars, M['label_white'], col, root))
    return join(P, 'Heatsink')


def logo_parts(P, col, root, M, cx, cy, W, Hh, z):
    """Simplified NVIDIA 'eye' mark: black box on the right 2/3, eye swirl strokes that are black outside
    the box and plate-coloured inside it."""
    bx0 = cx - W / 2 + 0.36 * W
    box_o = H['box']('Logo_Box', m(cx + W / 2 - bx0, Hh, 0.12), m((bx0 + cx + W / 2) / 2, cy, z + 0.06), M['label'], col, parent=root)
    P.append(box_o)
    ex0, ex1 = cx - W / 2 + 0.3, cx + W * 0.27
    ecx, ew, eh = (ex0 + ex1) / 2, (ex1 - ex0) / 2, Hh * 0.40
    lens = []
    for k in range(33):
        t = -math.pi / 2 + math.pi * k / 32
        lens.append((ecx + ew * math.sin(t), cy + eh * math.cos(t) ** 1.6))
    lens_lo = [(x, cy - (y - cy)) for x, y in lens]
    spiral = []
    for k in range(29):
        a = math.radians(200 - 300 * k / 28)
        r = Hh * (0.27 - 0.09 * k / 28)
        spiral.append((ecx + 1.0 + r * math.cos(a), cy + r * math.sin(a) * 0.95))
    bm_out, bm_in = bmesh.new(), bmesh.new()
    for pts in (lens, lens_lo, spiral):
        seg_out, seg_in = [], []
        for p in pts:
            (seg_out if p[0] < bx0 else seg_in).append(p)
        for seg, bm_ in ((seg_out, bm_out), (seg_in, bm_in)):
            if len(seg) > 1:
                ribbon(bm_, [m(*p)[:2] for p in seg], 1.0 * MM, (z + 0.0) * MM, 0.16 * MM)
    bm_box(bm_out, m(cx - W / 2 + 0.36 * W - 0.6, cy + eh * 0.15, z + 0.08), m(0.01, 0.01, 0.01))  # keep mesh non-empty
    P.append(mesh_obj('Logo_EyeOut', bm_out, M['label'], col, root))
    P.append(mesh_obj('Logo_EyeIn', bm_in, M['champagne'], col, root))


# ---------------------------------------------------------------- sockets, camera, render
def sockets(root, col):
    s = bpy.data.objects.new('SOCKET_power_in', None); s.empty_display_type = 'SINGLE_ARROW'; s.empty_display_size = 0.02
    s.location = m(0, 0, -BT - 4.5); col.objects.link(s); s.parent = root
    s.rotation_euler = (math.pi, 0, 0)
    p = bpy.data.objects.new('SOCKET_mezzanine', None); p.empty_display_type = 'ARROWS'; p.empty_display_size = 0.015
    lx0, _ = bot_px(935, 205); lx1, _ = bot_px(1130, 715)
    p.location = m((lx0 + lx1) / 2, 0, -BT - 4.5); col.objects.link(p); p.parent = root


def cam(loc, target, lens=50.0):
    c = bpy.data.objects['Camera']
    c.location = loc
    d = mathutils.Vector(target) - mathutils.Vector(loc)
    c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    c.data.lens = lens
    c.data.clip_start = 0.005
    bpy.context.scene.camera = c


def render(path):
    s = bpy.context.scene
    s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1280, 720, 100
    s.render.image_settings.file_format = 'PNG'
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)


def tri_count(objs):
    dg = bpy.context.evaluated_depsgraph_get(); t = 0
    for o in objs:
        if o.type == 'MESH':
            e = o.evaluated_get(dg); me = e.to_mesh(); me.calc_loop_triangles(); t += len(me.loop_triangles); e.to_mesh_clear()
    return t


def build(cfg):
    root, col = H['new_card_scene'](cfg['root'])
    M = mats()
    mod = build_module(cfg, root, col, M)
    hs = build_heatsink(cfg, root, col, M)
    sockets(root, col)
    for o in list(col.objects):  # stray cutters/empties other than ours
        if o.type == 'MESH' and o not in (mod, hs):
            print('WARN stray mesh', o.name)
    floor = bpy.data.objects.get('Floor')
    if floor:
        floor.location = (0, 0, -(BT + 4.5 + 0.05) * MM)
    print('TRIS module', tri_count([mod]), 'heatsink', tri_count([hs]))
    bpy.ops.wm.save_as_mainfile(filepath=cfg['blend'])
    os.makedirs(os.path.dirname(cfg['glb']), exist_ok=True)
    tris = H['export_glb'](cfg['root'], cfg['glb'])
    print('EXPORT', cfg['glb'], 'tris', tris, 'bytes', os.path.getsize(cfg['glb']))

    rd = os.path.join(BLEND_DIR, 'renders')
    pre = os.path.join(rd, cfg['render_prefix'])
    views = os.environ.get('SXM_VIEWS', 'top,side,34,bare,bare_top,bottom').split(',')
    if '34' in views:
        cam((0.20, -0.30, 0.26), (0.0, 0.0, 0.045), 50); render(pre + '_34.png')
    if 'top' in views:
        vs = bpy.context.scene.view_settings; ex = vs.exposure; vs.exposure = ex - 0.9
        cam((0.0, -0.001, 0.62), (0.0, 0.0, 0.0), 80); render(pre + '_top.png'); vs.exposure = ex
    if 'side' in views:
        cam((0.0, -0.75, 0.06), (0.0, 0.0, 0.055), 100); render(pre + '_side.png')
    hs.hide_render = True
    if 'bare' in views:
        cam((0.13, -0.17, 0.15), (0.0, 0.0, 0.0), 50); render(pre + '_bare.png')
    if 'bare_top' in views:
        vs = bpy.context.scene.view_settings; ex = vs.exposure; vs.exposure = ex - 0.9
        cam((0.0, -0.0005, 0.36), (0.0, 0.0, 0.0), 70); render(pre + '_bare_top.png'); vs.exposure = ex
    if 'bottom' in views:
        if floor: floor.hide_render = True
        cam((0.0, -0.0005, -0.36), (0.0, 0.0, 0.0), 70)
        bpy.data.objects['Camera'].rotation_euler = (math.pi, 0, 0)
        render(pre + '_bottom.png')
        if floor: floor.hide_render = False
    hs.hide_render = False
    return root


if not globals().get('SXM_LIBRARY_MODE'):
    build(CFG_H100)
