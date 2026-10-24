"""Yellow fibre raceway (Panduit FiberRunner 12x4 system) - tileable pieces.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python hall_02_fiber_tray.py [-- --norender]

Real references:
  - Panduit FR12X4YL6 FiberRunner channel: 6 ft (1.83 m) long, 13.46 in (342 mm) wide, ~4.45 in (113 mm) high,
    PVC, yellow (distributor listings mc-mc.com / lumen.ca).
  - Wikimedia 'Network Yellow Fiber Cable Mgmt.jpg': rolled top lips, smooth walls with one rib, grid floor seen
    from below, hooded spill-over fittings dropping into racks, couplers with metal QuikLock clips.
  - Straight pieces are 1.8 m (3 grid cells of 600 mm) instead of 1.829 m so rows tile with 600 mm racks.
Pieces (origin = floor under piece centre / tee centre / elbow corner; channel bottom at FIBER_Z = 3.80 m):
  Fiber_Straight_1m8, Fiber_Straight_0m6, Fiber_Elbow90, Fiber_Tee, Fiber_Waterfall, Fiber_Coupler,
  Fiber_EndCap, Fiber_Hanger
Flow: every piece carries an aqua OM4 fibre bundle 'FLOW_fiber*' (flow_kind = 'data') + SOCKET_data_in/out.
"""
import bpy, bmesh, math, mathutils, os, sys
from mathutils import Vector

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\hall_lib.py', encoding='utf-8').read())

FILE = 'hall_02_fiber_tray'
BLEND = os.path.join(BASE, FILE + '.blend')
reset_scene()
M = mats()
COL = 'HALL_FiberTray'
stats = []

WF, HF, T = 0.342, 0.113, 0.0035
HW = WF / 2
Z = FIBER_Z
RF = 0.08                       # tee inner fillet radius
RE = 0.26                       # elbow centreline radius


def u_profile(sx=1.0, sb=1.0, db=0.0):
    p = [(-HW, 0), (HW, 0), (HW, 0.050), (HW + 0.004, 0.050), (HW + 0.004, 0.058), (HW, 0.058), (HW, HF),
         (HW - 0.012, HF), (HW - 0.012, HF - 0.005), (HW - T, HF - 0.005), (HW - T, T), (-HW + T, T),
         (-HW + T, HF - 0.005), (-HW + 0.012, HF - 0.005), (-HW + 0.012, HF), (-HW, HF), (-HW, 0.058),
         (-HW - 0.004, 0.058), (-HW - 0.004, 0.050), (-HW, 0.050)]
    return [(a * sx, b * sb + db) for a, b in p]


WALL = [(0, 0), (T, 0), (T, HF - 0.005), (0.012, HF - 0.005), (0.012, HF), (0, HF), (0, 0.058), (-0.004, 0.058),
        (-0.004, 0.050), (0, 0.050)]
BUNDLE = ellipse(0.075, 0.011, 12, 0.0, T + 0.011)


def bundle(name, pts, root, col, radius=0.0):
    o, L = sweep(name, pts, BUNDLE, M['aqua'], col, root, radius=radius, smooth=True, flow='data', root=root)
    return o


def channel(name, pts, root, col, radius=0.0):
    o, L = sweep(name, pts, u_profile(), M['yellow'], col, root, radius=radius, segs90=12)
    return o


def floor_grid(name, x0, x1, root, col):
    """Grid relief under the floor (seen from below in the reference photo)."""
    def g():
        n = int((x1 - x0) / 0.03)
        for i in range(n + 1):
            yield (x0 + i * (x1 - x0) / n, 0, Z - 0.002), (0.004, WF - 0.01, 0.004)
        for k in range(9):
            yield ((x0 + x1) / 2, -HW + 0.02 + k * (WF - 0.04) / 8, Z - 0.002), (x1 - x0, 0.004, 0.004)
    return H['slat_array'](name, g, M['yellow'], col, root)


def straight(name, tag, L):
    root, col = piece(name, tag, COL)
    pts = [(-L / 2, 0, Z), (L / 2, 0, Z)]
    channel('Channel', pts, root, col)
    floor_grid('Floor_Grid', -L / 2 + 0.01, L / 2 - 0.01, root, col)
    bundle('FLOW_fiber', pts, root, col)
    joint('JOINT_a', (-L / 2, 0, Z), (-1, 0, 0), root, col)
    joint('JOINT_b', (L / 2, 0, Z), (1, 0, 0), root, col)
    socket('SOCKET_data_in', (-L / 2, 0, Z + 0.02), (-1, 0, 0), root, col)
    socket('SOCKET_data_out', (L / 2, 0, Z + 0.02), (1, 0, 0), root, col)
    root['length_m'] = L
    finish_piece(root, tag, FILE, stats)


straight('Fiber_Straight_1m8', 'FR_S18', 1.8)
straight('Fiber_Straight_0m6', 'FR_S06', 0.6)

# ------------------------------------------------------------------ 90 degree horizontal elbow (one cell, corner at origin)
root, col = piece('Fiber_Elbow90', 'FR_E', COL)
pts = [(-CELL / 2, 0, Z), (0, 0, Z), (0, CELL / 2, Z)]
channel('Channel', pts, root, col, radius=RE)
bundle('FLOW_fiber', pts, root, col, radius=RE)
joint('JOINT_a', (-CELL / 2, 0, Z), (-1, 0, 0), root, col)
joint('JOINT_b', (0, CELL / 2, Z), (0, 1, 0), root, col)
socket('SOCKET_data_in', (-CELL / 2, 0, Z + 0.02), (-1, 0, 0), root, col)
socket('SOCKET_data_out', (0, CELL / 2, Z + 0.02), (0, 1, 0), root, col)
finish_piece(root, 'FR_E', FILE, stats)

# ------------------------------------------------------------------ tee (main along X, branch +Y)
root, col = piece('Fiber_Tee', 'FR_T', COL)
E = CELL / 2
outline = [(-E, -HW), (E, -HW), (E, HW)]
outline += arc_pts((HW + RF, HW + RF), RF, 270, 180, 8)
outline += [(HW, E), (-HW, E)]
outline += arc_pts((-HW - RF, HW + RF), RF, 360, 270, 8)
outline += [(-E, HW)]
poly_prism('Floor', outline, Z, Z + T, M['yellow'], col, root)
walls = [
    ([(-E, -HW, Z), (E, -HW, Z)], 0.0),
    ([(E, HW, Z), (HW, HW, Z), (HW, E, Z)], RF),
    ([(-HW, E, Z), (-HW, HW, Z), (-E, HW, Z)], RF),
]
for i, (p, r) in enumerate(walls):
    sweep(f'Wall_{i}', p, WALL, M['yellow'], col, root, radius=r, segs90=10)
bundle('FLOW_fiber_main', [(-E, 0, Z), (E, 0, Z)], root, col)
bundle('FLOW_fiber_branch', [(-E, 0.05, Z), (-0.05, 0.05, Z), (-0.05, E, Z)], root, col, radius=0.12)
joint('JOINT_a', (-E, 0, Z), (-1, 0, 0), root, col)
joint('JOINT_b', (E, 0, Z), (1, 0, 0), root, col)
joint('JOINT_c', (0, E, Z), (0, 1, 0), root, col)
socket('SOCKET_data_in', (-E, 0, Z + 0.02), (-1, 0, 0), root, col)
socket('SOCKET_data_out_0', (E, 0, Z + 0.02), (1, 0, 0), root, col)
socket('SOCKET_data_out_1', (0, E, Z + 0.02), (0, 1, 0), root, col)
finish_piece(root, 'FR_T', FILE, stats)

# ------------------------------------------------------------------ waterfall / spill-over into a rack (+Y side)
root, col = piece('Fiber_Waterfall', 'FR_W', COL)
YO = HW + 0.06                  # drop axis offset from the tray centreline
ZTOP = Z + HF
hood_pts = [(0, HW - 0.08, ZTOP - 0.012), (0, YO, ZTOP - 0.012), (0, YO, Z - 0.09)]
sweep('Spill_Hood', hood_pts, rrect(0.13, 0.05, 0.018, 3), M['yellow'], col, root, radius=0.07, segs90=10, up0=(0, 0, 1))
# vertical 4x4 channel down to the rack roof, with a flared bottom
sweep('Drop_4x4', [(0, YO, Z - 0.07), (0, YO, RACK_H + 0.06)], rrect(0.112, 0.112, 0.008, 2), M['yellow'], col, root, up0=(0, 1, 0))
sweep('Drop_Flare', [(0, YO, RACK_H + 0.07), (0, YO, RACK_H + 0.02)], rrect(0.15, 0.15, 0.02, 2), M['yellow'], col, root, up0=(0, 1, 0))
H['box']('Drop_Clip_Top', (0.12, 0.12, 0.02), (0, YO, Z - 0.08), M['zinc'], col, parent=root)
bundle_path = [(0, -0.02, Z + T + 0.012), (0, HW - 0.08, Z + T + 0.012), (0, HW - 0.04, ZTOP - 0.014), (0, YO, ZTOP - 0.014), (0, YO, RACK_H + 0.02)]
sweep('FLOW_fiber_drop', bundle_path, ellipse(0.04, 0.012, 10), M['aqua'], col, root, radius=0.05, smooth=True,
      flow='data', root=root, up0=(0, 0, 1))
socket('SOCKET_data_in', (0, -0.02, Z + 0.02), (-1, 0, 0), root, col)
socket('SOCKET_data_out', (0, YO, RACK_H + 0.02), (0, 0, -1), root, col)
root['drop_offset_y'] = YO
root['drop_bottom_z'] = RACK_H + 0.02
finish_piece(root, 'FR_W', FILE, stats)

# ------------------------------------------------------------------ coupler (centred on the butt plane)
root, col = piece('Fiber_Coupler', 'FR_C', COL)
sweep('Sleeve', [(-0.055, 0, Z), (0.055, 0, Z)], u_profile((HW + 0.006) / HW, 1.04, -0.004), M['yellow'], col, root)
for s in (-1, 1):
    for x in (-0.03, 0.03):
        H['box'](f'QuikLock_{s:+d}_{x:+.2f}', (0.03, 0.006, 0.022), (x, s * (HW + 0.012), Z + 0.075), M['steel'], col, parent=root, bevel=0.002)
joint('JOINT_a', (0, 0, Z), (-1, 0, 0), root, col)
joint('JOINT_b', (0, 0, Z), (1, 0, 0), root, col)
finish_piece(root, 'FR_C', FILE, stats)

# ------------------------------------------------------------------ end cap
root, col = piece('Fiber_EndCap', 'FR_X', COL)
sweep('Cap', [(0, 0, Z), (0.012, 0, Z)], rect(WF + 0.01, HF + 0.006, 0, HF / 2 - 0.001), M['yellow'], col, root)
joint('JOINT_a', (0, 0, Z), (-1, 0, 0), root, col)
finish_piece(root, 'FR_X', FILE, stats)

# ------------------------------------------------------------------ trapeze hanger
root, col = piece('Fiber_Hanger', 'FR_H', COL)
strut('Strut', WF + 0.14, (0, 0, Z - 0.0205), 'y', root, col, M)
for s in (-1, 1):
    threaded_rod(f'Rod_{s:+d}', 0, s * (HW + 0.04), Z - 0.045, CEIL_Z, root, col, M)
    H['cyl'](f'Nut_{s:+d}', 0.009, 0.01, (0, s * (HW + 0.04), Z - 0.046), M['zinc'], col, verts=6, parent=root)
    H['cyl'](f'Anchor_{s:+d}', 0.03, 0.008, (0, s * (HW + 0.04), CEIL_Z - 0.004), M['zinc'], col, verts=12, parent=root)
root['rod_top_z'] = CEIL_Z
finish_piece(root, 'FR_H', FILE, stats)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
export_all(FILE, stats)

if DO_RENDER:
    P = {r.name: r for r, t in PIECES}
    for r, t in PIECES:
        for o in [r] + list(r.children_recursive):
            o.hide_render = True
    # run over a rack row (racks along X, centreline y=0) with an elbow and tee
    for x in (-2.7, -0.9):
        dup(P['Fiber_Straight_1m8'], (x + 0.9, 0, 0))
    dup(P['Fiber_Tee'], (1.2, 0, 0))
    dup(P['Fiber_Straight_0m6'], (1.8, 0, 0))
    dup(P['Fiber_Elbow90'], (2.4, 0, 0))
    dup(P['Fiber_Straight_0m6'], (2.4, 0.6, 0), math.pi / 2)
    dup(P['Fiber_Straight_0m6'], (1.2, 0.6, 0), math.pi / 2)
    dup(P['Fiber_EndCap'], (-2.7, 0, 0), math.pi)
    for x in (-0.9, 0.9, 1.5, 2.1):
        dup(P['Fiber_Coupler'], (x, 0, 0))
    for x in (-2.4, -1.8, -1.2, -0.6, 0.0, 0.6):
        dup(P['Fiber_Waterfall'], (x, 0, 0), math.pi)
    for x in (-2.2, -0.4):
        dup(P['Fiber_Hanger'], (x, 0, 0))
    context_racks([-2.4 + i * 0.6 for i in range(6)], -(HW + 0.06) - 0.535, facing=-1)
    studio(8.0, (0, 0, 2.8))
    add_sun(1.0)
    render_views(FILE, {
        'run':   ((-4.6, -4.8, 2.3), (0.0, 0.0, 3.4), 28),
        'top':   ((0.2, -2.6, 5.6), (0.9, 0.2, 3.7), 30),
        'below': ((-1.0, -1.3, 2.6), (-1.4, 0.0, 3.6), 26),
        'teeel': ((2.9, -1.9, 4.6), (1.8, 0.3, 3.8), 30),
        'drop':  ((-0.25, -1.2, 3.55), (-0.6, -0.2, 3.75), 30),
    })
