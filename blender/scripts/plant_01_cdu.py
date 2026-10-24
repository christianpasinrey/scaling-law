"""plant_01_cdu - Vertiv CoolChip CDU 2300 (row-based liquid-to-liquid coolant distribution unit, 2.3 MW).

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python plant_01_cdu.py

Dimensions (Vertiv product page, Physical characteristics): H 2400 x W 1200 x D 1200 mm.
Look (Vertiv product imagery, perspective front/right): matte near-black cabinet; top lip with perforated
vent strip; upper-left door with VERTIV logo, "CoolChip CDU", two small vent slots and a colour
touchscreen; upper-right door; two round fan grilles across the doors at ~1.16 m; one full-width lower
panel; plinth with two forklift slots. Pipe connections: modelled on top (overhead piping as in Vertiv's
hall render) - the real unit offers top/bottom options (approximate).
Origin = floor centre of the 1.2 x 1.2 m footprint, front faces -Y.
"""
import bpy, math, os, sys
exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\plant_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']; P = bpy.app.driver_namespace['PLANT']

ROOT = 'Plant_CDU_CoolChip2300'
BLEND = os.path.join(P['BASE'], 'plant_01_cdu.blend')
GLB = os.path.join(P['BASE'], 'export', 'plant_01_cdu.glb')
root, col, M, PM = P['setup'](ROOT)
mat = H['mat']
BODY = mat('PL_Vertiv_Body', (0.028, 0.028, 0.030), 0.15, 0.55)
SEAM = mat('PL_Vertiv_Seam', (0.004, 0.004, 0.004), 0.0, 0.8)
GRILLE = mat('PL_Vertiv_Grille', (0.010, 0.010, 0.011), 0.4, 0.45)
WHITE = PM['label_w']

W, D, HT = 1.2, 1.2, 2.4
X0, X1, Y0, Y1 = -W / 2, W / 2, -D / 2, D / 2
ZP = 0.13      # plinth top
ZL = 0.99      # lower panel top / upper doors bottom
ZD = 2.31      # doors top / top lip bottom

# ---------------------------------------------------------------- plinth with forklift slots (through Y)
slots = [(-0.35, -0.19), (0.18, 0.34)]
zs0, zs1 = 0.035, 0.10
def plinth():
    xs = [X0 + 0.02] + [v for s in slots for v in s] + [X1 - 0.02]
    for a, b in zip(xs[0::2], xs[1::2]):          # solid posts between slots
        yield ((a + b) / 2, 0, ZP / 2), (b - a, D - 0.04, ZP)
    for a, b in slots:                            # bridge over and floor under each slot
        yield ((a + b) / 2, 0, (zs1 + ZP) / 2), (b - a, D - 0.04, ZP - zs1)
        yield ((a + b) / 2, 0, zs0 / 2), (b - a, D - 0.04, zs0)
H['slat_array']('CDU_Plinth', plinth, M['black_mt'], col, root)

# ---------------------------------------------------------------- body shell
H['box']('CDU_Body', (W, D, ZD - ZP), (0, 0, (ZP + ZD) / 2), BODY, col, bevel=0.004, parent=root)
H['box']('CDU_TopLip', (W, D, HT - ZD), (0, 0, (ZD + HT) / 2), BODY, col, bevel=0.003, parent=root)
# perforated vent strip on the front of the top lip (and the rear)
def lip_vents():
    n = 46
    for i in range(n):
        x = X0 + 0.04 + (W - 0.08) * (i + 0.5) / n
        for y in (Y0 - 0.0006, Y1 + 0.0006):
            yield (x, y, (ZD + HT) / 2 + 0.005), (0.012, 0.0012, 0.045)
H['slat_array']('CDU_TopLip_Vents', lip_vents, PM['vent'], col, root)

# door / panel seams on the front face (thin dark grooves standing 0.5 mm proud)
yf = Y0 - 0.0005
def seams():
    yield (0, yf, ZL), (W - 0.01, 0.001, 0.006)              # lower panel / doors
    yield (0, yf, ZD - 0.002), (W - 0.01, 0.001, 0.005)      # doors / lip
    yield (-0.01, yf, (ZL + ZD) / 2), (0.006, 0.001, ZD - ZL)  # between doors
    yield (0, yf, ZP + 0.002), (W - 0.01, 0.001, 0.005)
    for x in (X0 + 0.006, X1 - 0.006):
        yield (x, yf, (ZP + ZD) / 2), (0.004, 0.001, ZD - ZP)
H['slat_array']('CDU_FrontSeams', seams, SEAM, col, root)

# side panels: two vertical seams + screw heads (right/left sides, as in the 3/4 image)
def side_details():
    for xs in (X0 - 0.0005, X1 + 0.0005):
        for y in (Y0 + 0.03, 0.0, Y1 - 0.03):
            yield (xs, y, (ZP + ZD) / 2), (0.001, 0.005, ZD - ZP - 0.02)
        for y in (Y0 + 0.045, Y1 - 0.045):
            for z in (0.35, 0.9, 1.45, 2.0):
                yield (xs, y, z), (0.002, 0.012, 0.012)
H['slat_array']('CDU_SideSeams', side_details, SEAM, col, root)

# ---------------------------------------------------------------- front details
# fan grilles: round, hex-perforated look -> dark disc + concentric rings + bezel
for i, xc in enumerate((-0.22, 0.16)):
    zc = 1.16
    P['cylinders'](f'CDU_FanGrille_{i}', [((xc, Y0 - 0.002, zc), 0.185, 0.004, (math.pi / 2, 0, 0))], GRILLE, col, root, verts=48)
    P['tori'](f'CDU_FanGrilleRings_{i}', [((xc, Y0 - 0.004, zc), r, 0.0025, (math.pi / 2, 0, 0)) for r in (0.05, 0.09, 0.13, 0.17, 0.185)],
              SEAM, col, root, major_segs=40, minor_segs=4)
# small vent slots left of the screen
H['slat_array']('CDU_DoorVents', lambda: (((-0.425, Y0 - 0.001, z), (0.085, 0.002, 0.034)) for z in (1.86, 1.66)), PM['vent'], col, root)
def vent_bars():
    for z in (1.86, 1.66):
        for k in range(4):
            yield (-0.425, Y0 - 0.002, z - 0.0125 + k * 0.0083), (0.085, 0.002, 0.002)
H['slat_array']('CDU_DoorVentBars', vent_bars, BODY, col, root)
# touchscreen (bezel + emissive screen the game can drive)
H['box']('CDU_ScreenBezel', (0.185, 0.008, 0.135), (-0.23, Y0 - 0.004, 1.74), M['black_gl'], col, bevel=0.003, parent=root)
P['led']('LED_hmi_screen', (-0.23, Y0 - 0.0085, 1.74), (0.160, 0.002, 0.105), PM['screen'], col, root)
# screen UI hint: a few bars (pump speed / temperatures)
H['slat_array']('CDU_ScreenUI', lambda: (((-0.29 + k * 0.03, Y0 - 0.0098, 1.71 + h / 2), (0.016, 0.0006, h)) for k, h in enumerate((0.05, 0.07, 0.04, 0.06, 0.03))),
                PM['label_w'], col, root)
P['led']('LED_status', (-0.23, Y0 - 0.003, 1.655), (0.05, 0.003, 0.006), PM['led_g'], col, root)
# logo + model name (white print)
P['text']('CDU_Logo_VERTIV', 'VERTIV', 0.045, WHITE, col, root, (-0.40, Y0 - 0.0006, 2.225))
H['cyl']('CDU_Logo_Mark', 0.022, 0.001, (-0.505, Y0 - 0.0006, 2.225), WHITE, col, verts=24, rot=(math.pi / 2, 0, 0), parent=root)
H['prism']('CDU_Logo_MarkV', [(-0.517, 2.236), (-0.493, 2.236), (-0.505, 2.212)], 'xz', Y0 - 0.0012, -0.001, BODY, col, parent=root)
P['text']('CDU_Label_Model', 'CoolChip CDU', 0.028, WHITE, col, root, (-0.44, Y0 - 0.0006, 2.14), font=P['FONT'])
# right-door latches (small round screws along the left edge of the right door, as in the photo)
P['cylinders']('CDU_Latches', [((0.03, Y0 - 0.003, z), 0.011, 0.006, (math.pi / 2, 0, 0)) for z in (2.25, 1.62, 1.03)], M['steel'], col, root, verts=16)
P['cylinders']('CDU_PanelScrews', [((x, Y0 - 0.002, z), 0.006, 0.004, (math.pi / 2, 0, 0))
                                    for x in (X0 + 0.025, X1 - 0.025) for z in (0.18, 0.95)], M['steel'], col, root, verts=12)

# ---------------------------------------------------------------- piping: 4 x DN150 on top (rear half)
r_pipe = 0.084            # DN150 (6") OD 168 mm
z_top, z_end = HT, 3.05
pipes = [  # name, x, material, direction ('in' = flow into the CDU)
    ('primary_in',    -0.42, PM['pipe_blue'], 'in'),   # facility water supply (from chillers / dry coolers)
    ('primary_out',   -0.15, PM['pipe_red'],  'out'),  # facility water return
    ('secondary_out',  0.15, PM['pipe_blue'], 'out'),  # TCS supply to racks
    ('secondary_in',   0.42, PM['pipe_red'],  'in'),   # TCS return from racks
]
yp = 0.28
flanges, valves, handles = [], [], []
for name, x, pm, d in pipes:
    a, b = (x, yp, z_top + 0.01), (x, yp, z_end)
    pts = [b, a] if d == 'in' else [a, b]
    P['flow_path'](f'FLOW_coolant_{name}', pts, pm, col, root, radius=r_pipe, verts=20, kind='coolant')
    sock = 'SOCKET_coolant_%s_%s' % (d, name.split('_')[0])
    P['socket'](sock, (x, yp, z_end), (0, 0, 1), root, col)
    for z in (z_top + 0.03, 2.72, 2.84, z_end - 0.02):
        flanges.append(((x, yp, z), r_pipe + 0.025, 0.012, (0, 0, 0)))
    valves.append(((x, yp, 2.78), r_pipe + 0.012, 0.10, (0, 0, 0)))
    handles.append(((x, yp - 0.16, 2.80), (0.03, 0.26, 0.02)))
P['cylinders']('CDU_PipeFlanges', flanges, M['steel'], col, root, verts=24)
P['cylinders']('CDU_Valves', valves, PM['grey'], col, root, verts=24)
H['slat_array']('CDU_ValveHandles', lambda: iter(handles), PM['label_r'], col, root)
P['cylinders']('CDU_PipeCollars', [((x, yp, z_top + 0.004), r_pipe + 0.05, 0.008, (0, 0, 0)) for _, x, _, _ in pipes], M['black_mt'], col, root, verts=24)
# pipe ID labels (white text bands)
for name, x, pm, d in pipes:
    P['text'](f'CDU_PipeLabel_{name}', ('FWS' if name == 'primary_in' else 'FWR' if name == 'primary_out' else 'TCS S' if name == 'secondary_out' else 'TCS R'),
              0.026, WHITE, col, root, (x, yp - r_pipe - 0.004, 2.58))

# ---------------------------------------------------------------- power feed (top, front-right)
P['cylinders']('CDU_PowerGland', [((0.42, -0.35, HT + 0.012), 0.045, 0.024, (0, 0, 0))], M['black_mt'], col, root, verts=20)
P['flow_path']('FLOW_power_in', [(0.42, -0.35, 2.95), (0.42, -0.35, HT + 0.02)], PM['cable'], col, root, radius=0.025, verts=12, kind='power')
P['socket']('SOCKET_power_in', (0.42, -0.35, 2.95), (0, 0, 1), root, col)

# ---------------------------------------------------------------- export + renders
tris = P['finish'](root, BLEND, GLB)
P['render']('plant_01_cdu', {
    'front':  ((0, -1, 0.05), 2.6, 50),
    '34':     ((-0.75, -1, 0.45), 2.6, 50),
    'rear34': ((0.9, 0.9, 0.7), 2.7, 50),
    'panel':  ((-0.2, -1, 0.1), 0.55, 50, (-0.25, -0.6, 1.75)),
    'top':    ((0.4, -0.6, 1.0), 0.75, 50, (0, 0.1, 2.6)),
}, (0, 0, 1.4), 3.0)
