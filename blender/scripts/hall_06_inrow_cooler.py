"""In-row chilled-water cooler (APC / Schneider Uniflair InRow RC ACRC301S, 300 mm wide, 42U height).

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python hall_06_inrow_cooler.py [-- --norender]

Real references:
  - ACRC301S: 300 W x 1095 D x 1991 H mm (retailer spec listings: lambda-tek, SHI, CDW 78.4 in), up to 40 kW,
    hot-swappable variable-speed fans, chilled water connected from the top (overhead) or bottom (raised floor)
    (se.com / apc.com product pages).
  - Fan count is not published in the listings found; 8 fans in one column is an approximation for the visual.
Convention: it sits IN a rack row, so it follows the rack convention: origin = floor, front-centre, front face
at y = 0 facing -Y (cold aisle), depth toward +Y (hot aisle).  Footprint 0.300 x 1.095 m, height 1.991 m.
Children: FAN_0..7 (spin about local Z), LED_fan_0..7, LED_status, LED_display, FLOW_chw_supply /
          FLOW_chw_return hoses with flow UV, SOCKET_coolant_in / SOCKET_coolant_out (top), SOCKET_power_in.
"""
import bpy, bmesh, math, mathutils, os, sys
from mathutils import Vector

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\hall_lib.py', encoding='utf-8').read())

FILE = 'hall_06_inrow_cooler'
BLEND = os.path.join(BASE, FILE + '.blend')
reset_scene()
M = mats()
stats = []

W, D, HT = 0.300, 1.095, 1.991
root, col = piece('InRow_RC_ACRC301S', 'IRC', 'HALL_InRow')

PERF = tex_mat('HALL_PerfBlack', perf_image('HALL_perf_black', 256, 16, 0.33, (0.012, 0.012, 0.013)), 0.3, 0.5, alpha_from_tex=True)
PERF_R = tex_mat('HALL_PerfBlackRear', perf_image('HALL_perf_black_r', 256, 16, 0.30, (0.012, 0.012, 0.013), alpha_holes=False,
                                                   hole_rgb=(0.0, 0.0, 0.0)), 0.3, 0.5)

# body (inset behind the doors), frame, feet
H['box']('Body', (W - 0.01, D - 0.04, HT - 0.06), (0, D / 2, 0.03 + (HT - 0.06) / 2), M['cab_black'], col, parent=root)
H['box']('Frame_Top', (W, D, 0.03), (0, D / 2, HT - 0.015), M['cab_black'], col, parent=root)
H['box']('Frame_Base', (W, D, 0.06), (0, D / 2, 0.03), M['cab_black'], col, parent=root)
for x in (-0.11, 0.11):
    for y in (0.06, D - 0.06):
        H['cyl'](f'Foot_{x}_{y}', 0.02, 0.02, (x, y, 0.01), M['steel'], col, verts=10, parent=root)
# fans behind the front door (single column)
NF = 8
FR = 0.092
fz = [0.17 + i * (1.62 - 0.17) / (NF - 1) for i in range(NF)]
for i, z in enumerate(fz):
    sweep(f'Fan_Shroud_{i}', [(0, 0.09, z), (0, 0.025, z)], circle(FR + 0.008, 20), M['fan'], col, root, caps=False, up0=(0, 0, 1))
    H['cyl'](f'Fan_Motor_{i}', 0.035, 0.05, (0, 0.10, z), M['black_dc'], col, verts=14, rot=(math.pi / 2, 0, 0), parent=root)
    fan_blades(f'FAN_{i}', 0.034, FR, 5, M['fan'], col, root, (0, 0.05, z), axis='Y', depth=0.018)
H['box']('Fan_Bulkhead', (W - 0.02, 0.01, 1.70), (0, 0.13, 0.92), M['port'], col, parent=root)
# front door: perforated (alpha) insert in a frame + top display panel
DZ0, DZ1 = 0.07, 1.76
quad('Front_Perf', W - 0.04, DZ1 - DZ0, (0, -0.012, (DZ0 + DZ1) / 2), PERF, col, root,
     uv_rep=((W - 0.04) / 0.08, (DZ1 - DZ0) / 0.08), rot=(math.pi / 2, 0, 0))
for s in (-1, 1):
    H['box'](f'Door_Stile_{s:+d}', (0.02, 0.02, HT - 0.06), (s * (W / 2 - 0.01), -0.01, HT / 2), M['cab_black'], col, parent=root)
H['box']('Door_Rail_Bottom', (W, 0.02, 0.05), (0, -0.01, 0.045), M['cab_black'], col, parent=root)
H['box']('Display_Panel', (W, 0.022, HT - DZ1 - 0.03), (0, -0.011, (DZ1 + HT - 0.03) / 2), M['cab_black'], col, parent=root)
PZ = (DZ1 + HT - 0.03) / 2
H['box']('Display_Bezel', (0.11, 0.004, 0.075), (-0.06, -0.0235, PZ + 0.02), M['black_gl'], col, parent=root)
led('LED_display', (0.085, 0.002, 0.05), (-0.06, -0.0258, PZ + 0.02), (0.35, 0.75, 1.0), root, col, 2.5)
led('LED_status', (0.008, 0.003, 0.008), (0.03, -0.024, PZ + 0.045), (0.1, 1.0, 0.2), root, col)
for i in range(NF):
    led(f'LED_fan_{i}', (0.006, 0.003, 0.006), (0.03 + (i % 4) * 0.022, -0.024, PZ + 0.015 - (i // 4) * 0.018), (0.1, 1.0, 0.2), root, col, 4.0)
H['text_mesh']('Text_Brand', 'APC', FONT, 0.03, M['label'], col, root, (0.085, -0.0225, PZ + 0.045), (math.pi / 2, 0, 0))
H['text_mesh']('Text_Model', 'InRow RC', FONT_R, 0.016, M['label'], col, root, (0.0, -0.0225, PZ - 0.045), (math.pi / 2, 0, 0))
H['box']('Handle', (0.012, 0.02, 0.16), (W / 2 - 0.03, -0.03, 1.0), M['steel'], col, parent=root, bevel=0.004)
# rear door (hot-aisle intake)
quad('Rear_Perf', W - 0.04, DZ1 - DZ0, (0, D + 0.012, (DZ0 + DZ1) / 2), PERF_R, col, root,
     uv_rep=((W - 0.04) / 0.08, (DZ1 - DZ0) / 0.08), rot=(math.pi / 2, 0, math.pi))
for s in (-1, 1):
    H['box'](f'Rear_Stile_{s:+d}', (0.02, 0.02, HT - 0.06), (s * (W / 2 - 0.01), D + 0.01, HT / 2), M['cab_black'], col, parent=root)
H['box']('Rear_Top', (W, 0.02, HT - DZ1 - 0.03), (0, D + 0.01, (DZ1 + HT - 0.03) / 2), M['cab_black'], col, parent=root)
H['box']('Rear_Bottom', (W, 0.02, 0.05), (0, D + 0.01, 0.045), M['cab_black'], col, parent=root)

# top: chilled water hoses up to the overhead header + power cord
TOPZ = 2.75                      # overhead header elevation (hose ends)
for name, x, mat_, sock, direc in (('FLOW_chw_supply', -0.06, M['pipe_blue'], 'SOCKET_coolant_in', 'in'),
                                    ('FLOW_chw_return', 0.06, M['pipe_red'], 'SOCKET_coolant_out', 'out')):
    path = [(x, 0.92, TOPZ), (x, 0.92, HT + 0.03)]
    if direc == 'out':
        path = list(reversed(path))
    sweep(name, path, circle(0.024, 14), mat_, col, root, smooth=True, flow='coolant', root=root)
    H['cyl'](name.replace('FLOW', 'Fitting') + '_bot', 0.032, 0.05, (x, 0.92, HT + 0.025), M['ss'], col, verts=14, parent=root)
    H['cyl'](name.replace('FLOW', 'Fitting') + '_top', 0.032, 0.05, (x, 0.92, TOPZ - 0.025), M['ss'], col, verts=14, parent=root)
    socket(sock, (x, 0.92, TOPZ), (0, 0, 1), root, col)
H['box']('Top_Gland_Plate', (0.24, 0.12, 0.01), (0, 0.92, HT + 0.005), M['steel'], col, parent=root)
sweep('FLOW_power_cord', [(0.10, 0.70, HT), (0.10, 0.70, HT + 0.35)], circle(0.009, 10), M['rubber'], col, root,
      smooth=True, flow='power', root=root)
socket('SOCKET_power_in', (0.10, 0.70, HT + 0.35), (0, 0, 1), root, col)

root['footprint_m'] = (W, D)
root['height_m'] = HT
finish_piece(root, 'IRC', FILE, stats)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
export_all(FILE, stats)

if DO_RENDER:
    colx = H['coll']('RenderContext')
    for i, x in enumerate((-0.45, -1.05)):
        H['box'](f'CTX_Rack_{i}', (0.596, 1.07, RACK_H), (x, 0.535, RACK_H / 2), M['cab_black'], colx)
    studio(4.5, (0, 0.5, 1.0))
    add_sun(1.0)
    render_views(FILE, {
        'front': ((1.6, -3.2, 1.7), (-0.1, 0.4, 1.05), 30),
        'close': ((0.45, -0.9, 1.75), (0.0, 0.0, 1.62), 35),
        'rear':  ((1.4, 3.4, 2.4), (0.0, 0.9, 1.6), 32),
    })
