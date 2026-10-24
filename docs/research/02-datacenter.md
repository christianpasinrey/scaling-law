# 02 — How Real AI Datacenters Work (research for the AI-lab management game)

Research date: 2026-10-24. Scope: physical layout, power, cooling, networking, failures and operations, staff, security and compliance, and visual reference, plus about 15 gameplay events grounded in real incidents.

**Reading conventions**
- **(unverified)** means the number comes from secondary or vendor sources, or from general industry knowledge I could not trace to a primary source in this session. Use it as a game-balance starting point, not as fact.
- Numbers from primary sources (papers, operator postmortems, official blogs) carry a link.
- Where sources conflict, I give the range and say so.

---

## 0. TL;DR for game design

| Takeaway | Game implication |
|---|---|
| **Power, not floor space, is the scarce resource.** Grid connections take years, large transformers take 2 to 4 years, switchgear is sold out to 2028. | The main expansion gate should be **MW secured**, not square metres. Long lead-time orders are a core strategic layer. |
| **Rack density went from about 5–10 kW (classic) to 120–140 kW (GB200/GB300 NVL72), and is heading to 600 kW (Kyber, 2027).** | Each hardware generation forces a **facility retrofit** (liquid cooling, busways, floor loading). Old halls cannot host new racks. |
| **Big synchronous training jobs fail all the time.** Llama 3 405B on 16K H100s had **419 unexpected interruptions in 54 days**, about one every 3 hours, 58.7% of them GPU-related. | Failures are *normal background noise*. Gameplay is about **effective training time** (goodput) via checkpointing, automation, spares and staff, not about avoiding failures entirely. |
| **Cooling failures cascade in minutes to hours.** Nebius in 2026: a storm took out the BMS and chillers, and halls hit a 58.5 °C inlet in about 2 hours. | Cooling incidents should be the most dramatic, time-critical events. They are well suited to a "red alert" mode. |
| **Human error and procedures matter.** CME/CyrusOne 2025: tower-draining procedure not followed. Azure Sydney 2023: 3 night staff could not restart chillers in time. | Staff count, training and SOP quality are real stats. Understaffing at night is a valid failure modifier. |

---

## 1. Physical layout progression (game "tiers")

| Stage | Typical IT power | GPUs (approx.) | Racks | Footprint | Notes and realism hooks |
|---|---|---|---|---|---|
| **T0 Garage / home lab** | 1–15 kW | 1–32 consumer or used datacenter GPUs | 0–2 (open frames, 4U towers) | 10–30 m² | A US household service is typically 100–200 A at 240 V (about 24–48 kW peak); a 4×GPU workstation draws about 1.5–3 kW. Problems: breaker trips, heat, noise (servers 70–90 dBA), residential power cost, no redundancy. (unverified, general knowledge) |
| **T1 Colocation cage** | 50 kW – 1 MW | 32 – 1,000 | 2–20 | 20–200 m² cage in a shared hall | You rent **power** (priced per kW/month) plus space and cross-connects. CBRE Q1 2026: N. Virginia asking rents of **$190–235 per kW/month** for 250–500 kW deployments; N. Virginia vacancy is **about 0.3%** ([CBRE 2026](https://www.cbre.com/insights/reports/global-data-center-trends-2026)). Liquid-cooled colo space reportedly costs a **22–28% premium** (unverified, [Datacentres.com](https://www.datacentres.com/news/hyperscaler-capex-surge-pushes-global-data-centre-capacity-pipeline-to-25-000-mw-2026-05-25)). The provider runs the facility; you run the IT. "Remote hands" fees apply. |
| **T2 Private data hall / suite** | 2–20 MW | 1K – 15K | 50–300 | 1,000–5,000 m² | Dedicated hall inside a provider building (a wholesale lease) or a build-to-suit. You choose the cooling design. Typical leases run 5–15 years. |
| **T3 Dedicated building** | 20–150 MW | 15K – 100K | 300–1,500 | 10,000–50,000 m² | Own substation, generator yard, chiller or dry-cooler yard, network meet-me rooms. Reference point: Meta's 24K-GPU H100 cluster has **8 pods × 192 racks × 16 GPUs** in a single building ([Llama 3 paper](https://arxiv.org/abs/2407.21783)). Crusoe's first 2 Abilene buildings: **about 980,000 ft² and over 200 MW IT** ([DCD](https://www.datacenterdynamics.com/en/news/crusoes-abilene-data-center-officially-live-serving-oracle-and-openais-stargate/)). |
| **T4 Multi-building campus** | 300 MW – 5 GW | 100K – 1M+ | 2,000–20,000+ | 100s of hectares | **Stargate Abilene**: 8 buildings, 1.2 GW target; Epoch estimated 4 of 8 operating in April 2026 (0.3–0.6 GW, the versions disagree) ([Epoch AI](https://epoch.ai/blog/openai-stargate-where-the-us-sites-stand)). **Meta Hyperion** (Louisiana): 2 GW by 2030, scalable to 5 GW ([etcentric](https://www.etcentric.org/?p=194421)). **xAI Colossus** (Memphis): ran about 35 unpermitted gas turbines (~421 MW) while waiting for grid substations ([TechCrunch](https://techcrunch.com/2025/06/18/xai-is-facing-a-lawsuit-for-operating-over-400-mw-of-gas-turbines-without-permits)). **Microsoft Fairwater**: Wisconsin and Atlanta linked by an AI WAN into one "superfactory" ([Microsoft](https://blogs.microsoft.com/blog/2025/11/12/infinite-scale-the-architecture-behind-the-azure-ai-superfactory/)). |

**Useful rule of thumb:** with GB200/GB300 NVL72 at about 130–140 kW per 72-GPU rack, plus networking, storage, CPUs and cooling overhead, plan **about 1.6–2.0 kW of facility power per GPU** (all-in, PUE 1.2–1.3). That is **about 500–600K GPUs per GW** (unverified, derived estimate).

---

## 2. Racks and rooms

### 2.1 Rack formats

| Format | Width | Height | Unit | Power delivery | Notes |
|---|---|---|---|---|---|
| EIA-310 "19-inch" | 19" rails (600 mm or 800 mm cabinet width) | 42U (≈2.0 m) / 48U (≈2.2 m) / 52U | U = 44.45 mm | AC PDUs (single or 3-phase, 208/230/415 V) | Classic enterprise and colo. Depth 1,000–1,200 mm. |
| OCP Open Rack V3 (ORv3) | 21" equipment width (600 mm cabinet) | 44 OU or 48 OU | **OU = 48 mm** | **48 V DC busbar** fed by power shelves | Used by Meta and others ([ATEN ORv3 datasheet](https://assets.aten.com/product/spec_sheet/RC8000-RC8100-ORV3-Standard-Rack-44OU-48OU-Datasheet-en.pdf)). |
| NVIDIA MGX / NVL72 (GB200/GB300) | ORv3-derived | 48U-class | — | Busbar with power shelves at the top and bottom; liquid-cooled trays | 18 compute trays + 9 NVLink switch trays, 72 GPUs. MGX 1.2 supports racks up to **about 250 kW** (unverified, [Spheron](https://www.spheron.network/blog/nvidia-mgx-1-2-explained-what-250kw-open-racks-mean-for-gb300/)). |
| OCP Open Rack Wide (ORW) | Double-wide | — | — | Higher power | Spec v1.0.0, 2025/2026 ([OCP](https://www.opencompute.org/documents/open-rack-wide-orw-base-specification-v1-0-0-final-pdf)). |
| NVIDIA Kyber (Rubin Ultra NVL576) | New mechanical design | — | — | **800 V DC** | About **600 kW per rack**, slated for 2027 ([DCD](https://datacenterdynamics.com/en/analysis/nvidia-gtc-jensen-huang-data-center-rack-density), [NVIDIA blog](https://blogs.nvidia.com/blog/gigawatt-ai-factories-ocp-vera-rubin)). |

**Weight:** a fully loaded NVL72 rack weighs about **1.3–1.4 tonnes** (unverified). That is why modern AI halls use **slab-on-grade** floors rather than raised floors.

### 2.2 Power density per rack over time

| Era | Typical kW/rack | Example |
|---|---|---|
| 2010–2018 enterprise | 3–8 kW | Uptime surveys: global average below 8 kW as late as 2024 ([Upsite summary](https://www.upsite.com/blog/data-center-trends-rack-density-rises-while-pue-and-outage-frequency-remain-flat/)) |
| 2018–2022 HPC/GPU (DGX-1/V100, DGX A100) | 15–30 kW | DGX A100 ≈ 6.5 kW per node; 2–4 per rack (unverified) |
| 2023–2024 H100 (8-GPU HGX, about 10.2 kW per node) | 20–45 kW air / rear-door | Meta's RoCE cluster: 2 servers (16 GPUs) per rack ([Llama 3](https://arxiv.org/abs/2407.21783)) |
| 2025 GB200 NVL72 | **≈120 kW** | ([Spheron, citing Lenovo](https://www.spheron.network/blog/nvidia-mgx-1-2-explained-what-250kw-open-racks-mean-for-gb300/)) |
| 2025–2026 GB300 NVL72 | **≈135 kW TDP, peaks around 155 kW** | Same source. Fairwater: about **140 kW per rack, 1,360 kW per row** ([DCD](https://www.datacenterdynamics.com/en/news/microsoft-launches-atlanta-fairwater-data-center-two-stories-no-ups-or-gen-sets/)) |
| 2026–2027 Vera Rubin NVL144 | 190–230 kW (unverified, NVIDIA has not confirmed) | 45 °C warm-water liquid cooling, liquid-cooled busbar ([NVIDIA](https://blogs.nvidia.com/blog/gigawatt-ai-factories-ocp-vera-rubin)) |
| 2027+ Rubin Ultra / Kyber | **≈600 kW** | 800 V DC |

Uptime's 2025 survey says most facilities are still in the **10–30 kW** band and few exceed 30 kW ([Uptime 2025 survey](https://intelligence.uptimeinstitute.com/resource/uptime-institute-global-data-center-survey-2025)). AI halls are an outlier class.

### 2.3 Room design elements (for the 3D view)

| Element | What it is | Visual cue |
|---|---|---|
| **Cold aisle / hot aisle** | Rack fronts face each other (cold aisle) and backs face each other (hot aisle). Invented at IBM in 1992 ([Strathclyde](https://www.esru.strath.ac.uk/EandE/Web_sites/09-10/Data_centres/Cooling_Approaches.html)). | Alternating aisles. Perforated tiles in front of racks on raised floors. |
| **Containment** | Hot-aisle containment (HAC) or cold-aisle containment (CAC): doors at row ends and a roof or chimneys. | Glass or polycarbonate sliding doors at aisle ends, ceiling panels, LED strips. |
| **Raised floor vs slab** | Legacy: 600×600 mm tiles 0.3–1.2 m above the slab, with cold air and cables underneath. Modern AI: **slab** (concrete) for weight, with everything overhead. | Raised floor = grey tiles with perforated vents. Slab = polished or sealed concrete, often with yellow/black safety striping. |
| **Overhead busway** | Rigid busbar track above the rows with tap-off boxes that drop power whips into each rack. | Long grey or white box sections with orange or yellow tap-off boxes. |
| **Cable trays** | Ladder or basket trays, often in tiers: power lowest, copper above, **fiber in yellow plastic raceway** (e.g. Panduit FiberRunner) at the top. | Yellow fiber ducts are iconic. Black or silver wire baskets. |
| **Liquid manifolds** | Supply and return pipes overhead or under the floor; rack manifolds with quick-disconnects (QDs). | Blue (supply, cool) and red (return, hot) hoses, stainless or insulated pipes, drip trays. |
| **CDUs** | Coolant distribution units, either in-row (cabinet size) or in a row-end gallery. | Cabinet-like units with pumps, gauges and touchscreens. |
| **Fan walls / CRAHs** | Large air handlers along the perimeter or in a gallery. | Arrays of fans behind grilles. |
| **Leak detection** | Rope sensors under pipes and racks. | Thin cable along the floor. |
| **Fire suppression** | Pre-action sprinklers (water held back until two signals), or clean agent (Novec 1230/FM-200, Inergen) in smaller rooms. VESDA aspirating smoke detection. | Red pipes at ceiling level, VESDA sampling pipes, gas cylinder banks. |

---

## 3. Power

### 3.1 The power chain (from grid to GPU)

```
Transmission grid (115–500 kV)
 └─ On-site HV substation (owned by the utility or the operator) ── HV breakers, main power transformers (e.g. 230 kV → 34.5 kV)
     └─ MV distribution ring (13.8–34.5 kV) ── MV switchgear
         └─ Unit substations / pad-mount transformers (MV → 415/480 V)
             ├─ Diesel or gas generators (2–3.5 MW each) + ATS/paralleling switchgear
             └─ UPS (static double-conversion or rotary/DRUPS) + batteries (VRLA or Li-ion, 5–10 min)
                 └─ LV switchboards → busways / PDUs / RPPs
                     └─ Rack: power shelves (AC→48 V DC or 800 V DC) → busbar → GPU tray VRMs
```

| Component | Typical numbers | Lead time and pain points |
|---|---|---|
| **Utility interconnection** | 100 MW – 1+ GW per campus | Median request-to-operation time for grid projects completed in 2024: **about 4.5 years** (LBNL, via [DCK](https://datacenterknowledge.com/energy-power-supply/why-ai-data-center-projects-face-years-of-delays-after-approval)). N. Virginia 100 MW connection: up to **7 years** (unverified). |
| **Large power transformers** | 50–300 MVA | Lead times rose from about 50 weeks (2021) to about 120 weeks (2024); range 80–210 weeks; **substation units above 160 weeks in 2026** (Wood Mackenzie, via [pv-magazine](https://pv-magazine-usa.com/2026/05/11/u-s-transformer-market-faces-severe-supply-constraints-as-lead-times-extend-to-four-years/)). Up to **4 years** for high-capacity units (PwC). |
| **Pad-mount / distribution transformers** | 1–5 MVA | **40+ weeks** ([GigaEnergy](https://www.gigaenergy.com/blog/lead-time-delays-for-data-centers), vendor blog) |
| **Switchgear** | MV/LV | "Effectively spoken for through 2028" at some suppliers (unverified) |
| **Diesel generators** | 2–3.5 MW each, N+1 or 2N; 24–72 h of fuel on site | Monthly no-load or load tests, annual load-bank tests, emissions permits. Large orders take 1–2 years (unverified). |
| **UPS + batteries** | 5–10 min ride-through to start generators | Li-ion is replacing VRLA. Battery string failures are a classic outage cause. AI load swings strain batteries (OECD incident monitor, [link](https://oecd.ai/en/incidents/2026-08-06-c38d)). |
| **Gas turbines / reciprocating engines on site** | 20–50 MW units | "Bridge power" while waiting for the grid (xAI Colossus). Permits matter: the EPA ruled in Jan 2026 that large turbines need permits even for temporary operation ([Wikipedia: Colossus](https://en.wikipedia.org/wiki/Colossus_(supercomputer))). |

**Design variant worth modelling:** Microsoft's **Fairwater Atlanta** has **no on-site generators or UPS**. It relies on a very resilient grid feed to target "4×9 availability at 3×9 cost" ([DCD](https://www.datacenterdynamics.com/en/news/microsoft-launches-atlanta-fairwater-data-center-two-stories-no-ups-or-gen-sets/)). This is a nice player choice: cheaper and faster to build, but a grid fault means downtime. Training workloads tolerate this because they can restart from checkpoints. Inference workloads tolerate it less.

**Redundancy tiers (Uptime Tier I–IV):** N (no redundancy) → N+1 → 2N (fully duplicated A/B feeds). AI training halls often use **N or N+1 for IT power** and keep 2N for networking, storage and control planes (unverified, common practice). A good game knob: **redundancy level vs. cost per MW**.

**Training load swings:** "tens of thousands of GPUs may increase or decrease power consumption at the same time… instant fluctuations… on the order of tens of megawatts, stretching the limits of the power grid" ([Llama 3, §3.3.4](https://arxiv.org/abs/2407.21783)). The mitigation is energy storage on the rack or campus. Vera Rubin racks add more energy storage for this reason ([NVIDIA](https://blogs.nvidia.com/blog/gigawatt-ai-factories-ocp-vera-rubin)).

### 3.2 PUE

PUE = total facility power ÷ IT power.

| Facility type | PUE |
|---|---|
| Global average (Uptime 2025) | **≈1.54**, flat for 6 years (value from a [secondary summary](https://mgrid.org/2025/10/01/uptime-institute-data-center-pue-stagnation-2025-liquid-cooling/); Uptime confirms "little change for the sixth consecutive year") |
| Hyperscale, best in class | 1.08–1.15 (Google fleet about 1.09–1.10, unverified) |
| Liquid-cooled AI halls | 1.10–1.25 (unverified) |
| Garage / office closet | 1.8–2.5+ (unverified) |

### 3.3 Energy procurement

| Mechanism | What it is | Real examples |
|---|---|---|
| **Utility tariff** | Buy from the grid at industrial rates (US $50–120/MWh; EU often €100–200/MWh, unverified) | Default |
| **PPA (physical or virtual)** | Long-term contract (10–25 years) with a specific generator | Solar and wind PPAs at hyperscalers |
| **Nuclear PPA / restart** | Buy the output of an existing or restarted reactor | **Microsoft–Constellation**: 20-year PPA for the restarted TMI Unit 1 ("Crane"), **837 MW**, about $100/MWh (unverified price), online around 2027–2028 ([DCF](https://www.datacenterfrontier.com/energy/article/55239739/data-center-energy-microsoft-three-mile-island)). **Google–NextEra** Duane Arnold restart, 25-year PPA, about Q1 2029. **Google–Kairos** 500 MW of SMRs. **Amazon–X-energy** up to 12 Xe-100 SMRs. **Meta** up to 6.6 GW across TerraPower, Oklo, Vistra and Constellation ([smrintel tracker](https://smrintel.com/nuclear-data-center-deals/), unverified aggregate) |
| **Behind-the-meter** | Generation co-located at the site and not routed through the grid | xAI gas turbines. Co-location next to nuclear plants (regulatory fights over grid-cost sharing) |

---

## 4. Cooling

### 4.1 Technology ladder

| Technology | Rack density supported | How it works | Visual | Game tier |
|---|---|---|---|---|
| **Room air (CRAC/CRAH)** | ≤ 10–15 kW | Perimeter units push cold air under the raised floor or into the room | Big beige or white cabinets at room edges | T0–T1 |
| **Contained air + in-row coolers** | 15–30 kW | In-row units between racks, with containment | Narrow cabinets interleaved with racks | T1–T2 |
| **Rear-door heat exchanger (RDHx)** | 30–60 kW (active fans up to about 75 kW, unverified) | Water coil in the rack's back door | Thick back doors with hoses at the bottom | T2 (retrofit option) |
| **Direct-to-chip (DLC), single-phase** | 60–250 kW+ | Cold plates on GPUs and CPUs, water/glycol (often PG25) at 25–45 °C, via manifolds and CDUs | Blue and red hoses, manifolds on rack backs | T3–T4 (mandatory for GB200+) |
| **Two-phase direct-to-chip** | 250 kW+ | Refrigerant boils on the cold plate | Similar, with thinner lines | Future tech |
| **Immersion (single-phase / two-phase)** | 100 kW+ per tank | Servers submerged in dielectric fluid | Horizontal tanks, servers lifted out by crane | Niche or crypto-style option. Messy servicing. |

Air still removes about 10–20% of heat even in DLC racks (power supplies, NICs, memory), so **hybrid air + liquid** is the norm (unverified).

**Adoption:** Uptime's 2025 cooling survey: perimeter air in 75% of facilities, **direct liquid cooling at 22%** ([Uptime 2025](https://intelligence.uptimeinstitute.com/resource/2025-cooling-systems-survey-results-and-crosstab-files)). The 2024 survey also found 22% using some DLC and 61% considering it. A Register survey: 38% expect to deploy liquid cooling within 2 years ([Bisnow](https://www.bisnow.com/news/national/data-center/inflection-point-one-in-three-data-centers-to-use-liquid-cooling-by-2026-report-says-123931)). All new frontier AI builds are liquid-cooled.

### 4.2 The heat-rejection chain

```
GPU cold plate → TCS loop (technology cooling system, in-rack)
  → CDU (liquid-to-liquid heat exchanger + pumps, N+1)
    → FWS (facility water system, 25–40 °C warm water)
      → Heat rejection: chillers (mechanical, compressor) and/or dry coolers (closed, no water)
        and/or evaporative cooling towers (open, consume water)
```

- **Chillers:** large compressor units (1–3 MW of cooling each, unverified), on roofs or in a "chiller yard". Azure Sydney 2023: a hall had **7 chillers (5 running + 2 standby)**. A power sag tripped all 5 and only 1 standby restarted ([The Register](https://www.theregister.com/2023/09/04/microsoft_australia_outage_incident_report/)).
- **Warm-water cooling (≥ 40–45 °C supply)** lets operators skip chillers most of the year ("free cooling" with dry coolers). Vera Rubin targets 45 °C liquid ([NVIDIA](https://blogs.nvidia.com/blog/gigawatt-ai-factories-ocp-vera-rubin)).
- **Cooling towers** must be drained or protected before freezing. Failing to do this caused the **CME/CyrusOne Nov 2025** outage ([DCK](https://www.datacenterknowledge.com/outages/cme-data-center-outage-caused-by-human-error-cyrusone-says)).
- **Microsoft Fairwater** uses a closed-loop liquid system whose initial fill equals the yearly water use of about 20 homes. It is refilled only if water chemistry drifts ([w.media](https://w.media/microsoft-launches-planet-scale-ai-superfactory/)).

### 4.3 Water (WUE = litres per kWh of IT energy)

| Operator / tech | WUE (L/kWh) | Source |
|---|---|---|
| AWS 2025 | 0.12 | [Oilprice](https://oilprice.com/Energy/Energy-General/The-AI-Boom-Could-Triple-Data-Center-Water-Use-by-2030.amp.html) |
| Meta 2024 | 0.19 | same |
| Microsoft FY2025 | 0.27 | same |
| Digital Realty 2025 | 0.59 | same |
| Equinix 2025 | 0.91 | same |
| Evaporative tower-cooled facility | about 1.5–2.4 (a 100 MW site evaporates about 1,800 m³/day) | [Datacentres.com](https://www.datacentres.com/news/data-centres-consumed-5-6-more-water-in-2025-as-ai-boom-strains-global-supply-slot3-2026-07-26) (sources conflict) |
| Closed-loop / dry coolers | ≈0–0.3 | various |

Game hook: **evaporative cooling = lower power and better PUE but high water use**. That creates local-politics and drought events. **Dry coolers = zero water but worse PUE in hot climates.**

---

## 5. Networking

### 5.1 Four networks in an AI datacenter

| Network | Purpose | Tech | Notes |
|---|---|---|---|
| **Scale-up (NVLink domain)** | GPU-to-GPU memory-semantic traffic inside a server or rack | NVLink / NVSwitch. 8 GPUs per HGX server; **72 GPUs per NVL72 rack** | The NVL72 spine is **5,184 copper cables, about 2 miles**. Optics would have added about 20 kW ([SemiAnalysis](https://newsletter.semianalysis.com/p/nvidias-optical-boogeyman-nvl72-infiniband), [The Register](https://www.theregister.com/2024/03/21/nvidia_dgx_gb200_nvk72)) |
| **Scale-out / back-end (GPU fabric)** | Gradient all-reduce across racks | **InfiniBand** (NVIDIA Quantum) or **RoCE Ethernet** (Spectrum-X, Arista, white-box). 400–800 Gb/s per GPU | InfiniBand held over 80% of AI back-end share in 2024. Dell'Oro expects Ethernet to pass it by 2028 ([Fierce](https://fierce-network.com/cloud/data-center-ethernet-nvidias-next-multi-billion-dollar-business)). Meta trained Llama 3 405B on RoCE. Fairwater uses a 2-tier 800 Gb/s Ethernet back-end. |
| **Front-end** | Storage, data loading, user/inference traffic, management | Standard Ethernet (100–400G) | Connects to the storage cluster (Meta: **240 PB on 7,500 servers, 2 TB/s sustained, 7 TB/s peak** for checkpoints ([Llama 3](https://arxiv.org/abs/2407.21783))) |
| **Out-of-band (OOB) management** | BMC/IPMI/Redfish, PDUs, CDUs, BMS | 1G copper | Separate switches in every rack. Lets you power-cycle a hung node. |

### 5.2 Topology: fat-tree / Clos

The canonical example, Meta's 24K-GPU RoCE cluster ([Llama 3 §3.3.1](https://arxiv.org/abs/2407.21783)):
- **Layer 1:** a ToR switch per rack (16 GPUs = 2 servers).
- **Layer 2:** **192 racks → 1 pod of 3,072 GPUs**, full bisection bandwidth (non-blocking).
- **Layer 3:** **8 pods → 24K GPUs**, aggregation layer **oversubscribed 1:7**. The scheduler is topology-aware and keeps traffic inside pods.
- Uses 16 flows per GPU pair plus enhanced ECMP for load balancing instead of DCQCN congestion control.

**Rail-optimised design:** NIC #k of every server connects to "rail k" leaf switches, so same-rank GPUs are one hop apart (unverified detail, standard NVIDIA SuperPOD practice).

### 5.3 Optics and cable counts (rough game numbers)

- Non-blocking 3-tier fat-tree: about **3 links per GPU at the scale-out layer** plus front-end links. With transceivers at both ends, that is **about 5–7 optical transceivers per GPU** at 100K+ GPU scale (unverified estimate; SemiAnalysis argues the NVL72 copper spine does not reduce optics per GPU).
- Transceiver generations: 400G → **800G (2024–26 mainstream)** → **1.6T (2026+)**. Co-packaged optics (CPO) switches are arriving from 2026 (unverified).
- Optical transceivers are a **top failure item**: lasers degrade, links flap, fiber connectors get dirty, and batches can be defective (see §6). A 100K-GPU cluster has hundreds of thousands of transceivers. Even a 0.1–0.5% annual failure rate means **hundreds of swaps per year** (unverified estimate).
- Cable types: **DAC** (passive copper, ≤ 2–3 m, in-rack), **AEC** (active copper, ≤ 7 m), **AOC** / **transceiver + MPO fiber** (row and building scale).

---

## 6. Operations and failures

### 6.1 What breaks, and how often. Primary data: Llama 3 405B (16K H100, 54 days)

466 interruptions in total: **47 planned** (firmware, kernel, config) and **419 unexpected** (about 7.8 per day, or **one every 3.1 hours**). About **78% hardware** (confirmed or suspected). **GPU issues = 58.7%**. Only **3 needed significant manual intervention**; automation handled the rest. Effective training time was **above 90%** ([Llama 3 paper, Table 5 and §3.3.4](https://arxiv.org/abs/2407.21783)).

| Component | Category | Count | % |
|---|---|---|---|
| Faulty GPU | GPU | 148 | 30.1% |
| GPU HBM3 memory | GPU | 72 | 17.2% |
| Software bug | Dependency | 54 | 12.9% |
| Network switch/cable | Network | 35 | 8.4% |
| Host maintenance | Unplanned maintenance | 32 | 7.6% |
| GPU SRAM memory | GPU | 19 | 4.5% |
| GPU system processor | GPU | 17 | 4.1% |
| NIC | Host | 7 | 1.7% |
| NCCL watchdog timeouts | Unknown | 7 | 1.7% |
| Silent data corruption | GPU | 6 | 1.4% |
| GPU thermal interface + sensor | GPU | 6 | 1.4% |
| SSD | Host | 3 | 0.7% |
| Power supply | Host | 3 | 0.7% |
| Server chassis | Host | 2 | 0.5% |
| IO expansion board | Host | 2 | 0.5% |
| Dependency | Dependency | 2 | 0.5% |
| CPU | Host | 2 | 0.5% |
| System memory | Host | 2 | 0.5% |

Note: the paper's percentages don't all match count/419 exactly (148/419 = 35.3%), but they are reproduced as printed.

**Other observations from the same paper (good flavour text):**
- **Diurnal 1–2% throughput variation**: mid-day heat triggers GPU DVFS throttling.
- **Stragglers**: a single slow GPU slows thousands. Finding them requires dedicated tooling.
- NVLink failures show up as **stalled CUDA kernels with no error code**, which makes them hard to debug.
- Checkpoints range from **1 MB to 4 GB per GPU**, and checkpoint writes saturate the storage fabric in bursts.

**Meta research clusters (A100, 11 months, 4M jobs, 150M GPU-hours):** **MTTF of 1,024-GPU jobs ≈ 7.9 hours, versus about 47.7 days for 8-GPU jobs** ([arXiv 2410.21680](https://arxiv.org/html/2410.21680v2); figure quoted via [Glenn Klockwood](https://www.glennklockwood.com/garden/papers/revisiting-reliability-in-large-scale-machine-learning-research-clusters), verify in the paper).

**Scaling rule for the game:** job failure rate ≈ N_GPUs × per-GPU failure rate. From Llama 3: 419 / (16,384 GPUs × 54 days) ≈ **4.7×10⁻⁴ interruptions per GPU per day**. So a job on **100K GPUs sees an interruption about every 30 minutes** (derived; real operators reduce this with better burn-in and hot spares).

### 6.2 Failure taxonomy for the game

| Failure | Typical symptom | Detection | Fix | Who |
|---|---|---|---|---|
| GPU fault / "fell off the bus" | Xid errors (e.g. Xid 79), job crash | DCGM, kernel logs | Drain node, reset, reseat, RMA the tray | DC tech + ML infra |
| HBM uncorrectable ECC | Xid 48/63/64, row remapping | DCGM | Row remap on reboot. Replace the GPU if remapping is exhausted. | Auto + DC tech |
| Silent data corruption (SDC) | Loss spikes, NaNs, wrong results with no error | Validation checks, deterministic replays | Identify and evict the bad GPU. Very costly to find. | Researchers + ML infra |
| NVLink / NVSwitch fault | Hangs, stalled kernels | NCCL watchdog / flight recorder | Replace the switch tray or cable cartridge | DC tech |
| Optics / cable flaps | Link down/up, packet loss, slow all-reduce | Switch telemetry, UFM | Clean the connector, swap the transceiver | Network tech |
| PSU / power shelf | Node or rack loss | BMC, PDU alarms | Hot-swap the PSU | DC tech |
| Fan / thermal | Throttling, over-temperature | BMC, DCGM temperature readings | Replace the fan or repaste the TIM | DC tech |
| CDU pump / leak | Rising coolant temperature, leak alarm | BMS, leak rope | Fail over to the redundant pump, isolate the loop, dry and replace | Facilities eng |
| Chiller / cooling tower | Room temperature climbing | BMS/EPMS | Restart, bypass, load-shed | Facilities eng (on site, 24/7) |
| Utility / UPS / generator | Power loss to a hall | EPMS | Transfer to generator, repair | Electrical eng + utility |
| Software (driver, NCCL, PyTorch) | Crashes, hangs | Logs | Patch or roll back | ML infra / SRE |
| Storage / checkpoint failure | Can't save or load | Monitoring | Fail over, re-replicate | Storage SRE |

### 6.3 Resilience techniques

| Technique | What it does | Realistic parameter |
|---|---|---|
| **Checkpointing** | Periodically save model/optimiser state | Every 10–60 min at frontier scale (unverified). Async or in-memory checkpointing cuts pause time. Lost work ≈ half the interval on average. |
| **Hot spares** | Keep N% of nodes idle so a failed node swaps in without waiting for repair | 1–5% of the fleet (unverified) |
| **Burn-in / acceptance testing** | Stress new nodes for days before production to weed out infant mortality | 1–2 weeks per batch (unverified) |
| **Automated health checks** | Pre-flight (DCGM diag levels 1–4), periodic, post-failure. Auto-drain bad nodes. | Most failures handled automatically (Meta: all but 3 of 466 in 54 days) |
| **Elastic / fault-tolerant training** | Continue with fewer replicas | Emerging |
| **Spares inventory & RMA** | Local cage of spare GPUs/trays, transceivers, PSUs, fans. RMA to the vendor or ODM. | RMA turnaround weeks to months (unverified). Running out of spares is a realistic event. |

### 6.4 Monitoring stack

| Layer | Tools |
|---|---|
| GPU | **NVIDIA DCGM** (health, Xid, ECC, temperature, power), dcgm-exporter → **Prometheus** → **Grafana** |
| Fabric | NVIDIA UFM (InfiniBand), switch gNMI/SNMP telemetry |
| Hosts | node_exporter, BMC/Redfish, syslog |
| Jobs | Slurm / Kubernetes (Kueue, Volcano) / in-house schedulers (Meta MAST), NCCL flight recorder |
| Facility | **BMS** (building management: HVAC), **EPMS** (electrical power monitoring), **DCIM** (asset, capacity). Lesson from Nebius 2026: environmental alerting should **not depend solely on the BMS** ([Nebius postmortem](https://nebius.com/blog/posts/incident-post-mortem-analysis-us-central1-service-disruption-on-august-19)). |
| Alerting / on-call | PagerDuty / Opsgenie; follow-the-sun or 24/7 on-site shifts |

### 6.5 Maintenance procedures

- **Method of Procedure (MOP)** for every non-trivial facility action, with peer review and a step-by-step checklist.
- **Change management** and maintenance windows. **Lockout/tagout (LOTO)** for electrical work. **Arc-flash PPE** for switchgear.
- **Planned maintenance**: generator load-bank tests (annual), UPS battery tests, IR thermography of electrical gear, chiller servicing, coolant chemistry checks (corrosion and biological growth in TCS loops), filter changes, firmware rollouts (Llama 3: rollouts caused **at least one interruption per day**).
- **Seasonal**: winterisation (drain or protect towers, as in CME 2025), summer peak load-shedding agreements with utilities (demand response).

### 6.6 Real outage examples (good event templates)

| Incident | What happened | Lesson / game mechanic |
|---|---|---|
| **Nebius us-central1, 19 Aug 2026** | A storm knocked out the **BMS and chilled-water loop**. No alert reached operators, who learned about it from GPU over-temperature alerts about 1 h 45 min later. Peak **58.5 °C inlet**. Racks tripped. Manual bypass and opened rack doors at about +2 h 45 min. Kubernetes recovery hit a disk-attach bug. Full GPU capacity restored about **24 h** later ([postmortem](https://nebius.com/blog/posts/incident-post-mortem-analysis-us-central1-service-disruption-on-august-19)) | Single point of failure in monitoring. Cold-start ordering. Recovery takes far longer than the root fix. |
| **CME / CyrusOne CHI1, 27–28 Nov 2025** | **Chiller plant failure**. Staff did not follow the procedure for **draining cooling towers before freezing**, and remediation made it worse. Global futures trading halted for about 10–11 h ([DCK](https://www.datacenterknowledge.com/outages/cme-data-center-outage-caused-by-human-error-cyrusone-says), [DCD](https://www.datacenterdynamics.com/en/news/cooling-issue-at-data-center-halts-futures-trading-for-cme-group/)) | Procedure compliance stat. Weather events. Choosing whether to fail over. |
| **Azure Australia East, Aug–Sep 2023** | A thunderstorm power sag tripped **5 of 5 running chillers**, and only 1 of 2 standby chillers restarted. **3 night staff** were too few. Microsoft raised it to 7. Impact up to about 46 h ([The Register](https://www.theregister.com/2023/09/04/microsoft_australia_outage_incident_report/), [DCD](https://datacenterdynamics.com/en/news/microsofts-slow-outage-recovery-in-sydney-due-to-insufficient-staff-on-site)) | Night-shift staffing directly affects recovery time. |
| **OpenAI, 11 Dec 2024** | A new **telemetry service** overloaded the Kubernetes API servers in large clusters, and DNS caching delayed the symptoms. Engineers were locked out of the control plane they needed for the fix. About 4 h 20 min outage ([OpenAI write-up](https://status.openai.com/incidents/ctrsv3lwd797/write-up)) | Software/config change events. "Lockout" mechanic. |
| **LRZ Munich AI systems, 25–26 May 2026** | **Grid power outage**, running jobs abruptly terminated, about 38 h to full restore ([LRZ status](https://status.lrz.de/issues/ai-systems/2026-05-25_offline-notice)) | Grid events. Unsaved progress lost since the last checkpoint. |
| **Groq US-Central, 1 Jul 2026** | Power loss → cooling failure, about 1.5 h ([pulsetic](https://pulsetic.com/status/groq/incidents/5076/)) | Power and cooling coupling. |
| **N. Virginia grid, 2024** | A single failed surge arrester dropped about **60 facilities / 1,500 MW** from the grid at once, and they all switched to generators (unverified, [dev.to summary](https://dev.to/ai_and_fitness_news_5eb6eaa63c/when-the-grid-goes-down-ai-infrastructure-crumbles-fast-kmc)) | Grid operators now worry about mass datacenter load drops. Regulatory events. |
| **xAI Colossus, 2024–2025** | Grid connection was slow, so it ran **about 35 gas turbines (~421 MW)** with permits for only 15. NAACP/SELC legal threat ([TechCrunch](https://techcrunch.com/2025/06/18/xai-is-facing-a-lawsuit-for-operating-over-400-mw-of-gas-turbines-without-permits)) | "Bridge power" choice with reputation and legal risk. |

Industry-wide (Uptime 2025 outage analysis): outage frequency and severity fell for the 4th straight year. **Power is still the #1 cause of impactful outages**. IT/network causes were **23%**. Human-error outages from **failure to follow procedures rose about 10 percentage points** ([Uptime press release](https://uptimeinstitute.com/about-ui/press-releases/uptime-announces-annual-outage-analysis-report-2025)).

---

## 7. Staff roles, ratios and salaries (drives the hiring system)

### 7.1 Ratios

| Context | Ops staff per MW | Source |
|---|---|---|
| Small site (1–5 MW) | 2–3 per MW | (unverified, [iRecruit](https://www.irecruit.co/insights/data-center-staffing-ratios-people-per-mw-2026)) |
| Colocation | 20–30 per 100 MW (0.2–0.3 per MW) | [Governing](https://www.governing.com/workforce/the-reality-of-data-center-jobs) |
| Hyperscale (>100 MW, automated) | 0.15–0.3 per MW | (unverified), e.g. Meta Hyperion about 1,000 permanent staff at 5 GW (≈0.2 per MW) |
| 24/7 minimum on-site crew, single building | 3 per shift is a known failure mode (Azure Sydney). 5–7+ per shift is safer. | [DCD](https://www.datacenterdynamics.com/en/analysis/staffing-levels-are-data-centers-at-risk-of-unnecessary-outages) |
| Construction peak | 1,000–5,000+ workers on a GW campus (unverified) | — |

Covering one 24/7 seat takes about **5.0–5.5 FTE** (168 h/week ÷ about 35 effective hours, plus holidays and sickness) (unverified rule of thumb, useful for the game).

**Suggested game ratios (tunable)**, per 1,000 GPUs at the T3/T4 level:
- DC technicians: 1–2 (more if density is low or reliability poor)
- Facilities (electrical/mechanical) engineers: about 0.5 per 10 MW
- Network engineers: about 1 per 5–10K GPUs
- SRE / ML infra: about 1 per 2–5K GPUs (software scales well)
- Security: 24/7 guards, about 5 FTE per guarded entry point
(all unverified, designer estimates derived from the ratios above)

### 7.2 Roles

| Role | Day-to-day | US salary (base, 2026) | EU salary (base, 2026) |
|---|---|---|---|
| **Data center technician (L1–L3)** | Racking and stacking, cabling, swapping GPUs/trays/PSUs/fans/optics, cleaning fiber, RMA paperwork, walk-throughs ("smart hands"), burn-in | Entry $45–62K, mid $60–85K, senior $85–110K ([Overwatch](https://smb.americanpress.com/article/Overwatch-Releases-Data-Center-Technician-Salary-Guide-for-Mission-Critical-Careers/6a4c2bf62095db0002a77cfa), [Kore1](https://www.kore1.com/data-center-jobs-2026/)). GPU/AI hardware techs $90–140K (unverified, [DCGeeks](https://dcgeeks.com/ai-data-center-jobs/)) | IE avg about €46K (€34–78K), NL about €47.5K, DE early-career about €52K ([PayScale IE](https://www.payscale.com/research/IE/Job=Data_Center_Technician/Salary)) |
| **Critical facilities engineer (electrical/mechanical, "CFE")** | Shift operation of UPS, generators, switchgear, chillers, CDUs. MOPs, LOTO, vendor supervision. First responder to facility alarms. | $75–95K entry, $100–135K mid, $140–185K senior ([Kore1](https://www.kore1.com/data-center-jobs-2026/)). Average about $112K (unverified, DCGeeks) | UK critical facilities tech £50–65K ([UK gov jobs](https://www.jobs.service.gov.uk/jobs/6a7a4c9bc2868c6068e9659c)). EU €55–90K (unverified) |
| **Facilities / site manager** | Owns site uptime, budget, contractors, compliance | $150–250K (unverified) | €90–150K (unverified) |
| **Network engineer (DC fabric)** | Design and operate the InfiniBand/RoCE fabric, triage link flaps, capacity planning, optics management | $130–220K (unverified) | €70–120K (unverified) |
| **SRE / production engineer** | On-call, automation, monitoring, incident response, control planes (Kubernetes/Slurm) | $160–300K base; total comp higher at big tech (unverified, levels.fyi typical) | €80–150K (unverified) |
| **ML infrastructure engineer** | Training framework, NCCL, checkpointing, scheduler, health checks, straggler detection, goodput | $180–350K base; frontier labs total comp $400K–1M+ (unverified) | €90–180K (unverified) |
| **Research scientist / engineer** | Design experiments, run training jobs, evals; cause and detect SDC/loss spikes | $200–400K base; top labs total comp $1M+ (unverified) | €90–200K (unverified) |
| **Security (physical)** | Guards, SOC operators, badge/biometric control, escorts, CCTV | $40–70K (unverified) | €30–50K (unverified) |
| **Security (cyber) / compliance** | IAM, SOC 2/ISO 27001 audits, model-weight security, export-control compliance | $150–250K (unverified) | €80–140K (unverified) |
| **Procurement / supply chain** | GPU allocations, transformer and switchgear orders, RMA logistics | $100–180K (unverified) | €60–110K (unverified) |
| **Energy / power procurement** | PPAs, utility negotiations, interconnection queue | $150–250K (unverified) | €90–150K (unverified) |

EU vendor guide context: engineers who "solve power bottlenecks, commission AI-ready halls, and optimise liquid cooling" are the top earners ([Eligo EU guide](https://eligo.sites.sourceflow.co.uk/insights/european-data-centre-salary-guide-2026/)).

---

## 8. Security and compliance basics

### 8.1 Physical security (layers, from outside in)

1. **Perimeter**: setback from the road, anti-ram fences and bollards (K-rated), guard house, vehicle inspection, perimeter cameras and thermal sensors.
2. **Building**: single staffed entrance, **mantrap/airlock** (one person at a time), badge plus **biometric** (palm vein or iris), visitor escort, weight-sensing portals.
3. **Data hall**: separate badge zone, cage locks (colo), CCTV covering every aisle with 90-day retention (unverified), no-tailgating policies.
4. **Rack**: locked doors and smart locks. **Media destruction**: drives shredded on site and never leave the building.
5. **Model weights** (AI-specific): frontier labs treat weights as crown jewels, with insider-threat programmes, two-person rules and restricted network egress (security levels as discussed in RAND's "Securing AI Model Weights", unverified mapping).

### 8.2 Compliance frameworks

| Framework | What it is | Game effect |
|---|---|---|
| **SOC 2 Type II** | AICPA audit of security, availability and confidentiality controls over 6–12 months | Unlocks enterprise customers. Annual audit cost. |
| **ISO/IEC 27001** | Information security management system | EU and international customers |
| **ISO 22301 / Uptime Tier certification** | Business continuity / facility tier | Raises SLA price |
| **PCI-DSS, HIPAA, FedRAMP** | Payments / health / US government | Niche customer unlocks (FedRAMP is slow and expensive) |
| **EU AI Act** (GPAI obligations from Aug 2025) and **EU Energy Efficiency Directive** (datacenters ≥ 500 kW must report energy and water) | Regulatory | Reporting events in the EU (unverified details) |

### 8.3 GPU export controls (status as of 2026)

- The US **AI Diffusion Rule** (Jan 2025, three-tier country system) was **rescinded in May 2025**. A replacement rule is still uncertain. BIS guidance says using **Huawei Ascend chips anywhere** may violate US export controls ([DCD](https://www.datacenterdynamics.com/en/news/department-of-commerce-formally-rescinds-ai-diffusion-rule-says-deploying-huawei-ascend-chips-violates-us-export-rules/), [NVIDIA 10-K FY2026](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm)).
- April 2025: H20-class GPUs required a licence for China. In 2026, H200 sales to China are reportedly allowed under conditions (unverified, single commentary source). The **GAIN AI Act** passed the Senate in the Oct 2025 NDAA (status uncertain).
- Operator obligations: **KYC on customers** (especially GPU cloud), end-use checks, no diversion to restricted entities. Chip smuggling cases are a recurring news theme.
- Game hook: a fictional **"compute export licence"** mechanic. Building in certain regions or selling compute to certain customers triggers licence delays and audits.

---

## 9. Visual reference (Blender / art direction)

### 9.1 What a modern AI data hall looks like

| Element | Description for modelling |
|---|---|
| **Overall mood** | Long, very regular, symmetrical rows that vanish into perspective. Cool white LED lighting (5000–6500 K), very clean. Floors in **light grey sealed concrete** (slab) or grey raised tiles (legacy). Ceilings 5–8 m high and full of infrastructure. |
| **Racks** | Matte **black** doors, mostly perforated mesh (hexagonal or round holes). NVL72 racks are fully black and roughly 0.6 m wide × 2.3 m tall × 1.2 m deep, with dense green/white status LEDs on the front trays. Some vendors use white or light grey racks (Meta, Google), so black vs white is an art-direction choice. |
| **Containment** | Transparent sliding doors at aisle ends with a coloured frame, often with a status light bar. Hot aisles are enclosed with a ceiling. |
| **Overhead** | **Yellow fiber raceways** (Panduit-style) are the signature colour accent. Black or chrome wire-basket trays for copper. Grey **busway** with orange/yellow tap-off boxes. Large insulated **liquid pipes** (white, blue, or green-grey insulation with coloured flow labels). |
| **Liquid cooling** | Blue (supply) and red (return) hoses dropping into the rear of each rack. Stainless manifolds. CDUs as cabinet-sized boxes with touchscreens and pressure gauges, often at row ends. Drip trays. |
| **Cable management in the back** | Thousands of thin cables: **aqua/turquoise** (OM3/OM4 multimode fiber), **yellow** (single-mode), black DAC copper, blue/red/green Cat6 for management. Neatly combed into vertical managers with velcro. |
| **Floor markings** | Yellow/black hazard striping, green emergency exit signage, red EPO (emergency power off) buttons on walls, fire extinguishers. |
| **Facility exterior** | Huge windowless rectangular sheds (grey or beige metal panels). Rooftop or yard **chillers / dry coolers** (rows of large fans). **Generator yard** with rows of container-sized gensets plus fuel tanks. **Substation** with transformers, gantries and insulators behind a fence. Cooling towers with visible plumes (if evaporative). |
| **Control room / NOC** | Dark room, video walls with Grafana-style dashboards, rows of desks with three monitors each. |
| **Garage stage** | Open-frame mining-style racks, a mix of consumer GPU boxes, a box fan, an extension-cord tangle, a whiteboard, a power meter display. |

### 9.2 Reference pages (open to collect images; check licences before reuse)

| Source | URL | What you'll find |
|---|---|---|
| Google data center gallery | https://www.google.com/about/datacenters/gallery/ | Famous colour-coded pipe photos, server rows, cooling plants (strong colour-coding art direction) |
| Meta data centers | https://datacenters.atmeta.com/ | Building exteriors, halls, white OCP racks |
| Microsoft Fairwater blog (Nov 2025) | https://blogs.microsoft.com/blog/2025/11/12/infinite-scale-the-architecture-behind-the-azure-ai-superfactory/ | Two-story AI hall, liquid-cooled GB200/GB300 racks, aerial site |
| NVIDIA GB200 NVL72 product page | https://www.nvidia.com/en-us/data-center/gb200-nvl72/ | Rack renders, compute trays, NVLink spine |
| NVIDIA OCP / Vera Rubin blog | https://blogs.nvidia.com/blog/gigawatt-ai-factories-ocp-vera-rubin | Next-gen rack renders, 800 VDC "AI factory" renders |
| ServeTheHome, xAI Colossus tour | https://www.servethehome.com/inside-100000-nvidia-gpu-xai-colossus-cluster-supermicro-helped-build-for-elon-musk/ | Real photos/video of a 100K-GPU liquid-cooled hall: Supermicro racks, CDUs, manifolds, network racks, cable trays |
| DCD Fairwater Atlanta article | https://www.datacenterdynamics.com/en/news/microsoft-launches-atlanta-fairwater-data-center-two-stories-no-ups-or-gen-sets/ | Hall photos |
| Crusoe Abilene (DCD) | https://datacenterdynamics.com/en/news/crusoe-tops-out-final-building-at-openai-stargate-data-center-campus-in-abilene-texas | Aerial campus construction shots (good for the T4 campus layout) |
| Wikimedia Commons, category "Data centers" | https://commons.wikimedia.org/wiki/Category:Data_centers | CC-licensed photos (server rooms, CERN, raised floors). Subcategories for server racks and cooling. |
| Wikimedia Commons, "Server racks" | https://commons.wikimedia.org/wiki/Category:Server_racks | CC-licensed rack and cable photos |
| OCP Open Rack specs | https://www.opencompute.org/projects/rack-and-power | Mechanical drawings for accurate rack geometry |

**Art-direction suggestion:** stylised low-poly with a **strong colour code** borrowed from Google's pipe photos:
- **Blue** = cold supply
- **Red** = hot return
- **Yellow** = fiber
- **Orange** = power busway
- **Green** = condenser water

Rack LEDs give status at a glance: green = healthy, amber = degraded/throttling, red = failed, blue pulsing = under maintenance. That gives a readable "datacenter view" where problems are visible spatially.

---

## 10. Proposed gameplay events (grounded in reality)

| # | Event | Cause (real-world basis) | Effect in game | Realistic mitigation (player levers) |
|---|---|---|---|---|
| 1 | **CDU pump failure → thermal throttling in Row C** | Pump bearing or VFD failure in a CDU. Single-pump CDUs or a failed redundant pump. | Row C GPUs throttle (−20–40% throughput) and then shut down if unresolved within N minutes. Training job slows or crashes. | N+1 pumps (capex), facilities engineer on shift, auto-failover, spare pump in stores. Load-shed the row to protect hardware. |
| 2 | **Storm takes out the BMS and chillers** | Nebius Aug 2026: halls overheat in about 2 h, 58.5 °C inlet | Hall-wide temperature rises over minutes. Cascading rack trips. Recovery takes hours, with extra delay from a software cold-start bug. | Independent environmental alerting (an upgrade), manual bypass SOP, an emergency load-shedding plan, cold-start drills (training stat). |
| 3 | **Transformer lead time blocks expansion** | Large power transformers take 120–210 weeks (Wood Mackenzie) | The new building is finished but cannot energise for 2–4 game-years | Pre-order transformers early (cash locked up), buy refurbished units at a premium, bridge with on-site gas turbines (permit risk), accept partial energisation. |
| 4 | **Grid interconnection queue** | Median about 4.5 years to connect; up to 7 years in N. Virginia | Campus site sits idle. Opportunity cost. | Pick sites with available power (secondary markets), co-locate with a power plant, sign a behind-the-meter deal, hire an energy procurement lead. |
| 5 | **Optics batch defect** | A bad transceiver lot (laser degradation) | Link flaps across many racks. All-reduce slows 10–30%. Repeated NCCL timeouts. | Burn-in testing (delays deployment), dual-source vendors, keep spare optics, network engineer fleet-wide swap campaign, vendor RMA (weeks). |
| 6 | **HBM ECC storm in a new GPU batch** | Infant mortality. HBM is 17% of Llama 3 interruptions. | Elevated failure rate on new nodes for the first weeks | Longer burn-in, hot spares, faster RMA contracts, ML infra health-check automation. |
| 7 | **Silent data corruption** | A defective GPU computes wrong values with no error (6 cases in 54 days at 16K GPUs) | Loss spike or NaN in a training run. Research must roll back to an earlier checkpoint, losing days. | Periodic deterministic checks (cost: about 1–2% throughput), keep older checkpoints, research and ML infra skill. |
| 8 | **Night-shift understaffing slows recovery** | Azure Sydney 2023: 3 people could not restart chillers in time | Any facility incident at night has longer recovery time if fewer than X facilities staff are on shift | Hire to 24/7 coverage (about 5 FTE per seat), automation of chiller restart sequences. |
| 9 | **Cooling-tower freeze (procedure not followed)** | CME/CyrusOne Nov 2025 | Winter event: chillers fail, about 10 h outage. Reputation hit with inference customers. | SOP quality and training stat, a winterisation checklist task, switch to dry coolers (no freeze risk). |
| 10 | **Grid frequency event / load-drop alarm** | Large training jobs swing tens of MW (Llama 3). Grid operators fear mass datacenter load drops (N. Virginia 2024). | The utility demands a ride-through or curtailment. Fines or forced power caps. | Rack- or campus-level battery storage, power-smoothing software (dummy GPU load during checkpoints), demand-response contract (earns money). |
| 11 | **Telemetry rollout overloads the control plane** | OpenAI Dec 2024 | Inference API down for about 4 h. Engineers locked out of the fix. | Staged rollouts (a canary policy), break-glass access, SRE headcount, change-review policy. |
| 12 | **Heat-wave diurnal throttling** | Llama 3: 1–2% daily throughput variation from heat | Summer reduces throughput across air- or dry-cooler-cooled sites. Worse in hot regions. | Warm-water DLC, evaporative assist (costs water), schedule heavy jobs at night, site selection in cool climates. |
| 13 | **Water-use controversy / drought restriction** | Evaporative sites use about 1.5–2.4 L/kWh. Local pushback. | Municipality caps water. PUE worsens if you switch to dry mode. Permit delays for the next building. | Closed-loop cooling (Fairwater-style), reclaimed water, community investment. |
| 14 | **Unpermitted bridge turbines lawsuit** | xAI Memphis: about 35 turbines with permits for 15 | Fines, injunction, reputation drop. Possible forced shutdown of turbines → less MW. | Get permits first (slower), buy cleaner units, accelerate the grid substation. |
| 15 | **Export-control rule change** | AI Diffusion Rule issued, then rescinded. Licences for China-bound GPUs. | GPU orders for an overseas site frozen, or a customer becomes ineligible | Compliance officer hire, diversify site locations, KYC processes. |
| 16 | **Generator fails to start during a utility outage** | Classic: battery or starter failure, fuel contamination | UPS runs out after about 5–10 min, then the hall goes dark. Running jobs lose progress since the last checkpoint. | Monthly generator tests (maintenance tasks with cost), N+1 generators, fuel polishing contracts, frequent checkpoints. |
| 17 | **Coolant leak in a rack** | Quick-disconnect failure or a cracked hose | Rack powered off, nearby trays at risk. Tech must isolate, dry and replace parts. | Leak detection ropes, drip trays, negative-pressure CDU option, quality QDs, trained techs. |
| 18 | **Spares stockout** | RMA backlog plus a supply shortage of GPUs and trays | Failed nodes stay down for weeks. Effective cluster size shrinks. | Spare-pool policy (1–5% of capex), a vendor advance-replacement contract, cannibalise lower-priority clusters. |
| 19 | **Straggler node** | A degraded but working GPU or NIC (Llama 3 notes a single straggler slows thousands) | Training slows 5–20% without obvious errors | Straggler-detection tooling (an ML infra research unlock), drain and replace. |
| 20 | **Physical intrusion / insider threat on model weights** | Model-weight theft is a recognised risk | Competitor gains your model tech. Reputation hit. | Mantraps, biometrics, two-person rule, security staff, network egress controls, SOC 2 controls. |

### 10.1 Suggested simulation constants (tunable starting points)

| Parameter | Suggested value | Basis |
|---|---|---|
| Unexpected interruptions per GPU per day | 4.7×10⁻⁴ (H100-era, mature ops) | Llama 3: 419 / (16,384 × 54) |
| Share by cause | GPU 59%, software 13%, network 8%, host/maintenance 13%, other 7% | Llama 3 Table 5 (grouped) |
| Time lost per interruption | Checkpoint interval ÷ 2 + restart time (5–30 min) | Derived |
| Effective training time | 85–95% at good ops; 50–70% at poor ops | Llama 3 ">90%"; poor-ops figure unverified |
| Facility power per GPU (GB300 era, all-in) | 1.6–2.0 kW | Derived from about 135 kW per 72-GPU rack × PUE 1.2 + overhead |
| PUE by cooling tier | Garage 2.0, colo air 1.5, contained 1.35, RDHx 1.25, DLC 1.12 | Uptime 1.54 average; others unverified |
| Time to overheat after total cooling loss | 5–15 min (high-density DLC) to about 2 h (air hall with thermal mass) | Nebius about 2 h; DLC figure unverified |
| Transformer lead time | 2–4 years (large); about 1 year (pad-mount) | Wood Mackenzie / PwC |
| Grid connection wait | 2–7 years | LBNL median 4.5 years |
| Ops staff per MW | 2–3 (small) → 0.2 (hyperscale) | §7.1 |
| Colo price | $150–235 per kW/month (US Tier 1) | CBRE Q1 2026 |

---

## Sources (main)

- Meta, *The Llama 3 Herd of Models* (2024): https://arxiv.org/abs/2407.21783
- Meta, *Revisiting Reliability in Large-Scale ML Research Clusters*: https://arxiv.org/html/2410.21680v2
- Nebius us-central1 postmortem (Aug 2026): https://nebius.com/blog/posts/incident-post-mortem-analysis-us-central1-service-disruption-on-august-19
- CME/CyrusOne: https://www.datacenterknowledge.com/outages/cme-data-center-outage-caused-by-human-error-cyrusone-says ; https://www.datacenterdynamics.com/en/news/cooling-issue-at-data-center-halts-futures-trading-for-cme-group/
- Azure Sydney 2023: https://www.theregister.com/2023/09/04/microsoft_australia_outage_incident_report/
- OpenAI Dec 2024 write-up: https://status.openai.com/incidents/ctrsv3lwd797/write-up
- Uptime Institute outage analysis 2025: https://uptimeinstitute.com/about-ui/press-releases/uptime-announces-annual-outage-analysis-report-2025
- Uptime Global Survey 2025: https://intelligence.uptimeinstitute.com/resource/uptime-institute-global-data-center-survey-2025
- Uptime Cooling survey 2025: https://intelligence.uptimeinstitute.com/resource/2025-cooling-systems-survey-results-and-crosstab-files
- Microsoft Fairwater: https://blogs.microsoft.com/blog/2025/11/12/infinite-scale-the-architecture-behind-the-azure-ai-superfactory/ ; https://www.datacenterdynamics.com/en/news/microsoft-launches-atlanta-fairwater-data-center-two-stories-no-ups-or-gen-sets/
- Epoch AI, Stargate sites: https://epoch.ai/blog/openai-stargate-where-the-us-sites-stand
- Crusoe Abilene: https://www.datacenterdynamics.com/en/news/crusoes-abilene-data-center-officially-live-serving-oracle-and-openais-stargate/
- xAI turbines: https://techcrunch.com/2025/06/18/xai-is-facing-a-lawsuit-for-operating-over-400-mw-of-gas-turbines-without-permits ; https://en.wikipedia.org/wiki/Colossus_(supercomputer)
- NVIDIA OCP / Vera Rubin: https://blogs.nvidia.com/blog/gigawatt-ai-factories-ocp-vera-rubin
- DCD rack density / Kyber: https://datacenterdynamics.com/en/analysis/nvidia-gtc-jensen-huang-data-center-rack-density
- SemiAnalysis NVL72 copper: https://newsletter.semianalysis.com/p/nvidias-optical-boogeyman-nvl72-infiniband
- Transformer lead times: https://pv-magazine-usa.com/2026/05/11/u-s-transformer-market-faces-severe-supply-constraints-as-lead-times-extend-to-four-years/
- Grid delays: https://datacenterknowledge.com/energy-power-supply/why-ai-data-center-projects-face-years-of-delays-after-approval
- Nuclear deals: https://www.datacenterfrontier.com/energy/article/55239739/data-center-energy-microsoft-three-mile-island ; https://smrintel.com/nuclear-data-center-deals/
- Water WUE: https://oilprice.com/Energy/Energy-General/The-AI-Boom-Could-Triple-Data-Center-Water-Use-by-2030.amp.html
- CBRE 2026 trends: https://www.cbre.com/insights/reports/global-data-center-trends-2026
- Export controls: https://www.datacenterdynamics.com/en/news/department-of-commerce-formally-rescinds-ai-diffusion-rule-says-deploying-huawei-ascend-chips-violates-us-export-rules/
- Salaries: https://www.kore1.com/data-center-jobs-2026/ ; https://eligo.sites.sourceflow.co.uk/insights/european-data-centre-salary-guide-2026/ ; https://www.payscale.com/research/IE/Job=Data_Center_Technician/Salary
- Staffing: https://www.governing.com/workforce/the-reality-of-data-center-jobs ; https://www.datacenterdynamics.com/en/analysis/staffing-levels-are-data-centers-at-risk-of-unnecessary-outages
