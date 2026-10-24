"""NVIDIA (Mellanox) Quantum QM8700 - 1U HDR 200Gb/s InfiniBand switch, 40x QSFP56 (2019/2020).

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python net_01_ib_quantum_qm8700.py

Sources: NVIDIA QM87xx user manual (networking-docs.nvidia.com/qm87xx/public-view/...):
  size 1.7" H x 17" W x 23.2" D = 43.6 x 433.2 x 590.6 mm, 19" rack mount, 40 QSFP56 cages,
  1+1 hot-swap PSUs, 5+1 hot-swap fans (6 fan modules on the rear).
  Front-view and rear-view drawings in the manual introduction: 2 rows x 20 cages in 4 groups of 5,
  odd ports on the top row ("1 ^v 2" printed between rows), management block at the right
  (status LEDs, USB, red reset button, 2 stacked RJ45 MGT/console), honeycomb-perforated face,
  "QM8700" bottom-left, Mellanox logo bottom-right.
Port pitch / row heights measured on that drawing (0.332 mm/px).
"""
import bpy, math, os, sys

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\rack_kit_lib.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\net_switch_lib.py', encoding='utf-8').read())
H = bpy.app.driver_namespace['HW']; RK = bpy.app.driver_namespace['RK']; NS = bpy.app.driver_namespace['NETSW']

ROOT = 'net_01_ib_quantum_qm8700'
BLEND = os.path.join(RK['BASE'], ROOT + '.blend')
root, col = H['new_card_scene'](ROOT)
mm = 0.001
W = 0.4332; xL = -W / 2
P = dict(
    name='QM8700', W=W, H=0.0436, D=0.5906, seam_y=0.24,
    port_type='QSFP56 (HDR 200Gb/s)',
    perf_pitch=0.0021,
    cage_open=(17.9 * mm, 8.2 * mm), cage_frame=(19.25 * mm, 11.0 * mm),
    row_z=(0.0004 + 28.7 * mm, 0.0004 + 15.6 * mm),
    group_z=(0.0004 + 8.6 * mm, 0.0004 + 35.7 * mm),
    ports_per_group=5, groups=4, port_pitch=19.25 * mm, group_pitch=100.2 * mm, group_border=1.5 * mm,
    x_first=xL + 2.98 * mm + 1.5 * mm,
    label_z=0.0004 + 22.15 * mm, led_dx=(-6.5 * mm, 0.8 * mm), num_dx=(-4.2 * mm, 3.4 * mm),
    cavity_depth=0.012,
    solid_panels=[(xL + 401.3 * mm, W / 2, 0.0004, 0.0440)],
    rj45=[(xL + 424.5 * mm, 0.0004 + 33.0 * mm), (xL + 424.5 * mm, 0.0004 + 21.0 * mm)],
    usb=(xL + 406.5 * mm, 0.0004 + 30.0 * mm, 7.0 * mm, 2.6 * mm),
    sys_leds=[('LED_sys_status', (xL + 404.0 * mm, 0.0004 + 38.6 * mm), 'g'), ('LED_sys_fan', (xL + 406.8 * mm, 0.0004 + 38.6 * mm), 'g'),
              ('LED_sys_psu1', (xL + 409.6 * mm, 0.0004 + 38.6 * mm), 'g'), ('LED_sys_psu2', (xL + 412.4 * mm, 0.0004 + 38.6 * mm), 'g'),
              ('LED_sys_uid', (xL + 414.0 * mm, 0.0004 + 6.0 * mm), 'o')],
    buttons=[('Btn_Reset', (xL + 406.5 * mm, 0.0004 + 22.8 * mm, 1.9 * mm), 'red')],
    texts=[('QM8700', (xL + 13.0 * mm, -0.0006, 0.0004 + 4.3 * mm), 2.6 * mm, 'white'),
           ('Mellanox', (xL + 421.0 * mm, -0.0006, 0.0004 + 5.0 * mm), 2.2 * mm, 'white')],
    psu_w=0.060, fans=6, latch_rgb=(0.02, 0.10, 0.55), fan_label_rgb=(0.02, 0.02, 0.02),
)
NS['build_switch'](P, root, col)
root['year'] = 2019
root['source'] = 'NVIDIA QM87xx 1U HDR InfiniBand Switch User Manual'

tris = RK['finish'](ROOT, BLEND, ROOT + '.glb')
C = (0, 0.25, 0.022)
RK['render']('net_01_qm8700', {
    'front': ((0, -0.75, 0.022), (0, 0, 0.022), 50),
    '34': ((-0.42, -0.55, 0.30), (0, 0.18, 0.022), 40),
    'ports': ((0.10, -0.14, 0.06), (0.12, 0, 0.022), 50),
    'mgmt': ((0.25, -0.09, 0.04), (0.19, 0, 0.022), 50),
    'rear': ((0.40, 1.15, 0.28), (0, 0.45, 0.022), 40),
}, 0.6, C, floor_z=0.0)
