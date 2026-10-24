"""NVIDIA H200 SXM (2024): same SXM5 board, GH100-class package with 6 HBM3e stacks (141 GB) and the same
NVIDIA HGX air-cooled heatsink. Everything is built by gpu_13a_h100_sxm5.py in library mode; only the
data that is visibly different is overridden here.

Visible differences found in photos (ServeTheHome, Supermicro SYS-821GE-TNHR / ASRock Rack 6U8X-EGS2):
  - heatsink shelf label reads 'H200 SXM5 141GB HBM3e AC', 'FRU: 965-2G520-0040-000', 'NVIDIA S/N: 1652...'
  - champagne top plate, NVIDIA logo, smoked end blocks and copper captive screws: identical to HGX H100
    (compare Gigabyte G593-SD0 HGX H100 tray photo).
  - bare module: same SXM5 PCB/footprint and 6-stack package; die marking/lot code not photographed -> generic.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python gpu_13b_h200_sxm.py
"""
import os

SXM_LIBRARY_MODE = True
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\gpu_13a_h100_sxm5.py', encoding='utf-8').read())

CFG_H200 = dict(
    CFG_H100,
    root='H200_SXM',
    blend=os.path.join(BLEND_DIR, 'gpu_13b_h200_sxm.blend'),
    glb=os.path.join(BLEND_DIR, 'export', 'gpu_h200_sxm.glb'),
    render_prefix='h200_sxm',
    die_lines=['NVIDIA'],          # lot code not photographed for H200
    pcb_pn='',
    label_top='H200 SXM5 141GB HBM3e AC',
    label_fru='FRU: 965-2G520-0040-000',
    label_sn='S/N: 1652224000000',
)

build(CFG_H200)
