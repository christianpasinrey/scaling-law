"""Floor and ceiling tiles for the data hall.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python hall_07_tiles.py [-- --norender]

Pieces:
  Tile_Concrete_1200        polished/sealed concrete slab tile 1.2 x 1.2 m (top at z=0, 0.1 m body below),
                            saw-cut joints baked into the texture (modern AI hall, slab-on-grade)
  Tile_Concrete_Hazard_1200 same with a yellow/black safety stripe band along the -Y edge
  Tile_RaisedPerf_600       600 x 600 x 35 mm perforated raised-floor panel, finished floor height 600 mm
                            (colocation era). Texture after Wikimedia 'All-steel perforated ventilation raised floor
                            panel 28 percent open area.jpg' (8 x 8 clusters of 3 x 3 holes). One pedestal at the
                            (-x,-y) corner + stringers on the -X and -Y edges, so a grid of tiles gets one per node.
  Tile_RaisedSolid_600      same, solid HPL top
  Tile_Ceiling_600_LED      600 x 600 lay-in mineral tile in a 24 mm T-bar grid with a linear LED luminaire
                            (LED_light emissive). Origin = tile centre on the ceiling plane (grid flange bottom z=0),
                            the game places it at the ceiling height. T-bars on the -X/-Y edges only (tiling).
  Tile_Ceiling_600          same without luminaire
Textures are generated procedurally (numpy) and packed into the .blend / .glb.
"""
import bpy, bmesh, math, mathutils, os, sys
import numpy as np
from mathutils import Vector

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\hall_lib.py', encoding='utf-8').read())

FILE = 'hall_07_tiles'
BLEND = os.path.join(BASE, FILE + '.blend')
reset_scene()
M = mats()
COL = 'HALL_Tiles'
stats = []
rng = np.random.default_rng(7)


def noise(px, octaves=((8, 0.5), (32, 0.3), (128, 0.15), (512, 0.05))):
    """Tileable value noise (wraps), 0..1."""
    acc = np.zeros((px, px), np.float32)
    for cells, amp in octaves:
        g = rng.random((cells, cells)).astype(np.float32)
        rep = px // cells
        # bilinear upsample with wrap
        idx = (np.arange(px) + 0.5) / rep - 0.5
        i0 = np.floor(idx).astype(int) % cells; i1 = (i0 + 1) % cells
        f = (idx - np.floor(idx)).astype(np.float32)
        f = f * f * (3 - 2 * f)
        a = g[i0][:, i0] * (1 - f)[None, :] + g[i0][:, i1] * f[None, :]
        b = g[i1][:, i0] * (1 - f)[None, :] + g[i1][:, i1] * f[None, :]
        acc += amp * (a * (1 - f)[:, None] + b * f[:, None])
    return acc / sum(a for _, a in octaves)


def concrete_img(name, hazard=False, px=512):
    n = noise(px)
    n2 = noise(px, ((64, 0.6), (256, 0.4)))
    base = 0.30 + 0.10 * (n - 0.5) + 0.04 * (n2 - 0.5)
    # sparse aggregate specks
    sp = rng.random((px, px)) > 0.996
    base = base - 0.07 * sp
    img = np.zeros((px, px, 4), np.float32)
    for c, tint in enumerate((1.0, 0.99, 0.96)):
        img[..., c] = base * tint
    img[..., 3] = 1
    # saw-cut joint: dark 3 px border (1.2 m tile -> ~3.5 mm)
    j = 2
    for c in range(3):
        img[:j, :, c] *= 0.25; img[-j:, :, c] *= 0.25; img[:, :j, c] *= 0.25; img[:, -j:, c] *= 0.25
    if hazard:
        band = int(px * 0.10 / 1.2)          # 100 mm band along -Y edge (image row 0 = v 0 = -Y)
        y, x = np.mgrid[0:band, 0:px]
        stripe = ((x + y) // int(px * 0.05 / 1.2)) % 2 == 0
        wear = 0.85 + 0.15 * n[:band, :]
        yel = np.array((0.85, 0.55, 0.0)); blk = np.array((0.02, 0.02, 0.02))
        for c in range(3):
            img[j + 4:band + j + 4, :, c] = np.where(stripe, yel[c], blk[c]) * wear
    return np_image(name, img)


def hpl_img(name, perforated, px=512):
    n = noise(px, ((16, 0.5), (64, 0.3), (256, 0.2)))
    base = 0.62 + 0.06 * (n - 0.5)
    img = np.zeros((px, px, 4), np.float32)
    for c, t in enumerate((1.0, 1.0, 0.97)):
        img[..., c] = base * t
    img[..., 3] = 1
    if perforated:
        y, x = np.mgrid[0:px, 0:px].astype(np.float32) + 0.5
        cell = px / 8.0
        cx = (x % cell) / cell; cy = (y % cell) / cell        # 0..1 within a cluster cell
        hole = np.zeros((px, px), np.float32)
        for hx in (0.33, 0.5, 0.67):
            for hy in (0.33, 0.5, 0.67):
                d = np.sqrt((cx - hx) ** 2 + (cy - hy) ** 2) * cell
                hole = np.maximum(hole, np.clip((cell * 0.065 - d) * 1.5 + 0.5, 0, 1))
        for c in range(3):
            img[..., c] = img[..., c] * (1 - hole) + 0.015 * hole
    return np_image(name, img)


def ceiling_img(name, px=512):
    n = noise(px, ((32, 0.5), (128, 0.5)))
    base = 0.72 + 0.05 * (n - 0.5)
    fiss = (rng.random((px, px)) > 0.985).astype(np.float32)
    base = base - 0.18 * fiss
    img = np.zeros((px, px, 4), np.float32)
    for c in range(3):
        img[..., c] = base
    img[..., 3] = 1
    return np_image(name, img)


# ------------------------------------------------------------------ concrete
for name, tag, hz in (('Tile_Concrete_1200', 'TL_C', False), ('Tile_Concrete_Hazard_1200', 'TL_CH', True)):
    root, col = piece(name, tag, COL)
    m = tex_mat('HALL_' + name, concrete_img('HALL_tex_' + name, hz), 0.0, 0.32)
    quad('Top', 1.2, 1.2, (0, 0, 0), m, col, root)
    H['box']('Body', (1.2, 1.2, 0.1), (0, 0, -0.0501), M['concrete_side'], col, parent=root)
    root['tile_size_m'] = 1.2
    finish_piece(root, tag, FILE, stats)

# ------------------------------------------------------------------ raised floor
FFH = 0.600
TT = 0.035
for name, tag, perf in (('Tile_RaisedPerf_600', 'TL_RP', True), ('Tile_RaisedSolid_600', 'TL_RS', False)):
    root, col = piece(name, tag, COL)
    m = tex_mat('HALL_' + name, hpl_img('HALL_tex_' + name, perf), 0.0, 0.45)
    quad('Top', 0.594, 0.594, (0, 0, FFH + 0.0002), m, col, root)
    H['box']('Panel', (0.6, 0.6, TT), (0, 0, FFH - TT / 2), M['black_pc'], col, parent=root)
    if perf:
        # damper / grating seen through the holes
        H['box']('Damper', (0.55, 0.55, 0.01), (0, 0, FFH - TT - 0.01), M['port'], col, parent=root)
    zs = FFH - TT
    H['box']('Stringer_X', (0.6, 0.022, 0.032), (0, -0.3, zs - 0.016), M['pedestal'], col, parent=root)
    H['box']('Stringer_Y', (0.022, 0.6, 0.032), (-0.3, 0, zs - 0.016), M['pedestal'], col, parent=root)
    H['box']('Pedestal_Head', (0.09, 0.09, 0.004), (-0.3, -0.3, zs - 0.034), M['pedestal'], col, parent=root)
    H['cyl']('Pedestal_Stem', 0.011, zs - 0.04, (-0.3, -0.3, (zs - 0.036) / 2 + 0.002), M['pedestal'], col, verts=10, parent=root)
    H['cyl']('Pedestal_Nut', 0.02, 0.02, (-0.3, -0.3, zs - 0.08), M['pedestal'], col, verts=6, parent=root)
    H['box']('Pedestal_Base', (0.1, 0.1, 0.004), (-0.3, -0.3, 0.002), M['pedestal'], col, parent=root)
    root['tile_size_m'] = 0.6
    root['finished_floor_height_m'] = FFH
    finish_piece(root, tag, FILE, stats)

# ------------------------------------------------------------------ ceiling
cm = tex_mat('HALL_CeilingTile', ceiling_img('HALL_tex_ceiling'), 0.0, 0.85)
for name, tag, with_led in (('Tile_Ceiling_600_LED', 'TL_CL', True), ('Tile_Ceiling_600', 'TL_CP', False)):
    root, col = piece(name, tag, COL)
    quad('Tile_Face', 0.576, 0.576, (0, 0, 0.004), cm, col, root, uv_rep=(1, 1), rot=(math.pi, 0, 0))
    H['box']('Tile_Body', (0.576, 0.576, 0.015), (0, 0, 0.0115), M['white_pnl'], col, parent=root)
    # inverted-T grid on the -X and -Y edges
    for nm, size, loc in (('TBar_X_Flange', (0.6, 0.024, 0.002), (0, -0.3, 0.001)),
                          ('TBar_X_Web', (0.6, 0.004, 0.036), (0, -0.3, 0.02)),
                          ('TBar_X_Bulb', (0.6, 0.008, 0.008), (0, -0.3, 0.04)),
                          ('TBar_Y_Flange', (0.024, 0.6, 0.002), (-0.3, 0, 0.001)),
                          ('TBar_Y_Web', (0.004, 0.6, 0.036), (-0.3, 0, 0.02)),
                          ('TBar_Y_Bulb', (0.008, 0.6, 0.008), (-0.3, 0, 0.04))):
        H['box'](nm, size, loc, M['tbar'], col, parent=root)
    if with_led:
        H['box']('Luminaire_Housing', (0.576, 0.09, 0.06), (0, 0, 0.032), M['tbar'], col, parent=root)
        led('LED_light', (0.56, 0.06, 0.003), (0, 0, 0.0005), (1.0, 0.97, 0.92), root, col, 12.0)
    root['tile_size_m'] = 0.6
    finish_piece(root, tag, FILE, stats)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
export_all(FILE, stats)

if DO_RENDER:
    PP = {r.name: r for r, t in PIECES}
    for r, t in PIECES:
        for o in [r] + list(r.children_recursive):
            o.hide_render = True
    # concrete floor 4 x 4 with a hazard row, raised floor patch, ceiling patch above
    for i in range(4):
        for j in range(4):
            n = 'Tile_Concrete_Hazard_1200' if j == 0 else 'Tile_Concrete_1200'
            dup(PP[n], (-2.4 + i * 1.2, -1.8 + j * 1.2, 0))
    for i in range(5):
        for j in range(4):
            n = 'Tile_RaisedPerf_600' if j == 1 else 'Tile_RaisedSolid_600'
            dup(PP[n], (2.7 + i * 0.6, -1.5 + j * 0.6, 0))
    for i in range(6):
        for j in range(4):
            n = 'Tile_Ceiling_600_LED' if j == 1 else 'Tile_Ceiling_600'
            dup(PP[n], (-0.3 + i * 0.6, -1.5 + j * 0.6, 3.0))
    bpy.data.objects['Floor'].hide_render = True
    studio(6.0, (0.5, 0, 1.0))
    add_sun(1.2)
    render_views(FILE, {
        'overview': ((-3.4, -6.2, 2.6), (1.5, 0.0, 0.5), 26),
        'perf':     ((4.4, -2.0, 1.6), (4.0, -0.6, 0.6), 30),
        'ceiling':  ((1.0, -3.0, 1.6), (1.2, -0.6, 3.0), 26),
        'raised_edge': ((2.0, -3.0, 0.8), (3.6, -1.2, 0.4), 30),
    })
