"""Perimeter chilled-water CRAH (Vertiv Liebert CW, CW060-class, downflow) on an EC-fan floor stand.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python hall_05_crah.py [-- --norender]

Real references:
  - Vertiv Liebert CW060 (60 kW): 74 in W x 35 in D x 72 in H = 1880 x 889 x 1829 mm (vertiv.com product page).
    For comparison Liebert PDX PX023 (DX CRAC): 876 x 879 x 1970 mm.
  - Downflow units take return air through the top and discharge down; Vertiv offers EC fans lowered into the
    floor stand; downflow models offer front / side discharge (vertiv.com). We model a 450 mm floor stand with
    front discharge so the unit also works on a slab floor and the three EC fans are visible.
  - Wikimedia 'CRAC Cabinet 1.jpg': long light cabinets with full-height door panels and vertical seams.
Origin = floor centre of the footprint, front (service side) faces -Y.  Footprint 1.880 x 0.889 m, height 2.279 m.
Children: FAN_0..2 (rotors, spin about local Z), LED_fan_0..2, LED_status, LED_display,
          FLOW_chw_supply / FLOW_chw_return (insulated pipes, flow UV), SOCKET_coolant_in / SOCKET_coolant_out,
          SOCKET_power_in.
"""
import bpy, bmesh, math, mathutils, os, sys
from mathutils import Vector

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\hall_lib.py', encoding='utf-8').read())

FILE = 'hall_05_crah'
BLEND = os.path.join(BASE, FILE + '.blend')
reset_scene()
M = mats()
stats = []

W, D, HC = 1.880, 0.889, 1.829
ST = 0.450                      # floor stand height
ZT = ST + HC                    # top of cabinet
YF = -D / 2
PANEL = M['white_pnl']

root, col = piece('CRAH_LiebertCW', 'CRAH', 'HALL_CRAH')

# ---------------------------------------------------------------- floor stand with EC fans (front discharge)
for s in (-1, 1):
    H['box'](f'Stand_Side_{s:+d}', (0.04, D, ST), (s * (W / 2 - 0.02), 0, ST / 2), M['black_st'], col, parent=root)
H['box']('Stand_Back', (W, 0.03, ST), (0, D / 2 - 0.015, ST / 2), M['black_st'], col, parent=root)
H['box']('Stand_TopRail', (W, 0.05, 0.04), (0, YF + 0.025, ST - 0.02), M['black_st'], col, parent=root)
H['box']('Stand_Kick', (W, 0.05, 0.03), (0, YF + 0.025, 0.015), M['black_st'], col, parent=root)
H['box']('Stand_Plenum', (W - 0.1, 0.02, ST - 0.08), (0, D / 2 - 0.05, ST / 2), M['port'], col, parent=root)
FX = (-0.6, 0.0, 0.6)
FR = 0.185
FZ = ST / 2
for i, x in enumerate(FX):
    # venturi ring (inlet cone) and motor
    sweep(f'Fan_Ring_{i}', [(x, YF + 0.20, FZ), (x, YF + 0.08, FZ)], circle(FR + 0.012, 24), M['fan'], col, root,
          caps=False, closed=True, up0=(0, 0, 1))
    H['cyl'](f'Fan_Motor_{i}', 0.07, 0.10, (x, YF + 0.24, FZ), M['black_dc'], col, verts=20, rot=(math.pi / 2, 0, 0), parent=root)
    fan_blades(f'FAN_{i}', 0.06, FR, 6, M['fan'], col, root, (x, YF + 0.15, FZ), axis='Y', depth=0.03)
    led(f'LED_fan_{i}', (0.012, 0.004, 0.012), (x + 0.24, YF - 0.002, ST - 0.02), (0.1, 1.0, 0.2), root, col)


def guard():
    for k in range(17):
        yield (0, YF + 0.004, 0.04 + k * (ST - 0.08) / 16), (W - 0.1, 0.004, 0.004)
    for k in range(48):
        yield (-W / 2 + 0.06 + k * (W - 0.12) / 47, YF + 0.006, ST / 2), (0.003, 0.004, ST - 0.08)
H['slat_array']('Fan_Guard', guard, M['zinc'], col, root)

# ---------------------------------------------------------------- cabinet
H['box']('Cabinet', (W, D, HC), (0, 0, ST + HC / 2), M['beige_pnl'], col, parent=root, bevel=0.004)
PW = (W - 0.04) / 3
for i in range(3):
    xc = -W / 2 + 0.02 + PW / 2 + i * PW
    H['box'](f'Door_{i}', (PW - 0.012, 0.012, HC - 0.06), (xc, YF - 0.006, ST + HC / 2 - 0.01), PANEL, col, parent=root, bevel=0.003)
    for zz in (ST + 0.9, ST + 1.15):
        H['box'](f'Latch_{i}_{zz:.2f}', (0.03, 0.012, 0.06), (xc + PW / 2 - 0.05, YF - 0.016, zz), M['plastic'], col, parent=root, bevel=0.004)
    if i == 2:
        H['box'](f'Door_Louvre_{i}', (PW - 0.2, 0.004, 0.3), (xc, YF - 0.0125, ST + 0.35), M['port'], col, parent=root)
        def louv(xc=xc):
            for k in range(10):
                yield (xc, YF - 0.016, ST + 0.22 + k * 0.028), (PW - 0.2, 0.006, 0.01)
        H['slat_array'](f'Door_Louvre_Slats_{i}', louv, PANEL, col, root)
# iCOM display on the left door
dx = -W / 2 + 0.02 + PW / 2
H['box']('Display_Bezel', (0.26, 0.012, 0.19), (dx, YF - 0.016, ZT - 0.33), M['black_gl'], col, parent=root, bevel=0.006)
led('LED_display', (0.21, 0.002, 0.13), (dx, YF - 0.0225, ZT - 0.33), (0.35, 0.65, 1.0), root, col, 2.5)
led('LED_status', (0.016, 0.003, 0.016), (dx + 0.10, YF - 0.0225, ZT - 0.455), (0.1, 1.0, 0.2), root, col)
H['text_mesh']('Text_Model', 'Liebert CW', FONT_R, 0.03, M['label_blk'], col, root, (dx, YF - 0.0125, ZT - 0.49), (math.pi / 2, 0, 0))
H['text_mesh']('Text_Brand', 'VERTIV', FONT, 0.07, M['label_blk'], col, root, (W / 2 - 0.02 - PW / 2, YF - 0.0125, ZT - 0.17), (math.pi / 2, 0, 0))
# top return-air grille + filters
H['box']('Top_Filter', (W - 0.08, D - 0.08, 0.01), (0, 0, ZT + 0.002), M['grey_pl'], col, parent=root)
def top_grille():
    for k in range(60):
        yield (-W / 2 + 0.06 + k * (W - 0.12) / 59, 0, ZT + 0.012), (0.006, D - 0.1, 0.02)
H['slat_array']('Top_Grille', top_grille, M['zinc'], col, root)
# electrical feed (top rear left)
H['box']('Elec_Box', (0.25, 0.2, 0.12), (-0.7, 0.3, ZT + 0.06), M['grey_pl'], col, parent=root)
sweep('FLOW_power_feed', [(-0.7, 0.3, CEIL_Z), (-0.7, 0.3, ZT + 0.12)], circle(0.025, 12), M['grey_pl'], col, root,
      smooth=True, flow='power', root=root)
socket('SOCKET_power_in', (-0.7, 0.3, CEIL_Z), (0, 0, 1), root, col)

# ---------------------------------------------------------------- chilled-water piping stubs (top rear right)
PZ = 3.00                        # overhead header elevation (pipe ends)
for name, x, mat_, sock, direc in (('FLOW_chw_supply', 0.55, M['pipe_blue'], 'SOCKET_coolant_in', 'in'),
                                    ('FLOW_chw_return', 0.78, M['pipe_red'], 'SOCKET_coolant_out', 'out')):
    path = [(x, D / 2 + 0.35, PZ), (x, 0.28, PZ), (x, 0.28, ZT + 0.02)]
    if direc == 'out':
        path = list(reversed(path))
    sweep(name, path, circle(0.052, 16), mat_, col, root, radius=0.16, segs90=8, smooth=True, flow='coolant', root=root)
    end = (x, D / 2 + 0.35, PZ)
    H['cyl'](name.replace('FLOW', 'Flange') + '_end', 0.075, 0.025, (x, end[1] - 0.0125, PZ), M['ss'], col, verts=16, rot=(math.pi / 2, 0, 0), parent=root)
    H['cyl'](name.replace('FLOW', 'Flange') + '_top', 0.07, 0.03, (x, 0.28, ZT + 0.015), M['ss'], col, verts=16, parent=root)
    H['box'](name.replace('FLOW', 'Label'), (0.002, 0.12, 0.05), (x - 0.053, D / 2 + 0.12, PZ), M['label'], col, parent=root)
    socket(sock, end, (0, 1, 0), root, col)
H['box']('Valve_Actuator', (0.12, 0.12, 0.10), (0.78 + 0.0, 0.28, PZ - 0.20), M['black_dc'], col, parent=root)

root['footprint_m'] = (W, D)
root['height_m'] = ZT
finish_piece(root, 'CRAH', FILE, stats)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
export_all(FILE, stats)

if DO_RENDER:
    studio(6.0, (0, 0, 1.2))
    add_sun(1.0)
    render_views(FILE, {
        'front': ((-2.2, -4.6, 1.8), (0.0, 0.0, 1.2), 32),
        'fans':  ((-0.6, -1.6, 0.6), (-0.3, 0.0, 0.25), 30),
        'top':   ((2.4, 2.8, 3.8), (0.2, 0.0, 2.3), 30),
    })
