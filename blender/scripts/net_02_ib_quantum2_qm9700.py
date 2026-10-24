"""NVIDIA Quantum-2 QM9700 - 1U NDR 400Gb/s InfiniBand switch, 32x OSFP cages = 64 NDR ports (2022).

Run headless:
  blender.exe -b C:\laragon\www\scaling-law\blender\studio_template.blend --python net_02_ib_quantum2_qm9700.py

Sources: NVIDIA QM97XX user manual (networking-docs.nvidia.com/qm97x0hw):
  Specifications: 17.2" x 1.7" x 26" = 438 W x 43.6 H x 660 D mm, 19" rack mount, 32 OSFP cages,
  1x/2x 200-240 Vac 10 A PSUs, 7 replaceable fans; front USB 3.0 type A, 1x MGT RJ45, console.
  Introduction: front-view drawing (2 rows x 16 OSFP cages in 4 groups of 4, "1 ^v 2" printed between the
  rows, left strip with UID button + LED, right block: status LEDs, vertical USB-A, 2 stacked RJ45,
  NVIDIA logo) and rear-view drawing (PSU at each end with IEC inlet, 7 fan modules between).
Pitches measured on the drawing (0.267 mm/px). Each OSFP cage carries 2 NDR ports (twin-port 2x400G
module); PORT_nn empties are per cage (nn = cage number 1..32).
"""
import bpy, math, os, sys

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\rack_kit_lib.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\net_switch_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']; RK = bpy.app.driver_namespace['RK']; NS = bpy.app.driver_namespace['NETSW']

ROOT = 'net_02_ib_quantum2_qm9700'
BLEND = os.path.join(RK['BASE'], ROOT + '.blend')
root, col = H['new_card_scene'](ROOT)
mm = 0.001
W = 0.438; xL = -W / 2
z0 = 0.0004
P = dict(
    name='QM9700', W=W, H=0.0436, D=0.660, seam_y=0.30,
    port_type='OSFP (2x NDR 400Gb/s per cage)',
    perf_pitch=0.0018,
    cage_open=(22.7 * mm, 13.0 * mm), cage_frame=(23.5 * mm, 15.0 * mm), cage_rgb=(0.42, 0.43, 0.44),
    row_z=(z0 + 31.85 * mm, z0 + 12.2 * mm),
    group_z=(z0 + 4.4 * mm, z0 + 39.6 * mm),
    ports_per_group=4, groups=4, port_pitch=23.5 * mm, group_pitch=97.3 * mm, group_border=0.4 * mm,
    x_first=xL + 13.6 * mm + 0.4 * mm,
    label_z=z0 + 21.8 * mm, led_dx=(-1.3 * mm, 1.3 * mm), num_dx=(-6.0 * mm, 6.0 * mm),
    cavity_depth=0.016,
    solid_panels=[(xL, xL + 13.4 * mm, z0, z0 + 43.6 * mm), (xL + 399.6 * mm, W / 2, z0, z0 + 43.6 * mm)],
    rj45=[(xL + 427.4 * mm, z0 + 35.6 * mm), (xL + 427.4 * mm, z0 + 23.6 * mm)],
    usb=(xL + 411.5 * mm, z0 + 31.5 * mm, 5.0 * mm, 12.5 * mm),
    sys_leds=[('LED_sys_status', (xL + 404.0 * mm, z0 + 38.5 * mm), 'g'), ('LED_sys_fan', (xL + 404.0 * mm, z0 + 35.6 * mm), 'g'),
              ('LED_sys_psu', (xL + 404.0 * mm, z0 + 32.7 * mm), 'g'), ('LED_sys_health', (xL + 404.0 * mm, z0 + 29.8 * mm), 'g'),
              ('LED_sys_mgt_link', (xL + 404.0 * mm, z0 + 17.0 * mm), 'g'),
              ('LED_sys_uid', (xL + 6.8 * mm, z0 + 25.5 * mm), 'b')],
    buttons=[('Btn_UID', (xL + 6.8 * mm, z0 + 15.5 * mm, 2.2 * mm), 'grey'), ('Btn_Reset', (xL + 404.0 * mm, z0 + 12.0 * mm, 1.4 * mm), 'grey')],
    texts=[('NVIDIA', (xL + 427.4 * mm, -0.0006, z0 + 8.0 * mm), 3.2 * mm, 'green')],
    psu_w=0.058, fans=7, latch_rgb=(0.02, 0.02, 0.022), fan_label_rgb=(0.36, 0.30, 0.04),
)
NS['build_switch'](P, root, col)
root['year'] = 2022
root['source'] = 'NVIDIA QM97XX 1U NDR 400Gbps InfiniBand Switch Systems User Manual'

tris = RK['finish'](ROOT, BLEND, ROOT + '.glb')
C = (0, 0.28, 0.022)
RK['render']('net_02_qm9700', {
    'front': ((0, -0.75, 0.022), (0, 0, 0.022), 50),
    '34': ((-0.42, -0.55, 0.30), (0, 0.2, 0.022), 40),
    'ports': ((0.10, -0.14, 0.06), (0.12, 0, 0.022), 50),
    'mgmt': ((0.25, -0.09, 0.04), (0.19, 0, 0.022), 50),
    'rear': ((0.40, 1.25, 0.28), (0, 0.5, 0.022), 40),
}, 0.6, C, floor_z=0.0)
