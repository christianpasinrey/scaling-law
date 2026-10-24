"""Rack accessories: blanking panels 1U/2U and horizontal cable managers 1U (D-ring) / 2U (finger duct + cover).

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python rack_accessories.py

Conventions: 19" EIA-310 (ears 482.6 mm, 1U = 44.45 mm). Each item has its own root empty whose origin is
bottom-front-centre on the rail mounting plane (y = 0 = front face of the front rail, i.e. the rack SLOT_Unn
pose). Items mount from the front; anything in front of the rail is at y < 0.
In the .blend/.glb the items are stacked as if mounted (node translation = n*U); mesh data is relative to each
item root, so the game can instance a root node at any SLOT_Unn.
References: APC AR8136BLK (1U toolless blanking panel), APC AR8425A-style 1U D-ring manager,
2U finger duct (Panduit NCMHAF2-style) with hinged cover.
"""
import bpy, bmesh, math, mathutils, os, sys

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\rack_kit_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']; RK = bpy.app.driver_namespace['RK']
V = mathutils.Vector
U = RK['U']

ROOT = 'rack_accessories'
BLEND = os.path.join(RK['BASE'], 'rack_accessories.blend')
root, col = H['new_card_scene'](ROOT)
mat = H['mat']
M = H['base_materials']()
PLAS = mat('RK_BlankPlastic', (0.012, 0.012, 0.013), 0.0, 0.55, spec=0.3)
STEEL_BK = mat('RK_PowderBlack', (0.012, 0.012, 0.013), 0.35, 0.5, spec=0.35)
SCREW = mat('RK_Screw', (0.55, 0.55, 0.57), 1.0, 0.3)
EAR_W = 0.4826
HOLE_X = 0.23255


def sub_root(name, z):
    e = RK['empty'](name, (0, 0, z), root, col, kind='PLAIN_AXES', size=0.05)
    return e


def screws(bm, n_u, mi, y=-0.0025):
    """Cage-nut screws through the ears, one per U at the middle hole."""
    for k in range(n_u):
        z = k * U + 0.0222
        for sx in (-1, 1):
            RK['add_cyl'](bm, (sx * HOLE_X, y, z), 0.0042, 0.003, 'Y', 12, mi)


def blank(name, n_u, z):
    r = sub_root(name, z)
    h = n_u * U - 0.0008
    bm = bmesh.new()
    # face plate (plastic, 2.5 mm) with chamfered look via a slightly smaller raised centre
    RK['add_box'](bm, (0, -0.00125, h / 2 + 0.0004), (EAR_W, 0.0025, h), 0)
    RK['add_box'](bm, (0, -0.0030, h / 2 + 0.0004), (0.420, 0.0012, h - 0.008), 0)
    # horizontal stiffening grooves (dark inset strips)
    for k in range(n_u):
        zc = k * U + U / 2
        RK['add_box'](bm, (0, -0.0037, zc), (0.400, 0.0004, 0.0016), 1)
    # rear return flanges (top/bottom) and toolless clips behind the rail
    RK['add_box'](bm, (0, 0.006, 0.0012), (0.440, 0.012, 0.0016), 0)
    RK['add_box'](bm, (0, 0.006, h - 0.0004), (0.440, 0.012, 0.0016), 0)
    for k in range(n_u):
        for sx in (-1, 1):
            RK['add_box'](bm, (sx * HOLE_X, 0.004, k * U + 0.0222), (0.009, 0.008, 0.009), 0)
    o = RK['mesh_obj'](name + '_body', bm, [PLAS, M['port']], col, r)
    r['rack_units'] = n_u; r['mount'] = '19in EIA-310'
    return r


def cablemgr_dring(name, z):
    """1U steel panel with 5 D-rings (open toward the front)."""
    r = sub_root(name, z)
    h = U - 0.0008
    bm = bmesh.new()
    RK['add_box'](bm, (0, -0.001, h / 2 + 0.0004), (EAR_W, 0.002, h), 0)
    screws(bm, 1, 1)
    xs = [-0.18, -0.09, 0.0, 0.09, 0.18]
    for x in xs:
        # D-ring: two arms out to y=-0.075 and a front bar, 30 mm tall opening, steel rod 6x4 mm
        for zz in (0.006, h - 0.006):
            RK['add_box'](bm, (x, -0.040, zz + 0.0004), (0.006, 0.076, 0.004), 0)
        RK['add_box'](bm, (x, -0.0775, h / 2 + 0.0004), (0.006, 0.005, h - 0.008), 0)
        RK['add_box'](bm, (x, -0.0045, h / 2 + 0.0004), (0.020, 0.005, 0.030), 0)   # base plate
    RK['mesh_obj'](name + '_body', bm, [STEEL_BK, SCREW], col, r)
    r['rack_units'] = 1; r['mount'] = '19in EIA-310'; r['depth_front_m'] = 0.08
    return r


def cablemgr_finger(name, z):
    """2U plastic finger duct (100 mm deep in front of the rail) with a hinged snap cover (separate object)."""
    r = sub_root(name, z)
    nU = 2; h = nU * U - 0.0008; D = 0.100
    bm = bmesh.new()
    RK['add_box'](bm, (0, -0.0012, h / 2 + 0.0004), (EAR_W, 0.0024, h), 0)        # back plate / ears
    screws(bm, nU, 1)
    RK['add_box'](bm, (0, -D / 2, 0.0020), (0.440, D, 0.0024), 0)                  # bottom tray
    RK['add_box'](bm, (0, -D / 2, h - 0.0012), (0.440, D, 0.0024), 0)              # top tray
    # fingers along the top and bottom edge (rectangular fingers with slots, 12 per side)
    n = 12; pitch = 0.432 / n
    for i in range(n):
        x = -0.216 + pitch * (i + 0.5)
        for zz in (0.0025 + 0.012, h - 0.0025 - 0.012):
            RK['add_box'](bm, (x, -D + 0.012, zz + 0.0004), (pitch - 0.0075, 0.024, 0.024), 0)
    # side walls
    for sx in (-1, 1):
        RK['add_box'](bm, (sx * 0.219, -D / 2, h / 2 + 0.0004), (0.0024, D, h), 0)
    RK['mesh_obj'](name + '_body', bm, [PLAS, SCREW], col, r)
    # cover: hinged on the bottom edge (origin at hinge), opens by rotating about X (open_angle_deg)
    bm = bmesh.new()
    RK['add_box'](bm, (0, -0.0015, h / 2), (0.444, 0.003, h - 0.004), 0)
    RK['add_box'](bm, (0, -0.0035, h / 2), (0.30, 0.0012, 0.016), 1)               # label recess
    cv = RK['mesh_obj'](name + '_cover', bm, [PLAS, M['black_mt']], col, r)
    cv.location = (0, -D - 0.0005, 0.0004)
    cv['hinge_axis'] = 'X'; cv['open_angle_deg'] = 95.0
    r['rack_units'] = 2; r['mount'] = '19in EIA-310'; r['depth_front_m'] = D + 0.004
    return r


items = [blank('blank_1u', 1, 0.0), cablemgr_dring('cablemgr_1u', U), blank('blank_2u', 2, 2 * U),
         cablemgr_finger('cablemgr_2u', 4 * U)]

tris = RK['finish'](ROOT, BLEND, 'rack_accessories.glb')
for it in items:
    print('ITEM', it.name, 'tris', RK['tris_of'](list(it.children_recursive)))

# preview: a pair of front rails for context (not exported: created after the export)
rail_m = mat('RK_RailPreview', (0.02, 0.02, 0.022), 0.6, 0.45)
for sx in (-1, 1):
    H['box']('preview_rail', (0.018, 0.002, 7 * U), (sx * 0.2325, 0.001, 3.5 * U), rail_m, col)
bpy.data.objects['cablemgr_2u_cover'].rotation_euler = (math.radians(95), 0, 0)   # preview: cover open
RK['render']('rack_accessories', {
    '34': ((-0.55, -0.75, 0.45), (0, -0.03, 0.14), 45),
    'front': ((0, -1.1, 0.14), (0, 0, 0.14), 40),
    'side': ((0.7, -0.35, 0.3), (0, -0.05, 0.14), 45),
}, 0.6, (0, 0, 0.15), floor_z=-0.001)
