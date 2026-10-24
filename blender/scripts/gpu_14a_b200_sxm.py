"""NVIDIA B200 SXM module (HGX B200, 2024-2025) + air-cooled HGX heatsink.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python gpu_14a_b200_sxm.py

Conventions: metres, module lies flat (PCB plane XY, bottom at z=0, parts toward +Z),
long axis = X (airflow direction on the HGX baseboard), origin = module centre.
Footprint (measured from STH HGX B200 photos, scaled by the ~72x77 mm package lid):
  module PCB 205 x 103 mm, bolster plate top z=6.2 mm, lid top z=6.8 mm,
  heatsink 203 x 101 x ~122 mm (top z=128 mm). Mezzanine connectors to z=-4 mm.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector

BASE = r'C:\laragon\www\scaling-law\blender'
exec(open(BASE + r'\lib\hw.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']
exec(open(BASE + r'\scripts\blackwell_common.py', encoding='utf-8').read())

ROOT = 'B200_SXM'
root, col = H['new_card_scene'](ROOT)
M = H['base_materials'](); M.update(extra_materials())
box, cyl, sa = H['box'], H['cyl'], H['slat_array']

MW, MH = 0.205, 0.103          # module PCB
T = 0.0020                      # PCB thickness
PZ0, PZ1 = 0.0022, 0.0062       # bolster plate z range
LW, LH = 0.072, 0.076           # lid / package substrate
LID_TOP = 0.0068


def join(name, objs):
    for o in objs:
        H['apply_all'](o)
    with bpy.context.temp_override(active_object=objs[0], object=objs[0], selected_objects=objs, selected_editable_objects=objs):
        bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


# ---------------------------------------------------------------- module PCB + underside
pcb = box('Module_PCB', (MW, MH, T), (0, 0, T / 2), M['pcb_mod'], col, bevel=0.0004, parent=root)
for i, y in enumerate((0.030, -0.030)):
    box(f'Mezz_Connector_{i}', (0.072, 0.011, 0.0040), (0.0, y, -0.0020), M['plastic'], col, bevel=0.0003, parent=root)
    sa(f'Mezz_Pins_{i}', lambda y=y: (((x * 0.0012, y + s * 0.0062, -0.0010), (0.0005, 0.0012, 0.0018))
                                     for x in range(-28, 29) for s in (-1, 1)), M['gold'], col, root)
# a few guide pins / backside caps
for i, (x, y) in enumerate(((-0.090, 0.040), (0.090, -0.040))):
    cyl(f'Guide_Pin_{i}', 0.0016, 0.006, (x, y, -0.0030), M['steel'], col, verts=16, parent=root)
sa('Backside_Caps', lambda: (((x, y, -0.0004), (0.0016, 0.0008, 0.0008))
                             for x in [i * 0.0034 for i in range(-9, 10)] for y in (-0.012, -0.0095, 0.0095, 0.012)),
   M['smd'], col, root)

# ---------------------------------------------------------------- package (substrate, interposer, 2 dies, 8 HBM3e)
box('Package_Substrate', (LW - 0.001, LH - 0.001, 0.0016), (0, 0, T + 0.0008), M['substrate'], col, bevel=0.0003, parent=root)
box('Interposer_Mold', (0.056, 0.059, 0.0008), (0, 0, T + 0.0016 + 0.0004), M['mold'], col, parent=root)
ZD = T + 0.0024
for i, x in enumerate((-0.0133, 0.0133)):
    box(f'Die_{i}', (0.0255, 0.0330, 0.0007), (x, 0, ZD + 0.00035), M['die'], col, parent=root)
k = 0
for x in (-0.0193, -0.0073, 0.0073, 0.0193):
    for y in (-0.0226, 0.0226):
        box(f'HBM3e_{k}', (0.0108, 0.0110, 0.0007), (x, y, ZD + 0.00035), M['hbm'], col, parent=root); k += 1
# die-to-die seam (NV-HBI) highlight + land-side caps ring on the substrate
box('NV_HBI_Seam', (0.0007, 0.0330, 0.00072), (0, 0, ZD + 0.00036), M['mold'], col, parent=root)


def sub_caps():
    rnd = random.Random(7)
    for side in range(4):
        for i in range(22):
            t = -0.030 + i * 0.00285
            if side < 2:
                x, y = t, (0.0322 if side == 0 else -0.0322)
                s = (0.0012, 0.0006, 0.0005)
            else:
                x, y = (0.0306 if side == 2 else -0.0306), t * 1.03
                s = (0.0006, 0.0012, 0.0005)
            if rnd.random() < 0.85:
                yield (x, y, T + 0.0016 + 0.00025), s


sa('Substrate_Caps', sub_caps, M['smd'], col, root)

# ---------------------------------------------------------------- IHS lid (separate so the dies can be shown)
lid_top = box('IHS_Lid', (LW, LH, 0.0014), (0, 0, LID_TOP - 0.0007), M['nickel'], col, bevel=0.0006, parent=root)
lid_skirt = frame_rect('IHS_Lid_Skirt', 0, 0, LW, LH, 0.0025, T + 0.0016, LID_TOP - 0.0014 - (T + 0.0016), M['nickel'], col, root)
lid = join('IHS_Lid', [lid_top, lid_skirt])
lid.parent = root
_lid_first = set(o.name for o in bpy.data.objects)
t = H['text_mesh']('Lid_Text_NVIDIA', 'NVIDIA', FONT_LOGO, 0.0105, M['black_mt'], col, root,
                   (0.0045, -0.001, LID_TOP + 0.00002), (0, 0, 0), extrude=0.00002, scale=(1.18, 1, 1))
# NVIDIA eye badge (square + ring) left of the word mark, printed
box('Lid_Logo_Square', (0.0125, 0.0105, 0.00004), (-0.0250, -0.0010, LID_TOP + 0.00002), M['black_mt'], col, parent=root)
cyl('Lid_Logo_Eye', 0.0032, 0.00006, (-0.0245, -0.0010, LID_TOP + 0.00003), M['nickel'], col, verts=24, parent=root)
cyl('Lid_Logo_Pupil', 0.0017, 0.00008, (-0.0245, -0.0010, LID_TOP + 0.00004), M['black_mt'], col, verts=20, parent=root)
H['text_mesh']('Lid_Text_Lot', 'TW 2418B0', FONT, 0.0028, M['black_mt'], col, root,
               (-0.010, -0.026, LID_TOP + 0.00002), (0, 0, 0), extrude=0.00002)

bpy.context.view_layer.update()
for o in list(bpy.data.objects):
    if o.name not in _lid_first and o.parent in (lid, root) and o.name.startswith('Lid_'):
        mw = o.matrix_world.copy()
        o.parent = lid; o.matrix_parent_inverse = lid.matrix_world.inverted(); o.matrix_world = mw

# ---------------------------------------------------------------- black bolster / load plate with windows
plate = box('Bolster_Plate', (MW - 0.002, MH - 0.002, PZ1 - PZ0), (0, 0, (PZ0 + PZ1) / 2), M['anod'], col, bevel=0.0005, parent=root)
H['apply_all'](plate)
PADS = [(-0.0860, -0.0285), (0.0874, -0.0255)]
cutters = [box('c_lid', (LW + 0.0015, LH + 0.0015, 0.02), (0, 0, PZ1), M['anod'], col)]
for i, (x, y) in enumerate(PADS):
    cutters.append(box(f'c_pad{i}', (0.0300, 0.0240, 0.02), (x, y, PZ1), M['anod'], col))
cutters.append(box('c_strip', (0.0110, 0.0710, 0.0016), (0.0447, 0, PZ1), M['anod'], col))
cutter = join('PlateCutter', cutters)
H['cut'](plate, cutter)
# pad fields visible through the windows (power / test pad arrays)
for i, (x0, y0) in enumerate(PADS):
    box(f'PadWindow_Floor_{i}', (0.030, 0.024, 0.0002), (x0, y0, T + 0.0001), M['pcb_mod'], col, parent=root)
    sa(f'PadArray_{i}', lambda x0=x0, y0=y0: (((x0 + (c - 4.5) * 0.0026, y0 + (r - 3.5) * 0.0026, T + 0.00025), (0.0017, 0.0017, 0.0002))
                                              for c in range(10) for r in range(8)), M['gold'], col, root)
# hex standoffs with green torque paint + silver screws
for i, (x, y) in enumerate(((-0.0665, 0.0460), (0.0655, 0.0460), (-0.0665, -0.0465), (0.0660, -0.0465))):
    cyl(f'Standoff_Torque_{i}', 0.0034, 0.0007, (x, y, PZ1 + 0.00035), M['green_ring'], col, verts=24, parent=root)
    cyl(f'Standoff_Hex_{i}', 0.0026, 0.0035, (x, y, PZ1 + 0.0024), M['black_st'], col, verts=6, parent=root)
    cyl(f'Standoff_Bore_{i}', 0.0012, 0.0002, (x, y, PZ1 + 0.0042), M['port'], col, verts=16, parent=root)
    sx = x + (0.0095 if x < 0 else -0.0095)
    cyl(f'Plate_Screw_{i}', 0.0022, 0.0012, (sx, y, PZ1 + 0.0006), M['steel'], col, verts=20, bevel=0.0003, parent=root)
    cyl(f'Plate_Screw_Hex_{i}', 0.0009, 0.0002, (sx, y, PZ1 + 0.00125), M['port'], col, verts=6, parent=root)
# printed white corner marks (lid window, pad windows, plate corners)
marks = list(corner_marks(0, 0, LW + 0.008, LH + 0.008, PZ1 + 0.00003))
for (x, y) in PADS:
    marks += list(corner_marks(x, y, 0.036, 0.030, PZ1 + 0.00003, arm=0.003))
marks += list(corner_marks(0, 0, MW - 0.012, MH - 0.012, PZ1 + 0.00003, arm=0.003))
sa('Plate_Corner_Marks', lambda: iter(marks), M['print'], col, root)
H['text_mesh']('Plate_Text_GPU', 'B200', FONT, 0.0040, M['print'], col, root,
               (-0.0700, 0.0300, PZ1 + 0.00002), (0, 0, 0), extrude=0.00002)

# PCB edge components peeking out around the plate (caps along the long edges)
sa('Edge_Caps', lambda: (((x * 0.0042, s * (MH / 2 - 0.0005), T + 0.0003), (0.0020, 0.0006, 0.0006))
                         for x in range(-23, 24) for s in (-1, 1)), M['smd'], col, root)

# ---------------------------------------------------------------- air-cooled HGX heatsink (child "Heatsink")
hs = bpy.data.objects.new('Heatsink', None); hs.empty_display_type = 'CUBE'; hs.empty_display_size = 0.01
col.objects.link(hs); hs.parent = root
HW_, HH_ = 0.203, 0.101
Z0 = LID_TOP                   # base sits on the lid
ZB = Z0 + 0.0050               # top of vapour-chamber base
ZT = 0.1240                    # fin top
ZR = 0.1280                    # shroud rim top
box('HS_Base_VaporChamber', (HW_ - 0.004, HH_ - 0.006, ZB - Z0), (0, 0, (Z0 + ZB) / 2), M['copper'], col, bevel=0.0006, parent=hs)
box('HS_Base_Pedestal', (LW - 0.004, LH - 0.004, 0.0004), (0, 0, Z0 + 0.0002), M['copper_dk'], col, parent=hs)
NF = 46
sa('HS_Fins', lambda: (((0, -0.0465 + i * (0.093 / (NF - 1)), (ZB + 0.001 + ZT) / 2), (HW_ - 0.006, 0.0003, ZT - ZB - 0.001))
                       for i in range(NF)), M['alu'], col, hs)
sa('HS_Fin_Flanges', lambda: (((0, -0.0465 + i * (0.093 / (NF - 1)), ZT - 0.0002), (HW_ - 0.006, 0.093 / (NF - 1) * 0.82, 0.0004))
                              for i in range(NF)), M['alu'], col, hs)
for j, x in enumerate((-0.060, 0.0, 0.060)):
    for k2, y in enumerate((-0.0300, 0.0300)):
        cyl(f'HS_HeatPipe_{j}{k2}', 0.0040, ZT + 0.0008 - ZB, (x, y, (ZB + ZT + 0.0008) / 2), M['copper'], col, verts=20, parent=hs)
        cyl(f'HS_HeatPipe_Cap_{j}{k2}', 0.0043, 0.0012, (x, y, ZT + 0.0012), M['copper_dk'], col, verts=20, bevel=0.0005, parent=hs)
for i, s in enumerate((-1, 1)):
    box(f'HS_Shroud_Side_{i}', (HW_, 0.0012, ZR - Z0), (0, s * (HH_ / 2 - 0.0006), (Z0 + ZR) / 2), M['anod'], col, bevel=0.0003, parent=hs)
# rim: wide black frame with a large opening (opening shows fins and heat-pipe ends)
H['ring']('HS_Shroud_Rim', [(-HW_ / 2, -HH_ / 2), (HW_ / 2, -HH_ / 2), (HW_ / 2, HH_ / 2), (-HW_ / 2, HH_ / 2)],
          [(-0.0815, -0.0395), (0.0815, -0.0395), (0.0815, 0.0395), (-0.0815, 0.0395)],
          'xy', ZT, ZR - ZT, M['anod'], col, hs)
# front/back end brackets (low, leave fins visible)
for i, s in enumerate((-1, 1)):
    box(f'HS_End_Bracket_{i}', (0.0016, HH_, 0.012), (s * (HW_ / 2 - 0.0008), 0, Z0 + 0.006), M['anod'], col, parent=hs)
    box(f'HS_End_TopBar_{i}', (0.010, HH_, 0.004), (s * (HW_ / 2 - 0.005), 0, ZR - 0.002), M['anod'], col, parent=hs)
# NVIDIA name plate across the top
box('HS_Crossbar', (0.172, 0.012, 0.0030), (0, 0, ZR - 0.0015), M['anod'], col, parent=hs)
box('HS_NamePlate', (0.150, 0.0165, 0.0014), (0, 0, ZR + 0.0007), M['gold'], col, bevel=0.0004, parent=hs)
H['text_mesh']('HS_Text_NVIDIA', 'NVIDIA', FONT_LOGO, 0.0090, M['black_mt'], col, hs,
               (0.004, -0.0003, ZR + 0.00142), (0, 0, 0), extrude=0.00002, scale=(1.18, 1, 1))
box('HS_Logo_Badge', (0.0105, 0.0090, 0.00004), (-0.0245, -0.0003, ZR + 0.00142), M['black_mt'], col, parent=hs)
cyl('HS_Logo_Eye', 0.0026, 0.00006, (-0.0240, -0.0003, ZR + 0.00144), M['gold'], col, verts=24, parent=hs)
cyl('HS_Logo_Pupil', 0.0012, 0.00008, (-0.0240, -0.0003, ZR + 0.00146), M['black_mt'], col, verts=16, parent=hs)
# spring-loaded mounting screws at the corners of the rim
for i, (x, y) in enumerate(((-0.090, 0.0445), (0.090, 0.0445), (-0.090, -0.0445), (0.090, -0.0445))):
    cyl(f'HS_Screw_{i}', 0.0032, 0.0020, (x, y, ZR + 0.0010), M['steel'], col, verts=20, bevel=0.0004, parent=hs)
    cyl(f'HS_Screw_Hex_{i}', 0.0013, 0.0003, (x, y, ZR + 0.0020), M['port'], col, verts=6, parent=hs)

# ---------------------------------------------------------------- sockets
empty('SOCKET_power_in', (0, 0, -0.0045), col, root, size=0.02, rot=(math.pi, 0, 0))

# ---------------------------------------------------------------- finalize
for o in [root] + list(root.children_recursive):
    if o.type == 'MESH':
        H['apply_all'](o)
objs = [root] + list(root.children_recursive)
hs_objs = [hs] + list(hs.children_recursive)
print('TRIS total', tri_count(objs), 'heatsink', tri_count(hs_objs))
glb = BASE + r'\export\gpu_b200_sxm.glb'
H['export_glb'](ROOT, glb)
print('GLB', os.path.getsize(glb))

setup_render()
cam = bpy.data.objects['Camera']
R = BASE + r'\renders\b200_sxm_'


def vis(obj_list, show):
    for o in obj_list:
        o.hide_render = not show; o.hide_viewport = not show


look_at(cam, (-0.30, -0.36, 0.30), (0, 0, 0.045), lens=50); render(R + '34.png')
look_at(cam, (0, -0.0001, 0.6), (0, 0, 0), ortho=0.235); render(R + 'top.png')
look_at(cam, (-0.50, -0.16, 0.32), (0, 0, 0.050), lens=50); render(R + 'side.png')
look_at(cam, (0, -0.58, 0.20), (0, 0, 0.050), lens=50); render(R + 'side_long.png')
vis(hs_objs, False)
look_at(cam, (-0.17, -0.22, 0.20), (0, 0, 0.0), lens=50); render(R + 'module.png')
vis([lid] + list(lid.children_recursive), False)
render(R + 'bare.png')
look_at(cam, (0.0, -0.075, 0.14), (0, -0.004, 0.0), lens=50); render(R + 'bare_close.png')
vis(objs, True)
look_at(cam, (-0.30, -0.36, 0.30), (0, 0, 0.045), lens=50)
bpy.ops.wm.save_as_mainfile(filepath=BASE + r'\gpu_14a_b200_sxm.blend')
print('DONE')
