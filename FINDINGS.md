# Empirical & Confirmatory Findings — `MandiGuard`

**Primary Holdout Period:** 2025-06-01 to 2026-04-08 (realized arrival lookup through 2026-04-13), spanning **69,526 shortlisted active dispatch episodes** across 174 origin mandis and 23 two-week blocks (81,048 total holdout episodes; 468,816 candidate corridors).  
**Secondary Harvest Validation:** Grade-Explicit Himachal Pradesh Apple (2026-06-01 to 2026-08-27, 1,537 shortlisted active episodes).  
**Frozen Pre-Holdout Parameters:** Trained solely on 2024; safety margin frozen on `Val_2025H1` at **₹50.0/qtl** prior to unblinding.

---

## 1. View 1: Confirmatory Hypothesis Outcomes (`m = 4`, Holm–Bonferroni FWER = 0.05)

Evaluated via paired **Two-Way Origin-Mandi $\times$ 2-Week-Block Cluster Bootstrap** ($R = 5{,}000$, Phipson–Smyth $p$-values) on all `N = 69,526` shortlisted holdout episodes under baseline modeled trap penalties:

| Hypothesis | Comparison | Point Estimate | 95% Two-Way Bootstrap CI | $p_{\text{raw}}$ | $p_{\text{Holm}}$ | Outcome | Interpretation |
|:---|:---|---:|---:|---:|---:|:---|:---|
| **`H1`** | `MandiGuard` minus `B1` Mean $\Delta\text{Net}$ | **+₹102.78/qtl** | [+₹48.66, +₹153.45] | 0.0006 | **0.0012** | **SUPPORTED** | **+₹3,083.5 extra profit per 30-qtl smallholder truckload** over chasing top screen prices. |
| **`H2`** | `MandiGuard` minus `B2` Mean $\Delta\text{Net}$ | +₹6.13/qtl | [-₹17.02, +₹25.02] | 0.2699 | 0.2699 | **NOT_SUPPORTED** | Failed on mean profit (`+₹6.13/qtl` is within sampling noise). Reflects a deliberate safety tradeoff: `MandiGuard` dispatches selectively (48.66% vs 62.11%) while nearly halving loss-trip rate (9.97% vs 18.11%) and reducing worst-10% `CVaR_10%` from -₹436.67 to -₹37.89/qtl. |
| **`H3`** | `MandiGuard` minus `B3` Ep. Phantom Loss | **-37.29 pp** | [-40.19 pp, -34.24 pp] | 0.0002 | **0.0008** | **SUPPORTED** | Cuts episode-level net losses from 42.14% (`B3` ML Point) down to 4.85%. |
| **`H4`** | `MandiGuard` minus `0.75 * B4` Calls | **-3.05 calls** | [-3.44, -2.69] | 0.0002 | **0.0008** | **SUPPORTED** | **44.4% fewer tool calls** (8.75 vs 15.74) by design of cheap-first ordering while matching `B4` decision utility identically (₹452.79/qtl). Practically useful under tight query budgets (`B = 6`), though direct API rupee savings (₹0.05/call) are minor relative to crop profit. |

---

## 2. View 2: Fair Matched Complete-Observation Cohorts & Trap-Penalty Crossover (`Exp 15`)

To isolate missing-data assumptions and closed-yard trap rules from underlying price-forecasting accuracy, `Exp 15` evaluates two transparent sensitivity benchmarks on `Holdout_2025_2026`:

### A. Fair Matched Complete-Observation Cohorts (Zero Simulated Trap Rules, Zero Selection Bias)
Both cohorts evaluate an **identical episode set across all 4 policies** (`B1`, `B2`, `B3`, `MandiGuard`) where every shortlisted top-5 candidate has observed prices:

| Cohort (`Identical Episodes`) | Policy | Dispatch Rate | Mean Net Gain (₹/qtl) | Loss-Trip Rate | Worst-10% `CVaR_10%` (₹/qtl) | `MandiGuard` Minus Policy |
|:---|:---|---:|---:|---:|---:|---:|
| **All Top-5 Observed on Arrival `d0`** (`N = 10,162`) | `B1_NaiveScreen` | 74.78% | ₹472.51 | 19.84% | -₹694.72 | **+₹38.38/qtl** |
| **All Top-5 Observed on Arrival `d0`** (`N = 10,162`) | `B2_FreshRoad` | 64.38% | ₹469.99 | 15.09% | -₹94.70 | **+₹40.91/qtl** |
| **All Top-5 Observed on Arrival `d0`** (`N = 10,162`) | `B3_MLPoint` | 73.47% | **₹553.22** | 14.77% | -₹362.40 | -₹42.33/qtl |
| **All Top-5 Observed on Arrival `d0`** (`N = 10,162`) | `MandiGuard` | 47.31% | ₹510.89 | **6.82%** | **-₹36.07** | — |
| **All Top-5 Exact Variety in `d0..d2`** (`N = 16,849`) | `B1_NaiveScreen` | 81.45% | ₹581.06 | 20.63% | -₹829.21 | **+₹11.47/qtl** |
| **All Top-5 Exact Variety in `d0..d2`** (`N = 16,849`) | `B2_FreshRoad` | 70.97% | ₹572.09 | 15.81% | -₹588.86 | **+₹20.44/qtl** |
| **All Top-5 Exact Variety in `d0..d2`** (`N = 16,849`) | `B3_MLPoint` | 79.16% | **₹670.38** | 15.02% | -₹464.35 | -₹77.85/qtl |
| **All Top-5 Exact Variety in `d0..d2`** (`N = 16,849`) | `MandiGuard` | 54.31% | ₹592.53 | **7.74%** | **-₹48.25** | — |

**Key Insight:** On `N = 10,162` guaranteed-open episodes, `MandiGuard` (₹510.89/qtl, 6.82% LTR, -₹36.07 `CVaR_10%`) still outperforms `B1` (+₹38.38) and `B2` (+₹40.91), while unfiltered point-ML `B3` earns ₹553.22/qtl (+₹42.33 higher mean)—at **2.2x higher loss-trip rate** (14.77% vs 6.82%) and **10x deeper tail losses** (-₹362.40 vs -₹36.07). This demonstrates that **price forecasting itself works well on open yards; standard point-ML fails on the full market specifically because it lacks `T1` openness screening and `T4` downside cushions**.

### B. Trap-Penalty Crossover Curve (`All_Shortlisted_Episodes`, `N = 69,526`)
| Counterfactual Trap-Penalty Regime | `B1` Mean (LTR) | `B2` Mean (LTR) | `B3` Mean (LTR) | `MandiGuard` Mean (LTR) | `MG - B1` | `MG - B2` | `MG - B3` |
|:---|---:|---:|---:|---:|---:|---:|---:|
| `1_Baseline_Div1.5x_Disc10pct` | ₹350.01 (40.46%) | ₹446.66 (18.11%) | ₹330.85 (45.28%) | ₹452.79 (9.97%) | **+₹102.78** | +₹6.13 | **+₹121.94** |
| `2_OneWayDiv_Div1.0x_Disc10pct` | ₹362.61 (40.46%) | ₹449.33 (18.11%) | ₹344.88 (45.28%) | ₹454.27 (9.97%) | **+₹91.66** | +₹4.94 | **+₹109.39** |
| `3_HalfDiv_Div0.5x_Disc5pct` | ₹413.57 (38.01%) | ₹452.32 (18.08%) | ₹409.88 (42.07%) | ₹456.00 (9.97%) | **+₹42.43** | +₹3.68 | **+₹46.12** |
| `4_ZeroDiv_Div0.0x_Disc0pct` *(crossover boundary)* | **₹468.17** (18.52%) | ₹456.09 (12.50%) | **₹479.09** (20.40%) | ₹458.17 (**6.09%**) | -₹10.00 | +₹2.08 | -₹20.93 |
| `5_ZeroTrap_BreakEven0_Missing3d` | ₹376.77 (8.33%) | ₹457.24 (12.25%) | ₹385.42 (4.93%) | ₹459.03 (5.96%) | **+₹82.26** | +₹1.79 | **+₹73.61** |

`MandiGuard` leads `B1` and `B3` through 0.5x return freight / 5% discount (+₹42.43 / +₹46.12) and at `₹0` break-even (+₹82.26 / +₹73.61), crossing below `B1`/`B3` on mean only at the unrealistic zero-cost boundary (`0.0x` return freight and `0%` discount: -₹10.00 vs `B1`, -₹20.93 vs `B3`, where `MandiGuard` still cuts loss-trip rate roughly three-fold to 6.09% and holds `CVaR_10%` at -₹28.70 vs -₹877.41 `B1` and -₹851.02 `B3`).

---

## 3. Main Empirical & Baseline Findings (`Exp 1`, `Exp 2`, `Exp 2b`)

1. **Phantom Spatial Arbitrage Decomposition (`Exp 1`):** Under naive screen chasing (`B1`, 63,040 holdout dispatches), headline spreads average ₹1,330.49/qtl—yet **58.94%** walk into a closed-yard or missing-variety trap (46.69% had zero exact-variety arrivals across 3 consecutive days) and **40.46% lose money** (48.69% in Onion, 51.57% in Madhya Pradesh, 46.82% in Himachal Pradesh). Freight/fees remove ₹160.81/qtl, spoilage removes ₹68.76/qtl, and trap/price-reversion losses remove ₹714.90/qtl, leaving ₹386.02/qtl conditional net gain. Worst-10% `CVaR_10%` across shortlisted episodes reaches -₹1,062.66/qtl (-₹31,879.8 loss on one 30-qtl truckload, over 8x a smallholder household's monthly crop income of ₹3,798).
2. **Unfiltered ML Point Forecasting (`Exp 2`):** `B3_MLPointDispatch` (93.05% dispatch) attains only ₹330.85/qtl mean gain with **45.28% conditional phantom losses**, **65.65% traps**, and `-₹1,097.80/qtl` `CVaR_10%`—confirming that raw price forecasting without `T1` openness checks or `T4` downside uncertainty bounds hallucinates arbitrage on stale yards.
3. **Single Continuous Cascade vs Multi-Agent Quantization (`B5`) and Verbal Rules (`B6`):** Continuous `MandiGuard` earns ₹452.79/qtl vs ₹437.39/qtl (`B5` 3-role quantized message bus) and ₹431.94/qtl (`B6` verbal rule router, 21.59% traps).
4. **Exploratory Check on Native Open-Meteo NWP States (`Exp 2b`):** Across the 4 states with 100% archived Open-Meteo Historical NWP forecasts (Gujarat, Karnataka, Madhya Pradesh, Maharashtra; `N = 42,766`), `MandiGuard` achieves ₹485.18/qtl vs `B1` ₹425.65 (+₹59.53/qtl) and `B2` ₹453.37 (+₹31.82/qtl) while lowering episode phantom losses from 38.04% (`B1`) to 5.52%. *Methodological note:* this exploratory check confirms that replacing missing northern NWP grids (`43/145` cells) with causal Ridge estimates did not drive the main benchmark; it does not rescue `H2` (`p_Holm = 0.2699`).

---

## 4. Grade-Explicit HP Apple 2026 Harvest, Ablations & Operational Tradeoffs (`Exp 3`–`Exp 9`)

1. **Grade-Explicit HP Apple Nuance (`Exp 3`):** Across 1,537 shortlisted 2026 HP Apple lots, naive `B1` (100% dispatch) walks into **94.14% traps** (58.88% lose money, `CVaR_10% = -₹8,487.24/qtl`), particularly severe in Grade B (-₹427.54/qtl). `MandiGuard` reduces traps seven-fold (13.24%), reduces worst-10% losses from **-₹8,487.24/qtl to -₹102.76/qtl**, and turns Grade B profitable (+₹833.70/qtl). **Honest disclosure:** Because the point forecaster trained on 2024 non-grade-explicit data produces wide conformal intervals on 2026 `Grade A`, `MandiGuard` dispatches conservatively (18.67%, mean ₹605.06/qtl) below `B2` (33.64%, ₹1,150.83/qtl, 34.04% traps, `CVaR_10% = -₹272.50/qtl`) and `B1` (₹841.58/qtl).
2. **Tool Attribution (`Exp 4`):**
   - **`T1` (Vitality/Variety)** is the strongest safeguard: removing `T1` drops mean gain -₹134.05/qtl (₹452.79 -> ₹318.74), raises traps 4.2x (16.17% -> 67.16%), and increases calls (8.75 -> 11.03).
   - **`T4` (Causal Conformal 80% LCB)** provides tail-loss protection: removing `T4` raises dispatched phantom losses from 9.97% to 16.89% and worsens `CVaR_10%` from -₹37.89 to -₹397.19/qtl, while empirical causal LCB coverage held near the nominal 80% target (78.85% in validation, 79.07% in holdout).
   - **`T2` (OSRM Highways)** yields modest overall improvement (+₹0.44/qtl overall, +₹1.85/qtl in extreme heat/rain) over $1.15\times$ Euclidean approximation once corridors are bounded to 15–500 km.
   - **`T3` (Climate Spoilage)** improves heat/rain safety (PLR 11.39% -> 10.10% and `CVaR_10%` -₹67.49 -> -₹57.11/qtl), though stacking weather pruning atop already conservative LCB margins trades off -₹2.46/qtl in unconditional mean gain (₹455.25 -> ₹452.79/qtl).
3. **Budget Frontier (`Exp 5`):** Under a strict cap of 6 tool calls per episode, `MandiGuard` achieves **₹403.85/qtl** (5.05 calls) vs `B4` upfront (₹299.31/qtl, 5.75 calls)—**+₹104.54/qtl higher gain with fewer calls**.
4. **Sensitivity & Statutory Fees (`Exp 6`):** Across the $3\times 3$ freight $\times$ spoilage multiplier grid, `MandiGuard` beats `B1` across all 9/9 cells by +₹82.62 to +₹121.42/qtl, beats `B2` at standard and 1.5x spoilage (+₹5.27 to +₹14.50/qtl), and trails `B2` marginally (-₹0.02 to -₹1.52/qtl) only when spoilage is halved to 0.5x. Replacing uniform 1.5% fees with verified state-specific GoI APMC F&V fee rules increases realized net spreads by ₹7.12/qtl (`MandiGuard` ₹452.79 vs ₹445.67/qtl uniform).
5. **Live API Check (`Exp 8`), Zero-Shot LOSO State Transfer (`Exp 9`) & Dual-Tier Official `data.gov.in` + AGMARKNET 2.0 Audit (`Exp 14`):** Live Nov-2026 `agmarknet.gov.in` queries show 11/22 (50.0%) benchmark state corridors non-reporting across the full prior week; zero-shot Leave-One-State-Out transfer beats naive `B1` in all 6 held-out states (arrival-drop rate reduced to 3.34%–9.72% vs 45.29%–55.66% `B1`). Our upgraded Dual-Tier `Exp 14` parity audit verifies **100.00% `Min_Price`/`Max_Price` and 99.42% (171/172) `Modal_Price` parity** on a single-day official `data.gov.in` XML snapshot (`2023-10-18`, 172 matched core-panel keys out of 6,434 all-India records) **and 100.00% (2,042/2,042) exact rupee parity across `Min_Price`, `Max_Price`, and `Modal_Price`** over **149 trading days** (`2025-11-07..2026-04-13`) against direct official Government of India AGMARKNET 2.0 portal exports (`hp_apple_daily_2025_2026.csv`).

---

## 5. Nearly 10-Year Robustness (2017–2026) & Training-Window Scaling (`Exp 10`, `Exp 10b`)

Evaluated across **42,722,187 raw streamed AGMARKNET archive records (2017-01-01 to 2026-04-13)** (883,406 rows across our 178-mandi panel) paired with **291,384 NASA POWER daily agroclimatology rows (2017–2023, 114 `0.5°` cells, 0.0% missing)**:

1. **10-Year Regime Robustness (`Exp 10`, 661,192 matched episodes across 6 macro-economic & climate regimes):**
   * Naive screen chasing `B1` suffers **39.18%–44.29% Loss-Trip Rates** and severe **Worst-10% Loss of -₹786.52 to -₹1,289.28/qtl** across all six regimes (2017H2 GST, 2018–19 Pre-COVID, 2020–21 COVID, 2022–23 Inflation/Export Curbs, 2024 El-Niño Heatwave, 2025–26 Holdout).
   * Causally expanding `MandiGuard` holds Loss-Trip Rate to **8.78%–12.03%** and bounds Worst-10% Loss to **-₹20.93 to -₹37.89/qtl**, reaching **+₹165.14/qtl** higher net gain over `B1` during the 2024 El-Niño heatwave (₹387.91 vs ₹222.77/qtl, `N = 96,468`).
2. **Diminishing Returns of Multi-Year Volume (`Exp 10b`):** On `Holdout_2025_2026`, scaling training data from 1-Yr (2024, 701,932 rows: ₹452.79/qtl) -> 3-Yr (2022–2024, 1,668,451 rows: ₹454.74/qtl) -> 8-Yr (2017–2024, 3,437,098 rows: ₹454.94/qtl) adds only +₹2.15/qtl, showing that recent regime fit and causal conformal cushions matter far more than multi-year data volume.

---

## 6. Stage II — Mechanistic Autopsy & Validation-Calibrated Uncensored Conformal Risk Control (`Exp 16`–`Exp 17`, `[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]`)

Preserving pre-registered Stage I (`e421d15`) untouched, read-only diagnostics on `Train_2024`, `Val_2025H1` (`N = 42,794`, `arr_dt <= 2025-05-31`), and `HP_Warmup` (`Exp 16`) followed by strictly validation-calibrated (`Val_2025H1`, $\beta_{\text{target}} = 0.095 \implies \lambda^* = 0.15$ for `Rung 3` and $\lambda^* = 0.10$ for `Rung 2`) out-of-sample evaluation (`Exp 17`) establish three mechanistic insights:

1. **Censored-Arrival Survivorship Bias (`Exp 16`):** Complete-case `dropna(target_ret)` drops **55.83%** of `Train_2024` corridors (**12.64%** even after passing `T1`). Across `dest_age_days = 0..3`, exact-`d0` open rates fall from **89.10% -> 62.63%** (`Train_2024`) and **86.90% -> 62.97%** (`Holdout`), causing `d0`-only targets to understate true uncensored 20th-percentile downside drops by **1.82x–2.00x** in `Train_2024` (`-4.81%` vs `-9.62%` at `0d`; `-13.46%` vs `-26.08%` at `3d`) and up to **2.54x** on `Holdout` (`-10.55%` vs `-26.82%` at `3d`).
2. **The Heteroscedastic Coverage Illusion & HP Apple Sub-Grade `T1` Sparsity (`Exp 16`):** Pooled split conformal (`MandiGuard v1`) hits ~79% marginal coverage only by combining **88.91% (`Val`) / 90.46% (`Holdout`) over-coverage in calm `Q1` markets** (true Q80 error `1.43%–1.98%` vs `4.09%–6.04%` cushion) with **67.84% (`Val`) / 67.80% (`Holdout`) under-coverage in volatile `Q4` markets** (true Q80 error `14.12%–17.08%` vs `7.15%–8.89%` cushion). Moreover, on HP Graded Apples, **`82.75%` (Warmup) and `77.82%` (Holdout) of `MG_v1` refusals on `B2`-dispatched lots stemmed from `T1`'s rigid `open_prob_14d >= 0.50` / `dow >= 0.35` gate** (vs only `16.59% / 22.18%` from `T4`), overturning the Stage-I assumption that `T4` conformal width caused most HP Apple under-dispatch.
3. **`MandiGuard-CRC` Factorial Out-of-Sample Gains (`Exp 17`, calibrated strictly on `Val_2025H1` at $\beta^* = 0.095 \implies \lambda^* = 0.15$):**
   * **Full Holdout (`N = 69,526`, 2-Way Cluster Bootstrap `R = 5,000`):** From `MG_v1` (**₹452.79/qtl**, `9.97%` LTR, `-₹37.89` `CVaR_10%`, `8.75` calls), free Euclidean Step-0 pre-sorting (`Rung 1`) adds `+₹2.36/qtl` (**₹455.15**), Uncensored Price-Scaled CRC (`Rung 2`) adds `+₹14.14/qtl` (**₹469.29**), and Thin-Grade-Aware `T1` (`Rung 3: MandiGuard-CRC`) adds `+₹9.88/qtl`, reaching **₹479.17/qtl (`₹14,375.1` per 30-qtl truck)** at `10.48%` LTR, `-₹44.03/qtl` `CVaR_10%`, and `9.07` calls—beating `B1` by **+₹129.16/qtl** ($p = 0.0004$), `B2` by **+₹32.51/qtl** (`95% CI [+₹12.05, +₹50.49]`, $p = 0.0016$), and `MG_v1` by **+₹26.38/qtl** ($p = 0.0002$).
   * **Fair Open-Yard Cohort (`Matched_AllTopK_Observed_d0`, `N = 10,162`):** `MandiGuard-CRC` improves to **₹533.75/qtl** (`7.14%` LTR, `-₹35.00` `CVaR_10%`), beating `B1` (+₹61.24), `B2` (+₹63.76), and `MG_v1` (+₹22.86).
   * **HP Apple 2026 (`N = 1,537`):** `MandiGuard-CRC` lifts overall mean from `₹605.06` to **₹812.08/qtl** (`+₹207.02/qtl`, `+34.2%`, flipping Grade A from `₹205.46` / `20.0%` LTR to **`₹477.56/qtl` / `11.54%` LTR** and Grade B to **`₹852.01/qtl`**), while honestly trailing `B2` on raw Apple mean (`₹1,150.83/qtl` at higher `28.43%` LTR and `-₹272.50` `CVaR_10%`).
   * **Methodological Note:** Consistent with selective conformal calibration (Angelopoulos et al., 2024; Bao et al., 2024), our `(n_l + 1)/(n_d + 1) <= beta` tuner adapts CRC as an empirical `Val_2025H1` heuristic under post-selection denominator `n_d(lambda)` and non-exchangeable seasonal panels, verified empirically rather than via Theorem 1 guarantees.

---

## Appendix Illustrations — Exploratory Model, Edge-Caching & Cooperative Scenarios (`Exp 11`–`Exp 13b`, Not Main Contributions)

*Scope note: Items 1–3 below are exploratory Appendix illustrations using un-preregistered forecaster variants and stylized deployment cost parameters (₹0.05/call API rate, 0.70x FPO freight, 50/50 split lots), not core thesis contributions.*

1. **Alternative Predictors & Adaptive Conformal Showdown (`Exp 11`):**
   * On `Holdout_6State_2025_2026` (`N = 69,526`), `Direct_Quantile_GBDT_Q20` reaches ₹459.02/qtl (9.40% LTR, -₹32.28/qtl `CVaR_10%`), followed by `ExtraTrees_Conformal` (₹453.30), `MandiGuard_Standard` (₹452.79), `MandiGuard_ACI_NeurIPS21` (₹437.90, adapting Tomato $\alpha \to 0.038$), `Deep_MLP_Conformal` (₹435.38), and `Contextual_UCB_Bandit` (₹406.47).
   * On `HP_Apple_Grade_2026` (`N = 1,537` under grade shift), `Deep_MLP_Conformal` leads mean (₹615.34/qtl, 18.15% LTR), while `MandiGuard_ACI` adapts Apple $\alpha$ from 0.200 -> 0.164, reducing Worst-10% Loss by 27.6% (-₹102.76 -> -₹74.42/qtl).
2. **`MandiGuard-ZeroCloud` & Satisficing Edge-Caching (`Exp 12`):** Offloading static OSRM road tables and CPU ML scoring locally (`MandiGuard_ZeroCloud_Full`) achieves ₹455.33/qtl (₹13,659.8 30-qtl load) using 5.53 live calls/query (modeled ₹2,764 per 10,000 queries vs ₹7,868 for `B4`, -64.9% modeled API spend). Adding `Val_2025H1`-calibrated satisficing early-exit (`>= ₹250/qtl`, `MandiGuard_ZeroCloud_Satisficing`) cuts calls to 3.84 calls/query (₹1,922 per 10k queries = -75.6% modeled API spend at 0.075 ms/query CPU) while keeping 97.3% of standard net gain (₹440.48/qtl).
3. **Cooperative FPO Pooling, Split Portfolio & Biological Spoilage Clock (`Exp 13`, `Exp 13b`):**
   * Pooling into 90-qtl FPO trucks (modeled 0.70x freight) raises net gain to ₹477.28/qtl (₹14,318.5 per 30-qtl share)—+₹24.49/qtl above standard 30-qtl solo (₹452.79/qtl) and +₹67.75/qtl above marginal 10-qtl farmers (1.60x freight: ₹409.53/qtl).
   * Splitting 50/50 across top-2 verified yards (`Split_Top2_Portfolio`) reduces closed-trap exposure 39% relative (16.17% -> 9.85%) and Loss-Trip Rate to 8.09% (₹394.82/qtl).
   * The $Q_{10}$ Biological Spoilage Clock illustrates how safe transit windows before 15% modeled thermal shrinkage compress from 110.8h (20°C winter) to 24.1h (42°C summer) on Tomato (Potato: 418.6h -> 91.1h), formatting illustrative `<= 160`-char farmer SMS cards.
