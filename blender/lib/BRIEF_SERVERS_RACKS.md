# Brief: servers, racks and datacenter kit (phase 2)

Free open-source browser game (Three.js) about running an AI lab 2017-2025. Phase 1 modelled every GPU
card/module. Phase 2 models the machines and the datacenter they live in. Everything must look like the real
thing (measure from photos/spec sheets) but stay light enough for a browser.

## Tools and hard rules
- Blender: `"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"`, **headless only**:
  `blender.exe -b C:\laragon\www\scaling-law\blender\studio_template.blend --python <script.py>` (~7 s per render).
  NEVER use `mcp__blender__*` tools (they drive the user's live Blender; other agents run in parallel).
- Helper library: `C:\laragon\www\scaling-law\blender\lib\hw.py` — read it fully. Do not modify it; put extra
  helpers in your own script (or a `scripts/<yourarea>_lib.py`). Use `H['cut']` for booleans (it probes solvers),
  `H['apply_all']` for modifiers. `prism` on concave outlines can fill the convex hull: build concave shapes from
  strips and verify in a render.
- Research: WebSearch/WebFetch; download reference photos with curl into your own new folder under
  `C:\Users\chris\AppData\Local\Temp\claude\C--laragon-www\3a063f4a-aa59-413e-a508-728b3cde4e03\scratchpad\refs\<area>\`
  and look at them with the Read tool. Good sources: ServeTheHome, NVIDIA docs/user guides (they include
  dimension tables and component diagrams), Supermicro/Dell/HPE/Vertiv/Schneider/APC spec sheets, Wikimedia.
- One re-runnable build script per asset in `C:\laragon\www\scaling-law\blender\scripts\`, saving
  `C:\laragon\www\scaling-law\blender\<file>.blend`, exporting `...\blender\export\<file>.glb` (`H['export_glb']`)
  and rendering previews to `...\blender\renders\<file>_<view>.png` (1280x720; create cameras in-script and
  reframe for the object size; the template camera/lights are sized for a ~30 cm card — scale/move them).
- Iterate: compare renders with photos, fix, re-run (5-10 iterations). Verify text orientation in renders.

## Conventions
- Metres, Z up.
- **Rack-mount equipment** (servers, switches, PDUs-in-U, power shelves): front panel in the XZ plane at y=0
  facing -Y, chassis depth toward +Y. Origin = bottom-front-centre. Width: 19" ears 482.6 mm, body ≤ 449 mm.
  1U = 44.45 mm. OCP/ORv3 gear: 21" rack, OU = 48 mm — note which standard you use.
- **Rack cabinets**: origin = floor, front-centre, front face at y=0 facing -Y. Add empties `SLOT_U01`…`SLOT_Unn`
  at each U position (bottom of the U, front rail plane) so the game can mount equipment.
- **Room/infrastructure items**: origin at floor centre of the footprint; note the footprint in the report.
- **Reuse phase-1 assets, never remodel them.** Cards/modules live in `C:\laragon\www\scaling-law\blender\gpu_*.blend`
  (each has a root empty, e.g. `A100_SXM4`, `H100_SXM5`, `B200_SXM`, `GB200_Superchip`, `V100_SXM2`, `A100_PCIe`,
  `H100_PCIe`, `L40S`, `Tesla V100 = TeslaV100_PCIe`, consumer cards `GTX1080Ti_FE`, `RTX3090_FE`, …). Append them
  with `bpy.data.libraries.load(path, link=False)` (collections/objects) for preview renders.
- **Export strategy for the game**: the exported .glb of a server/rack must NOT contain the GPUs. Instead add
  empties `SLOT_gpu_0`…`SLOT_gpu_N` (and `SLOT_cpu_*`, `SLOT_psu_*`, `SLOT_tray_*`, `SLOT_U*` as relevant) at the
  exact mount pose (location + rotation) where the game will instance the phase-1 GLB. Renders should show the
  assembled machine (appended assets) so we can judge it; delete/hide the appended assets before exporting.
- **Energy and coolant flow are a core visual of the game.** Every power path (PSU inlets, power cords, PDU
  outlets, busbars, busway, cables) and coolant path (hoses, manifolds, CDU pipes) gets:
  - an empty `SOCKET_power_in` / `SOCKET_power_out_*` / `SOCKET_coolant_in` / `SOCKET_coolant_out` at each end;
  - cables/hoses/busbars built as curves converted to mesh with **UV u = metres along the path, continuous**,
    v = 0-1 around/across, and custom props `flow_u_start`, `flow_u_end` (a shader will animate pulses along u).
- Status LEDs: separate small emissive objects named `LED_*` (the game drives their colour from simulation state).
- Budgets: a server ≤ ~120k triangles without GPUs; a rack shell ≤ ~40k; room items ≤ ~60k each. Use one merged
  mesh per repetitive pattern (`slat_array`), not hundreds of objects.
- Real brand names/logos as text are allowed (user decision).

## Report back (concise)
Files, triangle counts, .glb sizes, real dimensions used (with source), the slot/socket list, what was verified
against which photo, what is approximate, source URLs, best render paths.
