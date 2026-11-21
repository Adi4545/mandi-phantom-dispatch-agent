> This document records the earlier analysis. Use the [correction record](../final/CORRECTIONS.md) for the revised downside estimates, arrival-day diagnostics, weather control and reproduction commands.

# Plain-English Complete Study Guide — `MandiGuard`

**Who This Guide Is For:** Any M.Tech student, thesis guide, or external examiner who wants to understand—and defend—every idea, dataset, equation, and architectural choice in `MandiGuard` from first principles without drowning in dense math.

---

## 1. The Big Idea in Two Sentences

When a vegetable or apple farmer checks a price portal and sees a mandi 200 km away showing ₹700/qtl more than their home market, sending a truck there looks like an easy gain—yet across our 6-state holdout, 58.94% of naive price-chasing dispatches run into closed yards or missing variety auctions and 40.46% lose money outright. **`MandiGuard`** addresses this as a **risk-gated dispatch decision-support system**: a four-step verification cascade (`T1` → `T2` → `T3` → `T4`) that returns `REFUSE_PHANTOM_SPREAD` whenever the risk-adjusted net gain fails to clear a validation-frozen ₹50/qtl safety cushion.

---

## 2. A 5-Number Whiteboard Example (Do This by Hand in 60 Seconds!)

Imagine an examiner asks: *"Show me on the board how your math actually works on one 30-quintal truck of Tomatoes in summer."*

Take these **5 concrete numbers**:
1. **Local Market Price today:** ₹1,500/qtl (30-qtl load worth ₹45,000 at home).
2. **Distant Screen Price (180 km away in Madhya Pradesh, 5.5 hours drive → 2-day auction arrival):** Screen shows ₹2,050/qtl (an apparent **+₹550/qtl** spread).
3. **Highway Freight + Statutory MP Mandi Charge (`F_ij`):**
   - Base loading (₹35) + road freight (₹0.45 × 180 km = ₹81) + MP cross-district regulated mandi charge (1.5% × ₹1,500 = ₹22.5) = **₹138.50/qtl**.
4. **Weather Spoilage at 35°C summer heat (`T3`):**
   - Official MoFPI **NABCONS (2022)** benchmark reports Tomato market/transit loss at 20°C over 24 hours is **3.25%** (0.0325).
   - Because ambient heat is 35°C (+15°C hotter → biological Q10 = 2^(15/10) ≈ 2.83× faster decay) over 5.5 hours (5.5 / 24 = 0.229 days):
   - Estimated shrinkage is `0.0325 × 0.229 × 2.83` ≈ **2.11%** (and if stuck waiting 1 extra day or exposed to ≥ 35 mm rain, spoilage and downgrading rise further).
5. **Arrival-Day Uncertainty Haircut (`T4`, 80% Conformal Lower Bound):**
   - Suppose recent destination prices swing -8% downward over a 2-day transit (`P_arr_LCB` = ₹2,050 × 0.92 = ₹1,886/qtl).

Now subtract in **one simple line** (first-year engineering economics):

$$\text{Safe Gain} = \bigl(\text{₹}1,886 \times (1 - 0.0211)\bigr) - \text{₹}138.50 - \text{₹}1,500 = \text{₹}1,846.2 - \text{₹}138.5 - \text{₹}1,500 = \mathbf{+\text{₹}207.7/\text{qtl}}$$

* Since +₹207.7/qtl > ₹50/qtl safety cushion (frozen on validation), `MandiGuard` returns `DISPATCH` (+₹6,231 expected gain for the 30-qtl truck).
* **Now flip just one condition:** Suppose Tool `T1` checks the yard and finds that the exact tomato variety last traded 6 days ago (stale), or the arrival day is a closed Sunday (`arr_dow_open_rate = 0.15`), or heavy 40 mm rain triggers a quality downgrade (-10% price plus extra rot). `MandiGuard` prunes in `T1` or rejects at `T3`/`T4` with `REFUSE_PHANTOM_SPREAD`—avoiding a potential -₹500/qtl (-₹15,000) closed-yard diversion loss.

---

## 3. Data Sources, Official Benchmarks & What Is Observed vs. Modeled

| Layer | Exact Source | Coverage & Key Figures |
|:---|:---|:---|
| **Daily Market Prices & Varieties** | Public AGMARKNET archive mirror (2024-01-01..2026-04-13) + Nov 2026 Live API + Grade-Explicit HP Apple | 14,443,770 raw rows streamed → 673,971 clean → 260,043 balanced panel across 178 mandis in 6 states (Maharashtra, UP, Karnataka, MP, Gujarat, Himachal Pradesh) and 4 crops (Onion, Potato, Tomato, Apple) + 4,427 grade-explicit HP Apple rows (42 mandis). |
| **Official Dual-Tier Parity (`Exp 14`)** | Official `data.gov.in` Resource `9ef84268-d588-465a-a308-a864a43d0070` XML + Direct `AGMARKNET 2.0` Export + Live `agmarknet.gov.in` | Tier 1 single-day XML spot-check (`2023-10-18`, 6,434 all-India rows, 172 matched keys): 100.0% exact parity on `Min`/`Max`, 99.42% on `Modal`. Tier 2 **149-day AGMARKNET 2.0 export** (`2025-11-07..2026-04-13`, 2,042 matched keys): **100.00% exact parity on `Min`/`Max`/`Modal`**, plus 22 live Nov-2026 queries (11/22 silent over 7 days). |
| **Road Distances & Transit Times** | Public Open Source Routing Machine (OSRM) + district-validated geocoding | 220 mandis validated within ≤ 110 km of District HQ (150 exact matches, 70 centroids) → **8,147 intra-state road corridors** (15–500 km). |
| **Ambient Heat & Monsoon Weather** | ECMWF ERA5 realized reanalysis (145/145 grids) + Open-Meteo Historical NWP (102/145 grids) + causal 2024 nowcast (43 north grids) | 141,955 daily rows (2024-01-01..2026-09-05, no missing weather rows). Strict separation: system sees forecast on decision day *t*; evaluation uses realized ERA5 over [t, t+τ]. |
| **Official Post-Harvest Losses** | **MoFPI / NABCONS (2022)** Rajya Sabha Table (`PIB PRID 2151371`, 01 Aug 2025) | Market-level loss rates: Tomato 3.25%, Onion 1.96%, Apple 1.64%, Potato 0.86% (total losses 11.62%, 7.27%, 9.51%, 5.96%). |
| **State Statutory APMC Fees** | **GoI Ministry of Consumer Affairs (`PIB Release ID 154554`)** | Karnataka and Gujarat: 0.5% user charge (market fee exempt); HP: 0.5% veg / 1.0% Apple (Apple not exempt); Maharashtra: 1.0%; MP and UP: 1.5%. |
| **Hill Roads & Arrivals** | **GoHP *Economic Survey 2025–26*** | 91.59% single-lane motorable roads (39,465 / 43,091 km), 88.86% small/marginal growers, 65.01 lakh qtl F&V APMC arrivals. |
| **Smallholder Truckload & Income** | **MoSPI NSO *NSS Report No. 587* (77th Round)** (`PIB PRID 1753856`) | Potato harvest 2,933 kg (29.33 qtl), Onion 3,873 kg (38.73 qtl) → **30-quintal truckload**; average household net monthly crop receipt ₹3,798/month. |
| **10-Year Historical + NASA Climate Extension (2017–2023)** | Public AGMARKNET archive mirror (2017–2026) & **NASA POWER Agroclimatology** (0.5° grid) | 42,722,187 raw rows streamed across 2017–2026 → **883,406 rows** (178 core mandis) + **291,384 daily NASA POWER rows** (114 cells, no missing rows). |

**What Is Observed vs. Modeled (Open Limitation):** Daily prices, reporting gaps, OSRM highway times, and ERA5/NASA weather come from observed or routed public records. However, **we have no live farmer truck receipts, weighment slips, or field interviews yet**: per-quintal freight (₹35 + ₹0.45/km), Q10 biological rot anchored to NABCONS (2022), and closed-yard diversion penalties are modeled rather than field-measured. Furthermore, our 22/22 `pytest` checks verify code reproducibility, Dual-Tier parity manifests, Stage-II CRC invariants, and temporal leakage guards rather than field economics.

---

## 4. Understanding the 4 Tools & Why Their Order Matters

Think of `MandiGuard` like an airport screening cascade—**apply the cheapest elimination first:**
1. **`Step 0` (Free Screen, 0 API Calls):** Check regional boards; keep the top 5 markets within 15–500 km whose recent 7-day board beats local price by > ₹100/qtl.
2. **`Tool T1` (Vitality & Variety, 1 Call):** Has that exact variety traded recently (≤ 3 days old), at an active yard (≥ 50% open over the past 14 days), and is the arrival weekday usually open (≥ 35%)?
   * *Result:* Prunes 30.82% of candidate episodes early. Removing `T1` (`No_T1_Vitality`) reduces mean net gain by ₹134.05/qtl (₹452.79 → ₹318.74/qtl) and raises trap incidence from 16.17% to 67.16%.
3. **`Tool T2` (OSRM Road + APMC Fee, +1 Call):** Fetch road distance/duration and state APMC charges. Prune if the fresh spread fails to clear freight + yard charges.
4. **`Tool T3` (Weather Spoilage, +1 Call):** Check forecasted heat and monsoon rain along the corridor; compute Q10 spoilage and rain-grading adjustment.
   * *Honest Tradeoff:* Cuts loss rate on 21,656 extreme heat/rain episodes from 11.39% to 10.10% and improves heat/rain worst-10% loss (-₹67.49 → -₹57.11/qtl), while nudging unconditional overall mean down slightly (-₹2.46/qtl: ₹455.25 → ₹452.79) because `T3` + `T4` together reject a few borderline hot-weather trips that turned positive.
5. **`Tool T4` (Causal Arrival Return + 80% Conformal LCB, +1 Call):** Subtract the historical 80th-percentile downside shortfall (`q_hat_0.80`) from the ML point prediction so forecast optimism is buffered.
   * *Result:* Removing `T4` (`No_T4_ConformalLCB`) raises dispatched loss-trip rate from 9.97% to 16.89% and worsens worst-10% tail loss from -₹37.89 to -₹397.19/qtl.

**Why this order differs from running all tools upfront (`B4`) and quantized multi-module routing (`B5`):**
* **`B4_UpfrontAllTools`** reaches the exact same utility (₹452.79/qtl) when lookups are unlimited, while `MandiGuard` uses **44.4% fewer calls** (8.75 vs 15.74 calls/episode, `H4`). We note candidly that fewer average calls follow by design from cheap-first ordering; the empirical payoff appears under tight query budgets (`Exp 5`), where at `B = 6` calls/episode `MandiGuard` earns ₹403.85/qtl (5.05 calls) vs ₹299.31/qtl (5.75 calls) for `B4` (+₹104.54/qtl).
* **`B5_MultiAgentCoordinator`** splits the pipeline into three modules communicating coarse ₹150/qtl buckets (`LOW`/`MED`/`HIGH`)—losing ₹15.40/qtl (₹437.39 vs ₹452.79/qtl) from quantization near the decision boundary while using virtually the same calls (8.76 vs 8.75).

---

## 5. Honest Summary of Outcomes, Tradeoffs & Dual-View Open-Yard Defense

Across 69,526 untouched holdout episodes (June 2025–April 2026):
* **`H1` (vs Naive Screen `B1`): `SUPPORTED`** (+₹102.78/qtl, p_Holm = 0.0012, i.e., +₹3,083.5 per 30-qtl truck).
* **`H2` (vs Fresh+OSRM `B2`): `NOT_SUPPORTED` (p_Holm = 0.2699)** on overall mean profit (+₹6.13/qtl, 95% CI [-₹17.02, +₹25.02]). Put simply, **`B2` ties `MandiGuard` on overall mean profit** (₹446.66 vs ₹452.79/qtl). `MandiGuard` differs in risk profile—declining borderline high-variance trips (48.66% vs 62.11% dispatch), halving loss trips (9.97% vs 18.11%), and limiting worst-10% tail loss (-₹37.89 vs -₹436.67/qtl). Across the 42,766 episodes in the 4 states with native NWP forecasts (`Exp 2b`), `MandiGuard` earns ₹485.18 vs ₹453.37/qtl (+₹31.82/qtl), which we treat strictly as exploratory subgroup context.
* **`H3` (vs Point ML `B3`): `SUPPORTED`** (-37.29 pp episode-level losses, 42.14% → 4.85%, p_Holm = 0.0008).
* **`H4` (Tool Efficiency vs `B4`): `SUPPORTED`** (-3.05 calls vs `0.75 × B4`, 44.4% fewer calls by design, p_Holm = 0.0008; tight-budget empirical payoff at `B = 6` is +₹104.54/qtl).
* **Grade-Explicit HP Apple 2026 (`Exp 3`):** On overall HP Apple mean profit, **`B2` beats uncalibrated 2024 `MandiGuard`** (₹1,150.83 vs ₹605.06/qtl) because our 2024 training data had no `Grade A` tags, widening the frozen conformal buffer on high-priced 2026 `Grade A` lots (5.39% dispatch). Still, `MandiGuard` cuts trap incidence from 94.14% (`B1`) to 13.24%, keeps worst-10% loss at -₹102.76/qtl (vs -₹8,487.24 under `B1` and -₹272.50 under `B2`), and lifts `Grade B` from -₹427.54 (`B1`) to +₹833.70/qtl.

### Dual-View Missing-Data & Open-Yard Sensitivity (`Exp 15`)
Examiners naturally ask: *"What if missing 3-day entries are simply unreported open yards, or how do policies compare when every candidate yard has observed prices?"* We evaluate **both** views:

1. **View 1 — Trap-Penalty Crossover Curve (`All_Shortlisted_Episodes`, N = 69,526):**
   * `1_Baseline_Div1.5x_Disc10pct` (1.5× return freight, 10% variety discount): `MandiGuard` ₹452.79 (48.66% disp, 9.97% LTR, -₹37.89 CVaR10) vs `B1` ₹350.01 (40.46% LTR, -₹1,062.66; `MG - B1` = +₹102.78), `B2` ₹446.66 (18.11% LTR, -₹436.67; +₹6.13), `B3` ₹330.85 (45.28% LTR, -₹1,097.80; +₹121.94).
   * `2_OneWayDiv_Div1.0x_Disc10pct`: `MandiGuard` ₹454.27 (9.97% LTR) vs `B1` ₹362.61 (+₹91.66), `B2` ₹449.33 (+₹4.94), `B3` ₹344.88 (+₹109.39).
   * `3_HalfDiv_Div0.5x_Disc5pct`: `MandiGuard` ₹456.00 (9.97% LTR) vs `B1` ₹413.57 (38.01% LTR; +₹42.43), `B2` ₹452.32 (+₹3.68), `B3` ₹409.88 (42.07% LTR; +₹46.12).
   * `4_ZeroDiv_Div0.0x_Disc0pct` *(crossover boundary: 0.0× return freight, 0% variety discount)*: `MandiGuard` ₹458.17 (6.09% LTR, -₹28.70 CVaR10) vs `B1` ₹468.17 (18.52% LTR, -₹877.41; `MG - B1` = -₹10.00), `B2` ₹456.09 (12.50% LTR, -₹70.80; +₹2.08), `B3` ₹479.09 (20.40% LTR, -₹851.02; -₹20.93).
   * `5_ZeroTrap_BreakEven0_Missing3d` *(missing 3d yields ₹0.00 break-even)*: `MandiGuard` ₹459.03 (5.96% LTR) vs `B1` ₹376.77 (8.33% LTR; +₹82.26), `B2` ₹457.24 (+₹1.79), `B3` ₹385.42 (4.93% LTR; +₹73.61).
   * *Summary of View 1:* `MandiGuard` leads `B1` through 0.5× freight / 5% discount (+₹42.43/qtl) and crosses below on mean only at the zero-cost 0.0× / 0% boundary (-₹10.00 vs `B1`, while keeping LTR at 6.09% vs 18.52% and tail loss at -₹28.70 vs -₹877.41).

2. **View 2 — Fair Matched Complete-Observation Cohorts *(identical episode set across ALL 4 policies — zero simulated trap rules, zero selection bias)*:**
   * `6_Fair_Matched_AllTopK_Observed_d0` (N = 10,162 identical episodes where every top-5 candidate has observed arrival-day `d0` price): `MandiGuard` earns **₹510.89/qtl** (47.31% disp, 6.82% LTR, -₹36.07 CVaR10)—beating `B1` (₹472.51, 74.78% disp, 19.84% LTR, -₹694.72; **+₹38.38**) and `B2` (₹469.99, 64.38% disp, 15.09% LTR, -₹94.70; **+₹40.91**). Point-ML `B3` earns +₹42.33/qtl higher mean (₹553.22, 73.47% disp) at 2.2× higher loss-trip rate (14.77%) and 10× deeper tail loss (-₹362.40).
   * `7_Fair_Matched_AllTopK_Observed_3d` (N = 16,849 identical episodes where every top-5 candidate trades exact variety in `d0..d2`): `MandiGuard` earns **₹592.53/qtl** (54.31% disp, 7.74% LTR, -₹48.25 CVaR10)—beating `B1` (₹581.06, 81.45% disp, 20.63% LTR, -₹829.21; **+₹11.47**) and `B2` (₹572.09, 70.97% disp, 15.81% LTR, -₹588.86; **+₹20.44**), while `B3` earns ₹670.38/qtl (79.16% disp; `MG - B3` = -₹77.85) at 15.02% LTR and -₹464.35 CVaR10.
   * *Why does `B3` lead on mean when all yards are open (`N = 10,162`), yet lag on the full market (`N = 69,526`)?* **Price forecasting works when yards are open; it fails on the full market because it lacks `T1` openness checks and `T4` safety cushions.**

---

## 6. Minimal Metrics & 10-Year Robustness (`Exp 10`, `Exp 10b`) + Stage-II `MandiGuard-CRC` (`Exp 16`–`17`)

To keep thesis presentation focused for any examiner, center every comparison around **4 plain-English metrics**:
1. **Mean Net Gain** (₹/qtl, and × 30 per smallholder truckload)
2. **Loss-Trip Rate** (% of dispatched trucks that lose money)
3. **Worst-10% Loss** (₹/qtl, average outcome on the worst 10% of dispatches)
4. **Live API Calls / Query** (external lookups per farmer request)

Observed across 2017–2026 historical AGMARKNET and NASA POWER records (661,192 matched episodes across 6 regimes):
* Across GST transition, Pre-COVID, COVID lockdowns, Inflation/Export curbs, the 2024 El-Niño Heatwave (+₹165.14/qtl over `B1`), and 2025–2026, `MandiGuard` holds Loss-Trip Rate to 8.78%–12.03% vs 39.18%–44.29% (`B1`), while 1-Yr training (2024: ₹452.79/qtl) captures 99.5% of 8-Yr training (2017–2024: ₹454.94/qtl).

### Stage-II (`[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]`): Fixing the Three Stage-I Bottlenecks (`Exp 16`–`17`)
* **Autopsy (`Exp 16`):** We discovered why Stage-I tied `B2` on overall mean (`H2`) and under-dispatched HP Apples: (1) `dropna(target_ret)` hid closed-yard arrivals (discarding `55.83%` of raw `Train_2024` corridors and understating 3-day Q20 downside risk by **1.94x** in train / **2.54x** in holdout); (2) pooled cushions gave `90.46%` coverage on calm `Q1` markets vs `67.80%` on noisy `Q4` markets; (3) splitting Apple into thin grades caused **77.82%** of holdout HP Apple refusals vs `B2` at `T1`, not `T4`.
* **Fix (`MandiGuard-CRC`, `Exp 17`, `Val_2025H1` `lambda* = 0.15`):** Trains dual 2024 tree heads directly on uncensored payoff `Y_full` ($\hat{\mu}, \hat{p}_{\text{loss}}$), ranks routes with $\hat{\mu} - 0.15 \cdot P_{\text{loc}} \cdot \hat{p}_{\text{loss}}$ (empirical CRC validation heuristic, zero holdout tuning and no Theorem 1 exchangeability claim), pre-sorts Step-0 candidates (`screen_spread > ₹100/qtl`) by `1.20x` Euclidean freight before selecting the top 5, and uses the `fresh0 | strict` rule at `T1` (admitting same-day exact-variety/grade quotes `age == 0` with `open_prob_14d >= 0.20` and `dow_open_rate >= 0.25`, alongside persistent corridors `open_prob_14d >= 0.50` and `dow_open_rate >= 0.35`). Result on holdout (`N=69,526`): **₹479.17/qtl** (`₹14,375.1` per truck; `+₹129.16` vs `B1`, **`+₹32.51` vs `B2`** `$p=0.0016$`, `+₹26.38` vs `MG_v1` `$p=0.0002$`), **`₹533.75/qtl`** on trap-free `N=10,162` open yards (`7.14%` LTR), and **`₹812.08/qtl`** (+34.2%) on HP Graded Apples.

---

## Appendix Illustrations (`Exp 11`–`Exp 13b` — Exploratory, Not Main Contributions)

*Scope note: The items below are optional Appendix illustrations evaluated outside the pre-registered core suite rather than main thesis contributions.*

* **Alternative Predictors & NeurIPS'21 Adaptive Conformal (`Exp 11`, Appendix Illustration):** `Direct_Quantile_GBDT_Q20` reaches ₹459.02/qtl (9.40% loss rate) on 6-state holdout, `Deep_MLP_Conformal` leads HP Apple 2026 mean (₹615.34/qtl), and `MandiGuard_ACI` dynamically lowers HP Apple worst-10% tail loss by 27.6% (-₹102.76 → -₹74.42/qtl).
* **`MandiGuard-ZeroCloud` & Satisficing Edge-AI (`Exp 12`, Appendix Illustration):** Keeping static OSRM road tables and CPU scoring on-device (`ZeroCloud_Full`) reaches ₹455.33/qtl at 5.53 live calls (₹2,764 per 10k queries vs ₹7,868 for `B4` under illustrative ₹0.05/call pricing). Stopping search once a route clears a validation-frozen ₹250/qtl hurdle (`ZeroCloud_Satisficing`) drops calls to 3.84 calls/query (₹1,922 per 10k queries, 75.6% lower API cost than `B4`).
* **FPO 90-qtl Shared Truck Pooling, Split-Lot & Spoilage Clock (`Exp 13`/`13b`, Appendix Illustration):** Three 30-qtl farmers pooling a 90-qtl FPO truck (illustrative 0.70× freight factor) earn ₹477.28/qtl (+₹24.49/qtl over 30-qtl solo, +₹67.75/qtl over marginal 10-qtl farmers); splitting 50/50 across top-2 yards reduces closed traps from 16.17% to 9.85%; and the Biological Spoilage Clock warns extension staff when Tomato safe transit time compresses from 110.8h (20°C) to 24.1h (42°C).
