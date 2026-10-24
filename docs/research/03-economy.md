# 03 — The Economics of a Frontier AI Lab (research + game economy model)

> Research date: 2026-10-24. Figures come from web search (secondary press, aggregators, Epoch AI) plus well-documented public facts (model cards, papers).
> **Caveat on sources:** much 2026 reporting on private labs comes from anonymous sources or aggregators. Anything I could not trace to a reasonably primary source is marked **(unverified)**. For a game, the *order of magnitude* and the *shape of the curve* matter more than the exact digit, and both are solid.

---

## 0. TL;DR for the game designer

- **Revenue explodes, but compute eats it.** Real labs grow 3–10x a year (OpenAI ~$3.7B 2024 → ~$50B run-rate Sep 2026; Anthropic ~$1B → ~$9B → $65B+ run-rate) while gross margins sit at only **35–50%** because inference compute is so expensive.
- **Price per token for a fixed quality falls ~10x/year**, while the *frontier* price stays roughly flat ($5–15 in / $25–75 out per million tokens). So the game's treadmill is: yesterday's model is worth 1/10 next year.
- **Training cost per frontier generation rises ~2.5x/year** (GPT-3 ~$4M → GPT-4 ~$40–100M → 2025 frontier runs ~$500M+ → 2026–27 $1B+).
- **Capital is the real game resource.** Labs spend ahead of revenue with ever-bigger rounds ($10M seed → $100B+ rounds at ~$1T valuations), compute-for-equity deals with clouds, GPU-backed debt and, finally, IPOs.
- **Events move valuations violently.** DeepSeek R1 erased $589B from Nvidia in a day; the Gemini 3 launch lifted Alphabet ~6% intraday; a $1.5B copyright settlement; export-control flip-flops.

---

## 1. Revenue

### 1.1 API pricing per million tokens (USD)

| Era | Model (tier) | Input $/M | Output $/M | Notes |
|---|---|---|---|---|
| 2020-06 | GPT-3 davinci (frontier) | 60 (per 1M tok, single price) | — | ~$0.06/1k tokens, public pricing |
| 2023-03 | GPT-4 8k (frontier) | 30 | 60 | OpenAI launch pricing |
| 2023-11 | GPT-4 Turbo | 10 | 30 | 3x cheaper in 8 months |
| 2024-05 | GPT-4o | 5 | 15 | |
| 2024-07 | GPT-4o mini (budget) | 0.15 | 0.60 | ~100x cheaper than GPT-4 at similar-ish quality |
| 2024-03 | Claude 3 Opus (frontier) | 15 | 75 | Anthropic pricing |
| 2025-01 | DeepSeek V3/R1 (open-weights, cheap) | 0.27 / 0.55 | 1.10 / 2.19 | price-war trigger |
| 2025-08 | GPT-5 | 1.25 | 10 | [anotherwrapper](https://anotherwrapper.com/tools/llm-pricing/claude-opus-5/gpt-5-2025-08-07) |
| 2026 | Claude Opus 5 (frontier) | 5 | 25 | batch 2.5/12.5; "fast mode" 10/50; cache read 0.50 — [eesel](https://eesel.ai/blog/claude-opus-5-pricing) (unverified vs official page) |
| 2026 | GPT-5.5 Instant | 5 | 30 | [anotherwrapper](https://anotherwrapper.com/tools/llm-pricing/claude-opus-5/gpt-5.5-instant) (unverified) |
| 2026-09 | Flagship band / budget band | ~10 / ~0.20 | ~50 / ~1.20 | IntuitionLabs Sep 2026 report ([pdf](https://intuitionlabs.ai/pdfs/llm-api-pricing-cost-per-task-comparison.pdf)) (unverified) |

**Patterns worth modelling**
- **Output tokens cost 4–8x input** (output is sequential decode, memory-bandwidth bound).
- **Tiers:** frontier ($5–15 / $25–75), mid ($1–3 / $5–15), budget ($0.1–0.3 / $0.4–1.2). Roughly a **25–100x price spread** between frontier and budget.
- **Discount levers:** batch API −50%, prompt caching −90% on cached input, priority/fast mode +100%.
- **Deflation:** Epoch AI finds the price of a *fixed capability level* falls **9x–900x per year** depending on the benchmark threshold, median roughly 40–50x/yr, with the fastest drops recent ([Epoch, LLM inference price trends](https://epoch.ai/data-insights/llm-inference-price-trends)). A later Epoch update cited ~5–10x/yr ([Epoch blog](https://epoch.ai/blog/how-has-the-cost-of-llm-inference-changed)); a secondary summary reports "47% per quarter" ([pillitteri](https://pasqualepillitteri.it/nl/news/21055/epoch-ai-ai-prijzen-dalen-47-procent-kwartaal)) (unverified). **Game value: ~10x/year depreciation of a model's "quality-adjusted price".**
- **Reasoning models** bill hidden thinking tokens as output → effective cost per task can be 5–20x list price suggests.

### 1.2 Consumer subscriptions

| Tier | Price | Examples | Notes |
|---|---|---|---|
| Free | $0 | ChatGPT, Claude, Gemini | loss leader, ad experiments; costs inference |
| Low | ~$8/mo | ChatGPT "Go" style plan | launched because only ~5% of users pay ([wisernotify](https://wisernotify.com/blog/chatgpt-users/)) (unverified) |
| Standard | $20/mo | ChatGPT Plus, Claude Pro, Gemini Advanced | the industry anchor since 2023 |
| Power | $100–$250/mo | ChatGPT Pro $200, Claude Max $100/$200, Google AI Ultra ~$250 | heavy users can still be margin-negative |
| Team/Enterprise seats | $25–$60+/seat/mo | ChatGPT Team/Enterprise, Claude Team | volume discounts |

Scale: ChatGPT ~400M WAU (Feb 2025) → ~900M WAU (Feb 2026), 50M+ paying subscribers (unverified, [wisernotify](https://wisernotify.com/blog/chatgpt-users/)). **Free→paid conversion ≈ 5%** is a good game constant.

### 1.3 Enterprise deals
- Enterprise is the growth engine in 2026: OpenAI's 2026 growth "driven largely by its expanding enterprise business" ([citybiz](https://www.citybiz.co/?p=916777)); Anthropic's revenue is majority API/enterprise and coding agents.
- Typical shapes: committed-spend contracts ($1M–$100M+/yr), revenue through cloud marketplaces (AWS Bedrock, Google Vertex, Azure), government contracts (US DoD awarded several labs up to $200M each in 2025 — (unverified exact figures)).
- **Accounting gotcha (great game flavour):** Anthropic books the *gross* value of some cloud-partner sales, OpenAI books only its *net* share — which explains part of a reported $20B gap between a $70B projection and a ~$50B actual OpenAI run-rate ([Bloomberg via BGOV](https://news.bgov.com/artificial-intelligence/openais-annualized-revenue-nears-50-billion-ft-says)).

### 1.4 Revenue run-rates over time

| Date | OpenAI (annualized) | Anthropic (annualized) |
|---|---|---|
| end 2023 | ~$1.6B ([TechStory](https://shibboleth.idm.home.nyu.edu/revenue-of-openai/openai-achieves-record-1-6bn-in-annualised-revenue-techstory)) | ~$0.1B (unverified) |
| 2024 (full year) | ~$3.7B revenue ([Techleap](https://finder.techleap.nl/news/feed/openai-s-annualised-revenue-hits-25b-up-from-3-7b-in-2024)) | ~$1B run-rate end-2024 (unverified) |
| mid 2025 | ~$10B | ~$4–5B (unverified) |
| end 2025 | ~$21.4B | ~$9B ([Techeconomy](https://techeconomy.ng/anthropics-annual-revenue-run-rate-tops-65-billion)) |
| Feb–Apr 2026 | >$25B ([Techloy](https://www.techloy.com/openai-hits-25-billion-in-annualized-revenue-while-anthropic-surges-to-19-billion/)) | $19B → $30B ([aiweekly](https://aiweekly.co/alerts/anthropic-hits-30b-run-rate-leads-cnbc-disruptor-50)) |
| May 2026 | — | $47B (company statement, via Techeconomy) |
| Jul–Sep 2026 | ~$50B end-Sep (target ≥$70B by end-2026) ([BGOV](https://news.bgov.com/artificial-intelligence/openais-annualized-revenue-nears-50-billion-ft-says)) | >$65B end-Jul ([Techeconomy](https://techeconomy.ng/anthropics-annual-revenue-run-rate-tops-65-billion)) (gross accounting) |
| Projection | — | 2028: ~$190–200B (unverified) |

Other reference points: Mistral reportedly ~$0.3–1B ARR range in 2025–26 (unverified); CoreWeave (GPU cloud) revenue $229M (2023) → $5.1B (2025), guiding +235% for 2026 ([Techleap](https://finder.techleap.nl/news/feed/coreweave-stock-down-55-despite-235-revenue-growth-forecast-for-2026)).

**Game takeaway:** a top lab grows **~3x/yr (OpenAI)** to **~7x/yr (Anthropic 2025–26)**. Growth is lumpy and tied to model releases (e.g. coding agents).

---

## 2. Inference costs

### 2.1 GPU-hour prices

| GPU | Year | Price/GPU-hour | Source |
|---|---|---|---|
| A100 80GB | 2023 | $1.5–4 on-demand (unverified) | market common knowledge |
| H100 | 2023–24 peak | $8–10 on-demand (shortage) | [Spheron](https://www.spheron.network/blog/h100-price-per-hour-2026/) |
| H100 | Q2 2026 | $1.80–3.50 neoclouds; AWS ~$6.9, GCP ~$11, Azure ~$12.3 on-demand list | [Spheron](https://www.spheron.network/blog/h100-price-per-hour-2026/), [CloudZero](https://cloudzero.com/blog/h100-gpu-cost/) |
| H100 1-yr reserved | 2025→2026 | **up ~40%** (tightening again) | SemiAnalysis via [Spheron](https://www.spheron.network/blog/h100-price-per-hour-2026/) (unverified) |
| H200 | 2026 | $4.45–10.60 on-demand | [Jarvislabs](https://jarvislabs.ai/blog/h200-price), [Hyperbolic](https://www.hyperbolic.ai/blog/h200-price) |
| B200 | 2026 | $3.99–5.50 (neoclouds) | (unverified, single data point) |
| Owned H100 | 2024–26 | ~$25–35k per GPU, ~$40–50k per GPU all-in with server/network; ≈ **$1.0–1.5/hr** amortized over 4–5 yrs + power (unverified estimate) | |

**Ladder for the game:** hyperscaler on-demand (3–5x) > neocloud on-demand (1.5x) > 1–3 yr reserved (1.0x baseline) > owned (0.5–0.7x but huge upfront + ops risk).

### 2.2 Throughput, batching, utilization (simplified physics)
- **Decode is memory-bandwidth bound.** A rough rule: single-stream tokens/s ≈ memory bandwidth / bytes of active weights. H100 (3.35 TB/s) with a 70B model in FP8 (~70 GB) → ~40–50 tok/s per stream. **Batching** shares each weight read across many users → aggregate throughput of **2,000–10,000+ tok/s per H100** for a 70B-class dense model at reasonable latency (unverified ranges, consistent with public vLLM/TensorRT-LLM benchmarks).
- **Mixture-of-Experts** (DeepSeek V3: 671B total, 37B active) cuts compute per token by ~activeParams.
- **Latency vs. throughput trade-off:** bigger batches → cheaper per token but slower per user. Perfect game knob.
- **Utilization:** real fleets run 30–70% average utilization due to diurnal demand peaks; reserved capacity you don't fill is pure loss.
- **Cost-per-token formula:** `cost/Mtok = ($/GPU-hr) / (tokens/s per GPU × 3600 × utilization) × 1e6`. Example: $2/hr, 3,000 tok/s, 50% util → **$0.37 per million tokens** — far below list price for a mid model, which is why mid/budget tiers are profitable and frontier long-reasoning is not.
- DeepSeek published a "theoretical" 545% cost-profit margin for its inference at list prices in March 2025 (unverified here; widely reported) — shows serving itself can be very profitable at scale; losses come from free users, R&D compute and training.

### 2.3 Gross margins
| Company | Year | Gross margin | Source |
|---|---|---|---|
| Anthropic | 2024 | **−94%** | The Information via [iTiger](https://www.itiger.com/news/1154519858) |
| Anthropic | 2025 | ~40% (38% incl. free users); inference on Google/Amazon came in 23% above plan | same |
| OpenAI | 2025 | 33% adjusted vs 46% target (had to buy expensive last-minute compute) | (unverified, secondary) |
| OpenAI | 2025 "compute margin" (paid users) | ~70% by Oct 2025 | [SaaStr](https://www.saastr.com/have-ai-gross-margins-really-turned-the-corner-the-real-math-behind-openais-70-compute-margin/) — different metric |
| SaaS benchmark | — | 75–85% | standard |

**Game constant:** AI lab gross margin 30–60%, improving with scale and owned hardware, crashing when you must buy emergency compute.

---

## 3. Training costs

### 3.1 Successive generations

| Model | Year | Training compute (FLOP) | Hardware / time | Approx. compute cost | Source |
|---|---|---|---|---|---|
| GPT-3 175B | 2020 | 3.1e23 | ~V100 cluster, weeks | ~$2–5M | GPT-3 paper; Epoch |
| GPT-4 | 2023 | ~2e25 | ~25k A100 × ~90–100 days (unverified) | ~$40M compute (Epoch amortized); Altman: ">$100M" all-in | [Epoch](https://epoch.ai/publications/how-much-does-it-cost-to-train-frontier-ai-models) |
| Llama 3.1 405B | 2024 | 3.8e25 | 16k H100, 30.8M H100-hours | ~$60M at $2/hr | Meta model card |
| DeepSeek V3 | 2024-12 | ~3.4e24 | 2,048 H800, 2.79M GPU-hours (~2 months) | **$5.6M** for the final run only (excludes R&D, failed runs, capex) | DeepSeek V3 tech report |
| Llama 4 Scout/Maverick | 2025 | ~?e24–e25 | 5.0M / 2.4M H100-hours (Behemoth much larger, delayed) | ~$10–15M each final run (unverified) | Meta model card |
| Grok 4 | 2025 | ~5e26 (unverified) | Colossus (~100–200k H100/H200) | **~$500M** compute | [Epoch Grok 4](https://epoch.ai/data-insights/grok-4-training-resources) |
| Frontier 2026 (GPT-5.x, Claude Opus 5, Gemini 3.x) | 2025–26 | 1e26–1e27 (unverified) | 100k–500k GPU clusters | $0.5–2B per final run (unverified) | trend extrapolation |

- **Trend:** frontier training cost grows **2–3x/year**; >$1B runs by 2027 ([Epoch](https://epoch.ai/blog/how-much-does-it-cost-to-train-frontier-ai-models)). Training compute grows ~4–5x/yr. 30+ models exceeded 1e25 FLOP by 2025 ([Epoch](https://epoch.ai/data-insights/models-over-1e25-flop)).
- **Cost breakdown** (GPT-4/Gemini era): hardware 47–67%, R&D staff 29–49%, energy only 2–6% ([Epoch](https://epoch.ai/publications/how-much-does-it-cost-to-train-frontier-ai-models)).
- **The final run is a fraction of total R&D compute.** Experiments, ablations and failed runs typically cost 2–5x the final run (unverified ratio; OpenAI's 2024 R&D compute reportedly far exceeded final-run cost).

### 3.2 Scaling laws, game-ready
- **Compute:** `C ≈ 6 × N × D` (FLOPs = 6 × parameters × training tokens).
- **Chinchilla optimum:** `D ≈ 20 × N` → for compute C, `N ≈ sqrt(C/120)`. Modern labs "over-train" (Llama 3 8B saw 15T tokens ≈ 1,900 tok/param) because smaller models are cheaper to *serve*. **That is a real, interesting trade-off: train bigger (smarter, expensive inference) vs. train longer (cheaper inference).**
- **Loss:** `L(N,D) = E + A/N^α + B/D^β` (Chinchilla fit: E≈1.69, A≈406, B≈411, α≈0.34, β≈0.28). Practical game reduction: **capability gains a roughly constant step per 10x compute** (log-linear).
- **Game formula:** `quality = Q0 + k × log10(effectiveCompute)` where `effectiveCompute = rawFLOP × algorithmicEfficiency × dataQuality`. Algorithmic efficiency improves ~3x/yr industry-wide (Epoch estimate, (unverified exact rate)), so standing still = falling behind.

### 3.3 Failed runs and risks
- Loss spikes/divergence, hardware failures (Meta reported 419 unexpected interruptions during the 54-day Llama 3 405B run, ~1 every 3 hours), data contamination, disappointing results (Llama 4 Behemoth delayed; GPT-4.5 judged too expensive to serve and deprecated). Game: each run has P(failure/underwhelm) 10–25%, reducible by research spend and smaller pilot runs.

---

## 4. Capex vs. opex

| Item | Figure | Source |
|---|---|---|
| Datacenter build (shell + power + cooling, no IT) | **$11.3M/MW** global average 2026 (was $7.7M 2020) | JLL via [datacentres.com](https://www.datacentres.com/news/data-centre-construction-costs-11m-per-mw) |
| Regional spread | $7.9M (Taiwan) – $19.2M (Japan); $8.2M Dublin – $16.8M Tokyo | [DataCenterNews](https://datacenternews.asia/story/ai-lifts-asia-pacific-data-centre-costs-report-says), [datacentres.com](https://www.datacentres.com/news/global-data-centre-build-costs-diverge-sharply-8-2m-to-16-8m-mw-as-hyperscalers--slot3-2026-07-17) |
| AI-optimised, liquid cooled | $20M+/MW; all-in incl. some IT $20–37M/MW | [Archdesk](https://archdesk.com/blog/ai-data-center-costs) (unverified) |
| Including GPUs | ~$35–50B per GW all-in (unverified; 1 GW ≈ 500k–700k Blackwell-class GPUs) | |
| Power price | US ~$28–80/MWh typical industrial/wholesale, PJM wholesale ~$78 → $137/MWh Q1 2026; Europe $89–112/MWh | [aiweekly](https://aiweekly.co/alerts/europes-high-energy-costs-threaten-ai-data-center-edge) (unverified), [tomshw](https://www.tomshw.it/business/1200-twh-datacenter-rete-non-ce-la-fa) |
| PJM capacity price | $28.92 → $329.17/MW-day (2024/25 → 2026/27) | [Schneider](https://perspectives.se.com/supply/the-ai-power-crunch-what-companies-need-to-know-about-electricity-price-risk) |
| Power per GPU | H100 ~0.7 kW chip, ~1.2–1.5 kW all-in with PUE; B200 ~1 kW chip, ~1.8 kW all-in | specs (approx.) |

**Electricity per H100-hour** ≈ 1.3 kWh × $0.08 = ~$0.10 → power is small vs. hardware amortization (~$1/hr), but **availability of power** (grid connection queues of years) is the true bottleneck.

**Depreciation debate:** hyperscalers depreciate servers/GPUs over ~5.5–6 years (Meta raised to 5.5 yrs, cutting 9-month 2025 depreciation by $2.3B; Alphabet/Microsoft 6; Amazon cut some to 5). Michael Burry argues real useful life is 2–3 years given Nvidia's annual cadence, understating depreciation by ~$176B 2026–28 ([Yahoo Finance](https://finance.yahoo.com/news/fast-does-ai-chip-depreciate-164511602.html), [techstrong](https://techstrong.ai/features/tech-investor-michael-burry-alleges-accounting-irregularities-at-hyperscalers-in-pursuit-of-ai-boom/)). **Game hook:** player chooses the accounting schedule — longer = prettier earnings and stock price, but risk of a write-down event when a new GPU generation makes old ones obsolete.

**Buy vs. rent rule of thumb:** owning breaks even vs. reserved cloud at ~18–30 months of high utilization; renting wins if utilization <50% or the next GPU gen arrives soon.

---

## 5. Funding

### 5.1 Lab funding ladders (selected)

| Company | Round | Amount | Post-money | Source |
|---|---|---|---|---|
| Mistral | Seed (2023) | €105M | ~€240M | widely reported |
| Mistral | Series C (2025) | €1.7B (ASML €1.3B, ~11%) | €11.7B | [Sifted](https://sifted.eu/articles/mistral-confirms-series-c-asml) |
| Mistral | Series D (2026, Samsung-led) | €3B | >$24B (unverified) | [technews](https://finance.technews.tw/2026/09/08/mistral-valuation-surges-with-samsung-and-asml-investments/) |
| Mistral | Debt (Mar 2026) | $830M bank loan for GPUs | — | (unverified) via [komo](https://komo.ai/directory/mistral-ai-funding) |
| Safe Superintelligence | Seed/A (2024) | $1B | $5B | [the-decoder](https://the-decoder.com/openai-co-founder-sutskever-raises-2-billion-for-ai-startup-with-no-product/) |
| SSI | 2025 | $2B | $32B (no product) | same |
| Thinking Machines Lab | Seed (2025) | $2B | $12B | [fourweekmba](https://fourweekmba.com/thinking-machines-lab-officially-closes-2b-at-12b-valuation-teases-first-product-launch/) |
| Anthropic | Series F (2025) | $13B | $183B | widely reported |
| Anthropic | Series G (Feb 2026) | $30B | $380B | [Techeconomy](https://techeconomy.ng/anthropics-annual-revenue-run-rate-tops-65-billion) |
| Anthropic | Series H (May 2026) | $65B (incl. $15B hyperscaler commitments) | $965B | Reuters via same |
| OpenAI | 2019 Microsoft | $1B (largely Azure credits) | — | |
| OpenAI | 2023 Microsoft | ~$10B | ~$29B | |
| OpenAI | Mar 2025 (SoftBank) | $40B | $300B | |
| OpenAI | Mar 2026 | $122B committed | $852B | [BusinessToday](https://www.businesstoday.in/technology/story/openai-raises-122-billion-funding-ahead-of-ipo-buzz-523445-2026-04-01), [BGOV](https://news.bgov.com/financial-accounting/openai-filed-confidentially-for-ipo-as-rivals-race-to-market) |
| OpenAI | talks Sep 2026 | ? | >$1.2T (unverified) | [DealStreetAsia](https://www.dealstreetasia.com/?p=495280) |
| xAI | merged into SpaceX (2026) | — | xAI ~$125–250B; combined ~$1.25T | [Motley Fool](https://www.fool.com/investing/2026/03/31/spacex-absorbed-xai-at-a-combined-125-trillion-val/) |

**Typical generic ladder (non-superstar):** pre-seed $0.5–2M @ $5–15M → seed $3–10M @ $20–60M → A $20–60M @ $100–400M → B $100–300M @ $1–3B → C $0.5–2B @ $5–15B → mega $5B+ @ $50B+. **Superstar founders skip rungs** (SSI, TML: billions at seed). Dilution per round 10–25%; mega-rounds often only 5–10% because valuations are huge.

### 5.2 Strategic investors and compute credits
- Microsoft → OpenAI: much of the ~$13B was Azure compute; Amazon → Anthropic ($8B, AWS Trainium), Google → Anthropic (multi-$B + TPUs), Nvidia invests in customers (circular "vendor financing" criticism), ASML → Mistral, Samsung → Mistral.
- **Game mechanic:** "strategic round" = cheaper capital but strings attached (must buy their cloud/chips; exclusivity; revenue share; they can block a competitor's deal).

### 5.3 Debt
- **GPU-backed loans:** CoreWeave's 2023 $2.3B DDTL (Magnetar/Blackstone) lent to an SPV holding H100s + customer contracts, at ~SOFR+870bp; by March 2026 DDTL 4.0 ($8.5B) got an **investment-grade A3** rating at ~SOFR+225bp, backed by a $19B+ Meta contract ([Bloomberg Law](https://news.bloomberglaw.com/capital-markets/coreweave-raises-8-5-billion-gpu-loan-backed-by-meta-deal), [Wing VC](https://www.wing.vc/content/how-the-gpu-became-collateral)). Real collateral = contracted cash flow; weak customers → +450–550bp.
- Also high-yield notes (CoreWeave 9.25% 2030 notes), convertibles, credit facilities pre-IPO (Anthropic reported $15B facility — (unverified)).
- **Game:** debt = no dilution, but interest + covenants; a GPU price crash or lost anchor customer can trigger margin calls.

---

## 6. Public grants and subsidies

| Program | Region | What it gives | How it works | Notes |
|---|---|---|---|---|
| **EuroHPC AI Factories** (19+ sites incl. BSC Barcelona) | EU | free GPU-hours on public supercomputers (LUMI, Leonardo, MareNostrum 5, MeluXina, JUPITER) | Calls: *Playground* (SMEs/startups, quick; temporarily closed 2026 for platform transition), *Large Scale Access* (industry, >50k GPU-h, cut-offs twice monthly through Jan 2027), *AI for Science* | Compute, not cash; must be EU entity; results often must be published/open ([EuroHPC](https://eurohpc-ju.europa.eu/large-scale-access-ai-factories_en)) |
| **AI Gigafactories** (InvestAI, €20B target) | EU | co-funding of 100k+ GPU facilities | Tender launched July 2026 ([EuroHPC](https://eurohpc-ju.europa.eu/eurohpc-joint-undertaking-launches-ai-gigafactories-call-2026-07-30_en)) | industry consortia; late game |
| **Horizon Europe / EIC Accelerator** | EU | grants up to €2.5M + equity up to €10–15M | competitive, 3-stage, ~6–12 months, success rate ~5% (unverified) | deep-tech startups |
| **IPCEI (e.g. IPCEI-AI / Compute Infrastructure)** | EU member states | state aid for large consortium projects | multi-year design + Commission approval; years | only for big players |
| **PERTE Nueva Economía de la Lengua** | Spain | €1.1B public | sub-calls, e.g. €75M for co-official language tech; ALIA family of public models trained on MareNostrum 5 ([Garrigues](https://www.garrigues.com/es_ES/noticia/perte-nueva-economia-lengua-espanol-herramienta-crecimiento-economico), [Forbes ES](https://forbes.es/ultima-hora/194620/el-gobierno-destina-75-millones-a-proyectos-que-impulsan-las-tecnologias-del-lenguaje-en-lenguas-cooficiales/)) | Spanish/co-official languages focus |
| **ENIA / Estrategia IA 2024** | Spain | ~€1.5B package (unverified) | ministry calls, CDTI loans/grants | |
| **MareNostrum 5 access (RES / EuroHPC)** | Spain/EU | GPU hours on BSC | periodic RES calls (~every 4 months), peer review | academic/industrial |
| **NAIRR** | US | compute, models, data from 13–14 agencies + ~28 industry partners | Pilot since Jan 2024, ~400–900 teams; NSF $35M Operations Center (SDSC+TACC) from Sep 2026; monthly allocation cycles, competitive, renew per period ([SDSC](https://www.sdsc.edu/news/2026/PR20260901-NAIRR-OC.html), [Nextgov](https://www.nextgov.com/artificial-intelligence/2026/09/nsf-launches-new-ai-research-operations-center/415786/)) | research/education; startups mostly via SBIR |
| **DOE (Frontier, Aurora, Genesis Mission)** | US | supercomputer time (INCITE/ALCC), national-lab partnerships | annual INCITE call, peer reviewed | science-focused |
| **CHIPS and Science Act** | US | $52.7B, ~$39B manufacturing incentives | fabs, not labs (unless you go vertical into chips) | late-game branch |
| **UK AI Research Resource (Isambard-AI, Dawn, Zenith)** | UK | GPU hours, no cash | Open access call 50k–1.4M GPU-h (budget 8M GPU-h, closed 17 Jul 2026); Sovereign AI offer up to 1M GPU-h per startup; Gateway 10k GPU-h; Rapid Access 20k GPU-h ([GOV.UK](https://www.gov.uk/government/publications/ai-research-resource/ai-open-access-call), [UKRI](https://www.ukri.org/opportunity/access-to-isambard-ai-and-zenith-airr-supercomputers-gateway-route/)) | Isambard-AI = 5,448 GH200 |
| **Cloud startup credits** | global | $100k–$350k (AWS Activate, Google for Startups AI, Azure) | apply via accelerator/VC partner | early-game lifeline |

**Common grant mechanics for the game:** application cost (time/staff), review delay (1–12 months), success probability (5–40%), conditions (open publication, local HQ/jobs, language focus, no military use, reporting), clawback if conditions broken, and "compute not cash" (hours that expire).

---

## 7. Stock market

### 7.1 IPO path
1. Confidential S-1 → SEC review (3–6 months). OpenAI filed confidentially 8 Jun 2026; Anthropic 1 Jun 2026 ([BGOV](https://news.bgov.com/financial-accounting/openai-filed-confidentially-for-ipo-as-rivals-race-to-market), [BitMEX guide](https://www.bitmex.com/blog/anthropic-ipo-guide)).
2. Public S-1 (≥15 days before roadshow) → roadshow (~2 weeks) → pricing → listing. Lock-up 90–180 days for insiders.
3. Anthropic reportedly targeting a fall 2026 Nasdaq listing raising $60–100B at up to ~$2T (unverified; [TNW](https://thenextweb.com/news/anthropic-ipo-mid-october-midterms-15bn-credit-facility)); Altman said OpenAI's IPO won't be in 2026.
4. SpaceX/xAI aimed at $1.5–1.75T and $40–80B raise (unverified).
- **IPO float typically 10–20%**; underwriting fees 1–7%; first-day "pop" common.

### 7.2 What moves AI valuations (real examples)

| Event type | Example | Move |
|---|---|---|
| Cheap competitor / open weights | DeepSeek R1 (27 Jan 2025) | Nvidia −17%, −$589B in one day (record); Nasdaq −3.1% ([Yahoo/Reuters](https://finance.yahoo.com/news/chinas-deepseek-sets-off-ai-071458375.html)) |
| Strong model launch | Gemini 3 (18 Nov 2025) | Alphabet +6.6% intraday, +3% close, record high ([The Nightly](https://thenightly.com.au/business/google-roars-back-gemini-3-launch-reframes-ai-battle-c-20736772)) |
| Weak/mixed launch | GPT-5 "mixed reception"; Bard demo error Feb 2023 | Alphabet −7.7% (~$100B) on the Bard demo |
| Earnings/guidance miss | CoreWeave weak guidance (Feb 2026) | −20% day; −55% from 52-wk high of $187 ([TIKR](https://www.tikr.com/blog/coreweave-nasdaq-crwv-stock-plunges-20-as-weak-guidance-sparks-margin-concerns)) |
| Customer/financing scare | OpenAI funding scare (2026) | CoreWeave turbulence (~$96) (unverified) |
| Regulation/export | H20 ban then H200 approval with 25% fee | Nvidia multi-% swings ([CNAS](https://www.cnas.org/publications/commentary/cnas-insights-unpacking-the-h200-export-policy)) |
| Legal | $1.5B Bartz v. Anthropic settlement | priced as cost of doing business ([JURIST](https://www.jurist.org/news/2026/07/judge-approves-record-1-5-billion-settlement-involving-anthropic/)) |
| Governance scandal | OpenAI board ousts Altman (Nov 2023) | MSFT −1–2%; near-collapse of OpenAI tender |

### 7.3 Valuation multiples
- Private AI labs: **~15–40x forward run-rate revenue** (Anthropic $965B / ~$47–65B ≈ 15–20x; OpenAI $852B / ~$25–30B ≈ 30x; Mistral ~$24B / ~$1B ≈ 20x+ (unverified)). Pre-revenue labs priced purely on talent (SSI $32B).
- Public comps: Nvidia ~25–35x earnings; CoreWeave ~5–10x revenue; mature SaaS 5–15x revenue.
- **Uses of public stock:** acquisitions paid in shares, RSU equity compensation (retention), follow-on/secondary offerings to raise cash (dilutive, stock usually −3–8% on announcement), ATM programs, convertibles.

---

## 8. Talent costs

| Role | Typical total comp (US, 2025–26) | Notes |
|---|---|---|
| ML engineer (mid) at frontier lab | $300k–$600k | base $200–300k + equity (unverified ranges, levels.fyi-style) |
| Senior research scientist | $800k–$2M+ | |
| Top-tier researcher (2025 bidding war) | $10M–$100M+ over 4 yrs | Meta Superintelligence Labs offers reportedly up to **$300M over 4 years, >$100M first year** for a handful of people (WIRED; Meta disputed breadth) ([the-decoder](https://the-decoder.com/meta-reportedly-offers-top-openai-researchers-up-to-300-million-over-four-years)); an $18M offer was declined for Thinking Machines ([TechCrunch](https://techcrunch.com/?p=3022848)) |
| European researcher (Paris/Madrid) | €80k–€250k + equity (unverified) | 2–4x cheaper than SF; Mistral leverages this |
| Infra/datacenter ops engineer | $150k–$350k | |

- **Poaching:** Meta hired 11–20+ researchers from OpenAI/DeepMind/Anthropic in mid-2025; OpenAI responded with retention bonuses. Founders leaving to start rivals is the norm (Anthropic from OpenAI, SSI, TML, Mistral from DeepMind/Meta).
- Staff share of development cost ≈ 29–49% (Epoch).
- **Game hook:** stars give big research multipliers but have "loyalty" decaying with competitors' offers; equity vesting is your retention tool, and its value is tied to your stock price → feedback loop.

---

## 9. Risks & external events

| Risk | Real anchor | Game effect |
|---|---|---|
| EU AI Act | GPAI obligations since 2 Aug 2025; AI Office enforcement powers + fines up to **€15M or 3% of global turnover** from 2 Aug 2026; AI Omnibus (Reg. 2026/1744, in force 27 Jul 2026) delayed high-risk rules to Dec 2027/Aug 2028 ([Cooley](https://cdp.cooley.com/digital-ai-omnibus-delays-key-deadlines-introduces-new-rules/), [Law Society](https://www.lawsociety.ie/news/news/Stories/the-eu-ai-act-in-2026/)) | compliance cost per model (~1–3% of training budget), fines, EU market access |
| Export controls | H20 15% toll (Aug 2025); H200 to China allowed with 25% fee + 50% volume cap (Jan 2026); Blackwell/Rubin banned ([CNAS](https://www.cnas.org/publications/commentary/cnas-insights-unpacking-the-h200-export-policy)) | GPU tiers locked by region; China-based rival labs get cheaper but weaker chips |
| Copyright | Bartz v. Anthropic: $1.5B (~$3,000/book, ~465k works), training on bought books = fair use, pirated libraries ≠ ([JURIST](https://www.jurist.org/news/2026/07/judge-approves-record-1-5-billion-settlement-involving-anthropic/)); dozens of other suits (NYT v. OpenAI, Getty, music labels) | "dirty data" choice: faster/cheaper training now vs. lawsuit risk later |
| Safety incidents | jailbreaks, misuse, sycophancy rollback (GPT-4o Apr 2025), Grok antisemitic output (Jul 2025) | reputation hit → enterprise churn, regulator attention |
| GPU shortage | 2023–24 H100 shortage ($8–10/hr); reserved prices up ~40% again 2026 | build-queue delays, price spikes |
| Price war | DeepSeek/Qwen open weights; 10x/yr deflation | demand shifts to cheapest adequate model |
| Open-weights competitors | Llama, DeepSeek, Qwen, Mistral | caps the price of non-frontier tiers |
| Energy crisis | PJM capacity ×11; Europe 3–4x US power cost | opex spikes, site choice matters |
| Outages | ChatGPT/Claude multi-hour outages | churn, SLA penalties, small stock dip |
| Bubble/financing scare | CoreWeave −55%; "circular financing" critiques; Burry depreciation thesis | funding winter: valuations −30–60%, rounds harder |

---

## 10. PROPOSED SIMPLIFIED GAME ECONOMY

Design goal: **a few strong levers, visible feedback, real-world flavour** — not a spreadsheet. One tick = **1 week**; a full run spans ~10–12 in-game years (2020-like start to post-AGI-ish end).

### 10.1 Core variables (player-facing in bold)

| Variable | Meaning | Start (garage) |
|---|---|---|
| **Cash** | money in the bank | $10,000 (+ $100k cloud credits) |
| **Compute** | owned/reserved GPU capacity in "GPU units" (1 unit = 1 H100-equivalent) | 0 owned; rent on-demand |
| GPU generation | each gen ≈ 2.5x perf/$, released every ~2 years | Gen 1 (A100-like) |
| **Model Quality (Q)** | 0–100 log scale from compute + research | 10 (fine-tuned open model) |
| Frontier Q (market) | best competitor's Q, rises ~6–8 pts/yr | 30 |
| **Price tier** | per-Mtok price you set per product | budget |
| **Talent** | researchers (R) and engineers (E), each with skill 1–5 | 2 founders |
| Algorithmic efficiency (A) | multiplier on compute, from research | 1.0 |
| **Reputation** | 0–100 (safety, reliability, ethics) | 50 |
| **Hype** | 0–100, decays 5%/week, boosted by launches/PR | 10 |
| Equity owned | founder % | 100% |
| Valuation / share price | private mark, later public price | $0.5M |

### 10.2 Formulas

**Training**
```
effectiveCompute = GPUunits × weeks × genPerf × A × dataQuality      (in "compute points")
Q_new = 10 + 12 × log10(effectiveCompute)        # each 10x compute ≈ +12 quality
trainCost = GPUunits × weeks × 168 × gpuHourPrice
P(fail) = 0.20 − 0.03 × seniorResearchers − 0.05 × (did pilot run) , min 0.03
```
A failed run returns 30–60% of the compute as "lessons" (+A).

**Algorithmic progress**
```
A *= 1 + 0.004 × Σ(researcherSkill)   per week   (≈ 2–3x/yr for a strong team)
industryFrontierQ += 0.13/week (≈ +7/yr), boosted by "breakthrough" events
```

**Demand (per product tier)**
```
relQ = Q_you − Q_frontier                       # can be negative
appeal = exp(relQ / 8) × (priceRef / price)^1.3 × latencyFactor × (0.5 + reputation/100) × (1 + hype/200)
marketTokens(t) grows ~2.5x/yr (whole AI market)
yourShare = appeal / (appeal + Σ competitorAppeal)
demandTokens = marketTokens × yourShare
servedTokens = min(demandTokens, capacityTokens)
revenue = servedTokens × price + subscribers × subPrice + enterpriseContracts
```
- `priceRef` deflates **×0.25 per year** for a fixed Q (models price war + 10x/yr cost decline compromise).
- Unserved demand → **“capacity crunch”**: latency rises, churn +, hype −.

**Capacity & serving cost**
```
tokensPerGPUperSec = 3000 × genPerf / sqrt(modelSizeFactor)    # bigger model = slower
capacityTokens = GPUunits_serving × tokensPerGPUperSec × 604800 × util(≤0.7)
servingCost = GPUunits_serving × 168 × gpuHourPrice + power
grossMargin = (revenue − servingCost) / revenue    # target 30–60%
```

**Compute sourcing**
| Option | $/GPU-hr (Gen-relative) | Commitment | Notes |
|---|---|---|---|
| Hyperscaler on-demand | 3.0x | none | instant |
| Neocloud on-demand | 1.5x | none | may be sold out in shortage events |
| Reserved 1y/3y | 1.0x / 0.8x | pay even if idle | |
| Strategic cloud deal | 0.6x (credits) | exclusivity, equity given | |
| Owned | ~0.5x opex | capex $30k/unit + datacenter $12M/MW (1 MW ≈ 700 GPUs) | build time 6–18 months; depreciation 3–6 yrs (player choice) |
| Public grant hours | 0x | conditions, expire | |

Base gpuHourPrice: $2 at gen launch +shortage multiplier (1.0–4.0), falling ~30%/yr within a gen.

**Funding**
```
preMoney = multiple × forwardRunRate  OR  talentPremium (pre-revenue)
multiple = 12 + 0.25 × hype + 0.3 × max(0, growthYoY%) / 10 + (relQ > 0 ? 8 : 0) − riskPenalty
dilution = raise / (preMoney + raise)
roundCloseTime = 4–12 weeks; P(success) falls in "funding winter" events
```
Strategic investor variant: 30–70% paid in credits; adds a constraint.
GPU-backed debt: borrow ≤ 60% of GPU value at 8–14% APR (drops to ~6% with an anchor contract); covenant: if GPU market value falls below 1.2x loan → margin call.

**Stock price (post-IPO)**
```
fundamental = revenueRunRate × sectorMultiple(8–40, follows global "AI sentiment" random walk)
target = fundamental × (1 + (hype − 50)/100) × (0.7 + reputation/170)
price_t+1 = price_t + 0.15 × (target − price_t) + shock
shock: launch beats frontier +5–15%; misses guidance −10–25%; outage −1–3%; scandal −5–20%;
       rival open-weights shock −10–20% (sector-wide); regulation fine −2–8%
```
Stock price feeds: (a) cost of follow-on offerings, (b) value of employee equity → retention, (c) acquisitions paid in stock.

**Talent**
```
researcher salary/yr: junior $200k, senior $800k, star $5–25M (late game $100M "bidding war" event)
loyalty decays when competitor offer > 1.3 × your package; equity vesting (4y) slows decay
```

### 10.3 Progression milestones

| Stage | Valuation / scale | Typical state | Unlocks |
|---|---|---|---|
| 0. Garage | $10k cash, 2 founders | fine-tune open models, rent 1–8 GPUs, cloud credits | budget API, grants (cloud credits, EuroHPC Playground) |
| 1. Seed | raise $2–5M @ $15–25M | 5–10 staff, 32–64 rented GPUs, first own small model (Q≈25) | hiring market, consumer app $20 tier |
| 2. Series A/B | $50–300M raised, $0.5–3B val | 256–2,048 GPUs reserved, $5–50M run-rate | enterprise sales, strategic cloud deals, Large-Scale public compute |
| 3. Unicorn+ | $1–5B raised, $10–50B val | 10k GPUs, first datacenter lease, Q near frontier | GPU-backed debt, own datacenter build, $200 power tier |
| 4. Frontier contender | $10–60B raised, $100–500B val | 100k GPUs, $1B+ training runs, $5–50B run-rate | talent bidding wars, export-control & AI Act events, gigafactory tenders |
| 5. IPO | $500B–$2T market cap | listed; quarterly earnings events | secondary offerings, stock acquisitions, analyst expectations |
| 6. Endgame | $100B+ run-rate | GW-scale campuses, custom chips | victory conditions: AGI benchmark, market share, or "safe & profitable" score |

Pacing target: stage 0→1 in ~6–12 months of game time (≈15–25 min real time), whole run 3–6 hours.

### 10.4 Balancing notes
- **Keep the 10x deflation visible**: show a "model value decay" bar so players feel the treadmill.
- **Revenue must lag spend**: a well-played lab is cash-flow negative until stage 4–5; bankruptcy should be the main fail state, so funding is never optional.
- **Compute scarcity must bite**: random shortage events (×2–4 price, neocloud sold out) reward reserved/owned capacity.
- **Make frontier vs. efficiency a viable split**: the cheap/open-weights "DeepSeek strategy" (high A, low compute, low prices) should be able to win share but struggle to monetize.
- Rubber-band AI competitors (3–5 fictional labs with personalities: aggressive spender, safety-first, open-weights, Big-Tech-backed, state-backed).
- Use **log scales** for Q, compute and money in UI; humans read 10x steps better.
- Calibrate so a frontier run costs ~1–2 years of current revenue at every stage (true historically).

### 10.5 The 5–7 key decisions/tensions

1. **Train vs. serve (the GPU split).** Every GPU-hour goes to the next model (future) or to customers (cash now). Starving inference causes crunch & churn; starving training means falling behind the frontier.
2. **Big model vs. efficient model.** Bigger = higher Q but slower, costlier inference; over-trained small models = better margins. Real Chinchilla vs. Llama-style trade-off.
3. **Rent vs. own (capex bet).** Owning is 2x cheaper long-run but locks cash, takes a year to build, and can be obsoleted by the next GPU generation — plus the depreciation-schedule temptation.
4. **Whose money? (dilution vs. strings vs. debt).** VC (dilution), strategic cloud (cheap but locked-in), GPU-backed debt (no dilution, margin-call risk), public grants (free but slow and conditional), IPO (huge cash, quarterly pressure).
5. **Price strategy.** Premium frontier pricing vs. price war to grab share; free tier size (growth vs. burn).
6. **Speed vs. safety/legality.** Skip safety evals, use scraped/pirated data, launch early → faster Q and hype, but risk scandals, $1.5B-style lawsuits, AI Act fines, and reputation loss that hits enterprise demand and stock price.
7. **Talent war.** Pay stars ruinous packages (big research multiplier) or build a cheaper team in Europe with public compute; stock price ↔ equity value ↔ retention loop.

---

## Sources (main)
- Epoch AI: [inference price trends](https://epoch.ai/data-insights/llm-inference-price-trends), [cost of frontier training](https://epoch.ai/blog/how-much-does-it-cost-to-train-frontier-ai-models), [Grok 4 resources](https://epoch.ai/data-insights/grok-4-training-resources), [models >1e25 FLOP](https://epoch.ai/data-insights/models-over-1e25-flop)
- Revenue: [BGOV/Bloomberg OpenAI ~$50B](https://news.bgov.com/artificial-intelligence/openais-annualized-revenue-nears-50-billion-ft-says), [Techeconomy Anthropic $65B](https://techeconomy.ng/anthropics-annual-revenue-run-rate-tops-65-billion), [Techloy](https://www.techloy.com/openai-hits-25-billion-in-annualized-revenue-while-anthropic-surges-to-19-billion/)
- Margins: [iTiger/The Information](https://www.itiger.com/news/1154519858), [SaaStr](https://www.saastr.com/have-ai-gross-margins-really-turned-the-corner-the-real-math-behind-openais-70-compute-margin/)
- GPU prices: [Spheron](https://www.spheron.network/blog/h100-price-per-hour-2026/), [CloudZero](https://cloudzero.com/blog/h100-gpu-cost/), [Jarvislabs](https://jarvislabs.ai/blog/h200-price)
- Datacenters/power: [datacentres.com JLL](https://www.datacentres.com/news/data-centre-construction-costs-11m-per-mw), [Schneider](https://perspectives.se.com/supply/the-ai-power-crunch-what-companies-need-to-know-about-electricity-price-risk)
- Depreciation: [Yahoo Finance](https://finance.yahoo.com/news/fast-does-ai-chip-depreciate-164511602.html), [DSHR](https://blog.dshr.org/2026/02/mind-gaap-again.html)
- Debt: [Wing VC](https://www.wing.vc/content/how-the-gpu-became-collateral), [Bloomberg Law](https://news.bloomberglaw.com/capital-markets/coreweave-raises-8-5-billion-gpu-loan-backed-by-meta-deal)
- Funding/IPO: [BGOV IPO pipeline](https://news.bgov.com/financial-accounting/openai-filed-confidentially-for-ipo-as-rivals-race-to-market), [BusinessToday](https://www.businesstoday.in/technology/story/openai-raises-122-billion-funding-ahead-of-ipo-buzz-523445-2026-04-01), [TNW Anthropic IPO](https://thenextweb.com/news/anthropic-ipo-mid-october-midterms-15bn-credit-facility), [Sifted Mistral](https://sifted.eu/articles/mistral-confirms-series-c-asml), [the-decoder SSI](https://the-decoder.com/openai-co-founder-sutskever-raises-2-billion-for-ai-startup-with-no-product/), [Motley Fool SpaceX/xAI](https://www.fool.com/investing/2026/03/31/spacex-absorbed-xai-at-a-combined-125-trillion-val/)
- Grants: [EuroHPC Large Scale Access](https://eurohpc-ju.europa.eu/large-scale-access-ai-factories_en), [EuroHPC Gigafactories call](https://eurohpc-ju.europa.eu/eurohpc-joint-undertaking-launches-ai-gigafactories-call-2026-07-30_en), [SDSC NAIRR](https://www.sdsc.edu/news/2026/PR20260901-NAIRR-OC.html), [GOV.UK AIRR](https://www.gov.uk/government/publications/ai-research-resource/ai-open-access-call), [Garrigues PERTE](https://www.garrigues.com/es_ES/noticia/perte-nueva-economia-lengua-espanol-herramienta-crecimiento-economico)
- Markets/events: [Yahoo/Reuters DeepSeek](https://finance.yahoo.com/news/chinas-deepseek-sets-off-ai-071458375.html), [The Nightly Gemini 3](https://thenightly.com.au/business/google-roars-back-gemini-3-launch-reframes-ai-battle-c-20736772), [TIKR CoreWeave](https://www.tikr.com/blog/coreweave-nasdaq-crwv-stock-plunges-20-as-weak-guidance-sparks-margin-concerns)
- Risk: [Cooley AI Omnibus](https://cdp.cooley.com/digital-ai-omnibus-delays-key-deadlines-introduces-new-rules/), [CNAS H200](https://www.cnas.org/publications/commentary/cnas-insights-unpacking-the-h200-export-policy), [JURIST Bartz](https://www.jurist.org/news/2026/07/judge-approves-record-1-5-billion-settlement-involving-anthropic/)
- Talent: [the-decoder Meta offers](https://the-decoder.com/meta-reportedly-offers-top-openai-researchers-up-to-300-million-over-four-years), [TechCrunch](https://techcrunch.com/?p=3022848)
