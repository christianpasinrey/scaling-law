# 04 — Design References: AI Lab Tycoon (Three.js + TS, web, FOSS)

> Research date: 2026-10-24. Purpose: inspiration, **not** copying. Each reference lists what to **borrow** and what to **avoid**. Claims are cited; items marked *(unverified)* come from memory or thin sources and should be checked before relying on them.

---

## 0. Headline findings

1. **The niche is getting crowded fast.** In 2026 alone there are at least five AI-lab tycoons on Steam (LLM Tycoon, AI Lab Tycoon, Model Co., AI Startup Simulator, Artificial Ambition), plus a datacenter sim wave (Data Center, Cloud Server Simulator, Datacenter Simulator). **LLM Tycoon even has an in-game social feed called "Chirp"** for rival CEOs. Our differentiators must be: (a) free/open-source and in the browser, (b) the **living "brain" overlay tied to real GPU topology**, (c) a feed of *customer conversations* (not CEO tweets) that directly reads out service quality.
2. **The datacenter sims' best idea is visible traffic.** Waseku's *Data Center* shows customer traffic as coloured packet-balls moving through cables, which makes bottlenecks and idle links visible at a glance. That is the same instinct as our brain overlay: make throughput *visible*, not a number.
3. **The most common complaint across all business tycoons is mid/late-game repetition and micromanagement** (Software Inc., Game Dev Tycoon, City Game Studio, Crypto Mining Simulator). Delegation and new "verbs" at each scale tier are the standard fixes.

---

## 1. Management / tycoon games

### Cities: Skylines (Chirper, info views)
- **What it is:** Chirper is a Twitter-like feed showing how residents feel about your decisions. In C:S2 it got a "like" button and functions mainly as a feedback mechanism ([netzwelt.de](https://www.netzwelt.de/news/221707-cities-skylines-2-entwickler-integrieren-bug-neues-feature.html), [Game Informer review](https://gameinformer.com/review/cities-skylines-ii/utopian-thinking)). Info views (traffic, pollution, power, etc.) recolour the whole city to show one metric.
- **Borrow:**
  - Feed as *qualitative telemetry*: each post is a human-readable symptom of a simulation variable (latency, refusals, hallucination rate, downtime).
  - **Clickable posts** that jump the camera to the cause (the rack that's overheating, the model capability that failed).
  - Info-view pattern: one key toggles the datacenter into a **heatmap mode** (thermals, utilisation, power draw, failure risk), desaturating everything else.
- **Avoid:** TechRadar describes the C:S2 Chirper inbox filling with repeated, sometimes unreasonable complaints, turning criticism into a nuisance ([TechRadar](https://www.techradar.com/gaming/consoles-pc/cities-skylines-2-has-created-my-arch-nemesis-and-its-made-me-love-the-game-more)); C:S1 players asked how to stop the auto-open and chirp sound ([Steam thread](https://steamcommunity.com/app/255710/discussions/0/613958868364268310)). → **Deduplicate, rate-limit, aggregate** ("+214 users said the same"), never auto-open, never repeat unlock spam, mute option.

### Factorio (throughput, bottleneck visualisation)
- **Borrow:** Throughput as the core fantasy; production statistics graphs per item; "alt-mode" style overlay showing what each machine is doing. Community mods like EfficienSee display underemployed, blocked or starved machines on the map ([Factorio forum](https://forums.factorio.com/viewtopic.php?p=185968)) — i.e. players *want* bottleneck flags. Map to: GPU **starved** (no requests / waiting on network), **blocked** (memory-bound / thermal throttling), **saturated** (queue growing).
- **Avoid:** Factorio's depth relies on player-built layouts; we have no conveyor puzzle. Don't fake complexity with layout minutiae (cable routing per port) unless it's optional.

### Two Point Hospital (staff hiring / traits / rooms)
- **What it is:** Candidates shown with star ability, qualifications and up to five positive/negative traits; more stars and traits mean higher hiring/retention costs; staff can be trained ([Fandom wiki](https://two-point-hospital.fandom.com/wiki/Staff), [PCGamesN review](https://www.pcgamesn.com/two-point-hospital/two-point-hospital-review)).
- **Borrow:** A **small hiring pool that refreshes** (forces trade-offs), traits with humour ("Benchmarks Obsessively", "Ships Fridays", "Ex-Big-Lab"), training room = "reading group" that adds qualifications. Visual comedy of staff walking around and reacting.
- **Avoid:** Training/promotion admin at 50+ staff. Introduce **leads/managers** who auto-handle hiring for their team (see Software Inc. below).

### Prison Architect *(general knowledge)*
- **Borrow:** Clean top-down readability with "needs" overlays; reports screen that explains *why* a metric moved; grants as early-game funding with explicit objectives (PA's government grants fit our "grants" mechanic one-to-one).
- **Avoid:** Grant objectives that are pure checklists. Ours should be thematic (e.g., "serve 10k free medical-question conversations with <2% unsafe answers").

### RimWorld (event storytelling)
- **What it is:** A "story generator," not a competitive strategy game. An AI storyteller (modelled on Left 4 Dead's AI Director) analyses your situation and picks events for the best narrative; presets: Cassandra (rising/falling tension), Phoebe (more downtime), Randy (random) ([Wikipedia](https://en.wikipedia.org/wiki/RimWorld), [RimWorld wiki](https://rimworldwiki.com/wiki/About_RimWorld)).
- **Borrow:** An **event director** that reads company state (cash runway, hype, uptime, safety rep) and schedules events: GPU shortage, power outage, viral jailbreak, star researcher poached, regulator inquiry, a customer's heartfelt thank-you going viral. **Difficulty = director personality** (e.g. "Steady Board", "Hype Cycle", "Chaos Market").
- **Avoid:** Unfair spikes with no counterplay. Every negative event needs a visible warning signal or a mitigation lever.

### Startup Company *(general knowledge; review aggregators had no data)*
- **Borrow:** Building features → shipping → user growth loop; the office as a visible growing space.
- **Avoid:** *(unverified, from memory)* players commonly report a grindy mid-game of dragging components between employees. Avoid manual piece-shuffling as the main verb.

### Software Inc.
- **Praise:** deep, addictive once learnt; modding. **Complaints:** steep curve, weak tutorial, repetitive early contract grind, **excessive micromanagement that grows with company size**, late game repetitive, lag at 300+ employees, cluttered UI ([VaporLens summary](https://vaporlens.app/app/362620)). Players reduce burden by **delegating to C-level executives**.
- **Borrow:** Delegation as an unlock — hiring a COO/CTO/CFO literally removes a category of manual work and becomes a progression reward.
- **Avoid:** Cluttered spreadsheet UI; performance cliffs with many agents (we must instance staff and LOD them).

### Game Dev Tycoon (research → release → reviews)
- **Praise:** core design→release→improve loop; satisfying garage-to-company growth; easy to learn. **Complaints:** opaque, luck-driven review scoring; repetitive after a few playthroughs; weak tutorial ([VaporLens summary](https://vaporlens.app/app/239820)).
- **Borrow:** Discrete **"launch day" moments** with a review/benchmark reveal — perfect fit for "release next model": the leaderboard reveal, press reactions, Chirper-style feed explosion, stock jump/drop. Garage → office → campus transitions (literal map changes).
- **Avoid:** **Opaque scoring.** Show the benchmark breakdown (coding, reasoning, safety, speed, cost) and *why* each moved, so success feels earned not random.

### Data Center (Waseku, released 2026-03-31) — **verified, exists**
- Buy/place racks, servers, switches; run cables by hand; **traffic shown as coloured packet-balls along cables, making bottlenecks and idle links visible**; XP unlocks hardware; reputation attracts bigger clients; hardware ages and fails, rewarding redundancy. Steam: Mostly Positive, 76% of ~984 reviews ([Steam](https://store.steampowered.com/app/4170200/Data_Center/), [It's FOSS preview](https://itsfoss.com/data-center-game/)).
- Siblings: Cloud Server Simulator (Early Access, Sept 2025) ([Deku Deals](https://www.dekudeals.com/items/cloud-server-simulator)), first-person Datacenter Simulator, Hosting Simulator, Server-Admin Simulation (closet → datacenter).
- **Borrow:** Visible traffic; hardware ageing/failure + redundancy as a meaningful choice; reputation tiers unlock bigger customers.
- **Avoid:** Manual per-port cabling as the main activity (fun at 10 servers, chore at 1,000). Our scale goes to rack-scale systems — **abstract cabling into "pods/fabric" upgrades** once past the garage.

### Universal Paperclips (AI theme, incremental)
- Growth plateaus; the player invests money/materials/compute into a breakthrough to reach the next phase. Phases change the *game itself* (business → hypnodrones → space), with late game scaling by orders of magnitude ([Wikipedia](https://en.wikipedia.org/wiki/Universal_Paperclips), [GamesBeat](https://gamesbeat.com/this-clicker-game-lets-you-take-over-the-world-with-paper-clips/)).
- **Borrow:** **Plateau → breakthrough** rhythm; phase shifts that change the UI and verbs; minimal text that carries enormous thematic weight; the slow realisation of what the AI is becoming.
- **Avoid:** Pure number-go-up with no spatial/visual payoff — we have a 3D world; use it.

### Frostpunk (tension, moral choices)
- Book of Laws: branching, mostly **irreversible** laws with short- and long-term effects on Hope/Discontent; early laws mild, later ones darker; cooldown between laws ([PC Gamer](https://www.pcgamer.com/au/frostpunk-developers-on-hope-misery-and-the-ultimately-terrifying-book-of-laws), [Destructoid](https://destructoid.com/?p=220323)).
- **Borrow:** A **Policy Book** for the lab: data sourcing (licensed vs. scraped), safety evals before release vs. ship-fast, open-weights vs. closed, ad-supported tier, military contracts, layoffs vs. dilution. Two meters akin to Hope/Discontent: **Public Trust** and **Board/Investor Pressure**. Irreversibility + cooldown create weight.
- **Avoid:** Moralising. Present trade-offs neutrally; let consequences (feed, stock, staff morale, regulators) speak.

### Mini Metro (clean abstract UI)
- Minimalism born of constraint; geometric shapes carry all information; GDC 2017 "When Less Is More" on how UI/visual decisions create reward ([GDC news](https://gdconf.com/news/attend-gdc-2017-and-learn-the-value-of-less-is-more-from-a-mini-metro-dev), [Giant Bomb interview](https://giantbomb.com/users/3929/articles/interview-peter-curry-co-creator-of-mini-metro)).
- **Borrow:** The **brain overlay should be Mini Metro-grade legible**: shape + colour encode state, few elements, crisp motion. Overcrowding = growing ring around a node, same as Mini Metro's station timer.
- **Avoid:** Decorative noise. Every glowing thing must mean something.

### Satisfactory / Anno (production & economy chains)
- **Borrow (Satisfactory):** Tier milestones that unlock new *buildings* and visibly change the factory; awe of scale walking through what you built (camera fly-through of the datacenter when a new hall opens). **(Anno):** population tiers with escalating needs — map to **customer tiers** (hobbyists → startups → enterprises → governments), each demanding new capabilities (uptime SLA, data residency, safety certs).
- **Avoid:** Long resource chains (we're not about ore). Keep the chain short: **power → compute → model → customers → money/reputation → research → better model**.

### Capitalism Lab / Offworld Trading Company (markets & stock)
- Capitalism Lab: issue shares, buybacks, corporate takeovers; a stock view with 1/3/5/10-year performance ([capitalismlab.com](https://www.capitalismlab.com/?p=11605), [newsletter](https://www.enlight.com/dada/mail.cgi/archive/CapLabOwner/20200218052829/)).
- Offworld: prices move with supply/demand; buying raises and selling lowers price; Soren Johnson made the market the core and avoided buy/sell spreads that discourage market play ([Designer Notes #2](https://www.designer-notes.com/otc-designer-notes-2-free-markets/), [Shacknews](https://www.shacknews.com/article/93533/offworld-trading-company-taking-stock-in-space)).
- **Borrow:** Stock price driven by **legible drivers** (revenue growth, benchmark rank, hype index, incidents) plus a sector "AI bubble" sentiment wave; **GPU spot market** whose price reacts to global demand events (shortages, new-gen launch → used-GPU price crash). Funding rounds = dilution vs. runway trade-off; IPO as a mid-game phase change.
- **Avoid:** A stock price that's random noise, or full order-book trading that turns the game into a finance sim. One-click actions only (raise, buy back, issue).

---

## 2. Existing AI-company / GPU-farm / datacenter / mining games

| Title | Status | Notable mechanics | Lesson |
|---|---|---|---|
| **LLM Tycoon** (Futt Studio) | Demo; 2026 planned | Starts late 2022; six "ages" (Chat→Scale→Multimodal→Agentic→Superintelligence→Ascendancy); personality sliders (honesty, safety, tone) that can cause scandals; datacenters in 30 countries; espionage, IPO; **rival CEOs post on "Chirp"** ([Steam demo](https://store.steampowered.com/app/5071100/), [Steam](https://store.steampowered.com/app/4861430/)) | Strong direct competitor in theme. **Don't do world-map geopolitics; go deep on the physical datacenter + brain.** Rename our feed to avoid a "Chirp" clone. |
| **Model Co.** (TiredRocks) | Released 2026-07-24, ~$2 | Pick model type/product/scale, assign staff; models decay against a moving frontier; burnout, poaching; MRR, churn, inference cost; payroll miss = game over; IPO & AI-bubble meter ([Steam](https://store.steampowered.com/app/4894580/Model_Co/)) | "Models decay vs. frontier" is a great anti-stagnation pressure. Inference cost as a real line item is exactly our GPU fantasy. |
| **AI Lab Tycoon** (BT Games) | 2026 planned | 2016 start, 20-year arc to superintelligence ([Steam](https://store.steampowered.com/app/5015590)) | Historical arc framing is common; a fictional timeline keeps us free of real-company baggage. |
| **AI Startup Simulator** | Q4 2026 planned | First-person; buy GPUs, servers, cooling ([search listing](https://store.steampowered.com/app/5075960)) *(listing details unverified)* | First-person hardware fantasy validates Blender GPU models, but we are top-down management. |
| **Data Center** (Waseku) | Released 2026-03 | See §1 | Visible traffic flow. |
| **Crypto Mining Simulator** | Released | ~64% positive; reviews complain of repetition and abandonment, praise low-spec performance ([raijin.gg](https://raijin.gg/app/1596310/Crypto_Mining_Simulator), [wasdland](https://www.wasdland.com/game/crypto-mining-simulator-1596310/)) | Hardware-buying alone isn't enough content; needs goals/events. |
| **Crypto Miner Tycoon Simulator** | Released | ~83–88% positive ([Steam Starter Ed.](https://store.steampowered.com/app/2304990/Crypto_Miner_Tycoon_Simulator_Starter_Edition/)) | Market reaction (coin price ↔ hardware value) is a liked loop. |
| **PC Building Simulator** *(general knowledge)* | Released | Licensed real parts, accurate specs, satisfying assembly | Hardware *realism* sells — but we'll use **fictional** brands with plausible spec curves (FLOPS, VRAM, interconnect, watts) to stay FOSS-safe. |

**Common player complaints in this genre** (from §1 & §2 sources): repetitive mid/late game; micromanagement scaling with size; opaque scoring; weak tutorials; cluttered UI; performance collapse at scale; content abandonment.

---

## 3. Futuristic / sci-fi UI references

| Reference | Borrow | Avoid |
|---|---|---|
| **Dead Space** (RIG health on suit, holographic menus) — GDC 2013 "Crafting Destruction" ([Game Developer](https://gamedeveloper.com/design/video-designing-i-dead-space-i-s-immersive-user-interface), [HUDs+GUIs](https://www.hudsandguis.com/2012/08/22/dead-space-2-diegetic-interface-design)) | Diegetic status: GPU health shown on the rack itself (LED strips, tiny holo-labels) | Its holographic 3D map *failed* for navigation; fix was a simple ground locator ([Game Developer analysis](https://www.gamedeveloper.com/design/game-ui-discoveries-what-players-want)). → Critical info must stay in a flat, screen-space layer. |
| **Hardspace: Shipbreaker** — GDC 2021 diegetic UI + accessibility ([GDC Vault](https://gdcvault.com/play/1027036/Cutting-Apart-The-Diegetic-Interface)) | How to keep diegetic UI accessible (scaling, contrast options) | Full diegesis at the cost of usability |
| **Territory Studio** (film FUI: Avengers, Blade Runner 2049, Guardians) — their stated goal is **audience comprehension first**; "a simple map with a line between two points" ([VFX Voice/interview](https://vfxvoice.com/?p=13143400), [Pushing Pixels interview](https://www.pushing-pixels.org/2014/08/07/the-craft-of-screen-graphics-and-movie-user-interfaces-interview-with-david-sheldon-hicks-of-territory-studio.html), [HUDs+GUIs FUI](https://www.hudsandguis.com/fui-media)) | Layered motion, thin strokes, monospace numerics, "boot-up" transitions; one clear focal point per panel | Film UI is watched for 3 seconds, not used for 30 hours — dense decorative glyphs exhaust players |
| **Mass Effect / Deus Ex / Destiny / Cyberpunk 2077** *(general knowledge)* | ME: radial/holo omni-tool aesthetics, faction colour coding. Deus Ex HR: restrained gold/black palette = strong identity. Destiny: generous spacing, big type, calm motion — the most *usable* "futuristic" menus. CP2077: glitch/scanline flavour for alerts only. | CP2077's small, low-contrast red text was widely criticised *(unverified specific source)* — avoid low contrast and tiny type |
| **Hacknet / Observation** *(general knowledge)* | Hacknet: terminal-as-gameplay; a CLI-flavoured log panel for power users. Observation: you *are* the station AI — framing the player's view as the model's own perception (fits the "brain" overlay) | Text walls; making the player type commands to do basic actions |
| **Oblivion (2013) / Iron Man** *(GMUNK/ Territory-era aesthetics)* | Clean white/cyan on dark glass, large readable numerals, radial gauges | Over-animation; everything moving at once |

**Readability rules for a futuristic UI (synthesis):**
1. Two layers: **diegetic flavour** (in-world holo labels, rack LEDs) + **screen-space truth** (flat panels with numbers). Never put decision-critical info only in 3D.
2. Contrast ≥ WCAG AA for all text; glow is decoration around text, not the text itself.
3. Max **one animated element per panel** at rest; motion means "changed" or "needs attention".
4. Colour budget: 1 neutral glass, 1 brand accent (e.g., cyan), 3 semantic states (ok / warn / critical) + colour-blind-safe shapes (Mini Metro rule).
5. Monospace tabular numerals for live counters to prevent jitter.
6. UI scale slider + reduced-motion + "plain mode" (no scanlines/glitch).

---

## 4. Visualising neural activity in real time on the web

### Concrete references (URLs)
- **three.js official examples** (names verified against `examples/files.json`, dev branch, 2026-10-24):
  - Selective bloom (glow only on active neurons/synapses): [webgl_postprocessing_unreal_bloom_selective](https://threejs.org/examples/#webgl_postprocessing_unreal_bloom_selective), WebGPU: [webgpu_postprocessing_bloom_selective](https://threejs.org/examples/#webgpu_postprocessing_bloom_selective), [webgpu_postprocessing_bloom_emissive](https://threejs.org/examples/#webgpu_postprocessing_bloom_emissive)
  - Plexus/network of points with dynamic connecting lines: [webgl_buffergeometry_drawrange](https://threejs.org/examples/#webgl_buffergeometry_drawrange)
  - Instancing at scale: [webgl_instancing_performance](https://threejs.org/examples/#webgl_instancing_performance), [webgl_instancing_dynamic](https://threejs.org/examples/#webgl_instancing_dynamic), [webgl_buffergeometry_instancing](https://threejs.org/examples/#webgl_buffergeometry_instancing), [webgpu_instance_points](https://threejs.org/examples/#webgpu_instance_points)
  - GPU-simulated particles (signal pulses along edges): [webgl_gpgpu_birds](https://threejs.org/examples/#webgl_gpgpu_birds), [webgpu_compute_particles](https://threejs.org/examples/#webgpu_compute_particles), [webgpu_compute_points](https://threejs.org/examples/#webgpu_compute_points), [webgpu_tsl_compute_attractors_particles](https://threejs.org/examples/#webgpu_tsl_compute_attractors_particles), [webgpu_tsl_galaxy](https://threejs.org/examples/#webgpu_tsl_galaxy)
  - Thick, AA lines for synapses: [webgl_lines_fat](https://threejs.org/examples/#webgl_lines_fat), [webgpu_lines_fat](https://threejs.org/examples/#webgpu_lines_fat)
  - Batched meshes / LOD: [webgl_mesh_batch](https://threejs.org/examples/#webgl_mesh_batch), [webgl_batch_lod_bvh](https://threejs.org/examples/#webgl_batch_lod_bvh)
- **3d-force-graph** (vasturiano) — Three.js + d3-force-3d; built-in `linkDirectionalParticles` / `linkDirectionalParticleSpeed` for pulses along links ([GitHub](https://github.com/vasturiano/3d-force-graph), [three-forcegraph README](https://cdn.jsdelivr.net/npm/three-forcegraph@1.43.4/README.md)). Good for prototyping the layout; for production write our own instanced renderer.
- **TensorSpace.js** — TF.js + Three.js 3D layer visualisation of real models ([tensorspace.org](https://tensorspace.org/)) — reference for layer-stack look, not for real-time perf.
- **VizHub neural network sim** — neurons + curved connections + pooled pulse particles, adjustable firing rate ([VizHub](https://vizhub.com/nitanagdeote/db6ba4d9d493470ab62301fcd7399d28)).
- **Synapse background** (21st.dev) — proximity lines + hover pulses ([21st.dev](https://21st.dev/@dhileepkumargm/components/synapse-background)).
- WebGPU/TSL migration notes (bloom pipeline API renamed in recent revisions — pin version): [ics.media guide](https://ics.media/en/entry/250501/), [Utsubo migration guide (JP)](https://www.utsubo.com/ja/blog/webgpu-threejs-migration-guide).

### Recommended GPU-friendly architecture for the "brain"
1. **Nodes = 1 `InstancedMesh`** (icosphere or SDF billboard). Per-instance attributes: `activity` (0–1), `health`, `type` (GPU class), `selected`. Update one `Float32Array` per frame → `instanceMatrix`/custom `InstancedBufferAttribute` with `needsUpdate` on a range.
2. **Edges = 1 `LineSegments` / fat-lines geometry** built once from topology (GPU interconnect: NVLink-like intra-node, fabric inter-rack). Brightness encoded in a vertex attribute, not per-object materials.
3. **Pulses = shader-only.** Don't simulate particles on CPU: each edge has `phase` and `rate`; the fragment shader draws travelling dashes `fract(uv.x - time*rate + phase)`. Thousands of pulses for free. For many free-flying sparks use the WebGPU compute path with a WebGL2 fallback (GPGPU texture ping-pong like `webgl_gpgpu_birds`).
4. **Layout:** precompute (force-directed offline or deterministic: racks → clusters → hemispheres) and cache; **never run force layout every frame**. Animate only on topology change (new GPU = node "grows" in with a tween).
5. **Glow:** selective bloom on an emissive layer; keep bloom resolution at half-res; disable on low tier.
6. **Semantic mapping (important for gameplay):** node = GPU (or GPU group at scale), size = compute, colour = health/thermals, pulse rate = tokens/s served, **dark node = idle money burning**, red flicker = errors, edge thickness = interconnect bandwidth, edge congestion = queue. When the network is huge, aggregate: 1 node = 1 rack → 1 pod (semantic zoom).
7. **Overlay compositing:** render the brain in a separate scene/camera over the datacenter with a vignette + depth-faded background; minimised = picture-in-picture via scissor viewport (no second canvas, no second WebGL context).
8. **Performance budget:** target ≤ 3 draw calls for the whole brain (nodes, edges, sparks), adaptive quality tiers, and pause pulse animation when tab hidden.

---

## 5. Pacing & progression (garage → empire)

### Evidence
- Idle-game math: costs grow exponentially while production grows linearly/polynomially; generator chains approach exponential growth; prestige multiplies earnings ([Math of Idle Games I](https://www.gamedeveloper.com/design/the-math-of-idle-games-part-i), [II](https://www.gamedeveloper.com/disciplines/the-math-of-idle-games-part-ii), [III](https://www.gamedeveloper.com/design/the-math-of-idle-games-part-iii)).
- Paperclips: plateau → breakthrough → phase change ([Wikipedia](https://en.wikipedia.org/wiki/Universal_Paperclips)).
- Software Inc./Game Dev Tycoon/City Game Studio complaints: repetitive late game, micromanagement growth, progression too fast, no meaningful competition mid/late ([VaporLens SI](https://vaporlens.app/app/362620), [VaporLens GDT](https://vaporlens.app/app/239820), [VaporLens CGS](https://vaporlens.app/app/726840/city_game_studio_your_game_dev_adventure_begins)).
- Model Co.: models decay against a moving frontier — a built-in anti-complacency force ([Steam](https://store.steampowered.com/app/4894580/Model_Co/)).

### Proposed tiers (each changes the *map* and the *verbs*, not just numbers)
| Tier | Space | Hardware fantasy (fictional brands) | New verbs | Funding |
|---|---|---|---|---|
| 0 Garage | Garage / bedroom | Consumer GPUs in a gaming tower | Fine-tune open model, serve hobbyists, manual fixes | Savings, small grant |
| 1 Loft | Small office + 1 rack | Workstation/pro cards, first rack | Hire first staff, uptime SLA, first policy | Angel, research grant |
| 2 Colo | Rented colo cage | Datacenter accelerators, 8-GPU nodes | Train first own model, release day, enterprise tier | Seed / Series A |
| 3 Hall | Own datahall | Multi-node clusters, fast fabric, liquid cooling | Pods, power contracts, delegation (CTO/COO), rival labs | Series B–C |
| 4 Campus | Campus + substation | Rack-scale systems | IPO, stock, regulators, global outage events | IPO, bonds |
| 5 Frontier | Multiple campuses | Next-gen rack-scale + custom silicon research | Policy book endgame, "what is the brain becoming?" | Public markets |

### Anti-boredom / anti-spreadsheet techniques
- **Delegation unlocks** remove old chores as you scale (Software Inc. lesson).
- **Semantic zoom**: management granularity rises with scale (GPU → node → rack → pod → hall).
- **Moving frontier**: rivals release better models; your users churn if you stagnate (Model Co.).
- **Launch days** as punctuation every ~15–25 min (GDT lesson, but transparent scoring).
- **Event director** fills gaps between launches (RimWorld).
- **Questions not quotas**: grants and investors set narrative objectives.
- **Every number has a place in the world**: money spent on cooling → you *see* chillers being installed.

---

## 6. Synthesis

### Top 10 design principles
1. **Throughput must be visible, not read.** The brain overlay and datacenter must let a player diagnose a problem in < 3 seconds without opening a panel (Data Center packet-balls, Factorio flags, Mini Metro rings).
2. **One simulation, three lenses.** Datacenter (physical), Brain (computational), Feed (human). Each is a view of the same state; no mechanic exists in only one lens.
3. **The feed is telemetry with a human face.** Each conversation is generated from a sim variable (capability vs. task difficulty, latency, safety policy); clicking it explains the cause. Aggregated, rate-limited, never nagging.
4. **Every tier changes verbs and space**, not only multipliers (Paperclips/Satisfactory).
5. **Scale up = zoom out + delegate.** Old micro-tasks get automated by hires or upgrades the moment they'd become chores.
6. **Transparent scoring.** Benchmarks, reviews and stock moves show their drivers. Luck exists, but is labelled.
7. **Pressure from a moving frontier, not from punishment.** Rivals and model decay keep you moving; bankruptcy is a slow, readable spiral with escape hatches (emergency round, sell GPUs).
8. **Choices with weight.** A small Policy Book of irreversible, morally textured decisions with neutral framing (Frostpunk), feeding Trust vs. Investor Pressure.
9. **Futuristic, but legible first.** Two-layer UI (diegetic flavour + flat truth), AA contrast, motion = meaning, reduced-motion/plain mode.
10. **Web-native performance as a design constraint.** Instancing, shader-driven pulses, ≤ few draw calls for the brain, quality tiers, fast load (< 10 MB initial), runs on a laptop iGPU. Fictional brands and an original identity — FOSS-safe and clearly distinct from LLM Tycoon/Model Co.

### Proposed core loop
- **Moment-to-moment (5–60 s):** Watch the brain pulse and the feed scroll → spot a hotspot (red node, queue ring, angry post) → click it → act (reroute load, throttle a free tier, send a tech, buy/upgrade a GPU, approve overtime) → see the pulse normalise and the next posts turn positive.
- **Session (15–45 min):** Pick a goal (grant objective, investor milestone, next model) → expand capacity (place racks, sign power contract, hire) → run a **training job** that competes with inference for the same GPUs (core tension: serve today vs. train tomorrow) → **Launch day**: benchmark reveal, feed surge, stock reaction → reinvest; one director event mid-session.
- **Long-term (hours):** Climb tiers garage → frontier; funding rounds and IPO change who you answer to; Policy Book shapes the company's identity and the endgame; the brain grows from a handful of nodes into a dense, beautiful structure that *is* your save file's trophy. Optional prestige: "spin-off a new lab" with a legacy perk.

### 3 risks to avoid
1. **Spreadsheet drift / micromanagement wall.** Mid-game becomes menu management at scale (Software Inc., GDT, Crypto Mining Sim complaints). Mitigation: delegation unlocks, semantic zoom, every system surfaced through the three lenses, hard cap on number of panels.
2. **Spectacle over signal.** A gorgeous brain and holo-UI that don't actually communicate state (Dead Space's holo map lesson; film FUI ≠ game UI). Mitigation: every visual property bound to a sim variable; playtest "diagnose in 3 seconds".
3. **Theme collision and sameness.** The AI-lab tycoon niche is crowded (LLM Tycoon's "Chirp", Model Co.'s IPO/bubble meter). Copying their surface features would make the game read as a clone; tying to real companies/GPUs adds legal and dating risk. Mitigation: lean into what only we have (free web, 3D datacenter + live brain, customer-conversation feed), fictional brands/timeline, distinct naming for the feed.

---

## Sources (consolidated)
- Cities: Skylines Chirper: https://www.netzwelt.de/news/221707-cities-skylines-2-entwickler-integrieren-bug-neues-feature.html · https://www.techradar.com/gaming/consoles-pc/cities-skylines-2-has-created-my-arch-nemesis-and-its-made-me-love-the-game-more · https://steamcommunity.com/app/255710/discussions/0/613958868364268310 · https://gameinformer.com/review/cities-skylines-ii/utopian-thinking
- Factorio EfficienSee: https://forums.factorio.com/viewtopic.php?p=185968
- Two Point Hospital: https://two-point-hospital.fandom.com/wiki/Staff · https://www.pcgamesn.com/two-point-hospital/two-point-hospital-review
- RimWorld: https://en.wikipedia.org/wiki/RimWorld · https://rimworldwiki.com/wiki/About_RimWorld
- Software Inc. / Game Dev Tycoon / City Game Studio reviews: https://vaporlens.app/app/362620 · https://vaporlens.app/app/239820 · https://vaporlens.app/app/726840/city_game_studio_your_game_dev_adventure_begins
- Data Center: https://store.steampowered.com/app/4170200/Data_Center/ · https://itsfoss.com/data-center-game/ · https://www.dekudeals.com/items/cloud-server-simulator
- Universal Paperclips: https://en.wikipedia.org/wiki/Universal_Paperclips · https://gamesbeat.com/this-clicker-game-lets-you-take-over-the-world-with-paper-clips/
- Frostpunk: https://www.pcgamer.com/au/frostpunk-developers-on-hope-misery-and-the-ultimately-terrifying-book-of-laws · https://destructoid.com/?p=220323
- Mini Metro: https://gdconf.com/news/attend-gdc-2017-and-learn-the-value-of-less-is-more-from-a-mini-metro-dev · https://giantbomb.com/users/3929/articles/interview-peter-curry-co-creator-of-mini-metro
- Markets: https://www.designer-notes.com/otc-designer-notes-2-free-markets/ · https://www.shacknews.com/article/93533/offworld-trading-company-taking-stock-in-space · https://www.capitalismlab.com/?p=11605 · https://www.enlight.com/dada/mail.cgi/archive/CapLabOwner/20200218052829/
- AI-lab games: https://store.steampowered.com/app/5071100/ · https://store.steampowered.com/app/4861430/ · https://store.steampowered.com/app/4894580/Model_Co/ · https://store.steampowered.com/app/5015590 · https://store.steampowered.com/app/5075960
- Crypto mining: https://raijin.gg/app/1596310/Crypto_Mining_Simulator · https://www.wasdland.com/game/crypto-mining-simulator-1596310/ · https://store.steampowered.com/app/2304990/Crypto_Miner_Tycoon_Simulator_Starter_Edition/
- UI: https://gamedeveloper.com/design/video-designing-i-dead-space-i-s-immersive-user-interface · https://www.gamedeveloper.com/design/game-ui-discoveries-what-players-want · https://www.hudsandguis.com/2012/08/22/dead-space-2-diegetic-interface-design · https://gdcvault.com/play/1027036/Cutting-Apart-The-Diegetic-Interface · https://vfxvoice.com/?p=13143400 · https://www.pushing-pixels.org/2014/08/07/the-craft-of-screen-graphics-and-movie-user-interfaces-interview-with-david-sheldon-hicks-of-territory-studio.html · https://www.hudsandguis.com/fui-media
- Web viz: https://threejs.org/examples/ (example names above) · https://github.com/vasturiano/3d-force-graph · https://tensorspace.org/ · https://vizhub.com/nitanagdeote/db6ba4d9d493470ab62301fcd7399d28 · https://21st.dev/@dhileepkumargm/components/synapse-background · https://ics.media/en/entry/250501/
- Pacing math: https://www.gamedeveloper.com/design/the-math-of-idle-games-part-i · https://www.gamedeveloper.com/disciplines/the-math-of-idle-games-part-ii · https://www.gamedeveloper.com/design/the-math-of-idle-games-part-iii
