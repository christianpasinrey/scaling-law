"""Cable kit: reusable flow-UV cable segments + connector heads for routed cables in the game.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python cables_kit.py

Every segment is a mesh swept along a path with UV u = metres along the path (continuous from 0 at
the start), v = 0..1 around; custom props flow_u_start / flow_u_end / flow_radius / cable_type /
color_hex / min_bend_radius. All paths START at the object origin heading -Y (the direction a cable
leaves a port that faces -Y), so a connector head and a segment can be chained.

Connector heads: mating face at the origin, body extends toward -Y, empty <name>_EXIT at the cable
exit (cable continues along -Y from there).
"""
import bpy, bmesh, math, mathutils, os, sys

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\rack_kit_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']; RK = bpy.app.driver_namespace['RK']
V = mathutils.Vector

ROOT = 'cables_kit'
BLEND = os.path.join(RK['BASE'], 'cables_kit.blend')
root, col = H['new_card_scene'](ROOT)
mat = H['mat']


def srgb(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# type: (radius m, hex colour, min bend radius m, radial segments, description)
TYPES = {
    'smf_yellow': (0.0015, '#F2C500', 0.030, 8, 'OS2 single-mode fibre patch (3.0 mm round jacket), yellow'),
    'mmf_aqua':   (0.0015, '#16B8C8', 0.030, 8, 'OM3/OM4 multimode fibre patch (3.0 mm), aqua'),
    'dac_black':  (0.0030, '#151515', 0.045, 10, 'QSFP56/OSFP passive copper DAC (6.0 mm, 26-30 AWG twinax)'),
    'cat6_blue':  (0.0030, '#1F5FBF', 0.030, 8, 'Cat6 management patch (6.0 mm), blue'),
    'c13_power':  (0.0040, '#0E0E0E', 0.040, 12, 'C14-C13 power cord, 3x1.5 mm2 / 14 AWG SJT (8.0 mm)'),
    'c19_power':  (0.0048, '#0E0E0E', 0.050, 12, 'C20-C19 power cord, 3x2.5 mm2 / 12 AWG SJT (9.6 mm)'),
}
MAT = {}
for t, (r, hx, mb, sg, _) in TYPES.items():
    MAT[t] = mat('RK_Cable_' + t, srgb(hx), 0.0, 0.42 if 'power' in t or 'dac' in t else 0.35, spec=0.4)

SP = 0.0  # running x layout
layout_x = {}


def segments_for(t):
    r, hx, mb, sg, desc = TYPES[t]
    props = dict(cable_type=t, color_hex=hx, min_bend_radius=mb, description=desc, segs=sg)
    out = []
    # straight 1 m
    out.append(('straight_1m', [(0, 0, 0), (0, -1.0, 0)]))
    # 90 degree bend at min radius, 0.15 m legs, turning down (-Z)
    out.append(('bend90', RK['fillet_path']([(0, 0, 0), (0, -0.15, 0), (0, -0.15, -0.15)], mb, 10)))
    # 90 degree sideways bend (+X)
    out.append(('bend90_side', RK['fillet_path']([(0, 0, 0), (0, -0.15, 0), (0.15, -0.15, 0)], mb, 10)))
    # S-bend: 0.3 m run, 0.1 m lateral offset (cubic bezier)
    out.append(('sbend', RK['bezier_pts']((0, 0, 0), (0, -0.15, 0), (0.1, -0.15, 0), (0.1, -0.3, 0), 20)))
    # U-turn at 2x min bend radius (service loop)
    R = mb * 2
    out.append(('uturn', RK['fillet_path']([(0, 0, 0), (0, -0.1, 0), (0, -0.1 - R, 0), (2 * R, -0.1 - R, 0), (2 * R, -0.1, 0), (2 * R, 0, 0)], R, 10)))
    objs = []
    for nm, pts in out:
        o, L = RK['tube'](f'cable_{t}_{nm}', pts, r, MAT[t], col, root, segs=sg, props=props)
        objs.append(o)
    return objs


rows = []
for t in TYPES:
    rows.append(segments_for(t))

# ---------------------------------------------------------------- connector heads
M = H['base_materials']()
SHELL = mat('RK_ConnShell', (0.55, 0.56, 0.58), 1.0, 0.3)
LC_BLUE = mat('RK_LC_Blue', srgb('#1E5BC6'), 0.0, 0.4)
LC_AQUA = mat('RK_LC_Aqua', srgb('#16B8C8'), 0.0, 0.4)
WHITE = mat('RK_ConnWhite', (0.8, 0.8, 0.78), 0.0, 0.45)
BLACK = mat('RK_ConnBlack', (0.01, 0.01, 0.011), 0.0, 0.5, spec=0.3)
TAB_BLUE = mat('RK_PullTabBlue', srgb('#2A63B8'), 0.0, 0.55)
CLEAR = mat('RK_RJ45Clear', (0.7, 0.75, 0.78), 0.0, 0.15, alpha=0.55)
COPPER = mat('RK_Pin', (0.9, 0.7, 0.4), 1.0, 0.3)


def head(name, parts, exit_y, cable_type):
    """parts: list of (centre_mm, size_mm, mat) boxes or ('cyl', centre_mm, r_mm, len_mm, mat, axis)."""
    bm = bmesh.new(); mats = []
    for p in parts:
        if p[0] == 'cyl':
            _, c, r, ln, m, ax = p
            if m not in mats:
                mats.append(m)
            RK['add_cyl'](bm, V(c) * 0.001, r * 0.001, ln * 0.001, ax, 16, mats.index(m))
        elif p[0] == 'cone':
            _, c, r0, r1, ln, m = p   # along Y
            if m not in mats:
                mats.append(m)
            res = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=r0 * 0.001, radius2=r1 * 0.001, depth=ln * 0.001,
                                        matrix=mathutils.Matrix.Translation(V(c) * 0.001) @ mathutils.Matrix.Rotation(math.pi / 2, 4, 'X'))
            for f in {f for v in res['verts'] for f in v.link_faces}:
                f.material_index = mats.index(m)
        else:
            c, s, m = p
            if m not in mats:
                mats.append(m)
            RK['add_box'](bm, V(c) * 0.001, V(s) * 0.001, mats.index(m))
    o = RK['mesh_obj'](name, bm, mats, col, root)
    o['cable_type'] = cable_type
    o['exit_offset_m'] = exit_y * 0.001
    RK['empty'](name + '_EXIT', (0, exit_y * 0.001, 0), o, col, kind='SINGLE_ARROW', size=0.015, rot=(math.pi / 2, 0, 0))
    return o


heads = []
# LC duplex (pitch 6.25 mm), body from mating face to boot ~ 32 mm, boot to 52 mm
for nm, hm in (('conn_lc_duplex_smf', LC_BLUE), ('conn_lc_duplex_mmf', LC_AQUA)):
    parts = []
    for x in (-3.125, 3.125):
        parts += [((x, -7.5, 0), (4.5, 15, 4.5), hm), ('cyl', (x, 1.0, 0), 0.62, 2.0, WHITE, 'Y'),
                  ((x, -6, 3.0), (2.4, 9, 1.5), hm)]
    parts += [((0, -18, 0), (11.5, 8, 6.0), hm), ('cone', (0, -33, 0), 3.4, 1.8, 22, WHITE)]
    heads.append(head(nm, parts, -44, 'smf_yellow' if 'smf' in nm else 'mmf_aqua'))
# QSFP56 plug: shell 18.35 x 8.5, 42 mm visible outside the cage, boot + pull tab loop
parts = [((0, -21, 0), (18.35, 42, 8.5), SHELL), ((0, -46, 0), (14, 10, 7.5), BLACK), ('cone', (0, -58, 0), 4.6, 3.2, 16, BLACK),
         ((0, -32, 5.2), (8, 52, 0.9), TAB_BLUE), ((0, -60, 5.2), (14, 6, 0.9), TAB_BLUE)]
heads.append(head('conn_qsfp56_plug', parts, -66, 'dac_black'))
# OSFP plug: 22.58 x 13 with finned top, 45 mm outside the cage
parts = [((0, -22.5, 0), (22.58, 45, 9.5), SHELL)]
for i in range(9):
    parts.append(((-10 + i * 2.5, -22.5, 6.3), (1.0, 44, 3.2), SHELL))
parts += [((0, -50, 0), (17, 10, 9), BLACK), ('cone', (0, -62, 0), 5.0, 3.4, 16, BLACK), ((0, -40, -5.5), (9, 60, 1.0), BLACK)]
heads.append(head('conn_osfp_plug', parts, -70, 'dac_black'))
# RJ45 plug
parts = [((0, -10, 0), (11.7, 20, 8.0), CLEAR), ((0, -4, 4.6), (6, 10, 1.4), CLEAR), ((0, -1.5, -2.5), (8.5, 3, 2.5), COPPER),
         ('cone', (0, -27, 0), 4.6, 3.2, 16, MAT['cat6_blue'])]
heads.append(head('conn_rj45', parts, -35, 'cat6_blue'))
# IEC power heads (body profile approximated by boxes + strain relief)
for nm, w, h, ln, t in (('conn_c14_plug', 24, 16, 34, 'c13_power'), ('conn_c13_connector', 26, 18, 38, 'c13_power'),
                        ('conn_c20_plug', 30, 19, 38, 'c19_power'), ('conn_c19_connector', 32, 21, 42, 'c19_power')):
    parts = [((0, -ln / 2, 0), (w, ln, h), BLACK), ((0, -ln - 6, 0), (w * 0.6, 12, h * 0.6), BLACK),
             ('cone', (0, -ln - 20, 0), h * 0.32, TYPES[t][0] * 1000 * 1.05, 18, BLACK)]
    if 'plug' in nm:   # male: protruding pins
        pins = [(-7, 2), (7, 2), (0, -4)] if 'c14' in nm else [(-7.5, 0), (7.5, 0), (0, -6)]
        for px, pz in pins:
            sz = (1.6, 9, 4.0) if 'c14' in nm else (4.0, 9, 1.6)
            if pz < -3:
                sz = (1.6, 9, 4.0) if 'c20' not in nm else (1.6, 9, 4.0)
            parts.append(((px, 4.5, pz), sz, M['steel']))
    else:
        parts.append(((0, 0.3, 0), (w * 0.8, 0.6, h * 0.6), M['port']))
    heads.append(head(nm, parts, -(ln + 30), t))

# ---------------------------------------------------------------- layout for preview (geometry stays origin-relative)
# rows = cable types (top to bottom), columns = straight_1m, bend90, bend90_side, sbend, uturn; paths are rotated
# so they run toward +X in the preview (canonical direction in the mesh data is -Y from the origin)
for i, row in enumerate(rows):
    z = 1.1 - i * 0.17
    xs = [-1.05, 0.1, 0.45, 0.8, 1.25]
    for o, x in zip(row, xs):
        o.location = (x, 0.0, z)
        o.rotation_euler = (0, 0, math.pi / 2)
for j, h_ in enumerate(heads):
    h_.location = (-0.45 + j * 0.1, -0.05, 0.02)

tris = RK['finish'](ROOT, BLEND, 'cables_kit.glb')
for t, (r, hx, mb, sg, d) in TYPES.items():
    print(f'CABLE {t} r={r} colour={hx} minbend={mb} segs={sg}')
RK['render']('cables_kit', {
    'overview': ((0.1, -3.1, 0.75), (0.1, 0.0, 0.6), 40),
    'heads': ((0.05, -1.25, 0.42), (0.0, -0.05, 0.02), 35),
    'bends': ((0.55, -0.75, 1.0), (0.75, 0.0, 0.75), 40),
}, 1.5, (0, 0, 0.5), floor_z=0.0)
