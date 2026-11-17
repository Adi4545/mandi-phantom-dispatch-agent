# Empirical & Confirmatory Findings — `MandiGuard`

**Primary Holdout Period:** `2025-06-01`..`2026-04-08` (realized arrival lookup up to `2026-04-13`), spanning **`69,526` shortlisted active dispatch episodes** across `174` origin mandis and `23` two-week blocks (`81,048` total holdout episodes; `468,816` candidate corridors).  
**Secondary Harvest Validation:** Grade-Explicit Himachal Pradesh Apple (`2026-06-01`..`2026-08-27`, `1,537` shortlisted active episodes).  
**Frozen Pre-Holdout Parameters:** Trained solely on `2024`; safety margin frozen on `Val_2025H1` at **`Rs 50.0/qtl`** prior to unblinding.

---

## 1. Confirmatory Hypothesis Outcomes (`m = 4`, Holm–Bonferroni FWER = `0.05`)

Evaluated via paired **Two-Way Origin-Mandi $\times$ 2-Week-Block Cluster Bootstrap** ($R = 5{,}000$, Phipson–Smyth $p$-values):

| Hypothesis | Comparison | Point Estimate | 95% Two-Way Bootstrap CI | $p_{\text{raw}}$ | $p_{\text{Holm}}$ | Outcome | Interpretation |
|:---|:---|---:|---:|---:|---:|:---|:---|
| **`H1`** | `MandiGuard` minus `B1` Mean $\Delta\text{Net}$ | **`+₹102.78/qtl`** | `[+₹48.66, +₹153.45]` | `0.0006` | **`0.0012`** | **`SUPPORTED`** | **`+₹3,083.5` extra profit per 30-qtl smallholder truckload** over chasing top screen prices. |
| **`H2`** | `MandiGuard` minus `B2` Mean $\Delta\text{Net}$ | `+₹6.13/qtl` | `[-₹17.02, +₹25.02]` | `0.2699` | `0.2699` | **`NOT_SUPPORTED`** | Honest risk–return tradeoff: `MandiGuard` yields slightly higher mean $\Delta\text{Net}$ (`₹452.79` vs `₹446.66`) *while nearly halving Phantom Loss Risk (`9.97%` vs `18.11%`) and improving tail `CVaR_10%` 11.5x (`-₹37.89` vs `-₹436.67/qtl`)*. |
| **`H3`** | `MandiGuard` minus `B3` Ep. Phantom Loss | **`-37.29 pp`** | `[-40.19 pp, -34.24 pp]` | `0.0002` | **`0.0008`** | **`SUPPORTED`** | Cuts episode-level net losses from `42.14%` (`B3` ML Point) down to `4.85%`. |
| **`H4`** | `MandiGuard` minus `0.75 * B4` Calls | **`-3.05 calls`** | `[-3.44, -2.69]` | `0.0002` | **`0.0008`** | **`SUPPORTED`** | **`44.4%` fewer tool calls (`8.75` vs `15.74`)** while matching `B4` decision utility identically (`₹452.79/qtl`). |

---

## 2. Main Policy & Baseline Findings (`Exp 1`, `Exp 2`, `Exp 2b`)

1. **Phantom Spatial Arbitrage Is Real and Huge (`Exp 1`):** Under naive screen chasing (`B1`, `63,040` holdout dispatches), headline spreads average `₹1,330.49/qtl`—yet **`58.94%`** walk into a Closed-Yard or Missing-Variety Trap (`46.69%` had zero exact-variety arrivals across 3 consecutive days!) and **`40.46%` lose money** (`48.69%` in Onion, `51.57%` in Madhya Pradesh, `46.82%` in Himachal Pradesh). Worst-10% `CVaR_10%` reaches `-₹1,062.66/qtl` (`-₹31,879.8` loss on one 30-qtl truckload, >8x a smallholder household's monthly crop income of `₹3,798`).
2. **Unconstrained ML Point Forecasting Performs Worse Than Naive Screens (`Exp 2`):** `B3_MLPointDispatch` (`93.05%` dispatch) attains only `₹330.85/qtl` mean gain with **`45.28%` conditional phantom losses** and **`65.65%` traps**—proving that raw price forecasting without `T1` market-vitality checks or downside uncertainty bounds hallucinates arbitrage on stale yards.
3. **Unified Single-Agent Funnel Beats Multi-Agent Quantization (`B5`) and Verbal Heuristic Rules (`B6`):** Continuous `MandiGuard` earns `₹452.79/qtl` vs `₹437.39/qtl` (`B5` 3-agent quantized message bus) and `₹431.94/qtl` (`B6` verbal rule router, `21.59%` traps).
4. **Native Open-Meteo NWP Robustness (`Exp 2b`):** Across the **4 states with 100% native Open-Meteo Historical NWP forecasts** (`Gujarat`, `Karnataka`, `Madhya Pradesh`, `Maharashtra`; `N = 42,766`), `MandiGuard` achieves `₹485.18/qtl`, beating **both `B1` (`+₹59.53/qtl`) and `B2` (`+₹31.82/qtl`)** while reducing episode phantom losses from `38.04%` (`B1`) to `5.52%`.

---

## 3. Grade-Explicit HP Apple 2026 Harvest, Ablations, & Operational Tradeoffs (`Exp 3`–`Exp 9`)

1. **Grade-Explicit HP Apple Nuance (`Exp 3`):** Across `1,537` shortlisted 2026 HP Apple lots, naive `B1` (`100%` dispatch) walks into **`94.14%` traps** (`58.88%` lose money, `CVaR_10% = -₹8,487.24/qtl`), especially severe in `Grade B` (`-₹427.54/qtl`). `MandiGuard` slashes traps **7x** (`13.24%`), slashes tail ruin **82x** (`CVaR_10% = -₹102.76/qtl`), and turns `Grade B` strongly profitable (`+₹833.70/qtl`). **Honest disclosure:** Because the point forecaster trained on `2024` non-grade-explicit data produces wide conformal intervals on `2026` premium `Grade A`, `MandiGuard` dispatches conservatively (`18.67%`, mean `₹605.06/qtl`) below aggressive `B2` (`33.64%`, `₹1,150.83/qtl`, `34.04%` traps, `CVaR_10% = -₹272.50/qtl`).
2. **Tool Attribution (`Exp 4`):**
   - **`T1` (Vitality/Variety)** is overwhelmingly the strongest safeguard: removing `T1` drops mean gain `-₹134.05/qtl` (`₹452.79 -> ₹318.74`), raises traps `4.2x` (`16.17% -> 67.16%`), and increases calls (`8.75 -> 11.03`).
   - **`T4` (Causal Conformal 80% LCB)** provides tail & loss insurance: removing `T4` raises dispatched phantom losses `9.97% -> 16.89%` and worsens `CVaR_10%` by **10.5x** (`-₹37.89 -> -₹397.19/qtl`), while causal LCB empirical coverage held remarkably close to nominal `80%` (`78.85%` in validation, `79.07%` in holdout).
   - **`T2` (OSRM Highways)** yields modest overall improvement (`+₹0.44/qtl` overall, `+₹1.85/qtl` in extreme heat/rain) over $1.15\times$ Euclidean approximation once corridors are bounded to `15–500 km`.
   - **`T3` (Climate Spoilage)** improves heat/rain safety (`PLR 11.39% -> 10.10%` and `CVaR_10% -₹67.49 -> -₹57.11/qtl`), though stacking weather pruning atop already conservative LCB margins trades off `-₹2.46/qtl` in unconditional mean gain (`₹455.25 -> ₹452.79/qtl`).
3. **Pareto Dominance (`Exp 5`):** Under a strict budget of `6` tool calls per episode, `MandiGuard` achieves **`₹403.85/qtl`** (`5.05` calls) vs `B4` upfront (`₹299.31/qtl`, `5.75` calls) — **`+₹104.54/qtl` higher gain with fewer calls**.
4. **Sensitivity & Statutory Fees (`Exp 6`):** Across the $3\times 3$ freight $\times$ spoilage multiplier grid, `MandiGuard` beats `B1` across all `9/9` cells by `+₹82.62` to `+₹121.42/qtl`, beats `B2` at standard and `1.5x` spoilage (`+₹5.27` to `+₹14.50/qtl`), and trails `B2` marginally (`-₹0.02` to `-₹1.52/qtl`) only when spoilage is halved to `0.5x`. Replacing uniform `1.5%` fees with verified state-specific GoI APMC F&V fee rules increases realized net spreads by `₹7.12/qtl` (`MandiGuard ₹452.79` vs `₹445.67/qtl` uniform).
5. **Live API Check (`Exp 8`) & Zero-Shot LOSO State Transfer (`Exp 9`):** Live Nov-2026 API queries show `11/22` (`50.0%`) benchmark state corridors non-reporting across the full prior week; zero-shot Leave-One-State-Out transfer beats naive `B1` in all 6 held-out states cleanly (`ArrDrop` reduced to `3.3%–9.7%` vs `45.3%–55.7%` `B1`).

---

## 4. Nearly 10-Year Robustness (`2017–2026`), Modern AI / ACI, `ZeroCloud`, FPO Pooling & Spoilage Clock (`Exp 10`–`Exp 13b`)

Expanded across **`42,722,187` raw streamed official AGMARKNET records (`2017-01-01`..`2026-04-13`)** (`883,406` rows across our `178`-mandi panel) paired with **`291,384` NASA POWER daily agroclimatology rows (`2017–2023`, `114` `0.5°` cells, `0.0%` missing)**:

1. **10-Year Regime Robustness (`Exp 10`, `661,192` matched episodes across 6 macro-economic & climate regimes):**
   * Naive screen chasing `B1` suffers **`39.18%–44.29%` Loss-Trip Rates** and catastrophic **`Worst-10% Loss` of `-₹786.52` to `-₹1,289.28/qtl`** across every single macro era (`2017H2 GST`, `2018–19 Pre-COVID`, `2020–21 COVID`, `2022–23 Inflation/Export Curbs`, `2024 El-Niño Heatwave`, `2025–26 Holdout`).
   * Causally expanding `MandiGuard` cuts `Loss-Trip Rate` to **`8.78%–12.03%`** and bounds `Worst-10% Loss` to **`-₹20.93` to `-₹37.89/qtl`** (`28x–38x` tail-risk collapse), reaching **`+₹165.14/qtl`** higher net gain over `B1` during the `2024 El-Niño Heatwave` (`₹387.91` vs `₹222.77/qtl`, `N = 96,468`).
2. **Diminishing Returns of Multi-Year Volume (`Exp 10b`):** On `Holdout_2025_2026`, scaling training data from **`1-Yr` (`2024`, `701,932` rows: `₹452.79/qtl`) -> `3-Yr` (`2022–2024`, `1,668,451` rows: `₹454.74/qtl`) -> `8-Yr` (`2017–2024`, `3,437,098` rows: `₹454.94/qtl`)** adds only `+₹2.15/qtl`, proving that recent regime fit + causal conformal bounds matter far more than brute-force historical volume.
3. **Modern AI & Adaptive Conformal Showdown (`Exp 11`):**
   * On `Holdout_6State_2025_2026` (`N = 69,526`), **`Direct_Quantile_GBDT_Q20`** leads at **`₹459.02/qtl`** (`9.40%` LTR, `-₹32.28/qtl` `CVaR_10%`), followed by `ExtraTrees_Conformal` (`₹453.30`), `MandiGuard_Standard` (`₹452.79`), `MandiGuard_ACI_NeurIPS21` (`₹437.90`, adapting Tomato $\alpha \to 0.038$), `Deep_MLP_Conformal` (`₹435.38`), and `Contextual_UCB_Bandit` (`₹406.47`).
   * On `HP_Apple_Grade_2026` (`N = 1,537` under grade shift), **`Deep_MLP_Conformal`** leads mean (`₹615.34/qtl`, `18.15%` LTR), while **`MandiGuard_ACI`** adapts Apple $\alpha$ from `0.200 -> 0.164`, slashing `Worst-10% Loss` **`27.6%`** (`-₹102.76 -> -₹74.42/qtl`).
4. **`MandiGuard-ZeroCloud` & Satisficing Edge-AI (`Exp 12`):** Offloading static OSRM road tables and CPU ML scoring locally (`ZeroCloud_Full`) achieves **`₹455.33/qtl`** (`₹13,659.8` 30-qtl load) using only **`5.53` live calls/query** (`₹2,764` per `10,000` queries vs `₹7,868` for `B4`, **`-64.9%` API spend**). Adding `Val_2025H1`-calibrated satisficing early-exit (`>= ₹250/qtl`, `ZeroCloud_Satisficing`) cuts calls further to **`3.84` calls/query** (**`₹1,922` per `10k` queries = `-75.6%` cost** at `0.075 ms/query` CPU) while keeping `97.3%` of standard net gain (`₹440.48/qtl`).
5. **Cooperative FPO Pooling, Split Portfolio & Biological Spoilage Clock (`Exp 13`, `Exp 13b`):**
   * Pooling into **`90-qtl` FPO trucks (`0.70x` freight)** elevates net gain to **`₹477.28/qtl`** (`₹14,318.5` per 30-qtl equivalent share)—**`+₹24.49/qtl`** above standard `30-qtl` solo (`₹452.79/qtl`) and **`+₹67.75/qtl`** above marginal `10-qtl` farmers (`1.60x` freight: `₹409.53/qtl`).
   * Splitting 50/50 across top-2 verified yards (`Split_Top2_Portfolio`) cuts `Closed Trap Rate` **`39%` relative (`16.17% -> 9.85%`)** and `Loss-Trip Rate` to `8.09%` (`₹394.82/qtl`).
   * The **$Q_{10}$ Biological Spoilage Clock** shows safe transit windows before `15%` thermal shrinkage compress from **`110.8h` (`20°C` winter) to `24.1h` (`42°C` summer)** on Tomato (`Potato`: `418.6h -> 91.1h`), directly driving real `<= 160`-char farmer SMS advisories.
