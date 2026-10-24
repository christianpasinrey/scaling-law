"""APC Rack PDU 2G Switched, Zero U, 30 A 200/208 V, (21) C13 + (3) C19 - AP8941 (2G family, 2012-2022).

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python rack_pdu_0u.py

Conventions: vertical 0U PDU, outlet face in the XZ plane at y=0 facing -Y, body depth toward +Y,
origin = bottom-front-centre. The rack mounts it in its rear 0U channels with a 180 deg Z rotation so the
outlets face the rear door (see SLOT_pdu_* in rack_01_19in_42u).
Sources:
  - se.com AP8941 product page: Rack PDU 2G, Switched, ZeroU, 30A, 200/208V, (21) C13 & (3) C19,
    NEMA L6-30P input; product photos (front 3/4, rear) used for the layout (measured 1.37 mm/px).
  - Size: 2G ZeroU family cross-section 56 W x 44 D mm and 1791 mm length (AP8841 listing); the AP8941 exact
    length is not published in the sources found - outlet pitch measured on the photo (~34.8 mm) agrees with
    ~1.79 m. Replacement APDU9941 is 1829 x 55 x 46 mm.
Layout (top to bottom, photo): cord gland, rating label, Bank 1 breaker, outlets 1-7 C13, 8 C19, network
management module (APC logo, LCD, 3 buttons, ports), 9-15 C13, 16 C19, Bank 2 breaker, 17-23 C13, 24 C19.
"""
import bpy, bmesh, math, mathutils, os, sys

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\rack_kit_lib.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\net_switch_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']; RK = bpy.app.driver_namespace['RK']
V = mathutils.Vector
mm = 0.001

ROOT = 'rack_pdu_0u'
BLEND = os.path.join(RK['BASE'], ROOT + '.blend')
root, col = H['new_card_scene'](ROOT)
mat = H['mat']; M = H['base_materials']()
BODY = mat('RK_PDU_Body', (0.010, 0.010, 0.011), 0.35, 0.55, spec=0.3)
PLAS = mat('RK_PDU_Outlet', (0.006, 0.006, 0.007), 0.0, 0.35, spec=0.4)
CAV = mat('RK_PortCavity', (0.0015, 0.0015, 0.0015), 0.0, 1.0, spec=0.05)
WHITE = mat('RK_PrintWhite', (0.75, 0.75, 0.74), 0.0, 0.6)
LABEL = mat('RK_PDU_Label', (0.55, 0.56, 0.57), 0.6, 0.45)
INK = mat('RK_PDU_Ink', (0.03, 0.03, 0.03), 0.0, 0.6)
APC_RED = mat('RK_APC_Red', (0.65, 0.02, 0.02), 0.0, 0.45)
LCD = mat('RK_LCD', (0.15, 0.45, 0.65), 0.0, 0.25, emit=(0.35, 0.75, 1.0), emit_str=1.6)
LED_G = mat('RK_LED_Green', (0.05, 0.6, 0.1), 0.0, 0.3, emit=(0.1, 1.0, 0.2), emit_str=3.0)
BRASS = mat('RK_Brass', (0.85, 0.65, 0.3), 1.0, 0.3)
CORD = mat('RK_Cable_pdu_input', (0.006, 0.006, 0.006), 0.0, 0.42, spec=0.4)

L = 1.791; W = 0.056; D = 0.044
zt = lambda d_mm: L - d_mm * mm          # distance from the top (photo) -> z

# ---------------------------------------------------------------- layout
outlets = []   # (n, kind, z, bank)
for k in range(7):
    outlets.append((k + 1, 'C13', zt(549 + k * 34.8), 1))
outlets.append((8, 'C19', zt(816), 1))
for k in range(7):
    outlets.append((9 + k, 'C13', zt(1069 + k * 34.8), 1 if k < 4 else 2))
outlets.append((16, 'C19', zt(1347), 2))
for k in range(7):
    outlets.append((17 + k, 'C13', zt(1490 + k * 34.8), 2))
outlets.append((24, 'C19', zt(1766), 2))
OX = 0.004                                   # outlets sit right of centre, numbers on the left
DIMS = {'C13': ((25.0 * mm, 15.6 * mm), (31.0 * mm, 22.5 * mm)), 'C19': ((29.5 * mm, 20.5 * mm), (35.0 * mm, 26.5 * mm))}
modules = {'bank1': (zt(523), zt(424)), 'nmc': (zt(1042), zt(841)), 'bank2': (zt(1466), zt(1367)), 'label': (zt(267), zt(150))}

# ---------------------------------------------------------------- body (face plate with outlet openings)
bm = bmesh.new()
holes = []
for n, kind, z, bank in outlets:
    (cw, ch), (fw, fh) = DIMS[kind]
    holes.append((OX - cw / 2, OX + cw / 2, z - ch / 2, z + ch / 2))
# face plate (plate_with_holes / cavity come from net_switch_lib)
plate_with_holes(bm, -W / 2, W / 2, 0.0, L, 0.0, holes, 0)
# rest of the body: back, sides, ends (open box behind the face plate)
for q in (((-W / 2, 0, 0), (-W / 2, D, 0), (-W / 2, D, L), (-W / 2, 0, L)),
          ((W / 2, 0, 0), (W / 2, 0, L), (W / 2, D, L), (W / 2, D, 0)),
          ((-W / 2, D, 0), (W / 2, D, 0), (W / 2, D, L), (-W / 2, D, L)),
          ((-W / 2, 0, L), (W / 2, 0, L), (W / 2, D, L), (-W / 2, D, L)),
          ((-W / 2, 0, 0), (-W / 2, D, 0), (W / 2, D, 0), (W / 2, 0, 0))):
    bm.faces.new([bm.verts.new(p) for p in q])
# side ribs (the 2G extrusion has a stepped profile on the edges)
for sx in (-1, 1):
    RK['add_box'](bm, (sx * (W / 2 - 0.0015), -0.0008, L / 2), (0.003, 0.0016, L - 0.004), 0)
# rear mounting buttons (toolless pegs)
for zz in (0.12, L - 0.12):
    RK['add_cyl'](bm, (0, D + 0.004, zz), 0.0045, 0.008, 'Y', 16, 0)
    RK['add_cyl'](bm, (0, D + 0.0085, zz), 0.0075, 0.002, 'Y', 16, 0)
# top end cap + cord gland
RK['add_box'](bm, (0, D / 2, L + 0.003), (W - 0.004, D - 0.004, 0.006), 0)
RK['add_cyl'](bm, (0, D / 2, L + 0.015), 0.0115, 0.018, 'Z', 20, 1)
RK['add_cyl'](bm, (0, D / 2, L + 0.028), 0.0095, 0.010, 'Z', 20, 1)
body = RK['mesh_obj']('PDU_Body', bm, [BODY, PLAS], col, root)

# ---------------------------------------------------------------- outlets (frames, cavities, female inserts)
bm = bmesh.new()
for n, kind, z, bank in outlets:
    (cw, ch), (fw, fh) = DIMS[kind]
    x0, x1, z0, z1 = OX - cw / 2, OX + cw / 2, z - ch / 2, z + ch / 2
    # raised frame around the opening
    plate_with_holes(bm, OX - fw / 2, OX + fw / 2, z - fh / 2, z + fh / 2, -0.0018, [(x0, x1, z0, z1)], 0)
    for (a, b, c, d) in ((OX - fw / 2, OX + fw / 2, z - fh / 2, z - fh / 2 + 0.0005), (OX - fw / 2, OX + fw / 2, z + fh / 2 - 0.0005, z + fh / 2)):
        RK['add_box'](bm, ((a + b) / 2, -0.0009, (c + d) / 2), (b - a, 0.0018, d - c), 0)
    for xx in (OX - fw / 2 + 0.00025, OX + fw / 2 - 0.00025):
        RK['add_box'](bm, (xx, -0.0009, z), (0.0005, 0.0018, fh), 0)
    cavity(bm, x0, x1, z0, z1, -0.0018, 0.014, 1)
    # keyed chamfers on the two lower corners of the C13 opening (wedges)
    if kind == 'C13':
        for sx in (-1, 1):
            cx = x0 if sx < 0 else x1
            pts = [(cx, z0), (cx - sx * 0.0035, z0), (cx, z0 + 0.0035)]
            v0 = [bm.verts.new((a, -0.0018, b)) for a, b in pts]; v1 = [bm.verts.new((a, 0.012, b)) for a, b in pts]
            for f in (bm.faces.new(v0), bm.faces.new(list(reversed(v1)))):
                f.material_index = 0
            for i in range(3):
                j = (i + 1) % 3
                bm.faces.new((v0[i], v0[j], v1[j], v1[i])).material_index = 0
        # female insert block with 3 slots
        RK['add_box'](bm, (OX, 0.0065, z + 0.0005), (0.0195, 0.013, 0.0100), 0)
        for px, pz, sw, sh in ((-0.007, 0.0015, 0.0018, 0.0042), (0.007, 0.0015, 0.0018, 0.0042), (0.0, -0.0022, 0.0042, 0.0018)):
            RK['add_box'](bm, (OX + px, 0.0000, z + 0.0005 + pz), (sw, 0.0004, sh), 1)
    else:
        RK['add_box'](bm, (OX, 0.0068, z), (0.0245, 0.0136, 0.0150), 0)
        for px, pz, sw, sh in ((-0.0065, 0.0025, 0.0050, 0.0016), (0.0065, 0.0025, 0.0050, 0.0016), (0.0, -0.0035, 0.0016, 0.0050)):
            RK['add_box'](bm, (OX + px, -0.0001, z + pz), (sw, 0.0004, sh), 1)
RK['mesh_obj']('Outlets', bm, [PLAS, CAV], col, root)

# ---------------------------------------------------------------- modules: label, breakers, network management card
bm = bmesh.new()
a, b = modules['label']
RK['add_box'](bm, (0, -0.0003, (a + b) / 2), (0.040, 0.0006, b - a), 1)
for k in range(9):
    RK['add_box'](bm, (-0.006, -0.0007, b - 0.012 - k * 0.010), (0.016 + (k * 7 % 5) * 0.002, 0.0003, 0.0018), 2)
for key in ('bank1', 'bank2'):
    a, b = modules[key]
    RK['add_box'](bm, (0, -0.0012, (a + b) / 2), (0.048, 0.0024, b - a - 0.004), 0)
    RK['add_box'](bm, (-0.004, -0.0035, (a + b) / 2), (0.012, 0.0030, 0.018), 3)      # breaker rocker
    RK['add_box'](bm, (-0.004, -0.0052, (a + b) / 2 + 0.003), (0.010, 0.0006, 0.006), 0)
a, b = modules['nmc']
RK['add_box'](bm, (0, -0.0012, (a + b) / 2), (0.050, 0.0024, b - a - 0.004), 0)
# 3 buttons under the LCD
for k in range(3):
    RK['add_cyl'](bm, (-0.009 + k * 0.009, -0.0030, zt(965)), 0.0028, 0.0016, 'Y', 16, 4)
# management ports (network, serial, temp/humidity x2) - dark openings in a 2x2 block
for (xx, dd) in ((-0.008, 1000), (0.008, 1000), (-0.008, 1024), (0.008, 1024)):
    RK['add_box'](bm, (xx, -0.0024, zt(dd)), (0.0125, 0.0004, 0.0095), 2)
RK['mesh_obj']('Modules', bm, [PLAS, LABEL, INK, M['black_mt'], M['steel']], col, root)

LED = []
lcd = H['box']('LED_display', (0.026, 0.0006, 0.036), (0, -0.0026, zt(910)), LCD, col, parent=root)
lcd['led_role'] = 'LCD load display'
for n, kind, z, bank in outlets:
    (cw, ch), (fw, fh) = DIMS[kind]
    led = H['box'](f'LED_outlet_{n:02d}', (0.0022, 0.0008, 0.0022), (-0.0205, -0.0004, z + 0.0055), LED_G, col, parent=root)
    led['outlet'] = n
    RK['empty'](f'SOCKET_power_out_{n:02d}', (OX, -0.0018, z), root, col, rot=(math.pi / 2, 0, 0), kind='SINGLE_ARROW', size=0.02,
                props={'connector': 'IEC 60320 ' + kind + ' outlet', 'mates_with': 'C14 plug' if kind == 'C13' else 'C20 plug',
                       'bank': bank, 'outlet': n, 'max_amps': 10 if kind == 'C13' else 16})
for nm, dd in (('LED_status', 940), ('LED_network', 985)):
    H['box'](nm, (0.0022, 0.0008, 0.0022), (0.0165, -0.0028, zt(dd)), LED_G, col, parent=root)

# ---------------------------------------------------------------- print: outlet numbers, bank labels, APC logo
prints = []
TXT_ROT = (math.pi / 2, math.pi / 2, 0)     # reads top -> bottom along the PDU
for n, kind, z, bank in outlets:
    prints.append(RK['text_flat'](f'n{n}', str(n), 0.0040, (-0.0205, -0.0003, z - 0.0035), TXT_ROT, WHITE, col, root))
for key, txt in (('bank1', 'Bank 1'), ('bank2', 'Bank 2')):
    a, b = modules[key]
    prints.append(RK['text_flat'](key, txt, 0.0045, (0.014, -0.0026, (a + b) / 2), TXT_ROT, WHITE, col, root))
a, b = modules['label']
prints.append(RK['text_flat']('model', 'AP8941', 0.005, (0.012, -0.0008, (a + b) / 2), TXT_ROT, INK, col, root))
prints.append(RK['text_flat']('apc', 'APC', 0.010, (0.0, -0.0026, zt(860)), (math.pi / 2, 0, 0), APC_RED, col, root))
prints.append(RK['text_flat']('apc2', 'by Schneider Electric', 0.0028, (0.0, -0.0026, zt(872)), (math.pi / 2, 0, 0), WHITE, col, root, font=RK['FONT_REG']))
RK['join'](prints, 'PDU_Print')

# ---------------------------------------------------------------- input cord (flow UV) + NEMA L6-30P plug
gland_top = V((0, D / 2, L + 0.033))
corners = [(0, 0.30, L + 0.30), (0, D / 2, L + 0.30), tuple(gland_top)]       # plug -> PDU (u = 0 at the plug)
path = RK['fillet_path'](corners, 0.08, 12)
cord, clen = RK['tube']('Cord_Input', path, 0.0075, CORD, col, root, segs=12,
                        props={'cable_type': 'pdu_input_10-3_SJ', 'color_hex': '#101010', 'description': 'NEMA L6-30P input cord, 10 AWG x3, 15 mm OD (shown 0.6 m; real 3 m)'})
plug_c = V(corners[0])
bm = bmesh.new()
RK['add_cyl'](bm, plug_c + V((0, 0.035, 0)), 0.0255, 0.058, 'Y', 24, 0)
for k in range(4):
    RK['add_cyl'](bm, plug_c + V((0, 0.012 + k * 0.012, 0)), 0.0268, 0.004, 'Y', 24, 0)
RK['add_cyl'](bm, plug_c + V((0, 0.003, 0)), 0.012, 0.012, 'Y', 16, 0)
for ang in (90, 210, 330):
    a = math.radians(ang)
    RK['add_box'](bm, plug_c + V((math.cos(a) * 0.0135, 0.071, math.sin(a) * 0.0135)), (0.0035 if ang != 90 else 0.007, 0.016, 0.007 if ang != 90 else 0.0035), 1)
plug = RK['mesh_obj']('Plug_L6-30P', bm, [M['black_mt'], BRASS], col, root)
RK['empty']('SOCKET_power_in', tuple(plug_c + V((0, 0.079, 0))), root, col, rot=(-math.pi / 2, 0, 0), kind='SINGLE_ARROW', size=0.03,
            props={'connector': 'NEMA L6-30P', 'volts': 208, 'amps': 30, 'cord_u_at_plug': 0.0})
cord['flow_direction'] = 'plug (u=0) -> PDU (u=flow_u_end)'

root['model'] = 'APC AP8941'; root['form'] = '0U vertical'; root['outlets'] = '21x C13 + 3x C19 (2 banks)'
root['dimensions_mm'] = '1791 L x 56 W x 44 D (approx, 2G family)'; root['input'] = '200/208 V 30 A 1-ph, NEMA L6-30P'

tris = RK['finish'](ROOT, BLEND, ROOT + '.glb')
RK['render']('rack_pdu_0u', {
    'full': ((1.2, -4.3, 1.15), (0, 0.05, 1.03), 40),
    'top': ((0.55, -0.75, 2.3), (0, 0.12, 1.92), 35),
    'nmc': ((0.07, -0.16, 0.86), (0, 0, 0.84), 50),
    'outlets': ((0.07, -0.16, 0.36), (0, 0, 0.32), 45),
    'back': ((-0.25, 0.6, 1.2), (0, 0.02, 1.0), 30),
}, 0.9, (0, 0, 0.9), floor_z=0.0)
