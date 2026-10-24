"""Hot-aisle containment kit (APC/Schneider EcoAisle-style) sized to 600 mm racks.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python hall_04_containment.py [-- --norender]

Real module sizes:
  - Schneider EcoAisle: aisle widths 900 / 1200 / 1500 / 1800 mm, filler (blanking) panels 300 / 600 / 750 mm,
    emergency break-away sliding aisle-end doors, ceiling panels per rack position (Schneider launch PR /
    APC FAQ FA173296). We use a 1200 mm hot aisle and 600 mm modules.
  - Racks: APC NetShelter SX 48U 600 mm (AR3307) 2258 mm tall -> RACK_H.
  - 1U tool-less blanking panel (APC AR8136BLK): 19 in (482.6 mm) x 1U (44.45 mm).
Layout convention: the aisle runs along +X, rack REARS at y = +-0.6 (hot aisle between), floor z = 0.
Pieces:
  Contain_RoofModule_600   origin floor at the module centre (x 0.6 along aisle, spans the 1.2 m aisle)
  Contain_EndDoor          door plane x = 0, outside = -X; leaves 'DoorLeaf_L' / 'DoorLeaf_R' are separate
                           empties (props slide_axis/slide_m): open = translate leaf by slide_m along slide_axis
  Contain_Filler_600       full-height filler for an empty rack position (XZ plane at y=0, faces -Y)
  Contain_BrushStrip_600   brush seal on a rack-top edge (at RACK_H)
  Blank_1U, Brush_1U       rack-mount (front face y=0 facing -Y, origin bottom-front-centre)
"""
import bpy, bmesh, math, mathutils, os, sys
from mathutils import Vector

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\hall_lib.py', encoding='utf-8').read())

FILE = 'hall_04_containment'
BLEND = os.path.join(BASE, FILE + '.blend')
reset_scene()
M = mats()
COL = 'HALL_Containment'
stats = []
AW = 1.2                        # aisle width (rack rear to rack rear)
HA = AW / 2
RT = RACK_H
FR = M['black_pc']

# ------------------------------------------------------------------ roof module (600 mm)
root, col = piece('Contain_RoofModule_600', 'CT_R', COL)
for s in (-1, 1):   # support rails on the rack-top rear edges
    H['box'](f'Rail_{s:+d}', (0.6, 0.05, 0.08), (0, s * (HA + 0.025), RT + 0.04), FR, col, parent=root)
PZ = RT + 0.08
for s in (-1, 1):
    H['box'](f'Frame_X_{s:+d}', (0.6, 0.03, 0.03), (0, s * (HA + 0.015), PZ + 0.015), M['alu_dark'], col, parent=root)
    H['box'](f'Frame_Y_{s:+d}', (0.02, AW + 0.06, 0.03), (s * 0.29, 0, PZ + 0.015), M['alu_dark'], col, parent=root)
H['box']('Frame_Rib', (0.6, 0.02, 0.02), (0, 0, PZ + 0.01), M['alu_dark'], col, parent=root)
H['box']('Panel', (0.56, AW, 0.006), (0, 0, PZ + 0.02), M['glass'], col, parent=root)
H['box']('Light_Housing', (0.04, AW - 0.2, 0.025), (0, 0, PZ - 0.0125), M['alu_dark'], col, parent=root)
led('LED_aisle_light', (0.03, AW - 0.24, 0.004), (0, 0, PZ - 0.027), (1.0, 0.97, 0.9), root, col, 8.0)
joint('JOINT_a', (-0.3, 0, PZ), (-1, 0, 0), root, col)
joint('JOINT_b', (0.3, 0, PZ), (1, 0, 0), root, col)
finish_piece(root, 'CT_R', FILE, stats)

# ------------------------------------------------------------------ aisle end door (double sliding)
root, col = piece('Contain_EndDoor', 'CT_D', COL)
DH = 2.05                       # clear door height
for s in (-1, 1):
    H['box'](f'Post_{s:+d}', (0.05, 0.05, RT + 0.08), (-0.025, s * (HA + 0.025), (RT + 0.08) / 2), FR, col, parent=root)
H['box']('Header', (0.06, AW + 0.1, RT + 0.08 - DH), (-0.03, 0, (DH + RT + 0.08) / 2), FR, col, parent=root)
H['box']('Track', (0.06, AW * 2.0, 0.03), (-0.09, 0, DH + 0.015), M['alu_dark'], col, parent=root)
H['box']('Guide', (0.06, AW + 0.1, 0.012), (-0.08, 0, 0.006), M['alu_dark'], col, parent=root)
hz = (DH + RT + 0.08) / 2
H['box']('Sign', (0.002, 0.42, 0.08), (-0.061, 0.0, hz + 0.03), M['pipe_red'], col, parent=root)
H['text_mesh']('Text_Sign', 'HOT AISLE', FONT, 0.05, M['label'], col, root, (-0.0625, 0.0, hz + 0.03), (math.pi / 2, 0, -math.pi / 2))
led('LED_status_bar', (0.004, AW - 0.1, 0.012), (-0.062, 0, DH + 0.045), (0.1, 1.0, 0.3), root, col, 6.0)


def leaf(name, y0, y1, x, handle_y, slide):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'CUBE'; e.empty_display_size = 0.05
    col.objects.link(e); e.parent = root
    tag_obj(e, 'door_leaf', root)
    e['slide_axis'] = 'Y'; e['slide_m'] = slide
    w = y1 - y0; yc = (y0 + y1) / 2; hh = DH - 0.02; zc = 0.01 + hh / 2
    f = 0.04
    for s in (-1, 1):
        H['box'](f'{name}_Stile_{s:+d}', (0.03, f, hh), (x, yc + s * (w / 2 - f / 2), zc), M['alu_dark'], col, parent=e)
        H['box'](f'{name}_Rail_{s:+d}', (0.03, w - 2 * f, f), (x, yc, zc + s * (hh / 2 - f / 2)), M['alu_dark'], col, parent=e)
    H['box'](f'{name}_MidRail', (0.03, w - 2 * f, 0.03), (x, yc, 1.0), M['alu_dark'], col, parent=e)
    H['box'](f'{name}_Glass', (0.006, w - 2 * f, hh - 2 * f), (x, yc, zc), M['glass'], col, parent=e)
    H['box'](f'{name}_Handle', (0.02, 0.02, 0.35), (x - 0.03, handle_y, 1.05), M['steel'], col, parent=e, bevel=0.004)
    for zz in (0.9, 1.2):
        H['box'](f'{name}_HandleStandoff_{zz}', (0.03, 0.012, 0.012), (x - 0.017, handle_y, zz), M['steel'], col, parent=e)
    for k, yy in enumerate((y0 + 0.08, y1 - 0.08)):
        H['cyl'](f'{name}_Roller_{k}', 0.018, 0.02, (x, yy, DH + 0.0), M['plastic'], col, verts=12, rot=(0, math.pi / 2, 0), parent=e)
    return e


leaf('DoorLeaf_L', -HA, 0.02, -0.095, -0.03, -0.58)
leaf('DoorLeaf_R', -0.02, HA, -0.135, 0.03, 0.58)
finish_piece(root, 'CT_D', FILE, stats)

# ------------------------------------------------------------------ filler panel for an empty rack position
root, col = piece('Contain_Filler_600', 'CT_F', COL)
H['box']('Panel', (0.596, 0.02, RT), (0, 0.01, RT / 2), FR, col, parent=root, bevel=0.002)
for z in (0.5, 1.1, 1.7):
    H['box'](f'Stiffener_{z}', (0.56, 0.025, 0.03), (0, 0.032, z), M['alu_dark'], col, parent=root)
H['box']('Label', (0.12, 0.002, 0.05), (0, -0.001, 1.6), M['label'], col, parent=root)
H['text_mesh']('Text_Label', 'FILLER 600', FONT, 0.018, M['label_blk'], col, root, (0, -0.0025, 1.6), (math.pi / 2, 0, 0))
finish_piece(root, 'CT_F', FILE, stats)

# ------------------------------------------------------------------ brush strip seal (on rack top edge)
root, col = piece('Contain_BrushStrip_600', 'CT_B', COL)
H['box']('Extrusion', (0.6, 0.03, 0.02), (0, 0, RT + 0.01), M['alu_satin'], col, parent=root)


def bristles():
    for i in range(60):
        yield (-0.295 + i * 0.01, 0, RT + 0.04), (0.009, 0.004, 0.04)
H['slat_array']('Bristles', bristles, M['bristle'], col, root)
finish_piece(root, 'CT_B', FILE, stats)

# ------------------------------------------------------------------ 1U blanking + 1U brush panel (rack-mount)
U = 0.04445
root, col = piece('Blank_1U', 'CT_1U', COL)
H['box']('Face', (0.4826, 0.003, U - 0.0005), (0, 0.0015, U / 2), FR, col, parent=root, bevel=0.0008)
H['box']('Return', (0.44, 0.012, U - 0.008), (0, 0.009, U / 2), FR, col, parent=root)
for s in (-1, 1):
    H['box'](f'SnapTab_{s:+d}', (0.012, 0.02, 0.02), (s * 0.224, 0.013, U / 2), M['plastic'], col, parent=root)
finish_piece(root, 'CT_1U', FILE, stats)

root, col = piece('Brush_1U', 'CT_1B', COL)
for zc, h in ((0.006, 0.012), (U - 0.006, 0.012)):
    H['box'](f'Face_{zc:.3f}', (0.4826, 0.003, h), (0, 0.0015, zc), FR, col, parent=root)
for s in (-1, 1):
    H['box'](f'Ear_{s:+d}', (0.03, 0.003, U - 0.024), (s * (0.4826 / 2 - 0.015), 0.0015, U / 2), FR, col, parent=root)


def bristles1u():
    for i in range(42):
        for s in (-1, 1):
            yield (-0.21 + i * 0.01025, 0.004, U / 2 + s * 0.005), (0.009, 0.004, 0.009)
H['slat_array']('Bristles', bristles1u, M['bristle'], col, root)
for s in (-1, 1):
    H['cyl'](f'Screw_{s:+d}', 0.004, 0.003, (s * 0.2325, -0.0005, U / 2), M['steel'], col, verts=8, rot=(math.pi / 2, 0, 0), parent=root)
finish_piece(root, 'CT_1B', FILE, stats)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
export_all(FILE, stats)

if DO_RENDER:
    PP = {r.name: r for r, t in PIECES}
    for r, t in PIECES:
        for o in [r] + list(r.children_recursive):
            o.hide_render = True
    N = 6
    xs = [0.3 + i * 0.6 for i in range(N)]
    # two rows: fronts outward, rears at +-0.6
    col_ctx = H['coll']('RenderContext')
    for i, x in enumerate(xs):
        for s in (-1, 1):
            if s == 1 and i == 3:
                dup(PP['Contain_Filler_600'], (x, HA, 0), math.pi)
                continue
            H['box'](f'CTX_Rack_{i}_{s}', (0.596, 1.07, RT), (x, s * (HA + 0.535), RT / 2), M['cab_black'], col_ctx)
        dup(PP['Contain_RoofModule_600'], (x, 0, 0))
    d = dup(PP['Contain_EndDoor'], (0, 0, 0))
    # open the right leaf in the render to show the sliding motion
    for c in d.children:
        if c.name.startswith('DoorLeaf_R'):
            c.location.y += 0.45
    studio(7.0, (1.5, 0, 1.2))
    add_sun(1.0)
    render_views(FILE, {
        'door':   ((-3.6, -2.4, 1.7), (0.6, 0.0, 1.2), 30),
        'inside': ((3.2, 0.3, 1.5), (0.0, 0.0, 1.5), 22),
        'roof':   ((-1.6, -3.4, 4.2), (1.6, 0.0, 2.2), 30),
    })
    for o in bpy.data.collections['RenderContext'].objects:
        o.hide_render = True
    for n, x in (('Blank_1U', -0.3), ('Brush_1U', 0.3)):
        dd = dup(PP[n], (x, 0, 1.0))
    studio(1.0, (0, 0, 1.0))
    render_views(FILE, {'1u': ((0.0, -0.9, 1.25), (0.0, 0.0, 1.02), 40)})
