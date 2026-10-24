"""NVIDIA DGX B200 (2024-2025), 10U air-cooled, 8x B200 SXM + 2x NVLink 5 switch chips (HGX B200 8-GPU).

Run headless:
  blender.exe -b C:\laragon\www\scaling-law\blender\studio_template.blend --python srv_05_dgx_b200.py

Sources: NVIDIA DGX B200 User Guide, "Introduction to NVIDIA DGX B200 Systems"
(docs.nvidia.com/dgx/dgxb200-user-guide/introduction-to-dgxb200.html): 10U, H 444 mm, W 482.3 mm,
D 897.1 mm, 142.4 kg, 6x 3.3 kW PSU (5+1), 20 fan modules, 8x U.2 + console, 4 twin-port OSFP,
2x BlueField-3. DGX B200 Service Manual "Front Fan Module Replacement" (front view with module IDs
1-1..4-5, dual F/R fan module drawing). Positions measured in px off those drawings (~0.325 mm/px
front, ~1.05 mm/px rear). Geometry is built by dgx_lib.build().
"""
import os
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\dgx_lib.py', encoding='utf-8').read())

CFG = dict(
    root='DGX_B200', model='NVIDIA DGX B200', units=10,
    dims_note='H 444 x W 482.3 x D 897.1 (spec); body 445 W x 850 D, bezel 34, rear handles 13',
    blend=BASE + r'\srv_05_dgx_b200.blend', glb=BASE + r'\export\srv_05_dgx_b200.glb', render_prefix='srv_05_dgx_b200',
    module_blend=BASE + r'\gpu_14a_b200_sxm.blend', module_root='B200_SXM', module_lw=(0.205, 0.103), mezz_h=0.006,
    height=0.444,
    ear_screws=(0.4046, 0.287, 0.154, 0.0367), button_z=(0.365, 0.345, 0.326),
    fan_cols=5, fan_rows=4, fan_w=0.084, fan_h=0.083, fan_pitch_x=0.0865, fan_pitch_z=0.0885, fan_z0=0.086,
    fan_hex=0.0055, fan_handle='black', fan_handle_w=0.012, fan_ticks=True,
    drive_z0=0.0098, drive_h=0.0158, drive_w=0.076, drive_x=(-0.1685, -0.0878, 0.0874, 0.1673), console=(0.0, 0.090),
    logo_band=(0.052, 0.078, -0.170, -0.105, 22, 0.022),
    psu_w=0.069, psu_h=0.042, psu_d=0.30, psu_pitch=0.0735,
    mid_y=0.160,
    gpu_tray_z=(0.141, 0.444), mb_tray_z=(0.049, 0.139),
    baseboard_y=(0.190, 0.80), baseboard_z=0.150,
    gpu_y=(0.331, 0.603), gpu_x=(-0.156, -0.052, 0.052, 0.156),
    nvswitch=[], nvswitch_cover=(0.0, 0.467, 0.405, 0.060, 0.105),
    shroud_h=0.06, cpu_hs_h=0.064,
    gpu_rear_baffle=(0.376, 0.428), gpu_thumb_dz=0.026, slot1_rj45=True,
    bezel='b200',
)
run(CFG, default_views(CFG))
