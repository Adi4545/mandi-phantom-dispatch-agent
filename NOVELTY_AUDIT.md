# Adversarial Novelty Audit — `MandiGuard`

**Project Title:** *Phantom Spatial Arbitrage in Indian Mandis — A Climate-, Road-, and Freshness-Aware Dispatch Agent (`MandiGuard`)*  
**Purpose of Document:** This audit strictly classifies what is **genuinely novel and defensible** for an M.Tech thesis versus what is **borrowed/applied** from existing literature, ensuring zero exaggerated algorithmic claims during peer review or thesis viva defense.  
**Literature Anchor:** Grounded in [literature_matrix.md](file:///Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent/research/literature_matrix.md) and the multi-state extraction scope implemented in [extract_agmarknet_multistate.py](file:///Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent/src/data/extract_agmarknet_multistate.py).

---

## 1. Executive Classification of Target M.Tech Novelty

`MandiGuard` does **not** claim to invent new statistical learning theorems, new conformal coverage proofs, new general-purpose LLM reasoning algorithms, or new thermodynamic food-spoilage laws. Instead, its M.Tech novelty is **empirical, decision-formulation, systems-architectural, and benchmark-oriented**, spanning four concrete, testable axes:

| Novelty Axis | Type of Novelty | Specific Claim Defended by `MandiGuard` | Primary Anchor Literature Built Upon |
|:---|:---|:---|:---|
| **Axis 1: Empirical Anatomy of Phantom Spatial Arbitrage** | **Empirical / Domain-Measurement** | First multi-state, multi-crop quantitative decomposition of apparent AGMARKNET spatial arbitrage across **6 Indian states** (Maharashtra, Uttar Pradesh, Karnataka, Madhya Pradesh, Gujarat, Himachal Pradesh) and **4 perishable crops** (Onion, Potato, Tomato, Apple; Jan 2024–Apr 2026) into four explicit erosion mechanisms: **(1) variety/grade mismatch**, **(2) closed-yard / non-reporting hazard**, **(3) Haversine-vs-OSRM road-network distance/time gap**, and **(4) ERA5 ambient thermal spoilage**. | Jensen (2007); Sekhar (2012); Chatterjee & Kapur (2016/2017); Negi et al. (2018); Hersbach et al. (2020); Jha et al. (2015); NABCONS (2022) |
| **Axis 2: Asymmetric-Cost Selective Dispatch Formulation** | **Problem Formulation & Applied ML** | Reframes mandi market selection from naive symmetric RMSE price prediction or point-estimate profit ranking to **cost-sensitive selective dispatch** with an explicit **`HOLD_LOCAL` abstention rule** driven by calibrated downside risk bounds (`LCB` on net realized profit after freight, yard risk, and heat decay), evaluated via economic utility, false-dispatch rate, tail risk, and risk–coverage curves. | Chow (1970); Franc, Průša, & Voráček (2023); Angelopoulos & Bates (2023); Mitra et al. (2018) |
| **Axis 3: Sequential Verification Funnel Architecture** | **Systems & Agentic Efficiency** | Introduces a **staged verification funnel** for mandi dispatch that runs cheap structural, varietal, and yard-activity gates before invoking costly external OSRM routing, ERA5 corridor weather extraction, and calibrated predictive scoring—explicitly tracing the **realized utility vs. verification API/compute cost Pareto frontier** against unconstrained ReAct-style or all-pairs brute-force verification. | Yao et al. (2023); Kachuee et al. (2019); Han, Buntine, & Shareghi (2024); Luxen & Vetter (2011) |
| **Axis 4: Pre-Registered, Leak-Free Multi-Modal Benchmark** | **Benchmark & Reproducibility** | Delivers an open, SHA-256-verified multi-modal pipeline harmonizing 2024–2026 AGMARKNET schema/district renames, causal 2024-ranked market selection (eliminating holdout survivorship bias), strict temporal train/calibration/holdout splits, and pre-registered baselines/ablations—remediating evaluation gaps in prior applied mandi prototypes. | Madaan et al. (2019); Ma et al. (2019); Guo et al. (2020); Biradar & Divyashree (2026); Manimegalai et al. (2026) |

---

## 2. Adversarial Component-by-Component Audit: Borrowed vs. Novel

### A. Econometric & Mandi Price Analysis
* **What Already Exists (Borrowed / Prior):**
  * Long-run spatial cointegration and market segmentation across Indian mandis (Sekhar 2012; Chatterjee & Kapur 2016/2017).
  * Survey evidence that transport/communication frictions depress farmer prices (Negi et al. 2018), while raw price announcements alone fail without outside market access (Mitra et al. 2018).
  * Missing AGMARKNET entries tied to non-trading/closed market days (noted as a data-cleaning step by Guo et al. 2020 and imputed statistically by Ma et al. 2019 and Deka 2026).
  * Naive net-profit mandi recommenders combining AGMARKNET + XGBoost/SARIMA + OpenWeatherMap or Haversine distance (*Mandi Cast* 2026; *AgriMarket AI* 2026).
* **What `MandiGuard` Adds (Novel):**
  * Shifts from *macro price dispersion* or *price MSE* to **operational decision-time arbitrage auditing**: measuring exactly what share of apparently profitable daily inter-mandi trades turns negative or unexecutable once variety/grade equivalence, yard trading availability on arrival day, real OSRM road routes, and corridor thermal exposure are enforced.

### B. Climate & Freshness Degradation Modeling
* **What Already Exists (Borrowed / Prior):**
  * ERA5 reanalysis (Hersbach et al. 2020) for gridded hourly ambient temperature.
  * National Indian post-harvest loss surveys (ICAR-CIPHET, Jha et al. 2015; MoFPI/NABCONS 2022) and standard $Q_{10}$ / Arrhenius post-harvest spoilage kinetics in food engineering.
* **What `MandiGuard` Adds (Novel):**
  * **Operational coupling** of ERA5 corridor temperatures and OSRM transit duration into an explicit per-route freshness penalty benchmarked across contrasting Indian agro-climatic regimes (e.g., temperate HP Apple corridors vs. hot plains Onion/Tomato/Potato corridors).
* **Mandatory Honesty Disclosure (Ground-Truth Limitation):**
  * AGMARKNET reports daily market modal/min/max prices and reporting presence—it does **not** record truck-level consignment spoilage receipts or individual trader P&L. Consequently, transit freshness loss in our benchmark is a **physics-informed, literature-anchored structural model** (parameterized to CIPHET/NABCONS bounds and audited across sensitivity sweeps), *not* observed physical wastage per shipment. We must state this openly in both methodology and limitations.

### C. Selective Prediction, Asymmetric Risk & Conformal Calibration
* **What Already Exists (Borrowed / Prior):**
  * Optimal error–reject tradeoff under asymmetric costs (Chow 1970) and proper uncertainty scores for reject-option classifiers (Franc et al. 2023).
  * Split conformal prediction and conformal risk control (Angelopoulos & Bates 2023).
* **What `MandiGuard` Adds (Novel):**
  * **Domain instantiation & asymmetric utility alignment:** Translates abstract reject options into `HOLD_LOCAL` vs. `DISPATCH_TO_MANDI_j`, where false-positive dispatch destroys sunk logistics cost and perishable value, while false-negative rejection merely foregoes marginal spread.
* **Mandatory Honesty Disclosure (Statistical Assumption Gap):**
  * Standard split conformal guarantees require data exchangeability, which daily agricultural price panels violate across harvest/monsoon regime shifts. `MandiGuard` therefore must treat conformal intervals as **empirical rolling/time-ordered uncertainty calibration** validated via actual holdout coverage and tail-loss metrics—never claiming unconditional finite-sample guarantees under non-stationarity.

### D. Sequential Verification Funnel Agent
* **What Already Exists (Borrowed / Prior):**
  * Tool-interleaved reasoning (ReAct, Yao et al. 2023), budgeted test-time feature acquisition (Kachuee et al. 2019), and calibrated uncertainty-gated tool invocation (UALA, Han et al. 2024).
* **What `MandiGuard` Adds (Novel):**
  * **Domain-specific staged verification funnel:** Rather than calling OSRM road routing, ERA5 climate grids, and calibrated spread forecasting on all $(O, D)$ origin–destination pairs (or relying on ungrounded LLM heuristics), `MandiGuard` organizes external tools in ascending marginal cost:
    1. *Stage 1 (Zero-API Structural Gate):* Exact `(Commodity, Variety, Grade)` match + causal historical corridor plausibility + coarse Haversine upper bound.
    2. *Stage 2 (Low-Cost Statistical Gate):* Yard-openness / reporting-probability check + fast lag-based spread estimate.
    3. *Stage 3 (Targeted External Verification):* Invokes OSRM route geometry/duration + ERA5 corridor temperature profile + calibrated conformal profit lower bound **only** on surviving candidates, emitting either `DISPATCH(j*)` or `HOLD_LOCAL`.
  * The contribution is **architectural and empirical**: demonstrating a dominant Pareto tradeoff (matching or beating all-pairs brute force on net realized farmer utility while cutting expensive external verification calls by orders of magnitude).

---

## 3. Red-Line Check: Claims We MUST NOT Make

To protect academic integrity in the thesis text and viva, **strictly prohibit** the following overclaims:

1. **DO NOT claim** *"We prove a new conformal prediction theorem or new Bayes-optimal reject theory."*  
   *Truth:* We apply Chow (1970), Franc et al. (2023), and Angelopoulos & Bates (2023) to perishable spatial dispatch.
2. **DO NOT claim** *"We are the first ML system to predict AGMARKNET mandi prices or recommend mandis using distance and weather."*  
   *Truth:* Madaan et al. (2019), Ma et al. (2019), Guo et al. (2020), *Mandi Cast* (2026), and *AgriMarket AI* (2026) already predict mandi prices and/or build Haversine/weather recommenders. Our novelty is decomposing **why naive recommenders fail (phantom arbitrage)** and solving **calibrated risk + budgeted verification**.
3. **DO NOT claim** *"We measure real truck-by-truck physical spoilage directly from AGMARKNET."*  
   *Truth:* AGMARKNET lacks shipment spoilage telemetry; we combine real ERA5 temperatures and OSRM travel times with CIPHET (2015) / NABCONS (2022) calibrated thermal decay curves and run explicit parameter sensitivity analyses.
4. **DO NOT claim** *"Our sequential funnel invents a general-purpose RL feature-acquisition algorithm or new LLM agent theory."*  
   *Truth:* It is a domain-engineered sequential verification funnel inspired by Kachuee et al. (2019) and Han et al. (2024), evaluated empirically via utility–tool-cost Pareto curves.
5. **DO NOT claim** *"OSRM + ERA5 eliminates all real-world mandi frictions."*  
   *Truth:* Unobserved institutional frictions—local *arhtiya* credit ties, weighment/commission variations, sudden truck strikes, or intra-day arrival gluts—remain uncaptured in public portals and must be acknowledged as boundary limitations.

---

## 4. Likely Viva / Peer-Reviewer Objections & Pre-Registered Honest Answers

| Adversarial Question from Examiner / Reviewer | Honest, Defensible Answer |
|:---|:---|
| *"Isn't your 'sequential funnel' just standard cascade filtering / early pruning?"* | Yes, structurally it is a domain-specific **multi-stage verification cascade**—analogous to budgeted feature acquisition (Kachuee et al. 2019) and uncertainty-gated tool calling (Han et al. 2024). Its research contribution is not inventing cascade logic, but **formulating and empirically quantifying the utility–API-budget Pareto frontier** for multi-modal geospatial/climate agricultural dispatch, where OSRM + ERA5 + conformal verification per pair cannot scale naively across hundreds of mandis. |
| *"How can you claim thermal spoilage effects without truck-level spoilage ground truth?"* | We explicitly distinguish **observed data layers** (AGMARKNET prices & yard reporting flags, OSRM road travel times, ERA5 hourly corridor temperatures) from our **mechanistic spoilage penalty**, which is anchored to ICAR-CIPHET (2015) and NABCONS (2022) crop-specific loss bands and $Q_{10}$ kinetics. We evaluate every core finding across conservative-to-aggressive decay sensitivity sweeps so results do not hinge on one tuned constant. |
| *"Prior papers like AgriMarket AI (2026) and Mandi Cast (2026) already recommend mandis with weather and distance—what is actually new here?"* | Those systems exemplify the **exact naive baseline** we critique: point-estimate price forecasts combined with straight-line Haversine distance or covariate-only weather, with zero separation of variety/grade mismatch, zero closed-yard execution hazard modeling, zero transit thermal decay, and zero calibrated abstention (`HOLD_LOCAL`). We replicate those naive baselines directly in our benchmark to measure how much phantom arbitrage they mistakenly recommend. |
| *"Do split conformal guarantees hold when mandi prices are serially correlated and seasonal?"* | No—strict finite-sample exchangeability does not hold across seasonal regime shifts. We therefore calibrate on strictly prior rolling/chronological windows, report actual empirical holdout coverage alongside tail-loss CVaR and risk–coverage curves, and frame conformal bounds as a practical calibration wrapper rather than a distribution-shift-immune theorem. |
| *"Why should an M.Tech thesis care about closed-yard / missing AGMARKNET days if Guo et al. (2020) and Deka (2026) already noted missing values?"* | Prior work treated missing AGMARKNET entries as a **statistical imputation / data-cleaning problem** to improve forecast RMSE. In contrast, for a live dispatch agent, forwarding produce on a stale quote to a market that has zero trading activity or unrecorded arrival creates **operational execution failure**—which is a primary driver of phantom arbitrage rather than an imputation metric. |

---

## 5. Summary Verdict on Thesis Readiness

* **Novelty Profile:** **High Applied/Empirical + Systems-Benchmark Novelty** (strong fit for M.Tech thesis / applied AI4SG / ICTD / ACM COMPASS-style venue).
* **Core Strength:** Unifies rigorous agricultural economics intuition (phantom spreads, real transport/channel friction), verified multi-modal physical data (AGMARKNET + ERA5 + OSRM), and modern selective/budgeted AI agent evaluation—while staying 100% honest about theoretical inheritance and telemetry limits.
