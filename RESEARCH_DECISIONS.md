# Research & Architecture Decision Log — `MandiGuard`

## Decision 1: Pivot from Complex Multi-Ensemble VoI Router (`EVA-Mandi` v1) to Physical Spatial Dispatch (`MandiGuard`)
* **Context:** Prior v1 prototype (`EVA-Mandi`, archived untouched in `/Users/adityasharma/.gemini/antigravity/scratch/mandi-agentic-decision-research` at commit `59bef3f`) combined 9 HistGradientBoosting ensembles, Duan smearing, Knowledge-Gradient numerical integration, and strided delayed conformal bounds over HP Apple data alone. Four of five pre-registered hypotheses failed (`H1, H2, H4, H5`), and a simple zero-ML staleness threshold beat the VoI router on `H3` (`97.4%` vs `86.3%`).
* **Decision:** Pivot to an intuitive, high-impact agricultural engineering economics formulation: **Phantom Spatial Arbitrage in Multi-State Indian Mandis (`MandiGuard`)**.
* **Justification:** Keeps all mathematics transparent at M.Tech viva level (`Net Gain = Sale Price * (1 - Spoilage) - Highway Freight - Mandi Charges - Local Price`), grounds parameters in public Indian datasets (AGMARKNET + OSRM highways + ECMWF ERA5 + GoI surveys), and lets sequential verification-cascade tool ordering (`T1 -> T2 -> T3 -> T4`) demonstrate measurable value cleanly.

## Decision 2: Causal 2024-Ranked Active Panel (Eliminating Holdout Survivorship Bias)
* **Issue Addressed:** Selecting "active mandis" based on full 2024–2026 trading counts leaks future operational longevity into training/validation splits.
* **Decision:** Filter and rank top-30 mandis per state strictly using **2024 trading days** (`>= 20` days in 2024 and `>= 80` total days, yielding `178` core mandis across 6 states; `260,043` rows) plus all `42` grade-explicit HP Apple mandis in `2025-11-07..2026-09-01`.

## Decision 3: Strict Separation of Realized ERA5 Climate vs. Causal Forecast Weather & Quota Compliance
* **Context:** All `145/145` (`100%`) 0.1-degree ECMWF ERA5 ground-truth grid cells (`2024-01-01..2026-09-05`) and `102/145` (`70.3%`) Open-Meteo Historical NWP forecast grid cells (`100%` of `GJ, KA, MP, MH` + `8` UP cells) cached cleanly before Open-Meteo returned HTTP 429 daily request quota exhaustion.
* **Decision:** Never attempt to bypass rate limits. Fit a strictly causal $\le t$ Ridge nowcaster trained solely on `2024` overlap rows (`Val_2025H1` `tmax` MAE `1.05°C`, `rain` MAE `0.001 mm`, `rh` MAE `0.28%`) to populate forecast covariates for the remaining `43` northern grid cells, tag `fc_source`, and verify main benchmark results hold cleanly on both the full 6-state panel and the exploratory 4-state `100%` NWP subset (`Exp 2b`).

## Decision 4: Replacing Generic Assumptions with Official GoI Central & State Survey Parameters
* **Sources Archived & Hashed:**
  1. MoFPI / NABCONS (2022) Rajya Sabha Table (`PIB PRID=2151371`, `01 Aug 2025`): exact market-level loss rates (`Tomato 3.25%`, `Onion 1.96%`, `Apple 1.64%`, `Potato 0.86%`).
  2. GoI Ministry of Consumer Affairs (`PIB relid=154554`, `29 Nov 2016`): State APMC F&V statutory fee deregulation (`Karnataka & Gujarat 0.5%` user charge; `HP 0.5%` veg vs `1.0%` Apple [not exempt]; `Maharashtra 1.0%` yard supervision; `Madhya Pradesh & Uttar Pradesh 1.5%`).
  3. MoSPI NSO NSS 77th Round Report No. 587 (`PIB PRID=1753856`, `10 Sep 2021`): smallholders hold `<= 1 ha` predominantly, earn mean `Rs 3,798/month` net crop income (`50.2%` indebted), and produce ~`29.3–38.7 qtl` (grounding a `30 qtl` truckload benchmark).
  4. MoFPI Cold Storage State Capacity PDF (`20.11.2023`, `doc20231219291701.pdf`) & MoA&FW e-NAM (`PIB PRID=2086484`).
  5. GoHP Economic Survey 2025–26 (`91.59%` single-lane motorable roads `[39,465 / 43,091 km]`, `65.01 lakh qtl` APMC arrivals, `88.86%` small/marginal growers) justifying mountain road surcharges.
* **Sensitivity Integrity:** Maintain $3 \times 3$ freight $\times$ spoilage sensitivity grid plus explicit ablation against uniform `1.5%` fees (`Exp 6`).

## Decision 5: Honest Documentation Standards
* Manuscript (`paper/manuscript.md`) uses plain-English explanations, simple intuition equations, 4–5 decision metrics, zero commit hashes/SHA strings/`pytest` counts in body prose, and reports all confirmatory and subgroup results transparently—even where multi-step tools yield nuanced tradeoffs.
