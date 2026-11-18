# Research & Architecture Decision Log — `MandiGuard`

## Candidate Research Direction Decision Matrix (Weighted Evaluation)

Before converging on the final Two-Stage `MandiGuard` + `MandiGuard-CRC` contribution, we evaluated four candidate thesis directions across five non-negotiable academic criteria (`1–5` scale, max weighted score `5.00`):

| Candidate Direction | Genuine Novelty (25%) | Experimental Evidence (25%) | Simplicity & Explainability (20%) | Authenticity / Reproducibility (15%) | Viva Defensibility (15%) | Weighted Score | Decision |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **Candidate 1 (`EVA-Mandi` v1):** 9-ensemble + Duan smearing + Knowledge Gradient VoI on HP Apple | 3.0 | 1.5 *(4/5 H failed)* | 1.5 *(high black-box math)* | 3.5 | 1.8 | **2.28 / 5.00** | **REJECTED** *(archived untouched)* |
| **Candidate 2:** Pure point-ML price forecasting (`MSE/MAPE`) on open AGMARKNET series (`B3` family) | 2.0 | 4.5 *(open yards)* | 4.8 | 4.5 | 2.2 *(fails real market)* | **3.51 / 5.00** | **REJECTED** *(becomes baseline `B3`)* |
| **Candidate 3 (`Stage I`):** Empirical Phantom Arbitrage + deterministic 4-step conformal LCB cascade (`MG_v1`) | 4.2 | 4.0 *(`H1,H3,H4` pass; `H2` ties `B2`)* | 4.8 | 4.6 | 4.3 | **4.35 / 5.00** | **LOCKED STAGE I** *(commit `e421d15`)* |
| **Candidate 4 (`Two-Stage Final`):** Stage-I pre-registered audit + Stage-II Mechanistic Autopsy (`Exp 16`: Censored-Arrival Bias, Heteroscedastic Coverage Illusion, Sub-Grade `T1`) + `MandiGuard-CRC` (`Exp 17`) + Dual-Tier `Exp 14` | **4.7** | **4.9** *(`+₹129.16 vs B1`, `+₹32.51 vs B2`, `+₹207 HP Apple`, `2,214` official keys)* | **4.7** *(2 GBDTs + 1 scalar $\lambda^*$)* | **4.8** *(149d AGMARKNET 2.0 + XML)* | **4.9** *(no HARKing)* | **4.80 / 5.00** | **SELECTED FINAL** |

---

## Decision 1: Pivot from Complex Multi-Ensemble VoI Router (`EVA-Mandi` v1) to Physical Spatial Dispatch (`MandiGuard`)
* **Claim $\to$ Evidence:** `EVA-Mandi` (`mandi-agentic-decision-research`, commit `59bef3f`) failed 4/5 pre-registered hypotheses and trailed a zero-ML staleness threshold (`97.4%` vs `86.3%`), whereas `MandiGuard` reframes the task around observable farm-gate dispatch arbitrage (`Net = Sale*(1-spoil) - Freight - Fee - Local`).
* **Competing Explanation:** Perhaps multi-ensemble VoI fails only due to small HP Apple sample size. Refuted by scaling cleanly across `6` states, `4` crops, and `10` years (`Exp 10`), where simple domain-physics + causal risk gating dominates point-ML `B3` (`-37.29 pp` episode losses).
* **Limitation & Defense:** Keeps math explainable on a whiteboard; assumes smallholder 30-qtl open truck economics anchored to GoI surveys rather than unverified micro-forecasts.

## Decision 2: Causal 2024-Ranked Active Panel (Eliminating Holdout Survivorship Bias)
* **Claim $\to$ Evidence:** Selecting active mandis using full 2024–2026 counts leaks future survival. Ranking top-30 mandis/state strictly on calendar **2024** trading days (`>= 20` days in 2024, `>= 80` total) locks `178` core mandis (`260,043` 2024–2026 rows; `883,406` 2017–2026 rows) plus `42` grade-explicit HP Apple mandis.
* **Defense:** Zero 2025–2026 market closures contaminate the panel roster.

## Decision 3: Strict Separation of Realized ERA5 Climate vs. Causal Forecast Weather & Quota Compliance
* **Claim $\to$ Evidence:** All `145/145` realized ERA5 grids (`2024-01-01..2026-09-05`) and `102/145` Open-Meteo Historical NWP grids cached cleanly before Open-Meteo returned HTTP 429 daily quota exhaustion.
* **Experiment & Result:** Never bypass rate limits; fit a strictly $\le t$ `2024` Ridge nowcaster on the remaining `43` northern grids (`Val_2025H1` `tmax` MAE `1.05°C`, `rain` MAE `0.001 mm`, `rh` MAE `0.28%`), and verify results on the 4-state `100%` native-NWP subset (`Exp 2b`: `+₹31.82/qtl` over `B2` across `42,766` episodes).

## Decision 4: Replacing Generic Assumptions with Official GoI Central & State Survey Parameters
* **Evidence Anchored & SHA-256 Hashed:**
  1. MoFPI / NABCONS (2022, `PIB PRID=2151371`): exact market-level loss rates (`Tomato 3.25%`, `Onion 1.96%`, `Apple 1.64%`, `Potato 0.86%`).
  2. GoI Ministry of Consumer Affairs (`PIB relid=154554`): state statutory F&V APMC fees (`KA & GJ 0.5%`, `HP 0.5% veg / 1.0% Apple`, `MH 1.0%`, `MP & UP 1.5%`).
  3. MoSPI NSO NSS 77th Round Report No. 587 (`PIB PRID=1753856`): smallholder reference truck `30 qtl` (`29.3–38.7 qtl` harvest) and mean net crop income `₹3,798/month`.
  4. GoHP Economic Survey 2025–26 (`91.59%` single-lane hill roads `[39,465 / 43,091 km]`), justifying the `1.45x` HP road multiplier; plus sensitivity sweep `[0.5x..1.5x]` (`Exp 6`).

## Decision 5: Honest Documentation & Two-Stage Epistemic Discipline (Preventing HARKing)
* **Claim $\to$ Evidence:** Holdout `2025-06-01..2026-04-08` was unblinded under pre-registered commit `e421d15` (`MandiGuard v1`). Subsequent forensic checks on `Train_2024`, `Val_2025H1`, and `HP_Warmup` (`Exp 16`) uncovered three mechanistic flaws in `v1`: (1) complete-case `dropna(target_ret)` discarded `55.83%` of `Train_2024` corridors and understated `Q20` downside risk by `1.82x–2.00x` (`2.54x` holdout), (2) pooled split conformal averaged `88.91%–90.46%` calm `Q1` over-coverage with `67.84%–67.80%` volatile `Q4` under-coverage, and (3) `T1`'s rigid `open_prob >= 0.50` blocked `77.82%–82.75%` of `MG`-refused HP Apple dispatches (`exp16`).
* **Design Decision:** Never overwrite or retroactively re-label Stage I! Preserve `H1`–`H4` untouched (`e421d15`) and isolate `Exp 16` & `Exp 17` (`MandiGuard-CRC`, trained strictly on `arrival_date+2 <= 2024-12-31`, calibrated strictly on `Val_2025H1` at $\lambda^* = 0.15$) as **Stage II (`[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]`)**—paired with dual-tier official provenance parity in `Exp 14` (`172` XML keys + `2,042` 149-day AGMARKNET 2.0 keys).
* **Prose Discipline:** Keep manuscript prose clear, crisp, and free of hype adjectives, placing software test/SHA counts in reproducibility/limitation documentation rather than overclaiming economic truth.
