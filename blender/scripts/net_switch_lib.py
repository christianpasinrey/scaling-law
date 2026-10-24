"""Builder for 1U fixed InfiniBand switches (NVIDIA Quantum QM8700 / Quantum-2 QM9700).

Load after hw.py + rack_kit_lib.py. Published as bpy.app.driver_namespace['NETSW'].

Frame: connector side = front, in the XZ plane at y=0 facing -Y; chassis depth toward +Y; origin bottom-front-
centre (rail plane, bottom of the U). 19" EIA-310 1U.
Port empties PORT_nn: at the centre of each cage opening on the front face; local +Z points OUT of the port
(-Y in switch space). Power inlets SOCKET_power_in_1/2: rear PSU inlets, local +Z points out (+Y).
"""
import bpy, bmesh, math, mathutils

H = bpy.app.driver_namespace['HW']; RK = bpy.app.driver_namespace['RK']
V = mathutils.Vector
mm = 0.001
OUT_FRONT = (math.pi / 2, 0, 0)     # local +Z -> -Y
OUT_REAR = (-math.pi / 2, 0, 0)     # local +Z -> +Y


def cavity(bm, x0, x1, z0, z1, y0, depth, mi):
    """Open box (no front face) going from y0 toward +Y, i.e. a recessed opening."""
    y1 = y0 + depth
    P = lambda x, y, z: bm.verts.new((x, y, z))
    quads = [((x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)),        # floor
             ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)),        # ceiling
             ((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)),        # left
             ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)),        # right
             ((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0))]        # back
    for q in quads:
        f = bm.faces.new([P(*p) for p in q]); f.material_index = mi


def plate_with_holes(bm, x0, x1, z0, z1, y, holes, mi, uv_tile=None, facing=-1):
    """Rectangle [x0,x1]x[z0,z1] minus axis-aligned holes [(hx0,hx1,hz0,hz1)], built from quads.
    Holes must not overlap; decomposition by z-bands then x-gaps."""
    zs = sorted({z0, z1} | {h[2] for h in holes} | {h[3] for h in holes})
    zs = [z for z in zs if z0 <= z <= z1]
    for za, zb in zip(zs[:-1], zs[1:]):
        zm = (za + zb) / 2
        cut = sorted((h[0], h[1]) for h in holes if h[2] <= zm <= h[3])
        xa = x0
        for hx0, hx1 in cut:
            if hx0 > xa + 1e-7:
                RK['add_quad_xz'](bm, xa, hx0, za, zb, y, mi, uv_tile, facing)
            xa = max(xa, hx1)
        if x1 > xa + 1e-7:
            RK['add_quad_xz'](bm, xa, x1, za, zb, y, mi, uv_tile, facing)


def tri_led(name, x, z, y, up, size, material, col, parent):
    bm = bmesh.new()
    s = size
    pts = [(-s / 2, -s * 0.43), (s / 2, -s * 0.43), (0, s * 0.43)] if up else [(-s / 2, s * 0.43), (0, -s * 0.43), (s / 2, s * 0.43)]
    v0 = [bm.verts.new((x + a, y, z + b)) for a, b in pts]
    v1 = [bm.verts.new((x + a, y + 0.0006, z + b)) for a, b in pts]
    bm.faces.new(v0); bm.faces.new(list(reversed(v1)))
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((v0[i], v0[j], v1[j], v1[i]))
    return RK['mesh_obj'](name, bm, [material], col, parent)


def led_box(name, c, s, material, col, parent):
    bm = bmesh.new(); RK['add_box'](bm, c, s, 0)
    return RK['mesh_obj'](name, bm, [material], col, parent)


def rj45(bm, xc, zc, y, mi_frame, mi_dark, mi_gold):
    w, h = 11.6 * mm, 9.0 * mm
    plate_with_holes(bm, xc - w / 2 - 1.2 * mm, xc + w / 2 + 1.2 * mm, zc - h / 2 - 1.2 * mm, zc + h / 2 + 1.2 * mm, y - 0.0010,
                     [(xc - w / 2, xc + w / 2, zc - h / 2, zc + h / 2)], mi_frame)
    cavity(bm, xc - w / 2, xc + w / 2, zc - h / 2, zc + h / 2, y - 0.0010, 0.012, mi_dark)
    for k in range(8):
        RK['add_box'](bm, (xc - 3.5 * mm + k * 1.0 * mm, y + 0.006, zc + h / 2 - 0.8 * mm), (0.45 * mm, 6 * mm, 0.4 * mm), mi_gold)
    return (xc - w / 2, xc + w / 2, zc - h / 2, zc + h / 2)


def build_switch(P, root, col):
    """P: dict of parameters (see net_01/net_02 scripts)."""
    M = H['base_materials'](); mat = H['mat']
    W, Hh, D = P['W'], P['H'], P['D']
    xL, xR = -W / 2, W / 2
    zb, zt = 0.0004, 0.0004 + Hh
    CHASSIS = mat('RK_SwChassis', (0.22, 0.225, 0.23), 0.85, 0.45)
    FRONT_PERF = RK['perf_material']('RK_SwFrontPerf', (0.035, 0.036, 0.04), 0.5, 0.5, see_through=False)
    FRONT_DARK = mat('RK_SwFrontBlack', (0.012, 0.012, 0.013), 0.4, 0.5, spec=0.3)
    CAGE = mat('RK_SwCage', P.get('cage_rgb', (0.30, 0.31, 0.32)), 0.9, 0.38)
    GOLD = M['gold']; DARK = mat('RK_PortCavity', (0.0015, 0.0015, 0.0015), 0.0, 1.0, spec=0.05)
    LED_G = mat('RK_LED_Green', (0.05, 0.6, 0.1), 0.0, 0.3, emit=(0.1, 1.0, 0.2), emit_str=3.0)
    LED_A = mat('RK_LED_Amber', (0.6, 0.35, 0.02), 0.0, 0.3, emit=(1.0, 0.55, 0.05), emit_str=3.0)
    LED_B = mat('RK_LED_Blue', (0.05, 0.2, 0.7), 0.0, 0.3, emit=(0.1, 0.3, 1.0), emit_str=3.0)
    LED_OFF = mat('RK_LED_Off', (0.08, 0.09, 0.08), 0.0, 0.25)
    WHITE = mat('RK_PrintWhite', (0.75, 0.75, 0.74), 0.0, 0.6)
    RED = mat('RK_ButtonRed', (0.6, 0.02, 0.02), 0.0, 0.4)
    LATCH = mat('RK_Latch_' + P['name'], P['latch_rgb'], 0.0, 0.45)
    LABEL = mat('RK_FanLabel_' + P['name'], P.get('fan_label_rgb', (0.02, 0.02, 0.02)), 0.0, 0.5)
    ptile = (P['perf_pitch'], P['perf_pitch'] * math.sqrt(3))

    # ------------------------------------------------ chassis
    bm = bmesh.new()
    y0 = P['cavity_depth'] + 0.002
    RK['add_box'](bm, (0, (D + y0) / 2, (zb + zt) / 2), (W, D - y0, Hh), 0)
    for zz in (zb + 0.0004, zt - 0.0004):                                   # front skin (top / bottom)
        RK['add_box'](bm, (0, y0 / 2, zz), (W, y0, 0.0008), 0)
    for sx in (-1, 1):
        RK['add_box'](bm, (sx * (W / 2 - 0.0004), y0 / 2, (zb + zt) / 2), (0.0008, y0, Hh), 0)
    # top-cover seam + side rail-kit studs
    RK['add_box'](bm, (0, P['seam_y'], zt + 0.0001), (W + 0.0002, 0.002, 0.0003), 1)
    for sx in (-1, 1):
        for yy in (0.10, D * 0.5, D - 0.08):
            RK['add_cyl'](bm, (sx * (W / 2 + 0.0015), yy, Hh / 2), 0.003, 0.003, 'X', 12, 2)
    RK['mesh_obj']('Chassis', bm, [CHASSIS, DARK, M['steel']], col, root)

    # ------------------------------------------------ ears (front, flush with the front plate)
    bm = bmesh.new()
    for sx in (-1, 1):
        RK['add_box'](bm, (sx * (W / 2 + 0.01235), 0.0012, (zb + zt) / 2), (0.0247, 0.0024, Hh), 0)
        RK['add_box'](bm, (sx * (W / 2 + 0.001), 0.012, (zb + zt) / 2), (0.002, 0.022, Hh - 0.004), 0)
        for zz in (0.0064, 0.0381):
            RK['add_cyl'](bm, (sx * 0.23255, -0.0006, zz), 0.0035, 0.0024, 'Y', 12, 1)
    RK['mesh_obj']('Ears', bm, [FRONT_DARK, M['steel']], col, root)

    # ------------------------------------------------ ports
    cw, ch = P['cage_open']          # opening w, h
    fw, fh = P['cage_frame']         # frame outer w, h
    zc_top, zc_bot = P['row_z']
    nper = P['ports_per_group']; ngr = P['groups']
    yF = -0.0014                      # front face of the cage block
    holes_plate = []                  # cut-outs in the perforated plate
    group_holes = []
    port_xs = []
    for g in range(ngr):
        gx0 = P['x_first'] + g * P['group_pitch']
        gx_l = gx0 - P['group_border']
        gx_r = gx0 + (nper - 1) * P['port_pitch'] + fw + P['group_border']
        holes_plate.append((gx_l, gx_r, P['group_z'][0], P['group_z'][1]))
        for i in range(nper):
            x = gx0 + i * P['port_pitch'] + fw / 2
            port_xs.append(x)
            for zc in (zc_top, zc_bot):
                group_holes.append((x - cw / 2, x + cw / 2, zc - ch / 2, zc + ch / 2))
    # perforated front plate (with holes where the cage blocks and side panels sit)
    bm = bmesh.new()
    for hx in P['solid_panels']:
        holes_plate.append(hx)
    plate_with_holes(bm, xL, xR, zb, zt, -0.0003, holes_plate, 0, ptile)
    RK['mesh_obj']('Front_Perf', bm, [FRONT_PERF], col, root)
    # solid side panels (management area)
    ux, uz, uw, uh = P['usb']
    mg_holes = [(xc - 5.8 * mm, xc + 5.8 * mm, zc - 4.5 * mm, zc + 4.5 * mm) for (xc, zc) in P['rj45']]
    mg_holes.append((ux - uw / 2, ux + uw / 2, uz - uh / 2, uz + uh / 2))
    bm = bmesh.new()
    for (a, b, c, d) in P['solid_panels']:
        plate_with_holes(bm, a, b, c, d, -0.0004, [h for h in mg_holes if a <= h[0] <= b], 0)
    RK['mesh_obj']('Front_Panels', bm, [FRONT_DARK], col, root)
    # cage blocks: metal face with openings + recessed cavities + contact tongue
    bm = bmesh.new()
    for (gx_l, gx_r, gz0, gz1) in holes_plate[:ngr]:
        hs = [h for h in group_holes if gx_l <= h[0] <= gx_r]
        plate_with_holes(bm, gx_l, gx_r, gz0, gz1, yF, hs, 0)
        # block sides (thickness to the plate)
        RK['add_box'](bm, ((gx_l + gx_r) / 2, (yF - 0.0003) / 2, gz0 + 0.0002), (gx_r - gx_l, -yF + 0.0003, 0.0004), 0)
        RK['add_box'](bm, ((gx_l + gx_r) / 2, (yF - 0.0003) / 2, gz1 - 0.0002), (gx_r - gx_l, -yF + 0.0003, 0.0004), 0)
    for (x0, x1, z0, z1) in group_holes:
        cavity(bm, x0, x1, z0, z1, yF, P['cavity_depth'], 1)
        # card-edge tongue (PCB with gold fingers)
        xm = (x0 + x1) / 2; zm = (z0 + z1) / 2
        RK['add_box'](bm, (xm, P['cavity_depth'] * 0.75, zm), ((x1 - x0) * 0.6, P['cavity_depth'] * 0.5, 0.0011), 2)
        RK['add_box'](bm, (xm, P['cavity_depth'] * 0.55, zm), ((x1 - x0) * 0.5, 0.0012, 0.00116), 3)
    RK['mesh_obj']('Cage_Blocks', bm, [CAGE, DARK, M['pcb'], GOLD], col, root)

    # port empties, LEDs, labels
    n = 0
    labels = []
    for c, x in enumerate(port_xs):
        for row, zc in enumerate((zc_top, zc_bot)):
            n = 2 * c + row + 1           # top row odd, bottom row even (as printed: "1 ^v 2")
            RK['empty'](f'PORT_{n:02d}', (x, yF - 0.0002, zc), root, col, rot=OUT_FRONT, kind='SINGLE_ARROW', size=0.012,
                        props={'port_type': P['port_type'], 'port_index': n})
        zl = P['label_z']
        tri_led(f'LED_port_{2 * c + 1:02d}', x + P['led_dx'][0], zl, yF - 0.0007, True, 0.0016, LED_G, col, root)
        tri_led(f'LED_port_{2 * c + 2:02d}', x + P['led_dx'][1], zl, yF - 0.0007, False, 0.0016, LED_G, col, root)
        labels.append(RK['text_flat'](f'lbl_{c}a', f'{2 * c + 1}', 0.0017, (x + P['num_dx'][0], yF - 0.0002, zl), (math.pi / 2, 0, 0), WHITE, col, root, font=RK['FONT_REG']))
        labels.append(RK['text_flat'](f'lbl_{c}b', f'{2 * c + 2}', 0.0017, (x + P['num_dx'][1], yF - 0.0002, zl), (math.pi / 2, 0, 0), WHITE, col, root, font=RK['FONT_REG']))
    for txt, loc, size, m in P['texts']:
        labels.append(RK['text_flat']('txt', txt, size, loc, (math.pi / 2, 0, 0), {'white': WHITE, 'green': mat('RK_NvGreen', (0.28, 0.6, 0.0), 0.0, 0.5)}[m], col, root))
    RK['join'](labels, 'Front_Print')

    # management area: LEDs, buttons, USB, RJ45
    bm = bmesh.new()
    for (xc, zc) in P['rj45']:
        rj45(bm, xc, zc, -0.0004, 0, 1, 2)
    plate_with_holes(bm, ux - uw / 2 - 0.0008, ux + uw / 2 + 0.0008, uz - uh / 2 - 0.0008, uz + uh / 2 + 0.0008, -0.0012,
                     [(ux - uw / 2, ux + uw / 2, uz - uh / 2, uz + uh / 2)], 0)
    cavity(bm, ux - uw / 2, ux + uw / 2, uz - uh / 2, uz + uh / 2, -0.0012, 0.008, 1)
    if uh > uw:   # vertical USB-A
        RK['add_box'](bm, (ux - uw * 0.15, 0.002, uz), (uw * 0.3, 0.006, uh * 0.7), 3)
    else:
        RK['add_box'](bm, (ux, 0.002, uz - uh * 0.15), (uw * 0.7, 0.006, uh * 0.3), 3)
    RK['mesh_obj']('Mgmt_Ports', bm, [CAGE, DARK, GOLD, mat('RK_USBBlue', (0.05, 0.12, 0.45), 0.0, 0.4)], col, root)
    for nm, (x, z), m in P['sys_leds']:
        led_box(nm, (x, -0.0007, z), (0.0018, 0.0012, 0.0012), {'g': LED_G, 'a': LED_A, 'b': LED_B, 'o': LED_OFF}[m], col, root)
    for nm, (x, z, r), m in P['buttons']:
        bm = bmesh.new(); RK['add_cyl'](bm, (x, -0.0008, z), r, 0.0016, 'Y', 16, 0)
        RK['mesh_obj'](nm, bm, [{'red': RED, 'grey': M['steel'], 'blue': LED_B}[m]], col, root)

    # ------------------------------------------------ rear: PSUs + fans
    yR = D
    psu_w, fan_n = P['psu_w'], P['fans']
    fan_w = (W - 2 * psu_w - 0.004) / fan_n
    bm_f = bmesh.new(); bm_d = bmesh.new()
    REAR_PERF = RK['perf_material']('RK_FanGrille', (0.04, 0.04, 0.045), 0.5, 0.5, see_through=False)
    # fans: hex grille face + hub disc + latch
    for i in range(fan_n):
        x0 = xL + psu_w + 0.002 + i * fan_w
        xc = x0 + fan_w / 2
        RK['add_quad_xz'](bm_f, x0 + 0.0008, x0 + fan_w - 0.0008, zb + 0.001, zt - 0.001, yR + 0.0004, 0, (0.004, 0.004 * math.sqrt(3)), facing=1)
        RK['add_cyl'](bm_d, (xc - 0.003, yR + 0.0010, (zb + zt) / 2), 0.0085, 0.0012, 'Y', 20, 0)
        RK['add_box'](bm_d, (x0 + fan_w - 0.006, yR + 0.003, (zb + zt) / 2), (0.006, 0.006, 0.022), 1)     # latch
        RK['add_box'](bm_d, ((x0 + xc) / 2 + 0.004, yR + 0.0009, zt - 0.006), (fan_w * 0.6, 0.0008, 0.006), 4)  # label band
        RK['add_box'](bm_d, (x0 + 0.0005, yR + 0.001, (zb + zt) / 2), (0.001, 0.002, Hh - 0.002), 0)      # divider
        led_box(f'LED_fan_{i + 1}', (x0 + fan_w - 0.006, yR + 0.0010, zb + 0.005), (0.0018, 0.0012, 0.0014), LED_G, col, root)
    # PSUs: face, C14 inlet, handle, latch, LED
    for k, sx in enumerate((-1, 1)):
        x0 = xL + 0.001 if sx < 0 else xR - psu_w - 0.001
        xc = x0 + psu_w / 2
        RK['add_box'](bm_d, (xc, yR + 0.0006, (zb + zt) / 2), (psu_w - 0.001, 0.0012, Hh - 0.002), 2)
        ix = xc + sx * 0.008
        RK['add_box'](bm_d, (ix, yR + 0.004, (zb + zt) / 2 + 0.002), (0.030, 0.007, 0.0235), 3)       # inlet boss
        RK['add_box'](bm_d, (ix, yR + 0.0078, (zb + zt) / 2 + 0.002), (0.0245, 0.0006, 0.0165), 6)    # inlet cavity look
        for px, pz in ((-0.007, 0.004), (0.007, 0.004), (0, -0.003)):
            RK['add_box'](bm_d, (ix + px, yR + 0.0072, (zb + zt) / 2 + 0.002 + pz), (0.0016, 0.004, 0.005), 5)
        hx = xc - sx * 0.017
        RK['add_box'](bm_d, (hx, yR + 0.010, (zb + zt) / 2), (0.003, 0.018, 0.028), 5)                 # handle
        RK['add_box'](bm_d, (hx, yR + 0.019, (zb + zt) / 2), (0.006, 0.003, 0.028), 5)
        RK['add_box'](bm_d, (xc - sx * 0.006, yR + 0.003, zb + 0.008), (0.010, 0.005, 0.006), 1)        # latch
        led_box(f'LED_psu_{k + 1}', (xc - sx * 0.008, yR + 0.0014, zt - 0.007), (0.0022, 0.0012, 0.0022), LED_G, col, root)
        RK['empty'](f'SOCKET_power_in_{k + 1}', (ix, yR + 0.0075, (zb + zt) / 2 + 0.002), root, col, rot=OUT_REAR,
                    kind='SINGLE_ARROW', size=0.02, props={'connector': 'IEC C14 inlet', 'psu': k + 1})
    RK['mesh_obj']('Rear_Grilles', bm_f, [REAR_PERF], col, root)
    RK['mesh_obj']('Rear_Modules', bm_d, [M['black_mt'], LATCH, FRONT_DARK, M['plastic'], LABEL, M['steel'], DARK], col, root)
    root['model'] = P['name']; root['rack_units'] = 1; root['mount'] = '19in EIA-310'
    root['ports'] = len(port_xs) * 2; root['port_type'] = P['port_type']
    root['dimensions_mm'] = f"{W * 1000:.1f} W x {Hh * 1000:.1f} H x {D * 1000:.1f} D"


NETSW = dict(build_switch=build_switch)
bpy.app.driver_namespace['NETSW'] = NETSW
