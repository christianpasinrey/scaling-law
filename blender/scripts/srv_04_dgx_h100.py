"""NVIDIA DGX H100 / H200 (2022-2024), 8U air-cooled, 8x H100 SXM5 + 4x NVSwitch (HGX H100 8-GPU).

Run headless:
  blender.exe -b C:\laragon\www\scaling-law\blender\studio_template.blend --python srv_04_dgx_h100.py
  (optional env DGX_VIEWS=front,rear to render a subset)

Sources: NVIDIA DGX H100/H200 User Guide, "Introduction to the NVIDIA DGX H100 System"
(docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html): 8U, H 356 mm, W 482.3 mm,
D 897.1 mm, 130.45 kg, 6x 3.3 kW PSU (4+2), 12 fan modules, 8x U.2 + front console, rear GPU tray /
motherboard tray / PSUs, 4 twin-port OSFP. Positions below are measured in px off the guide's
front-view, rear-panel-modules and port-view drawings (scale ~0.39-0.41 mm/px) and the GPU tray /
motherboard tray component images. Geometry is built by dgx_lib.build().
"""
import os
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\dgx_lib.py', encoding='utf-8').read())

CFG = dict(
    root='DGX_H100', model='NVIDIA DGX H100 / H200', units=8,
    dims_note='H 356 x W 482.3 x D 897.1 (spec); body 445 W x 850 D, bezel 34, rear handles 13',
    blend=BASE + r'\srv_04_dgx_h100.blend', glb=BASE + r'\export\srv_04_dgx_h100.glb', render_prefix='srv_04_dgx_h100',
    module_blend=BASE + r'\gpu_13a_h100_sxm5.blend', module_root='H100_SXM5', module_lw=(0.150, 0.079), mezz_h=0.0069,
    height=0.356,
    ear_screws=(0.316, 0.182, 0.036), button_z=(0.278, 0.258, 0.238),
    fan_cols=4, fan_rows=3, fan_w=0.096, fan_h=0.094, fan_pitch_x=0.104, fan_pitch_z=0.100, fan_z0=0.047,
    fan_hex=0.0075, fan_handle='champ', fan_handle_w=0.014, fan_ticks=False,
    drive_z0=0.009, drive_h=0.0165, drive_w=0.075, drive_x=(-0.1677, -0.0883, 0.0867, 0.1660), console=(0.0, 0.088),
    logo_band=None,
    psu_w=0.069, psu_h=0.042, psu_d=0.30, psu_pitch=0.0735,
    mid_y=0.245,
    gpu_tray_z=(0.143, 0.356), mb_tray_z=(0.046, 0.137),
    baseboard_y=(0.272, 0.80), baseboard_z=0.152,
    gpu_y=(0.425, 0.580), gpu_x=(-0.123, -0.041, 0.041, 0.123),
    nvswitch=[(x, 0.705, 0.074, 0.074, 0.072) for x in (-0.123, -0.041, 0.041, 0.123)], nvswitch_cover=None,
    shroud_h=0.06, cpu_hs_h=0.064,
    gpu_rear_baffle=(0.290, 0.338), gpu_thumb_dz=0.024, slot1_rj45=False,
    bezel='h100',
)
CFG['views'] = None
run(CFG, default_views(CFG))
