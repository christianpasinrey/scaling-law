# 01 — AI Lab Hardware Progression Ladder (research, as of 2026-10-24)

Purpose: factual data to (a) model each item in Blender for a Three.js browser game and (b) drive game numbers (compute, memory, power, heat, cost, failures).

## Conventions and caveats

- **Throughput** is given as **dense** Tensor-core TFLOPS/PFLOPS unless marked "sparse". Vendors usually headline the *sparse* figure (2x dense). For gameplay, use dense.
- Consumer GeForce FP16 figures depend on accumulate mode (FP16 vs FP32 accumulate, 2x difference); the number given is the FP16-accumulate figure from NVIDIA's whitepapers and is marked.
- **Prices** are highly volatile in 2026: a GDDR7/DRAM/HBM shortage pushed consumer and workstation cards well above MSRP, and datacenter parts are sold mostly in system/rack bundles through OEMs. Treat every price as an order of magnitude.
- **(unverified)** = figure from memory or a single low-quality source that I could not confirm against a vendor document in this session.
- Release year = first general availability (not announcement) where known.

---

## Tier 1 — Garage (consumer GPUs, desktops, open mining frames)

| Item | Year | Memory | Bandwidth | FP16 / FP8 / FP4 (dense) | Power | Form factor / size | Weight | Cooling | Price |
|---|---|---|---|---|---|---|---|---|---|
| GeForce RTX 3090 (Ampere) | 2020 | 24 GB GDDR6X | 936 GB/s | ~142 TF FP16 (FP16-acc; 71 with FP32-acc) / no FP8 / no FP4 | 350 W | 3-slot, FE 313 x 138 x 61 mm | ~2.19 kg (FE) | Air, flow-through 2 fans | $1,499 MSRP; used ~$700–1,000 (unverified) |
| GeForce RTX 4090 (Ada) | 2022 | 24 GB GDDR6X | 1,008 GB/s | ~330 TF FP16 (FP16-acc) / ~660 TF FP8 / no FP4 | 450 W | 3-slot, FE 304 x 137 x 61 mm | ~2.19 kg (FE) | Air, flow-through 2 fans | $1,599 MSRP; street 2026 above MSRP (unverified) |
| GeForce RTX 5090 (Blackwell) | Jan 2025 | 32 GB GDDR7 | 1,792 GB/s | ~419 TF FP16 (unverified) / ~838 TF FP8 (unverified) / 3,352 "AI TOPS" FP4 **sparse** | 575 W | **2-slot** FE 304 x 137 x 48 mm | ~1.8 kg (unverified) | Air, double flow-through, liquid-metal TIM | $1,999 MSRP; **2026 street $2,400–4,000 US, >€5,000 EU** ([guru3d](https://www.guru3d.com/story/geforce-rtx-5090-street-prices-in-eu-now-exceed/), [shopback guide](https://www.shopback.com/blog/electronics/rtx-5090-vs-rtx-5080-vs-rx-9070-xt-us-2026-holiday-buy-guide)) |
| NVIDIA DGX Spark (GB10 Grace Blackwell mini-PC) | Oct 2025 | 128 GB LPDDR5X unified | ~273 GB/s (unverified) | ~1 PFLOP FP4 **sparse** | ~240 W PSU (unverified) | 150 x 150 x 50.5 mm desktop box (unverified) | ~1.2 kg (unverified) | Air | $3,999 at launch (unverified) |
| Desktop tower host (e.g. ATX full tower, Ryzen/Threadripper) | — | 64–256 GB DDR5 | — | — | 1,000–1,600 W PSU | ~230 x 500 x 550 mm | 12–20 kg | Air / AIO | $1.5–4k excluding GPU (estimate) |
| Open-air mining-style frame (6–8 GPUs on PCIe riser cables) | 2017+ | per GPU | — | per GPU | 2–4 kW, needs 2–3 PSUs, 240 V circuit | aluminum extrusion ~650 x 400 x 300 mm (typical, unverified) | ~5 kg frame | Air (box fans) | $100–300 frame |

Notes and sources:
- RTX 5090 price drivers: Nvidia raised board-partner prices ~$300 in May 2026 citing GDDR7 cost (~+40% since late 2025) ([buysellram](https://www.buysellram.com/blog/why-rtx-5090-prices-keep-climbing-nvidias-wholesale-hike-and-the-gddr7-shortage-behind-it/), [mp1st](https://mp1st.com/?p=307222)). Spec page: https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/
- RTX 4090: https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/ ; RTX 3090: https://www.nvidia.com/en-us/geforce/graphics-cards/30-series/rtx-3090-3090ti/
- DGX Spark: https://www.nvidia.com/en-us/products/workstations/dgx-spark/

**Visual description (modeling):**
- **RTX 3090 FE**: matte dark-gray + silver aluminum "X" frame shroud, one fan on front (bottom side) and one fan on the back (top side) pushing through a cut-away PCB; illuminated "GEFORCE RTX" side logo (white LED); 12-pin power connector mounted at an angle mid-card; 3 DP + 1 HDMI bracket.
- **RTX 4090 FE**: same language but bigger: dark gunmetal shroud, silver frame, two 115 mm fans (opposite faces), dense vertical aluminum fin stack visible through gaps, 16-pin 12VHPWR connector top edge, white-lit logo.
- **RTX 5090 FE**: slimmer 2-slot "double flow-through": PCB is a small central island, two fans on the **same face** blowing through two fin stacks at both ends; dark silver; 16-pin angled connector; 3 DP 2.1 + 1 HDMI.
- **Mining frame**: open rectangular aluminum rail cage, cards standing vertically in a row with 20–30 mm gaps, blue PCIe riser USB cables, 2 ATX PSUs on the lower shelf, small motherboard on lower deck, zip-ties and box fans. Great "scrappy garage" vibe.
- **DGX Spark**: small gold/champagne metal-foam-faced cube (Founders Edition styling mirrors DGX Station). (unverified finish)

---

## Tier 2 — Workstation / prosumer

| Item | Year | Memory | Bandwidth | FP16 / FP8 / FP4 (dense) | Power | Form factor / size | Cooling | Price |
|---|---|---|---|---|---|---|---|---|
| RTX A6000 (Ampere) | 2020 | 48 GB GDDR6 ECC | 768 GB/s | ~155 TF FP16 (unverified) / – / – | 300 W | 2-slot FHFL, 267 x 111 mm, NVLink bridge (2-way) | Air, blower | $4,650 MSRP; used ~$3–4k (unverified) |
| RTX 6000 Ada | 2022 | 48 GB GDDR6 ECC | 960 GB/s | ~364 TF FP16 (unverified) / ~728 TF FP8 (unverified) / – | 300 W | 2-slot FHFL 267 x 111 mm | Air, blower | $6,800 MSRP (unverified) |
| RTX PRO 6000 Blackwell Workstation Ed. | 2025 | **96 GB GDDR7 ECC**, 512-bit | 1,792 GB/s | ~4,000 "AI TOPS" FP4 sparse (unverified) | **600 W**, 1x 16-pin | 2-slot, depth 305 mm x height 137 mm ([SHI](https://www.shi.com/Product/50042624)) | Air, double flow-through (5090-style) | Launch ~$8,000–8,500; **2026 retail $9k–11.5k** ([digitalcitizen](https://www.digitalcitizen.life/nvidia-rtx-pro-6000-blackwell-prices-climb-past-10000-as-ai-demand-keeps-rising/)) |
| RTX PRO 6000 Blackwell Max-Q | 2025 | 96 GB GDDR7 | 1,792 GB/s | as above, lower clocks | 300 W | 2-slot, blower | Air, blower (stackable 4x) | ~same as above (unverified) |
| RTX PRO 6000 Blackwell Server Ed. | 2025 | 96 GB GDDR7 | 1,792 GB/s | as above | up to 600 W | passive 2-slot, 266.7 x 111.7 mm ([SHI EU](https://eu.shi.com/product/50005747/NVIDIA-RTX-PRO-6000-Blackwell)) | Passive (server airflow) | similar |
| 4-GPU workstation tower (e.g. Threadripper PRO / Xeon W, 4x blower cards) | — | 256 GB–2 TB DDR5 RDIMM | — | sum of GPUs | 1,600–2,400 W (2 PSUs) | ~250 x 550 x 650 mm tower | Air | $20–60k (estimate) |
| DGX Station GB300 (desktop superchip) | 2025–26 | 784 GB coherent (288 GB HBM3e GPU + ~496 GB LPDDR5X) (unverified) | 8 TB/s HBM (unverified) | ~20 PF FP4 sparse (unverified) | ~1.6 kW (unverified) | Large tower | Liquid internal (unverified) | Not public; >$50k (unverified) |

Sources/images: RTX PRO 6000 https://www.nvidia.com/en-us/products/workstations/professional-desktop-gpus/rtx-pro-6000/ ; RTX 6000 Ada https://www.nvidia.com/en-us/design-visualization/rtx-6000/ ; DGX Station https://www.nvidia.com/en-us/products/workstations/dgx-station/

**Visual description:**
- **A6000 / RTX 6000 Ada**: classic pro "blower" card: flat black (A6000) or black + gold-accent (Ada) shroud, single radial fan at the rear-top end, exhaust vents across the bracket, smooth flat surfaces, no RGB. Ada adds gold trim lines. Power plug at the card end (8-pin EPS / 16-pin).
- **RTX PRO 6000 WS**: looks like an RTX 5090 FE in black with subtle silver; two fans one side, flow-through fin stacks.
- **Multi-GPU tower**: big black workstation case with mesh front, 4 cards packed slot-to-slot (blowers exhaust out the back), large CPU tower cooler or AIO radiator up top.

---

## Tier 3 — Small server (PCIe datacenter cards in 2U/4U)

| Item | Year | Memory | Bandwidth | FP16 / FP8 / FP4 (dense) | Power | Form factor | Cooling | Price |
|---|---|---|---|---|---|---|---|---|
| A100 PCIe 80 GB | 2021 | 80 GB HBM2e | 1,935 GB/s | 312 TF / – / – | 300 W | FHFL 2-slot, 267 x 111 mm | Passive (gold-bronze shroud) | Launch ~$15k; used 2026 ~$6–12k (unverified) |
| L40S (Ada) | 2023 | 48 GB GDDR6 ECC | 864 GB/s | ~366 TF / ~733 TF / – | 350 W | FHFL 2-slot 267 x 111 mm | Passive | ~$7.5–10k (unverified) |
| H100 PCIe 80 GB | 2022 | 80 GB HBM2e | 2.0 TB/s | ~756 TF / ~1,513 TF / – | 300–350 W | FHFL 2-slot | Passive | $25–40k new ([intuitionlabs](https://intuitionlabs.ai/articles/data-center-gpu-pricing-2026)) |
| H100 NVL 94 GB | 2023 | 94 GB HBM3 | 3.9 TB/s | ~835 TF / ~1,671 TF / – | 350–400 W | FHFL 2-slot, NVLink bridge pairs | Passive | ~$30k (unverified) |
| H200 NVL | 2024–25 | 141 GB HBM3e | 4.8 TB/s | ~835 TF / ~1,671 TF / – | up to 600 W | FHFL 2-slot, 2- or 4-way NVLink bridge | Passive | ~$30–35k (unverified) |
| RTX PRO 6000 Server Ed. | 2025 | 96 GB GDDR7 | 1.79 TB/s | see Tier 2 | 600 W | FHFL 2-slot | Passive | ~$9–15k |
| 2U GPU server (e.g. Dell R760xa / Supermicro 2U, 4 double-wide GPUs) | — | 0.5–2 TB DDR5 | — | — | 2.4–3.2 kW (2x PSU) | 2U: 87 x 482 x ~800 mm | Air, 6–8 hot-swap fans | $25–40k excluding GPUs (estimate) |
| 4U 8–10 GPU PCIe server (e.g. Supermicro SYS-421GE / 4U 10-GPU) | — | 1–4 TB DDR5 | — | — | 4–6 kW (4x PSU) | 4U: 176 x 437 x ~800 mm | Air, mid-wall fan bank | $40–60k excluding GPUs (estimate) |

Sources: H100 https://www.nvidia.com/en-us/data-center/h100/ ; H200 https://www.nvidia.com/en-us/data-center/h200/ ; L40S https://www.nvidia.com/en-us/data-center/l40s/ ; A100 https://www.nvidia.com/en-us/data-center/a100/

**Visual description:**
- **Datacenter PCIe cards** (A100/H100/L40S/H200 NVL): fanless, closed box shroud, full-length, fin stack visible at both ends, no display outputs, an 8-pin CPU / 16-pin connector at the rear end, NVLink fingers on top edge (H100/H200 NVL). A100/H100 PCIe shrouds are **bronze/champagne-gold with a black "NVIDIA" stripe**; L40S is black with gold.
- **2U server**: flat steel box, front has 8–24 hot-swap 2.5" drive bays with blue/amber LED, bezel with ID light; rear has 2 PSUs (green release latch), NIC ports, GPUs mounted in riser cages at the rear or front.
- **4U 8-GPU PCIe**: tall chassis, a wall of 8–10 80 mm fans mid-body, cards stacked side-by-side in a PCIe switch board, rear shows 4 PSUs.

---

## Tier 4 — SXM/OAM 8-GPU baseboards (DGX/HGX, AMD Instinct platforms)

### Per-accelerator

| GPU | Year | Memory | Bandwidth | FP16/BF16 | FP8 | FP4 | TDP | Notes |
|---|---|---|---|---|---|---|---|---|
| A100 SXM4 80GB | 2020 | 80 GB HBM2e | 2.0 TB/s | 312 TF | – | – | 400 W | NVLink3 600 GB/s |
| H100 SXM5 | 2022–23 | 80 GB HBM3 | 3.35 TB/s | 989 TF | 1,979 TF | – | 700 W | NVLink4 900 GB/s |
| H200 SXM | 2024 | 141 GB HBM3e | 4.8 TB/s | 989 TF | 1,979 TF | – | 700 W | same die as H100 |
| B200 (HGX/DGX) | late 2024–25 | 180–192 GB HBM3e | 8 TB/s | ~2.25 PF | ~4.5 PF | ~9 PF | ~1,000 W | NVLink5 1.8 TB/s; dual-die |
| B300 / Blackwell Ultra | 2H 2025 | 288 GB HBM3e (12-high) | 8 TB/s | ~2.25 PF (unverified) | ~4.5 PF (DGX B300: 72 PF/8, sparse? see note) | ~13.5–15 PF dense | ~1,100–1,400 W (unverified) | ConnectX-8 on board |
| AMD MI300X (OAM) | Dec 2023 | 192 GB HBM3 | 5.3 TB/s | ~1.3 PF | ~2.6 PF | – | 750 W | Infinity Fabric 8-way |
| AMD MI325X (OAM) | 2025 Q1 | 256 GB HBM3e | 6 TB/s | ~1.3 PF | ~2.6 PF | – | 1,000 W | ([tensorwave](https://tensorwave.com/blog/mi325)) |
| AMD MI350X (OAM) | 2H 2025 | 288 GB HBM3e | 8 TB/s | ~2.3 PF (unverified) | ~4.6 PF | ~9.2 PF (18.45 sparse) | 1,000 W, **air** | ([AMD](https://www.amd.com/en/partner/browse-by-resource/partner-insights-articles/instinct-mi350x-data-center-ai-leadership.html)) |
| AMD MI355X (OAM) | 2H 2025 | 288 GB HBM3e | 8 TB/s | ~2.5 PF | ~5.0 PF | ~10 PF (20.1 sparse) | 1,400 W, **liquid** | ([Tom's HW](https://www.tomshardware.com/tech-industry/artificial-intelligence/amd-reveals-core-specs-for-instinct-mi355x-cdna4-ai-accelerator-slated-for-shipping-in-the-second-half-of-2025), [SemiAnalysis](https://inferencex.semianalysis.com/chips/mi355x)) |

Note on B300: DGX B300 is quoted at 72 PF FP8 training and 144 PF FP4 inference for 8 GPUs; 144 PF is sparse, 108 PF dense ([NVIDIA DGX B300](https://www.nvidia.com/en-eu/data-center/dgx-b300)).

### Systems

| System | Year | Contents | Power | Size (H x W x D) | Weight | Cooling | Price |
|---|---|---|---|---|---|---|---|
| DGX A100 | 2020 | 8x A100, 6x NVSwitch, 2x EPYC 7742, 1–2 TB RAM, 8x 200G ConnectX-6 | 6.5 kW | 6U, 264 x 482 x 897 mm | ~123 kg | Air | $199k launch |
| DGX H100 / H200 | 2023 / 2024 | 8x H100/H200, 4x NVSwitch3, 2x Xeon 8480C, 2 TB RAM, 8x ConnectX-7 400G (OSFP "cedar" modules), 2x BlueField-3 | **10.2 kW max** | **8U**, 356 x 482 x 897 mm | **130.45 kg** | Air (12 front fans) | ~$300–500k (unverified) |
| DGX B200 | 2025 | 8x B200 (1,440 GB total), 2x Xeon 8570, 8x ConnectX-7, 2x BlueField-3 | **~14.3 kW max** | **10U**, ~444 x 482 x 897 mm (unverified) | ~142 kg (unverified) | Air | ~$500k (unverified) |
| DGX B300 | 2H 2025 | 8x B300 (8 x 288 GB = 2.3 TB), 8x ConnectX-8, 2x BlueField-3 | **14.5 kW busbar / 15.1 kW PSU** | **10U, 442 x 482.6 x 904.2 mm** | **168 kg (PSU) / 123 kg (busbar)** | Air (liquid HGX variants exist) | not public (unverified) |
| HGX 8-GPU baseboard (H100/B200/B300) | — | 8 SXM modules + NVSwitch chips on one PCB tray | 5.6 kW (H100) – ~9–11 kW (B300) GPU-only (unverified) | ~ 417 x 553 mm class board + heatsinks (unverified) | ~ 30–60 kg with heatsinks (unverified) | Air (huge copper/vapor-chamber heat sinks) or cold plates | GPUs dominate cost |
| AMD Instinct 8-GPU platform (UBB 2.0) | 2023–25 | 8x MI300X/MI325X/MI35x OAM | ~6–11 kW GPU-only | board **417 x 553 mm** ([AMD MI325X platform](https://amd.com/en/products/accelerators/instinct/mi300/mi325x/platform.html)) | (unverified) | Air (MI300X/325X/350X) / liquid (MI355X) | (unverified) |

Sources: [DGX H100 user guide](https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html), [DGX B200 datasheet](https://openzeka.com/wp-content/uploads/2024/11/dgx-scale-ai-infrastructure-dgx-b200-datasheet-nvidia-web-1-1.pdf), [DGX B300 user guide](https://docs.nvidia.com/dgx/dgxb300-user-guide/introduction-to-dgxb300.html), [DGX B300 datasheet](https://openzeka.com/wp-content/uploads/2025/08/dgx-scale-ai-infrastructure-datasheet-gtc25-dgx-b300-nvidia-us-3725750-web.pdf).
Per-GPU prices 2026: H100 $25–40k new, $6–22k used; B200 $30–40k list, $45–50k street ([intuitionlabs](https://intuitionlabs.ai/articles/data-center-gpu-pricing-2026)). Rental: H100 ~$1.4–12/GPU-h, B200 ~$2–6/GPU-h.

**Visual description (hero candidates):**
- **DGX H100**: famous **gold metal-foam front bezel** (looks like brushed gold sponge / honeycomb), black frame, "NVIDIA DGX" etched; behind the bezel a grid of 12 large fans; rear: 6 PSUs, many OSFP network cages, two 1U-high "network trays". 8U tall: square-ish profile.
- **DGX B200 / B300**: similar gold foam bezel language but 10U; B300 adds black/gray accent and a busbar option (rear vertical copper clip instead of PSUs).
- **SXM module** (H100/B200): flat green PCB rectangle with the GPU package in the middle surrounded by HBM stacks (6 for H100, 8 for B200), mounted *face-down* onto the baseboard; on top sits a tall **copper-base + aluminum fin heatsink** (air) or flat **copper cold plate with two hose barbs** (liquid). 8 sit in a 2x4 grid; NVSwitch chips with smaller heatsinks sit at one end.
- **AMD OAM** (MI300X): ~102 x 165 mm module (OCP OAM spec, unverified for exact AMD part), large central package with 8 HBM stacks around 4+4 compute dies; heatsinks similar; AMD branding in red/black/silver.

---

## Tier 5 — Rack-scale systems

| System | Status (Oct 2026) | GPUs / CPUs | GPU memory | Compute (rack) | Power | Rack size / weight | Cooling | Price |
|---|---|---|---|---|---|---|---|---|
| **GB200 NVL72** | Shipping since ~Dec 2024 / 2025 | 72 B200 + 36 Grace (36 GB200 superchips) | ~13.5 TB HBM3e, 576 TB/s | 1.44 EF FP4 sparse (~720 PF dense); 130 TB/s NVLink domain | **~120–132 kW** | **1,068 x 600 x 2,299 mm** ([Gigabyte](https://www.gigabyte.com/Enterprise/GIGAPOD-Rack-Scale/AI-DLC-Rack_NVIDIA-GB200-NVL72)); HPE lists 2,495 mm height and **~1,470 kg (3,245 lb)** loaded ([HPE](https://www.hpe.com/us/en/collaterals/collateral.a50009224enw.html)) | Direct liquid (cold plates) + some air | ~$3M (unverified) |
| **GB300 NVL72** (Blackwell Ultra) | Shipping since 2H 2025 | 72 B300 + 36 Grace | ~20 TB HBM3e (288 GB/GPU) | 1.08 EF FP4 dense / 1.44 EF sparse | **132 kW nominal, ~155 kW peak (EDPp); provision 192 kW** ([HPE](https://www.hpe.com/us/en/collaterals/collateral.a50009244enw.html)); Gigabyte "up to 140 kW" | same Oberon rack; ~1.36 t ([introl](https://introl.com/blog/why-nvidia-gb300-nvl72-blackwell-ultra-matters)) | Direct liquid | $3–6.5M depending on method ([intuitionlabs](https://intuitionlabs.ai/articles/data-center-gpu-pricing-2026)) |
| **Vera Rubin NVL72** (was branded "NVL144" in 2025, counting dies) | First deliveries **Q4 2026**, volume 2027 ([boerse-express/ISC 2026](https://www.boerse-express.com/news/articles/vera-rubin-architektur-nvidia-praesentiert-7-exaflops-ki-plattform-920915)) | 72 Rubin (2 dies each) + 36 Vera CPUs | **288 GB HBM4/GPU at ~22 TB/s** ([Klockwood](https://glennklockwood.com/garden/processors/R200)) | **3.6 EF NVFP4 inference, 2.5 EF training** ([NVIDIA 2026 1H deck via Gigabyte](https://www.gigabyte.com/FileUpload/Global/WebPage/1052/NVIDIA_2026_1H_V2.pdf)); 50 PF NVFP4 per GPU | ~190 kW (Max-Q) to ~230 kW (Max-P) reported, **no official figure** (unverified) ([cudo](https://www.cudocompute.com/products/nvidia-vera-rubin)) | Oberon-class rack (unverified) | 100% liquid | not public (unverified; >$5M plausible) |
| **Vera Rubin NVL144 CPX** | Announced Sep 2025, slated late 2026; no shipment confirmed | 144 Rubin CPX + 144 Rubin + 36 Vera | 100 TB fast memory; CPX = 128 GB GDDR7 each | 8 EF NVFP4; CPX ~30 PF NVFP4 each | (unverified) | (unverified) | Liquid | (unverified) ([maginative](https://www.maginative.com/nvidia-unveils-rubin-cpx-a-gpu-designed-specifically-for-massive-ai-context-windows)) |
| **Rubin Ultra NVL576 "Kyber"** | Target 2H 2027; a 2028 slip reported but denied by NVIDIA ([spheron](https://www.spheron.network/blog/nvidia-kyber-rack-delayed-to-2028-what-it-means-for-rubin-ul/), [cryptobriefing](https://cryptobriefing.com/nvidia-rubin-ultra-hbm4e-kyber-2027/)) | 144 packages (4 dies each = 576 dies) | 1 TB HBM4E/GPU original target, reportedly cut to 768 GB | 15 EF FP4 inference, 5 EF FP8 training | **~600 kW per rack** ([DCD](https://datacenterdynamics.com/en/news/nvidias-rubin-ultra-nvl576-rack-expected-to-be-600kw-coming-second-half-of-2027)) | Vertical blade "book" trays, 800 V DC (unverified) | Liquid | n/a |
| **AMD Helios** (MI455X / MI450 series) | In full production; shipments from end of Q3 2026; OpenAI/Oracle/Anthropic deployments late 2026–2027 ([cxodigitalpulse](https://www.cxodigitalpulse.com/?p=59311), [NextPlatform](https://www.nextplatform.com/2026/02/23/amd-says-helios-racks-and-mi400-series-gpus-on-track-for-2h-2026/)) | 72 MI455X + EPYC "Venice" (18 per rack per Supermicro) | **432 GB HBM4/GPU, ~23.3 TB/s** (older docs 19.6); 31 TB/rack, 1.4 PB/s | **2.9 EF FP4, 1.4 EF FP8** | (unverified; ~200 kW class) | **Double-wide OCP Open Rack Wide** ([AMD blog](https://amd.com/en/blogs/2025/amd-helios-ai-rack-built-on-metas-2025-ocp-design.html), [Supermicro datasheet](https://www.supermicro.com/datasheet/datasheet_AMD_Helios.pdf)) | Liquid | ~$5–5.5M reported (unverified) |
| **Google TPU7x "Ironwood"** (cloud only, not sold) | GA in Google Cloud 2025 | per pod 9,216 chips | **192 GiB HBM/chip, ~7.37 TB/s** | **4,614 TF FP8/chip**, 2,307 TF BF16; ~42.5 EF FP8 per pod | (unverified) | 64-chip racks/cubes, optical circuit switches (unverified) | Liquid | rent only | 

Sources for TPU: [Google Cloud TPU7x docs](https://docs.cloud.google.com/tpu/docs/tpu7x), [TrendForce](https://www.trendforce.com/news/?p=47994).

### NVL72 internal layout (Oberon rack) — key for modeling
From [Gigabyte GB200 NVL72](https://www.gigabyte.com/Enterprise/GIGAPOD-Rack-Scale/AI-DLC-Rack_NVIDIA-GB200-NVL72) / [HPE QuickSpecs](https://www.hpe.com/us/en/collaterals/collateral.a50009224enw.html):
- **18x 1U compute trays** (each: 2 Grace + 4 Blackwell GPUs, cold plates, front OSFP/E1.S bays) — 10 above the switches, 8 below (typical, unverified exact split).
- **9x 1U NVLink switch trays** in the middle (2 NVSwitch chips each), all connected through the **rear copper "NVLink spine"** (~5,000 copper cables / ~2 miles, NVIDIA marketing figure, unverified).
- **6+ power shelves** (1U, ~33 kW each with 6x 5.5 kW PSUs, unverified) feeding a **54 V DC vertical busbar** at the rear.
- Liquid **manifolds** (two vertical stainless pipes, supply/return, blue/red quick disconnects) on the rear.
- Top-of-rack management switch, cable managers.

**Visual description:** black 48U-class tall rack (taller than a standard 42U), glass or perforated front door; each 1U tray front shows a gold/black grille strip with OSFP cages and status LEDs (green/amber); rear is a dense wall of copper twin-ax bundles in the center, vertical copper busbar, and two thick colored coolant manifolds with dozens of hose pairs running into trays. Total looks like a "server-rack-meets-plumbing" machine.

---

## Tier 6 — Supporting hardware

### CPUs

| CPU | Year | Cores | Memory | TDP | Package size | Used in |
|---|---|---|---|---|---|---|
| AMD EPYC 7742 (Rome) | 2019 | 64 | 8ch DDR4 | 225 W | SP3, ~75 x 58 mm | DGX A100 |
| Intel Xeon Platinum 8480C/+ (Sapphire Rapids) | 2023 | 56 | 8ch DDR5 | 350 W | LGA4677 ~77.5 x 56.5 mm | DGX H100 |
| Intel Xeon Platinum 8570 (Emerald Rapids) | 2023–24 | 56 | 8ch DDR5 | 350 W | LGA4677 | DGX B200 (unverified exact SKU) |
| AMD EPYC 9654 (Genoa) / 9965 (Turin, 192c Zen 5c) | 2022 / 2024 | 96 / 192 | 12ch DDR5 | 360 / 500 W | SP5, ~72 x 75.4 mm | many HGX servers |
| Intel Xeon 6 6980P (Granite Rapids) | 2024 | 128 | 12ch DDR5/MRDIMM | 500 W | LGA7529 | HGX B200 options |
| **AMD EPYC "Venice" 9996 (Zen 6c, 2 nm)** | **2026** | **256 / 512 threads** | 16ch, 1.6 TB/s with MRDIMM, 128 PCIe 6 lanes | (unverified) | SP7 | **Helios** ([StorageReview](https://www.storagereview.com/news/amd-6th-gen-epyc-venice-256-cores-1-6tb-s-and-the-first-pcie-gen-6-server-cpu), [Tom's HW](https://www.tomshardware.com/pc-components/cpus/amds-256-core-epyc-9996-venice-claims-up-to-a-3-4x-jump-over-intel-xeon-competition-20-percent-over-nvidia-vera-zen-6-comes-with-up-to-1024mb-of-l3-16-channel-memory-and-5ghz-clock-speeds)) |
| NVIDIA Grace (72x Neoverse V2) | 2023 | 72 | up to 480 GB LPDDR5X on-package | ~250–500 W (unverified) | on GB200 board | GB200/GB300 |
| **NVIDIA Vera** (custom Arm "Olympus") | **launched GTC Mar 2026** | **88 / 176 threads** | LPDDR5X SOCAMM (unverified capacity) | (unverified) | on Vera Rubin board | VR NVL72 ([TechSpot](https://www.techspot.com/news/112724-amd-claims-next-gen-zen-6-server-cpu.html)) |

Visual: CPUs are small; model as flat silver IHS rectangles under black/copper heatsinks; mostly hidden in trays. Low-detail kit piece only.

### NICs / DPUs

| Item | Year | Speed | Form | Notes |
|---|---|---|---|---|
| ConnectX-6 | 2019 | 200 Gb/s HDR / 200GbE | PCIe Gen4 HHHL / OCP3 | DGX A100 |
| ConnectX-7 | 2022 | 400 Gb/s NDR / 400GbE | PCIe Gen5, OSFP | DGX H100/B200 |
| ConnectX-8 SuperNIC | 2025 | 800 Gb/s (2x400G Ethernet typical), integrated PCIe Gen6 switch | on HGX B300 / GB300 trays | |
| **ConnectX-9 SuperNIC** | **2026** (FW GA Feb 2026) | **800 Gb/s per port; 1.6 Tb/s per Rubin GPU** (2 NICs) | PCIe Gen6 | ([PNY datasheet](https://www.pny.com/en-eu/file%20library/professional/datasheet/mellanox/pny-connectx-datasheet-connectx-9.pdf), [NVIDIA FW notes](https://docs.nvidia.com/networking/display/connectx9firmwarev82481000)) |
| BlueField-3 DPU | 2022–23 | 400 Gb/s, 16 Arm A78 cores | FHHL PCIe Gen5 | DGX H100/B200/B300 |
| **BlueField-4** | **2026** | 800 Gb/s (ConnectX-9) + **64-core Grace**, 128 GB LPDDR5X | PCIe Gen6 x16 or self-hosted | ([Klockwood](https://glennklockwood.com/garden/bluefield-4)) |
| AMD Pensando Pollara 400 / Vulcano 800 | 2025 / 2026 | 400 / 800 GbE (UEC) | PCIe | Helios scale-out (Vulcano unverified) |

Visual: low-profile green PCB with a heatsink and 1–2 big **OSFP cages** (finned top) on the bracket; DPUs larger, with a fan-less finned heatsink. Optical transceivers: silver OSFP modules with finned tops and a pull tab (cyan/blue/black), MPO fiber (aqua/magenta).

### Switches

| Switch | Year | Ports | Throughput | Size | Cooling | Price |
|---|---|---|---|---|---|---|
| Quantum (HDR) QM8700 | 2019 | 40x 200G | 16 Tb/s | 1U | Air | (unverified ~$20–30k) |
| Quantum-2 QM9700 (NDR) | 2022 | 64x 400G via 32 OSFP (twin-port) | 51.2 Tb/s | 1U | Air | (unverified ~$30–40k) |
| **Quantum-X800 Q3400-RA** (XDR) | 2025 | **144x 800G via 72 OSFP** | **115.2 Tb/s** | **4U** | Air (Q3400-LD liquid variant) | ~$107–150k reseller ([NADDOD datasheet](https://resource.naddod.com/files/products-Switches/2025-03-28/nvidia-quantum-x800-infiniband-switches-datasheet-011078.pdf), [Dell datasheet](https://www.delltechnologies.com/asset/en-my/products/networking/technical-support/nvidia-quantum-x800-q3200-ra-and-q3400-ra-datasheet.pdf)) |
| Quantum-X800 **Q3450 CPO** (co-packaged optics) | 2026 | 144x 800G, fiber direct to switch | 115.2 Tb/s | (unverified) | Liquid | (unverified) ([STH GTC 2026](https://www.servethehome.com/gigabyte-nvidia-vera-rubin-and-more-at-nvidia-gtc-2026/2/)) |
| Spectrum-4 SN5600 (Spectrum-X Ethernet) | 2023–24 | 64x 800GbE (OSFP) | 51.2 Tb/s | 2U (unverified) | Air | (unverified) |
| Spectrum-X Photonics (CPO Ethernet) | 2026 (unverified) | up to 512x 800G (unverified) | 409.6 Tb/s (unverified) | (unverified) | Liquid | (unverified) |
| NVLink Switch tray (NVL72) | 2024+ | 2 NVSwitch chips, connects to rear spine | 130 TB/s across 9 trays (GB200); ~260 TB/s VR NVL72 (unverified) | 1U | Liquid | part of rack |

Visual: front panel is a wall of OSFP cages (two rows, 36 each for Q3400 in 4U) with link LEDs; heavy fiber bundles in aqua/yellow; rear PSUs and fan trays (air models). CPO switches have fiber pigtails coming straight out the front, no transceivers.

### Storage

| Item | Typical spec | Size | Notes |
|---|---|---|---|
| All-flash AI storage node (e.g. DDN AI400X2/X3, VAST, WEKA on 1U/2U) | 24x NVMe U.2/E3.S, 100s TB–PB per node, 50–100+ GB/s read (unverified) | 1U–2U | Front: rows of drive sleds with blue/green activity LEDs |
| JBOF / NVMe-oF enclosure | 24–32 E3.S drives | 1U–2U | |
| Bulk HDD JBOD (data lake) | 60–106 HDD, 1–3 PB raw | 4U top-loading, ~100+ kg | heavy drawer that slides out; great "sci-fi" kit piece |

Product refs: https://www.ddn.com/products/a3i-accelerated-any-scale-ai/ (unverified page path), https://www.vastdata.com/

### Power and cooling

| Item | Key spec | Size / weight | Visual | Source |
|---|---|---|---|---|
| Rack PDU (vertical, 0U, 3-phase 415 V, 32–60 A) | 17–43 kVA per PDU (unverified range) | ~1,800 x 55 x 55 mm | long black/silver bar with C13/C19 outlets, small LCD, colored outlet groups | vendor generic (APC/Raritan/Vertiv) |
| NVL72 power shelf | ~33 kW, 6x 5.5 kW PSUs (unverified) | 1U | row of 6 PSU faces with LEDs | NVIDIA/OEM |
| 54 V DC busbar | rack-height copper bar, 1,400 A+ class (unverified) | rear vertical | bright copper strip | [Gigabyte](https://www.gigabyte.com/Enterprise/GIGAPOD-Rack-Scale/AI-DLC-Rack_NVIDIA-GB200-NVL72) |
| 800 V DC power (Kyber/Rubin Ultra era) | NVIDIA roadmap for MW racks | sidecar power racks | (unverified details) | [TechRadar](https://www.techradar.com/pro/megawatt-class-ai-server-racks-may-well-become-the-norm-before-2030-as-nvidia-displays-600kw-kyber-rack-design) |
| In-rack CDU (4U, liquid-to-liquid) | ~80–150 kW (unverified) | 4U, ~50–80 kg (unverified) | 4U box with pumps, pressure gauges, small LCD, 4 hose ports | Vertiv/CoolIT/Motivair product pages |
| **Vertiv CoolChip CDU 2300** (row/facility) | **2,300 kW** at 4 °C approach, 47.8 kW pump power, 6" sanitary flanges, redundant pumps | **2,400 x 1,200 x 1,200 mm, 1,793 kg wet** | big gray/white cabinet, 7" touchscreen, front+rear doors | [datasheet SL-80005](https://www.vertiv.com/49b02f/globalassets/shared/vertiv-coolchip-cdu-2300kw-data-sheet-sl-80005.pdf) |
| Cold plate (per GPU/CPU) | copper micro-channel, ~1–2.3 kW per GPU | ~ GPU package size + 2 barbs | polished/nickel copper block, 2 hoses, quick disconnects (UQD, blue=cold, red=hot) | generic |
| Rear-door heat exchanger (active, with fans) | up to **75 kW per rack** (Motivair ChilledDoor) | full rack height door, ~150–300 mm deep (unverified) | black door with fin coil grid and a column of fans | [Motivair brochure](https://www.motivaircorp.com/uploads/files/brochures/2024/The%20ChilledDoor.pdf) |
| Chiller / dry cooler (outside) | MW class | container-size | roof/yard units with big round fans | (generic) |

---

## Failure modes (for gameplay events)

Grounding statistic: Meta's Llama 3.1 405B run on **16,384 H100s for 54 days had 466 interruptions, 419 unexpected (~1 every 3 hours)**; GPU-related faults ~58.7% of unexpected interruptions, **HBM3 errors 72 (17.2%)**, faulty GPUs ~148; >90% effective training time; only 3 manual interventions ([sdxcentral](https://www.sdxcentral.com/news/meta-report-details-hundreds-of-gpu-and-hbm3-related-interruptions-to-llama-3-training-run/), [3dtested/Tom's HW mirror](https://www.3dtested.com/tech-industry/artificial-intelligence/faulty-nvidia-h100-gpus-and-hbm3-memory-caused-half-of-the-failures-during-llama-3-training-one-failure-every-three-hours-for-metas-16384-gpu-training-cluster)). Rule of thumb for the game: **~1 unexpected job interruption per ~2,000 GPU-days per 1,000 GPUs**, i.e. failure rate scales linearly with GPU count.

| Event | Tier where it fits | Real-world basis | Suggested game effect |
|---|---|---|---|
| Melting 12VHPWR/16-pin power connector | 1–2 (4090/5090/PRO 6000) | widely reported 4090/5090 connector burns | card destroyed, small fire risk, repair cost |
| Fan failure / dust clogging | 1–3 | air-cooled consumer/server | thermal throttle -30% perf until repaired |
| Thermal throttling (hot room, bad airflow) | all | GPUs clock down at temp limit | perf scales with cooling headroom |
| Breaker trip / PSU overload | 1–3 | garage circuits ~1.8–3.7 kW | node offline, need electrical upgrade |
| HBM uncorrectable ECC / row remap exhausted (NVIDIA XID 48/94/95) | 3–5 | 17.2% of Llama 3 interruptions | job restart from checkpoint, GPU RMA |
| "GPU fell off the bus" (XID 79) | 3–5 | common H100 fault | node reboot |
| NVLink / NVSwitch errors (XID 74), NVLink tray failure | 4–5 | NVL72 copper spine/trays | whole NVLink domain degraded |
| InfiniBand/optical link flaps, bad transceiver | 4–6 | very frequent in large clusters | slower all-reduce, swap optic |
| Silent data corruption (SDC) | 4–5 | Meta/Google reported SDC from faulty chips | loss spike / ruined training run unless detected |
| Coolant leak at quick-disconnect / cold plate | 5–6 | liquid-cooled racks | rack shutdown, damage nearby trays |
| CDU pump failure | 5–6 | redundant pumps exist for this reason | rack throttles/shuts down in seconds without N+1 |
| Early rack-scale bring-up issues (overheating, connector faults) | 5 | reported delays on early GB200 NVL72 (late 2024–2025) (unverified details) | "new platform" penalty: lower uptime first months |
| Supply shortage / price spike (HBM, GDDR7) | economy | 2026 GDDR7/DRAM shortage, HBM4 gating Rubin volume | market event: prices +X%, delivery delays |
| Grid power cap | 5–6 | 130–600 kW racks need utility upgrades | expansion blocked until substation built |

---

## Game-number cheat sheet (normalized, dense)

| Tier | Representative unit | FP8 dense per unit | Memory per unit | Power per unit | Price per unit (2026, approx.) |
|---|---|---|---|---|---|
| 1 | RTX 3090 | ~0 (no FP8; use ~0.14 PF FP16) | 24 GB | 0.35 kW | $0.8k used |
| 1 | RTX 4090 | ~0.66 PF | 24 GB | 0.45 kW | $2–3k |
| 1 | RTX 5090 | ~0.84 PF (unverified) | 32 GB | 0.575 kW | $2.4–4k |
| 2 | RTX PRO 6000 | ~1 PF (unverified) | 96 GB | 0.6 kW | $9–11k |
| 3 | H100 PCIe | ~1.5 PF | 80 GB | 0.35 kW | $25–30k |
| 4 | DGX H100 (8 GPU) | ~15.8 PF | 640 GB | 10.2 kW | ~$300–400k (unverified) |
| 4 | DGX B200 | ~36 PF | 1.44 TB | 14.3 kW | ~$500k (unverified) |
| 4 | DGX B300 | ~36 PF (FP4 ~108 PF) | 2.3 TB | 14.5 kW | (unverified) |
| 5 | GB200 NVL72 | ~360 PF (FP4 ~720 PF) | 13.5 TB | ~120–132 kW | ~$3M (unverified) |
| 5 | GB300 NVL72 | ~360 PF (FP4 1.08 EF) | ~20 TB | 132–155 kW | $3–6.5M |
| 5 | AMD Helios | 1.4 EF (vendor, likely sparse) | 31 TB | ~200 kW (unverified) | ~$5M (unverified) |
| 5 | Vera Rubin NVL72 | (FP4 3.6 EF inference) | ~20.7 TB HBM4 | ~190–230 kW (unverified) | (unverified) |
| 5+ | Rubin Ultra NVL576 | (FP4 15 EF) | ~110–147 TB | ~600 kW | endgame |

---

## Blender modeling plan (browser game, Three.js, .glb)

### Hero-quality models (unique, close-up, showcase on "unlock")
1. **RTX 4090/5090-style consumer card** — the first thing players see; 6–12k tris, 1k–2k texture set, emissive logo.
2. **Open mining frame with 6 GPUs** — built from instanced card + riser + frame kit; frame itself ~3k tris.
3. **Workstation tower (glass side panel)** — 8–15k tris, interior visible.
4. **DGX H100/B300 8U/10U box** with gold foam bezel — 10–20k tris; bezel as normal map + alpha-tested or parallax material, not geometry.
5. **SXM8 HGX baseboard (exploded view)** — 15–25k tris; used in tech-tree/upgrade screen only.
6. **NVL72 rack (front + rear)** — 25–40k tris at LOD0 using instanced 1U trays; rear "copper spine" as a textured card with a few cylinders.
7. **CDU 2300 cabinet** and **Kyber-style 600 kW rack** — 8–15k tris each (endgame showpieces).

### Modular kit (reused everywhere, instanced in Three.js)
- **Rack shell** 42U and 48U (Oberon-style 600 x 1,068 mm) with door variants (glass, perforated, rear-door heat exchanger): 1–2k tris.
- **Chassis** 1U / 2U / 4U / 8U / 10U generic boxes with swappable **front-panel decals** (drive bays, fan grille, OSFP rows, gold foam): 300–1,500 tris each.
- **Blanking panel** 1U/2U: ~50 tris.
- **Network switch 1U/2U/4U** with OSFP cage row as normal-map + a few instanced cages: 500–2k tris.
- **PSU / power shelf face**, **PDU bar**, **busbar strip**: 100–500 tris.
- **Cable bundles**: spline-based tube meshes (fiber aqua/yellow, copper black, coolant blue/red) — bake to 200–800 tris per bundle; use a single tiling texture.
- **Coolant manifold** (vertical pipe + N quick-disconnect stubs), **cold plate**, **hose pair**: 200–1k tris.
- **Floor tiles** (raised floor), **hot/cold aisle containment panels**, **cable tray** overheads: <500 tris each.
- **Status LED strip**: use instanced quads with emissive material; drive color from game state (green/amber/red) via per-instance attribute.

### Poly and texture budgets (WebGL2/WebGPU, mid-range laptop target)
- Total visible scene: **≤ 500k–1M triangles**, **≤ 150–250 draw calls** (instancing + texture atlases are mandatory for racks).
- Per hero model LOD0: 10–40k tris; LOD1 ~30%; LOD2 ~10% / impostor billboard for far racks.
- Kit pieces: 50–2k tris.
- Textures: shared **2048² trim-sheet atlases** (metal, mesh grilles, port rows, decals) in KTX2/Basis; heroes may get a 2048² unique set. Use glTF **EXT_meshopt_compression** or Draco for geometry.
- Materials: PBR metal-roughness; gold foam bezel = normal + roughness map; brushed aluminum anisotropy optional; emissive for LEDs/logos (bloom pass).
- Naming in .glb: `kit_rack_48u_shell`, `kit_chassis_1u`, `kit_blank_1u`, `hero_dgx_h100`, `hero_nvl72_rack`, `fx_led_strip`, with empties as **socket nodes** (`socket_u01`...`socket_u48`, `socket_gpu_0..7`) so the game snaps instances procedurally.

### Physical scale reference for Blender (1 unit = 1 m)
- 1U = 44.45 mm; 19" rack mount width = 482.6 mm (450 mm inner); 42U standard rack ~2,000 x 600 x 1,070–1,200 mm.
- NVL72 rack: 600 W x 1,068 D x ~2,300–2,500 H mm, ~1.4–1.5 t.
- Consumer GPU: ~304 x 137 x 48–61 mm. FHFL PCIe card: 267 x 111 mm, 2-slot = 40 mm.
- Vertiv CDU 2300: 2,400 H x 1,200 W x 1,200 D mm.
