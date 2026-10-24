# Scaling Law

A free, open-source browser game about running an AI lab from 2017 to 2025: start in a garage with a
couple of gaming GPUs and grow into a liquid-cooled campus of rack-scale systems. Serve your model to
customers, train the next one, chase grants and funding rounds, go public, and keep the power and the
coolant flowing.

The goal is realism you can learn from: every piece of hardware is modelled from real photos and spec
sheets, and every number in the simulation comes from the real industry.

> Status: 3D asset production. The game itself (Three.js) has not started yet.

## What's here

```
blender/
  lib/hw.py                     shared modelling helpers (conventions documented in the header)
  lib/BRIEF_SERVERS_RACKS.md    conventions for servers, racks and datacenter assets
  scripts/*.py                  one re-runnable headless build script per asset
  *.blend                       source scenes
  export/*.glb                  game-ready exports (glTF 2.0)
  studio_template.blend         studio lighting used for previews
```

### Hardware ladder (2017-2025)

| Year | Consumer / workstation | Datacenter PCIe | SXM modules |
|---|---|---|---|
| 2017 | GTX 1080 Ti FE, Titan V | Tesla V100 PCIe | V100 SXM2 |
| 2018 | RTX 2080 Ti FE | | |
| 2020 | RTX 3090 FE | A100 PCIe | A100 SXM4 |
| 2022 | RTX 4090 FE | H100 PCIe | H100 SXM5 |
| 2023 | | L40S | |
| 2024 | MSI RTX 4070 Ti SUPER Ventus 3X | | H200 SXM, B200 SXM |
| 2025 | RTX 5090 FE, RTX PRO 6000 Blackwell | | GB200 Superchip |

### Machines and datacenter

- Garage: 2017 ATX tower, open-air 6-GPU frame
- Servers: Supermicro 4U 8x PCIe GPU, DGX-1 (V100), DGX A100, DGX H100/H200, DGX B200
- Rack scale: GB200 NVL72 (compute tray, NVLink switch tray, full rack)
- Rack kit: 42U cabinet, 0U PDU, InfiniBand switches (QM8700, QM9700), accessories, cable kit
- Data hall: overhead busway, fibre and wire-basket trays, hot-aisle containment, CRAH, in-row cooler, tiles
- Plant: liquid CDU, UPS + batteries, switchgear + PDU, pad-mount transformer, diesel generator,
  dry cooler, chiller

### Conventions the game relies on

- Servers and racks export **without** GPUs; empties named `SLOT_*` mark where the game instances
  the GPU/module GLBs.
- Every power and coolant path carries `SOCKET_*` empties at its ends and a mesh whose UV `u` runs in
  metres along the path (`flow_u_start` / `flow_u_end` exported as glTF extras), so a shader can
  animate electricity and coolant flowing from the grid to each GPU.
- Status lights are separate `LED_*` objects; fans are separate rotors.

## Rebuilding an asset

```
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b blender/studio_template.blend --python blender/scripts/<asset>.py
```

Built with Blender 5.2. Scripts use absolute Windows paths for now.

## License

- Code (scripts, helpers): MIT — see `LICENSE`.
- 3D assets (`.blend`, `.glb`): CC BY 4.0.
- Product names, logos and trademarks shown on the models (NVIDIA, GeForce, Tesla, MSI, Supermicro,
  APC, Schneider Electric, Vertiv, Eaton, Caterpillar, Carrier, Starline, Panduit, NZXT…) belong to
  their respective owners. They are reproduced only to depict the real hardware; this project is not
  affiliated with or endorsed by any of them.
