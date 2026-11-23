# When Online Mandi Prices Mislead: A Leak-Free Replay and Risk-Aware Triage Rules on Public Indian Wholesale Data

**Aditya Sharma** (M.Tech Thesis Research, supervised by **Dr. Sonia**) — Shoolini University, Solan, Himachal Pradesh, India

## Abstract

Whether spreads on India's AGMARKNET portal survive transit hinges on unobserved arrival-day blanks. Under sequential closed-yard settlement (`div = 1.5`), chasing lagged spreads above `₹100/qtl` across `171` zero-lookahead markets (`N = 57,634` test episodes, `June 2025–April 2026`) loses money on **`45.07%`** of dispatches (`ES10 −₹642.15/qtl`); under open-yard Missing-At-Random (MAR) counterfactuals, road dispatch (`B2_age_matched`) earns `+₹97.01/qtl` higher mean than zero-tuned-parameter triage (`Safe_EV_Sunk_m0`).

Claiming no methodological novelty, we benchmark two tuning-free 6 a.m. triage heuristics (`Safe_EV_Sunk_m0`: $p_{\text{dow}} G_{\text{1SD}} > F_{\text{road}}$; `Safe_EV_Phys_m0`: `1.5F`) and calculator rule `RT_2F_Min_m0` ($p_{\min} G > 2F_{\text{road}}$) under a `<= t - 1` firewall. Across locked `PREREG_A18` tests (`R = 2,000`, `p_holm_2s = 0.0040`), `Safe_EV_Sunk_m0` (`63.23%` dispatch) attains `₹452.74/qtl` mean (`+₹33.12`), `14.88%` losses (`−11.56 pp`), **`ES10 −₹345.53/qtl`** (`+₹179.24`), and **`cond_ES10 −₹447.48/qtl`** (`+₹180.89`), outperforming `B2` and fitted `<= t - 1` ML/OR baselines on `cond_ES10`. `Safe_EV_Sunk_m0` gains `ES10` across all six states (`Holm11`) and five crop slices, though HP (`B = 12`, `p_stud = 0.186`, `cond_ES10 p = 0.124`) and Apple (`p_stud = 0.058`, `cond_ES10 p = 0.055`) turn borderline/non-significant, and Mean CIs cross zero in five slices (`RT_2F_Min_m0` keeps positive Means yet fails `cond_ES10` under `t - 2` lag). Mean gains vanish under free turn-back (`p = 0.220–0.256`), reverse under 3-day hindsight and worst-case Manski bounds, and erode under herding (`max = 27`). Across untouched `2018–2023` data (`166` markets, `N = 383,952`), `Safe_EV_Sunk_m0` gains `+₹169.27` `ES10` (`+₹155.08` `cond_ES10`, `p = 0.001`), with `2020`/`2023` Means non-significant; rules filter 6 a.m. alerts ahead of trader calls.

---

## 1. Three Research Questions and Honest Methodological Scope

Indian wholesale agricultural markets (*mandis*) publish daily minimum, modal, and maximum prices by variety on AGMARKNET. While digital price dissemination reduces spoilage when execution is smooth [jensen2007digital, goyal2010information], and targeted market-information services can raise realized farmer prices under symmetric bargaining [courtois2015farmer], empirical trials across rural India show that portal quotes frequently fail to deliver arbitrage when transport, fees, volatility, and bargaining frictions bind [fafchamps2012sms, mitra2018asymmetric, chatterjee2023market]. Four operational mechanisms drive our retrospective audit:
1. **Reporting Latency (`<= t - 1` or `<= t - 2`):** At 6 a.m. decision day $t$, same-day auctions have not cleared, and thinner yards publish `1–7` days late (and even slower under multi-day portal lag).
2. **Transfer Frictions and Deterioration:** Road freight, single-lane terrain, out-of-district market friction, and ambient transit decay erode nominal spreads [baulch1997transfer, nabcons2022phl].
3. **Price Volatility and Silent Arrival Boards:** Volatile lagged modal prices (`dest_price_cv_28d`) revert on arrival day $t + \tau$, while blank arrival rows (`settle_any_min_dw = NaN`) trigger sequential turn-back or fallback losses [deka2026missing].
4. **Role as an Upstream 6 a.m. Alert Filter:** Smallholders routinely phone a destination *arhtiya* (commission agent) for 30 seconds before dispatch [jensen2007digital, ziegler2019fresh]. These heuristics screen out fragile portal alerts *before* calling traders and never replace live confirmation.

We examine six Indian states (Gujarat, Himachal Pradesh, Karnataka, Madhya Pradesh, Maharashtra, Uttar Pradesh) and four crops (Onion, Potato, Tomato, Apple) through three questions:
- **RQ1 (Screen-Chasing Risk & Settlement Realism):** Under a `<= t - 1` causal firewall and sequential arrival settlement, how often do lagged portal spreads (`> ₹100/qtl`) lose money, and how strongly do 3-day hindsight and day-$t$ origin conditioning distort apparent risk?
- **RQ2 (Lower-Bound Triage Heuristics vs Baselines, Hard Gates & ML/OR Models):** On equal Top-5 menus (`age 1..3`), how do two fixed, **zero-validation-tuned-parameter** lower-bound triage heuristics (`Safe_EV_Sunk_m0`, `Safe_EV_Phys_m0`) and calculator rule `RT_2F_Min_m0` compare against tuned road dispatch (`B2_age_matched`), ML-stripped hard gates (`MG_T1_T2`), reliability-weighted `RR_Abstain`, and fitted `<= t - 1` ML/OR policies (Ridge, HistGradientBoosting, Mean-Variance) on both unconditional `ES10` and dispatched conditional `cond_ES10`?
- **RQ3 (Partial Identification, Structural Stress Tests & Multi-Year Robustness):** How sensitive are conclusions to true coupled/decoupled Manski bounds [manski1990bounds, rubin1976inference], `<= t - 2` upload latency, Schedule #7 biological decay, stochastic conditional MAR (`Stoch_CondMAR`), SUTVA crowding, exact-geocode subsets, small-cluster studentized inference (`B = 12` blocks), clean `166`-market `2018–2023` pre-period data (`N = 383,952`) with NASA POWER climate [sparks2018nasapower], and Himachal graded apples?

### Explicit Protocol Chronology (`Stage I -> A10 -> A18 -> Final Audit`)
1. **Stage I Legacy Baseline (`e421d15`):** An unlagged gradient-boosted tree system (`HistGradientBoostingRegressor`) with ERA5 weather and conformal LCB proved **inconclusive against road dispatch `B2`** on confirmatory `H2` (`+₹6.13/qtl`, 95% CI `[−₹17.02, +₹25.02]`, Holm `p = 0.2699`) and failed on HP graded apples.
2. **Audit Remediation (`A10`, Commit `87a0b62`):** Removed day-$t$ leaks and `98.64%` ERA5-identical forecast leakage (`66,222 / 67,135`), fixed APMC fee bases (`M9`), fixed fractional `ES10`, and tested `RR_Abstain_matched` (which hit grid ceiling `kappa* = 5.0`, averaged `rep28` over Sunday closures, and shifted cutoff to `−₹328.99` at `kappa = 20.0` in `a10_summary.json`).
3. **Closed-Form Simplification (`PREREG_A18.md`, `4cbb02d`) & Comprehensive 16-Agent Final Audit:** Committed three tuning-free rules before running `eval_a18.py`, replaced `178` lookahead markets with strict `2024`-active `171` markets (`N_test = 57,634`), evaluated a clean `166`-market `2018–2023` non-lookahead intersection (`N = 383,952`, plus `115`-market `2017`-active `N = 325,993`), and added Phase 6 causal/economic stress tests (`v7_exp1..5`). Because `2025-06-01..2026-04-08` and HP apples were exposed prior to `A18`, **all 2025–2026 results remain labeled exploratory**.

---

## 2. Identification Architecture, Stylized Calibration, and Causal Firewall

### 2.1 Epistemic Layers: Observed vs Estimated vs Stylized vs Unidentified

| Epistemic Layer | Exact Variables / Mechanisms | Source & Explicit Caveats |
|---|---|---|
| **Observed (Public Archives)** | Daily AGMARKNET `Min/Modal/Max_Price`, variety/grade, arrival reporting; OSRM `road_km` (`15.19–499.43`); realized ERA5 `Tmax, RH, rain_mm` & NASA POWER `2017–2023` | AGMARKNET OGD via HuggingFace mirror (`99.42%` [`171/172`] Tier-1 XML parity; `100%` HP); OSRM/OSM ODbL [luxen2011osrm]; ERA5 [hersbach2020era5]; NASA POWER [sparks2018nasapower] |
| **Estimated (`<= t - 1`)** | 8w same-weekday Laplace `p_dow`, `rep28`, `rep14`, `cv28`; two-way cluster bootstrap (`R = 2,000`), CGM / studentized `t` / Webb6 tests | Strictly `date < t`; inference uses state-prefixed `State\|Market` clusters across fortnights |
| **Stylized / Survey-Anchored** | `F_road = 35 + 0.45 * h_s * km` (`h_s = 1.45` HP); stylized `{0.5, 1.0, 1.5}%` seller-fee tiers; cumulative NABCONS `{3.25, 1.96, 1.64, 0.86}%` scaled as 24h benchmark alongside USDA Schedule #7; `₹25` wait; `30 qtl` load | NITI/RMI `₹0.258/qtl-km` *national avg* heavy truck [nitiaayog2021freight]; GoHP `91.59%` single-lane roads [hpeconsurvey2026]; GoI PIB `relid=154554` [pib154554apmc] (qualitative F&V deregulation; omits UP; statutory APMC fees usually buyer-paid); NABCONS [nabcons2022phl] & CIPHET [jha2015ciphet]; NSS 587 [nss77report587] (holdings/income benchmark, not truckload survey); RBI WP [rbi2024top] |
| **Unidentified (Bounded)** | Whether blank arrival row (`no_comm_divert`) is a closed/inactive yard or unrecorded open auction; unmodeled SUTVA crowd price impact | Coupled/decoupled Manski bounds [manski1990bounds, horowitz2000nonparametric, rubin1976inference], stochastic Cond-MAR, blind-wait causal clocks, exact break-even (`v7_exp2..3`), crowding stress (`v7_exp5`) |
| **Unobserved Out-of-Scope** | Negotiated truck bills, *arhtiya* cash commission (`0–6%` swept), live calls, weighment loss, smallholder credit ties | Disclosed in Section 6; prospective field trial required (`Gate J`) [levi2025improving] |

### 2.2 Tracked Official Data Provenance and Transparency
Six tracked files regenerate all outputs offline cleanly without live network calls:
1. **`agmarknet_6state_top_apple_2024_2026.parquet` (`260,043` raw, `178` core markets):** Extracted from the AGMARKNET HuggingFace mirror (`1 Jan 2024–13 Apr 2026`). Legacy `Exp 14` XML parity is `99.42%` (`171/172`) on Tier-1 vs `100.0%` on HP Apple. Retaining `369` extreme outlier rows (`<₹100` or non-Apple `>₹15,000`) and pooling `90.3%` grade strings (causing a `25.62%` variety-grade mismatch on cross-grade pairs) in baseline is audited directly in `v7_exp5` (`OutlierClean369` & `GradeExplicit_6State`). Strict `2024`-only selection (`>= 80` days in 2024, `<= 30`/state) drops 7 post-2024 lookahead yards and `1` OSRM-distant yard (`>500 km`), yielding **`171` zero-lookahead markets** (`257,576` raw rows).
2. **`agmarknet_6state_decade_2017_2026.parquet` (`623,363` raw, `2017–2023`):** To stay offline inside the `2024`-active OSRM Top-30 corridor frame while removing all 7 post-2024 lookahead yards from the legacy `173`-market extract (`N = 389,357`), we intersect with `171` to form a **clean `166`-market non-lookahead pre-period panel (`N = 383,952`)** plus a **`115`-market `2017`-active cohort (`N = 325,993`)**, matched against tracked `nasa_power_climate_2017_2023.parquet` (`0.5°` grid) [sparks2018nasapower].
3. **`hp_apple_daily_2025_2026.csv` & `osrm_corridor_matrix.parquet`:** `4,427` grade-explicit HP apple rows (`42` yards) and `8,147` OSRM road corridors (`15.19–499.43 km`; `59.50%` exact-geocode test rows; `19,362` all-5 exact-geocode episodes; no `+4h` buffer stored in `truck_hours`).
4. **`state_apmc_and_loss_parameters.csv` & `mandi_weather_2024_2026.parquet`:** Because statutory APMC fees are predominantly buyer-paid and PIB `154554` omits UP, our `{0.5%, 1.0%, 1.5%}` seller tiers represent **stylized market-friction tiers** (`0%–6%` stress-tested). Weather variables are **excluded completely from all decisions** (`98.64%` ERA5 forecast leak fixed); arrival-day realized ERA5 (`0.1°`, clipped to `[5, 48]°C` and `[20, 100]%` RH) enters settlement only.

### 2.3 Reconciled Cleaning Funnel and Ex-Post Conditioning
Strict deduplication (`Median` modal, `Min` floor) collapses `257,576` raw `171`-market rows (`−759` out-of-range -> `256,817`; `−2,284` duplicate excess across `1,481` conflicting modal groups -> `254,533`; `−8,695` variant merges) to `245,838` canonical rows (`317,985` Top-5 rows across `35,870` val + `57,634` test episodes). Dropping `939` spillover episodes from validation (`arrival_date + 2d > 2025-05-31`, `v7_exp4`) leaves `B2` threshold untouched (`₹200.00`). Conditioning baseline episodes on day-$t$ local uploads (`settle_local_price_d0`) omits `28,420` missing-origin episodes from `86,054` unconditional test episodes; we audit the complete **`86,054`-episode unconditional panel** both baseline (`d0_or_lag`, `outside_origin_lag`) and with symmetric origin-blackout holding costs (`v7_exp3`).

### 2.4 Causal Timing Firewall
Every feature in shortlisting/scoring satisfies `dest_quote_date < t` and `origin_quote_date < t` (extending cleanly to `<= t - 2` in `v7_exp1`). Counterfactual tests in `pytest` (`test_timing_and_leakage_r3.py`) inject `₹99,999/qtl` spikes and drop active yards for all days `>= t*` and assert bit-for-bit invariance of menus and scores for `t <= t*`.

---

## 3. Payoff Physics, Sequential Settlement, and Decision Rules

### 3.1 Physical Freight, Stylized Fee Tiers (`M9`), and Biological Decay
For corridor $c = (o \to d)$ in state $s$ and commodity $k$, freight is $F_{\text{road}}(c) = 35.0 + 0.45 \cdot h_s \cdot \text{road\_km}(c)$ (`h_s = 1.45` HP, `1.0` elsewhere). Ambient `20°C / 65%` RH reference spoilage over transit `truck_hours` plus wait days $w \in \{0, 1, 2\}$ [kader2002postharvest, gross2016usda66] uses:
$$s(k, w) = \min\!\left(0.55,\; b_k \cdot \frac{\max(1,\; \text{truck\_hours} + 24 w)}{24}\right)$$
with stylized daily rates $b_k \in \{0.0325 \text{ Tomato}, 0.0196 \text{ Onion}, 0.0164 \text{ Apple}, 0.0086 \text{ Potato}\}$ calibrated from NABCONS cumulative market-stage shares [nabcons2022phl] — contrasted directly in `v7_exp2` against biological Schedule #7 ($24\tau_{\text{days}}$ from harvest/loading + USDA-66 $Q_{10} = 2^{(T_{\max}-20)/10}$). Stylized destination fees $\tau_{\text{fee}} \in \{0, 0.005, 0.010, 0.015\}$ (`0` intra-district or unsold return) apply strictly on post-decay destination gross auction sales.

<!-- WORKED_EXAMPLE_START -->
> **Worked Example 1 (Physical Freight, Decay & Post-Decay Fee):** On an out-of-district MP Tomato trip (`fee = 1.5%`, `km = 200`, `truck_hours = 6`, arrival sale `₹2,000` vs local `₹1,500`): $F = 35 + 0.45(200) = ₹125.00/\text{qtl}$; $s(0) = 0.0325(6/24) = 0.008125$; post-decay gross $= 2000(0.991875) = ₹1,983.75$; net after 1.5% fee $= 1983.75(0.985) = ₹1,953.99$; net gain $= 1953.99 - 125 - 1500 = +₹328.99/\text{qtl}$.
<!-- WORKED_EXAMPLE_END -->

### 3.2 Sequential Non-Anticipative Settlement vs Hindsight Lookahead
Starting at $w = 0$ on arrival $t + \tau$ (`tau_days in 1..3`): if exact variety trades (`Modal_Price` present), sell at $P_{\text{sale}}(1 - s(k, w))(1 - \tau_{\text{fee}}) - F - 25w - P_{\text{loc}, d0}$; if missing while another variety trades (`settle_any_min_dw > 0`), wait 1 day (`₹25` + decay) for $w < 2$ (selling at `0.90 * settle_any_min_d2` at $w = 2$); if zero commodity trade prints on day $w$, divert home: $\Delta\text{Net}_{\text{divert}}(w) = -\text{div}\cdot F - P_{\text{loc}, d0} s(k, w) - 25w$ (`div = 1.5`, zero fee). Blindly waiting 1–2 days regardless of empty day-0 boards is tested in `Causal_BlindWait` (`v7_exp2`).

<!-- WORKED_EXAMPLE_START -->
> **Worked Example 2 (Sequential vs 3-Day Hindsight):** If destination Tomato is absent on arrival day 0 yet trades at `₹2,000` on day +1, sequential settlement returns at $w = 0$ ($\Delta\text{Net} = -1.5(125) - 1500(0.008125) = -₹199.69$), whereas 3-day hindsight records $+₹239.97$ — a ₹439.66/qtl distortion.
<!-- WORKED_EXAMPLE_END -->

### 3.3 Equal-Menu Baselines, Heuristics, and Zero-Tuned-Parameter Lower-Bound Rules
On identical Top-5 candidates (`lag_spread > 100`, max 1 pick, abstention `0`), all equal-age (`1..3d`) comparators match `val_171` dispatch (`70.43%`): `B1_lagged_screen` (1 free param, age `1..7`, `100%`), `B2_age_matched` ($G - F > ₹200$, `1` param), `B_simple_activity_matched` (`rep14 >= 0.50`, `₹168.46`, `2` params), `MG_T1_T2_matched` (ML-stripped `rep14 >= 0.50 & dow8 >= 0.35`, `₹133.03`, `4` params; distinct from intact conformal `MG_T1..T4` in `v7_exp4`), and `RR_Abstain_matched` (`κ*=5.0`, `m*=₹5.40`, `2` params).

Locked in `PREREG_A18.md` (`S > 0`), we examine three **lower-bound triage heuristics with zero validation-tuned parameters** (built from 7 fixed structural choices: `age 1..3`, Laplace $p_{\text{dow}} = (k+1)/10$, `28d` window, $z=1.0$ `cv28` haircut, `0.05` `cnt28<2` fallback [checked against `cnt28<5`], sunk $F$/$2F$/$1.5F$, threshold `0`):
- **`Safe_EV_Sunk_m0` (Product Score):** Using $G_{\text{1SD}}(c, t) = P_{\text{dest,lag}}(1 - \text{cv}_{28})(1 - \tau_{\text{fee}}) - P_{\text{orig,lag}}$, select $\arg\max_{c} S_{\text{Safe-EV}}(c,t) = p_{\text{dow}} G_{\text{1SD}} - F_{\text{road}} > 0$ (whose acceptance gate $S > 0 \iff G_{\text{1SD}}/F_{\text{road}} > 1/p_{\text{dow}}$; the argmax objective is non-invariant under ratio transformation, causing `5,113` candidate switches [`14.03%`] in `v7_exp4`). Explicitly, $S_{\text{Safe-EV}}$ is a conservative lower-bound score assuming `0` return payoff on failure (not a literal expected value).
- **`Safe_EV_Phys_m0`:** $p_{\text{dow}}(G_{\text{1SD}} - F) - (1 - p_{\text{dow}}) 1.5 F > 0$ (explicit return cost lower bound).
- **`RT_2F_Min_m0` (`0` params, NO `cv28`, NO `spoil`):** Using plain $G$ and $p_{\min} = \min(\text{rep}_{28}, p_{\text{dow}})$, dispatch if $p_{\min} G - 2F > 0$.

<!-- WORKED_EXAMPLE_START -->
> **Worked Example 3 (Pocket Arithmetic):** On MP Tomato ($G = +₹470$, `cv28 = 0.15`, $G_{\text{1SD}} = +₹174.50$, $F = ₹125$): steady yard (`dow8 = 0.90`, `p_min = 0.85`) yields `Safe_EV = +₹32.05 > 0` and `RT_2F = +₹149.50 > 0` (**DISPATCH**); Sunday yard (`dow8 = 0.20`, `p_min = 0.20`) gets `B2 = +₹345` blindly yet yields `Safe_EV = −₹90.10` and `RT_2F = −₹156.00` (**STAY HOME**).
<!-- WORKED_EXAMPLE_END -->

### 3.4 Fractional `ES10`, Conditional `cond_ES10`, and Small-Cluster Inference
Following coherent expected shortfall [rockafellar2000cvar], we report both **unconditional `ES10`** (including `0` on abstention — rewarding selectivity mechanically via zero-padding) and **conditional `cond_ES10`** evaluated solely across dispatched trips (equalizing risk on committed capital) with fractional interpolation $m = 0.10n = k + f$:
$$\text{ES10}(x) = \frac{1}{m}\left(\sum_{i=1}^{k} x_{(i)} + f \cdot x_{(k+1)}\right)$$

<!-- WORKED_EXAMPLE_START -->
> **Worked Example 4 (Fractional `ES10`):** On $\{1, 2, \dots, 11\}$, $m = 1.1$ ($k = 1, f = 0.1$), giving $(1 + 0.1 \times 2)/1.1 \approx 1.09$.
<!-- WORKED_EXAMPLE_END -->

Locked confirmatory inference evaluates the `PREREG_A18.md` 4-test family at exact `R = 2,000` paired two-way cluster bootstraps [phipson2010permutation, holm1979simple] (`166` `State|Market` × `23` fortnights), supplemented by Cameron–Gelbach–Miller (`CGM`) `G*` t-tests, studentized `t` bootstraps, Webb 6-point wild tests (`B = 12` `4w` blocks & HP `B = 12`), and joint `val+test` threshold propagation (`v7_exp5`).

---

## 4. Results

### 4.1 RQ1 & RQ2: Primary `171`-Market Benchmark (`N = 57,634`) and Conditional Tail (`cond_ES10`)

Across `N = 57,634` episodes (`v7_main_171.csv`), blind spread-chasing (`B1`) loses on **`45.07%`** (`mean ₹384.61`, `ES10 −₹642.15`), with `69.78%` (`40,217`) `d0` sales, `0.49%` (`284`) waits, `1.06%` (`609`) distress fallbacks, and **`28.67%`** (`16,524`) zero-commodity returns; 3-day hindsight drops `B1` losses artificially to `31.27%` (`mean ₹523.68`). Table 3 compares all rules on both unconditional `ES10` and dispatched `cond_ES10`.

| Policy (`N = 57,634`, `171` Mkts) | Params | Disp (%) | Mean (₹/qtl) | EpL (%) | `ES10` (₹/qtl) | `cond_ES10` (₹/qtl) | LGL | Mean km |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **`B1_lagged_screen`** (`1..7d`) | 1 | `100.00%` | `₹384.61` | `45.07%` | `−₹642.15` | `−₹642.15` | `−₹271.11` | `225.09` |
| **`B2_age_matched`** (`1..3d`, `₹200`) | 1 | `71.73%` | `₹419.62` | `26.43%` | `−₹524.78` | `−₹628.37` | `−₹294.33` | `207.06` |
| **`B_simple_activity_matched`** | 2 | `70.46%` | `₹426.29` | `23.30%` | `−₹505.84` | `−₹614.38` | `−₹299.27` | `207.36` |
| **`MG_T1_T2_matched`** *(ML-stripped)* | 4 | `69.16%` | `₹454.07` | `18.35%` | `−₹508.72` | `−₹638.55` | `−₹330.98` | `204.49` |
| **`RR_Abstain_matched`** (`k*=5.0`) | 2 | `68.75%` | `₹461.41` | `17.07%` | `−₹459.46` | `−₹584.66` | `−₹308.82` | `183.15` |
| **`Safe_EV_Sunk_m0`** *(0-param)* | **0** | **`63.23%`** | **`₹452.74`** | **`14.88%`** | **`−₹345.53`** | **`−₹447.48`** | **`−₹261.53`** | `196.56` |
| **`Safe_EV_Sunk_matched`** | 1 | `70.74%` | `₹457.08` | `18.37%` | `−₹367.79` | **`−₹443.54`** | **`−₹244.85`** | `194.81` |
| **`Safe_EV_Phys_m0`** (`1.5F`, `0` p.) | **0** | `60.84%` | `₹449.52` | **`13.70%`** | **`−₹334.80`** | **`−₹447.33`** | `−₹265.89` | `194.89` |
| **`RT_2F_Min_m0`** *(NO `cv28`)* | **0** | `64.79%` | **`₹463.98`** | `16.21%` | `−₹464.84` | `−₹618.35` | `−₹323.98` | `177.52` |
| **`EV_RT_Min_m0`** | **0** | `77.17%` | `₹470.44` | `20.38%` | `−₹512.47` | `−₹602.97` | `−₹307.16` | `191.18` |

Key findings from Tables 3–5 and `v7_exp4`:
1. **`PREREG_A18` Locked Family (`R = 2,000`, Table 4):** All 4 locked contrasts pass `p_holm_2s_prereg4 = 0.0040` across all 3 clusterings (`H_A18_1` `ES10` `+₹179.24`; `H_A18_2` `+₹91.67` matched vs `RR`; `H_A18_3` EpLoss `−11.56 pp`; `H_A18_4` `RT_2F` Mean `+₹44.36`). Under CGM `G*` and studentized checks (`v7_exp_summary.json`), `H_A18_1/3/4` remain significant (`p <= 0.0096`), whereas `H_A18_2` is borderline under `b2dest` (`p_cgm_gstar = 0.0659`, `p_stud = 0.0575`; joint `val+test` CI `[+₹34.81, +₹158.11]`, `p_null = 0.0030`) and `4w` (`B = 12`) Mean of `Safe_EV_Sunk_m0` shows `p_cgm_gstar = 0.0818` NS (`p_stud = 0.0050`, `p_webb6 = 0.0070`).
2. **Conditional Tail (`cond_ES10`) Exposes `RT_2F` & `Safe_EV_Phys` Limits:** `Safe_EV_Sunk_m0` cuts **dispatched `cond_ES10`** from `−₹628.37` (`B2`) to **`−₹447.48` (`+₹180.89`)** — even at matched `63.23%` dispatch (`B2_test_matched` `cond_ES10 −₹644.95`, diff `+₹197.47`) — and cuts `cv28` static 10% (`−₹586.30`) by `+₹138.82`. By contrast, **`Safe_EV_Phys_m0` (`−₹447.33`) beats `Safe_EV_Sunk_m0` (`−₹447.48`) by only `+₹0.15/qtl` on `cond_ES10`**, showing its `ES10` gap (`+₹10.73`) comes from abstaining more (`60.84%`). Crucially, **Class-8 `RT_2F_Min_m0` collapses on conditional tail protection (`cond_ES10 −₹618.35` vs `B2 −₹628.37`)**, turning negative or NS across Apple (`−₹163.18`), HP (`−₹54.63`), MH (`−₹61.44`), GJ (`p = 0.580`), KA (`p = 0.104`), MP (`p = 0.115`), Tomato (`p = 0.078`), and `<= t - 2` latency (`p = 0.981`!).
3. **Clean `<= t - 1` ML/OR Pareto & Intact `MG_T1..T4` (`v7_exp4`):** Trained strictly on `val_purged` (`−939` spillover episodes), linear `Ridge` (`₹470.75` Mean, `−₹466.19` `ES10`, `−₹530.30` `cond_ES10`), unconstrained `HGBR_EV_TV_age13` (`₹464.23` / `−₹459.68` / `−₹523.53`), Vargas-style Mean–Variance [vargas2026mean] (`OR_Vargas_MeanVar_g0002`: `₹432.39` / `−₹426.41` / `−₹496.76`), `HGBR_RiskAverse_L500` (`₹445.79` / `−₹359.12` / `−₹512.43`), and intact conformal `MG_T1_T2_T3_T4_Intact_matched` (`q80=162.5`, `₹448.54` / `−₹423.09` / `−₹531.66`) [romano2019conformalized, lei2018distribution, gibbs2021adaptive] all beat hard gates `MG_T1_T2`, while **`Safe_EV_Sunk_m0` dominates every learned ML/OR policy on `cond_ES10` (`−₹447.48`) with zero fitted weights**, echoing out-of-sample simplicity findings [demiguel2009optimal, gigerenzer2011heuristic]. Formula checks confirm `cv28 == 0` fix (`5,274` rows, `Mean ₹452.10`, `ES10 −₹345.52`) and unrestricted `top_k = None` (`307k` rows, `Mean ₹454.37`, `ES10 −₹344.47`) invariance.

| Contrast (`N = 57,634`, Locked `R = 2,000`, `v7_bootstrap_prereg_2000.csv`) | Est. | `origin_x_2week` (`166×23`) | `b2dest_or_origin` (`166×23`) | `policy_dest_or_origin` (`165–166×23`) |
|---|---:|---|---|---|
| **`H_A18_1`:** `ES10(Safe_EV_Sunk_m0 − B2)` (`p_holm_2s`) | **+₹179.24** | `[+121.99, +251.09]` (**0.0040**) | `[+103.83, +296.01]` (**0.0040**) | `[+121.87, +267.10]` (**0.0040**) |
| **`H_A18_2`:** `ES10(Safe_EV_matched − RR_matched)` (`p_holm_2s`) | **+₹91.67** | `[+39.11, +161.52]` (**0.0040**) | `[+25.45, +203.65]` (**0.0040**) | `[+36.37, +175.47]` (**0.0040**) |
| **`H_A18_3`:** `EpLoss(Safe_EV_Sunk_m0 − B2)` (`p_holm_2s`) | **−11.56 pp** | `[−13.30, −9.96]` (**0.0040**) | `[−14.11, −8.95]` (**0.0040**) | `[−14.34, −9.26]` (**0.0040**) |
| **`H_A18_4`:** `Mean(RT_2F_Min_m0 − B2)` (`p_holm_2s`) | **+₹44.36** | `[+31.22, +59.30]` (**0.0040**) | `[+23.31, +68.04]` (**0.0040**) | `[+25.81, +66.20]` (**0.0040**) |
| `SEC_1`: `Mean(Safe_EV_Sunk_m0 − B2)` (`p_2s`) | +₹33.12 | `[+13.59, +54.50]` (`0.0040`) | `[+1.42, +66.87]` (`0.0430`) | `[+6.60, +63.90]` (`0.0110`) |
| `SEC_2`: `ES10(Safe_EV_Phys_m0 − B2)` (`p_2s`) | +₹189.97 | `[+132.14, +262.24]` (`0.0010`) | `[+114.41, +306.03]` (`0.0010`) | `[+131.77, +278.20]` (`0.0010`) |
| `SEC_3`: `ES10(MG_T1_T2_matched − B2)` *(NS)* | +₹16.05 | `[−14.80, +43.23]` (`0.2409`) | `[−21.56, +50.25]` (`0.3428`) | `[−21.43, +48.37]` (`0.3258`) |

| Ablation & Clean `<= t - 1` ML/OR Pareto (`N = 57,634`, `v7_ablations` & `v7_exp4`) | Disp (%) | Mean (₹/qtl) | EpL (%) | `ES10` (₹/qtl) | `cond_ES10` (₹/qtl) |
|---|---:|---:|---:|---:|---:|
| `B2_test_matched_to_SafeM0` (`th=₹295.00`) | `63.23%` | `₹413.34` | `23.12%` | `−₹501.23` | `−₹644.95` |
| `Safe_EV_fixed10pct_m0` (static `10%`) | `63.50%` | `₹453.62` | `16.74%` | `−₹444.73` | `−₹586.30` |
| `Safe_EV_euclid120_m0` (`1.20 * euclid_km`) | `64.23%` | `₹452.35` | `15.43%` | `−₹355.30` | `−₹454.35` |
| `ML_Ridge_EV_m0` (`Ridge > 0`) | `79.81%` | `₹470.75` | `22.37%` | `−₹466.19` | `−₹530.30` |
| `ML_HGBR_EV_TV_age13_m0` (`<= t - 1` HGBR) | `79.61%` | `₹464.23` | `21.91%` | `−₹459.68` | `−₹523.53` |
| `ML_HGBR_RiskAverse_L500` (`EV - 500*P(loss)`) | `56.75%` | `₹445.79` | `12.16%` | `−₹359.12` | `−₹512.43` |
| `OR_Vargas_MeanVar_g0002` (`Mean - 0.0002*Var`) | `76.16%` | `₹432.39` | `20.30%` | `−₹426.41` | `−₹496.76` |
| `MG_T1_T2_T3_T4_Intact_matched` (`q80=162.5`) | `68.42%` | `₹448.54` | `16.33%` | `−₹423.09` | `−₹531.66` |
| **`Safe_EV_Sunk_m0`** *(0 tuned params ref.)* | **`63.23%`** | **`₹452.74`** | **`14.88%`** | **`−₹345.53`** | **`−₹447.48`** |

![Risk-coverage curves with 95% cluster confidence bands across B2_age_matched, hard-gated MG_T1_T2, RR_Abstain, and zero-parameter Safe_EV_Sunk alongside B1 and RT_2F_Min](../figures/rev_fig1_risk_coverage_ci.png)

![Fair ablations against Safe_EV_Sunk_m0 and RT_2F_Min_m0 on the primary 171-market panel (left) and worst-10% ES10 comparison across Onion, Potato, Tomato, NonApple, and Apple subsets (right)](../figures/rev_fig2_ablations_and_crops.png)

### 4.2 RQ3: Identification Bounds, Latency, Biology, Subgroups, and Crowding Stress
1. **Prominent Failure / Reversal Regimes (`v7_missing_tests_171.csv`, `v7_exp3`):** Under **free turn-back** (`div_0.0_spoil_only` / `exact_zero_divert_payoff_0`), `Safe_EV_Sunk_m0` Mean is non-significant (`+₹12.03` `p=0.220` / `+₹11.21` `p=0.256`), though `ES10` retains `+₹174.40`/`+₹169.82` (`p=0.001`); under **Open-MAR** (`open_yard_MAR_lagged_price`), **`B2` leads Mean by `+₹97.01/qtl`** (`₹698.17` vs `₹601.16`, `p=0.001`) while `Safe_EV` retains `+₹189.97` `ES10` (`−₹193.47` vs `−₹383.44`); under **`3`-day hindsight**, **`B2` leads Mean** (`₹549.81` vs `Safe_EV ₹533.14` `p=0.163` NS, `RT_2F ₹534.11` `p=0.025`). Under true **worst-case Manski bounds (`Manski_Supp1..3`, `v7_exp3`)**, coupled worst-case Mean favors `B2` (`−₹124.95`, `−₹199.51`, `−₹325.40`), whereas under cross-crop blackout MNAR (`b2_blackout=8,933` vs `other=2,517`) `Safe_EV` gains `+₹9.88` Mean and `+₹188.56` `ES10`. On **`PreChoice_AllCandidates_ExactD0`** (`N = 24,654` all-open menus), `B2` leads Mean (`₹478.23` vs `₹457.48`) while `Safe_EV` gains `+₹260.20` `ES10` (`−₹184.60` vs `−₹444.80`); on **`Unconditional_86054_SymClosedOrigin`** (`20,219` origin blackouts penalized), `Safe_EV` preserves `+₹34.92` Mean (`₹462.60` vs `₹427.69`) and `+₹175.19` `ES10`.
2. **Portal Latency (`<= t - 2`, `v7_exp1`) & Smallholder Biology × `Stoch_CondMAR` × Blind Wait (`v7_exp2`):** Restricting to `t - 2` latency (`N = 57,047`, `ages 2..3`), **`Safe_EV_Sunk_m0` maintains both `ES10` (`−₹364.48` vs `B2 −₹508.36`, `p=0.001`) and `cond_ES10` (`−₹484.32` vs `−₹672.39`, `+₹188.07`, `p=0.001`)**, while `RT_2F_Min_m0` loses both `ES10` (`p=0.363`) and `cond_ES10` (`p=0.981` NS). Under Schedule #7 biological clock + smallholder `4%` *arhtiya* + ERA5 (`S6_Frozen`), `Safe_EV` outperforms `B2` on Mean (`₹310.40` vs `₹254.11`) and `cond_ES10` (`−₹693.55` vs `−₹924.02`); adding `Stoch_CondMAR_p1.00` flips Mean (`B2 ₹473.48` vs `Safe_EV ₹432.71`) while `Safe_EV` preserves `+₹366.85/qtl` **`cond_ES10`** (`−₹595.27` vs `−₹962.12`). Blindly waiting 1–2 days (`Sched7 ERA5`) confirms strong `cond_ES10` gains (`−₹506.58` / `−₹497.83` vs `B2 −₹809.56` / `−₹844.17`).
3. **Subgroups & Small-Cluster Limits (`v7_splits_171.csv`, `v7_exp5`):** On unconditional **`ES10`**, `Safe_EV_Sunk_m0` passes percentile CIs across all 6 states and 5 crop slices (`Holm11 <= 0.039`; Potato `−₹242.00` trails `RR −₹224.80` by `−₹17.20`). **However, on `cond_ES10` and studentized inference**, Himachal Pradesh (`B = 12`, `N = 7,068`) is **non-significant** (`cond_ES10 +₹250.82`, `p = 0.1239`; `p_stud = 0.1864`; `basic ES10 CI [−₹148.92, +₹544.34]`), and Apple (`N = 6,164`) is borderline/NS (`cond_ES10 +₹462.22`, `p = 0.0550`; `p_stud = 0.0585`; `basic CI [−₹83.41, +₹994.48]`), while GJ/KA/MP/MH/UP and NonApple/Onion/Potato/Tomato pass both. Meanwhile `Safe_EV` Mean CIs cross zero in GJ (`p=0.940`), MH (`0.160`), UP (`0.116`), Tomato (`0.877`), and Apple (`0.143`), whereas `RT_2F_Min_m0` retains positive Mean CIs across all 11 slices (`p = 0.001–0.032`). Across **all 36 tornado cells (`v7_tornado_171.csv`)**, `Safe_EV` wins `+₹15.03..+₹61.22` Mean, `+₹114.97..+₹263.60` `ES10`, and `+₹172.97..+₹322.24` `cond_ES10`. Structural checks hold on pure all-5 exact geocodes (`N = 19,362`: `cond_ES10 −₹567.95` vs `−₹850.28`, `p = 0.001`), clean `N = 55,820`, `N = 55,674` (`1–3d` origin), and `N = 86,054` unconditional origins (`ES10 −₹336.19` vs `−₹513.75`).
4. **SUTVA Crowding (`v7_exp5`):** Only `14.0%` of `Safe_EV` dispatches target unique `(arrival, crop, variety, dest)` slots (`34.14% <= 3` trucks; `max = 27`). Imposing `5%` / `10%`-per-extra-truck crowding penalties reduces `Safe_EV` Mean to `₹86.06` and `−₹5.31/qtl` (while `B2` collapses to `₹17.26` / `−₹75.37`), whereas capping herds at `k <= 2` (`31.29%` disp) preserves `₹207.00` Mean and `−₹230.30` `ES10` (`cond_ES10 −₹523.12`). Coordinated multi-FPO adoption requires dispatcher de-confliction.

![Re-scored parameter sensitivity across 10 representative freight and commission regimes from the 18-scenario tornado (left) and ES10 across missing-quote and Open-MAR bounds (right)](../figures/rev_fig3_sensitivity_tornado_and_missing.png)

![Left: Clean 166-market 2018–2023 annual ES10 generalization across six years including COVID-19 2020 (N=383,952). Right: Lagged HP graded-apple holdout (N=2,802)](../figures/rev_fig4_settlement_and_hp_apple.png)

### 4.3 Realized ERA5, Silent-Market Break-Even, `166`-Mkt `2018–2023` Archive, and HP Apples
- **Realized ERA5 Settlement & `178 -> 171` Shift (`v7_era5_and_reconcile.csv`, `v6_upgrades.csv`, `v7_breakeven_171.csv`):** Under `100%`-matched arrival ERA5, `Safe_EV_Sunk_m0` retains `Mean ₹440.28` (`+₹34.55` vs `B2 ₹405.73`), `ES10 −₹365.11` (`+₹187.80`, `p_holm_2s = 0.0024`), reconciling the `−₹31.16` `B1` shift into `−₹13.26` (`178->171`) + `−₹17.90` (`20°C->ERA5`). Exact silent break-even against `B2` requires `+₹348.61/qtl` above turn-back (`+₹117.97` flat; `25.45%` Open-MAR share; `26.65%` under ERA5; `resid = 0.0`). On 2D thin/thick MAR checks (`v7_exp3`), when thick silent yards stay closed, break-even Open-MAR share on thin silent yards is `29.78%` (`12.76%` if thick yards are 100% open).
- **Clean `166`-Market `2018–2023` Archive (`N = 383,952` & `115`-Mkt `N = 325,993`, Zero Retuning, `v7_decade_*.csv`):** Dropping all 7 post-2024 lookahead yards from the legacy `173` extract (`389,357`) leaves **`166` clean non-lookahead markets (`N = 383,952`)** within the `2024` OSRM frame: `Safe_EV_Sunk_m0` gains `+₹35.00` Mean (`₹356.57` vs `B2 ₹321.57`), `−12.57 pp` EpLoss (`12.64%`), `+₹169.27` `ES10` (`−₹304.29`), and **`+₹155.08` `cond_ES10`** (`−₹421.35` vs `−₹576.44`, all `p = 0.001`; vs equal-dispatch `B2_eq_SafeM0`: **`+₹174.27` `cond_ES10`, `p = 0.001`**). Holds identically on `115` `2017`-active markets (`N = 325,993`: `ES10 −₹290.68` vs `−₹450.51`, `cond_ES10 −₹408.34` vs `−₹554.48`), under CPI-deflated `B2` (`th=303` / year-median), and under realized `2018–2023` **NASA POWER climate × Schedule #7** (`Safe_EV` `₹330.84` vs `B2 ₹291.41`, `cond_ES10 −₹473.26` vs `−₹644.03`, `v7_exp5`). **Year-by-year honesty (`v7_decade_by_year_boot_2000.csv`):** `Safe_EV_Sunk_m0` wins `ES10` and `cond_ES10` in `6/6` years (`p = 0.001`), while **`2020` (`+₹12.93`, `p = 0.208`) and `2023` (`+₹20.35`, `p = 0.077`) Means are non-significant** (vs `B2_eq`: `2020` `p = 0.059` NS; `2023` `p = 0.021`), and `RT_2F_Min_m0` `cond_ES10` turns non-significant across the `166`-mkt pooled `b2dest` check (`p = 0.079`) and in `2020`/`2021`/`2023` (`p = 0.265–0.528`).
- **HP Graded Apples (`v7_hp_apple_171.csv`, `N = 2,802`):** Calibrated using `val_171` thresholds, `Safe_EV_Sunk_m0` narrows `ES10` (`−₹1,454.86` vs `B2 −₹2,392.12`, `p = 0.002`) and Mean (`₹1,354.85` vs `₹1,199.31`, `p = 0.028`, basic CI `[−₹0.36, +₹287.09]`), **yet `cond_ES10` (`+₹613.46`, `p = 0.0940` NS, `n_clusters = 34`) and `41.38%` dispatched losses** prove phone confirmation remains essential for graded apples.

| Robustness / Stress Panel | `B2_age` (Mean / `ES10` / `cond_ES10`) | `Safe_EV_Sunk_m0` (Mean / `ES10` / `cond_ES10`) | `RT_2F_Min_m0` (Mean / `ES10` / `cond_ES10`) |
|---|---|---|---|
| `div_0.0_spoil_only` *(`Safe_EV` Mean NS)* | `₹461.04` / `−₹360.86` / — | `₹473.07` / **`−₹186.46`** / — | **`₹481.62`** / `−₹348.53` *(NS)* / — |
| `open_yard_MAR_lagged_price` *(`B2` Mean wins)* | **`₹698.17`** / `−₹383.44` / — | `₹601.16` / **`−₹193.47`** / — | `₹611.88` / `−₹357.40` / — |
| `t2_age_2_3` (`<= t - 2` latency, `N = 57,047`) | `₹393.49` / `−₹508.36` / `−₹672.39` | `₹431.17` / **`−₹364.48`** / **`−₹484.32`** | **`₹437.19`** / `−₹494.68` *(NS)* / `−₹671.92` *(NS)* |
| `S6_Smallholder_4pctArh_Sched7_ERA5_Frozen` | `₹254.11` / `−₹789.08` / `−₹924.02` | `₹310.40` / **`−₹550.89`** / **`−₹693.55`** | **`₹311.30`** / `−₹701.98` / `−₹903.22` |
| `S6_Frozen × Stoch_CondMAR_p1.00` *(`B2` Mean wins)* | **`₹473.48`** / `−₹754.09` / `−₹962.12` | `₹432.71` / **`−₹407.13`** / **`−₹595.27`** | `₹427.76` / `−₹653.68` / `−₹918.36` |
| `Clean 166-Mkt 2018–2023` (`N = 383,952`) | `₹321.57` / `−₹473.56` / `−₹576.44` | `₹356.57` / **`−₹304.29`** / **`−₹421.35`** | **`₹370.86`** / `−₹395.63` / `−₹553.64` |
| `Clean 115-Mkt 2017-Active` (`N = 325,993`) | `₹306.93` / `−₹450.51` / `−₹554.48` | `₹335.28` / **`−₹290.68`** / **`−₹408.34`** | **`₹352.51`** / `−₹377.61` / `−₹533.05` |
| `Decade 166 NASA POWER × Sched #7` | `₹291.41` / `−₹521.99` / `−₹644.03` | `₹330.84` / **`−₹337.33`** / **`−₹473.26`** | **`₹339.87`** / `−₹444.47` / `−₹627.21` |

---

## 5. Related Work and Surviving Applied Contribution

Five streams frame this retrospective audit:
1. **Spatial Arbitrage and Agri-Information Trials:** Parity-bound models [baulch1997transfer] and Indian market integration analyses [sekhar2012agricultural, chatterjee2016six, negi2018farmers, mahajan2021covid, chatterjee2023market] explain why transport, fees, and market power erode raw spreads. Field evidence ranges from mobile-phone arbitrage gains in fisheries [jensen2007digital], soybeans [goyal2010information], and MIS bargaining [courtois2015farmer] to muted SMS effects under credit/middleman ties [fafchamps2012sms, mitra2018asymmetric] and e-auction gains [levi2020impact, levi2025improving].
2. **Mandi Price Forecasting and Imputation:** Forecasting and advisory papers optimize price RMSE or user workflows [madaan2019price, ma2019price, guo2020mandi, ziegler2019fresh, ladhar2023ai, biradar2026agrimarket, manimegalai2026mandicast] or reconstruct blank North-East rows [deka2026missing], without evaluating sequential missing-arrival turn-backs or `cond_ES10`.
3. **Decision-Focused Learning, Selective Prediction & Operational Heuristics:** Reject-option and DFL theory optimize risk-aware decisions [chow1970optimum, el_yaniv2010selective, geifman2017selective, ban2019bigdata, elmachtoub2022smart, franc2023optimal, mandi2024dfl], while produce export optimization models mean-variance tradeoffs [vargas2026mean]. Consistent with $1/N$ portfolio out-of-sample evidence [demiguel2009optimal] and fast-and-frugal heuristics [gigerenzer2011heuristic], zero-tuned-parameter triage heuristics outperform both hard activity gates and `<= t - 1` ML/OR baselines on `cond_ES10`.
4. **Partial Identification and Expected Shortfall:** Rubin missingness [rubin1976inference], Manski bounds [manski1990bounds, horowitz2000nonparametric], selective-label confounding [lakkaraju2017selective, kallus2021minimax], and CVaR/ES10 [rockafellar2000cvar] anchor our coupled/decoupled identification bounds.
5. **Why Conformal Risk Control Is Excluded:** Although conformal quantile regression, non-exchangeable calibration, and conformal decision theory offer finite-sample guarantees [lei2018distribution, romano2019conformalized, gibbs2021adaptive, angelopoulos2023conformal, barber2023beyond, jin2023selection, angelopoulos2024conformal, lekeufack2024conformal], Stage I `H2` stayed inconclusive and sequential missing-arrival panels violate exchangeability; we claim zero conformal guarantees.

**Surviving Contribution:** Claiming no methodological novelty, this study delivers a leak-free open benchmark (`171`-market `2025–2026` + `166`-market `2018–2023`) showing that two **zero-validation-tuned-parameter** lower-bound triage heuristics improve both `ES10` and dispatched `cond_ES10` over equal-age road dispatch and `<= t - 1` ML/OR policies under closed-yard, latency (`t - 2`), Schedule #7 × ERA5/NASA POWER, and stochastic MAR stresses, while mapping exact Manski reversals and subgroup/crowding failure boundaries.

---

## 6. Explicit Limitations and Non-Claims

1. **Modeled Payoffs $\ne$ Farm Income:** Freight, buyer-paid vs stylized fees, NABCONS cumulative anchors, and `30 qtl` scaling are model approximations, not audited truck *patti* slips.
2. **Blank Row $\ne$ Closed Gate (Open-MAR & Manski Reversals):** True coupled/decoupled worst-case Manski bounds and Open-MAR reverse Mean in favor of `B2`, crossing break-even at `25.45%` silent-open share (`+₹348.61/qtl`).
3. **6 a.m. Alert Filter Ahead of Phone Calls:** Never replaces calling destination traders (`Gate J` prospective FPO trial remains open beyond `2026-04-13` archives).
4. **Statistical & Temporal Limits:** Exploratory `2025–2026` calendar exposure; HP (`B = 12`, `p_stud = 0.1864`, `cond_ES10 p = 0.124`) and Apple (`cond_ES10 p = 0.055`, `41.38%` loss) remain fragile; clean `2020`/`2023` decade Means are NS (`p = 0.208`/`0.077`).
5. **General Equilibrium (SUTVA), Offline Corridor Frame, & Non-Conformal Scope:** Uncoordinated herding (`max = 27`) erodes arbitrage unless capped (`k <= 2`); clean `166`-market `2018–2023` offline panel remains inside the `2024` OSRM frame; zero conformal guarantees are claimed.

---

## 7. Conclusion

Chasing AGMARKNET spreads above `₹100/qtl` loses money on `45.07%` of dispatches under strict `<= t - 1` chronological timing and sequential closed-yard settlement. Benchmarking two fixed **zero-validation-tuned-parameter** triage heuristics (`Safe_EV_Sunk_m0`, `Safe_EV_Phys_m0`) alongside calculator rule `RT_2F_Min_m0` shows `Safe_EV_Sunk_m0` cuts losses (`14.88%`) and lowers worst-10% shortfall across both unconditional (`−₹345.53/qtl`) and dispatched capital (`cond_ES10 −₹447.48/qtl`, dominating fitted ML/OR models and surviving `<= t - 2` latency, Schedule #7 × `Stoch_CondMAR`, and clean `166`-market `2018–2023` archives), while openly scoping HP/Apple fragility, `2020/2023` Mean nulls, Manski reversals, and multi-truck crowding ahead of prospective FPO field trials.

---

## 8. Data, Code, Reproducibility, and Ethics Statement

All analyses use public aggregated quotes (AGMARKNET OGD NDSAP), OSM/OSRM routing (ODbL), Copernicus ERA5 (CC-BY), and NASA POWER meteorology, with zero PII. All tables, figures, PDFs, and LaTeX/DOCX bundles regenerate offline deterministically from tracked repository data, verified by cleanroom `a16_independent_audit.py`, `verify_traceability.py`, automated leakage tests (`pytest`), and zero-diff clean-clone rebuild verification (`Makefile` reproduction target).

---

## References

- `[angelopoulos2023conformal]` Angelopoulos, A. N., & Bates, S. (2023). Conformal prediction: A gentle introduction. *Foundations and Trends in Machine Learning* 16(4), 494–591. DOI: `10.1561/2200000101`
- `[angelopoulos2024conformal]` Angelopoulos, A. N., Bates, S., Fisch, A., Lei, L., & Schuster, T. (2024). Conformal risk control. *ICLR 2024*.
- `[ban2019bigdata]` Ban, G.-Y., & Rudin, C. (2019). The big data newsvendor: Practical insights from machine learning. *Operations Research* 67(1), 90–108. DOI: `10.1287/opre.2018.1757`
- `[barber2023beyond]` Barber, R. F., Candès, E. J., Ramdas, A., & Tibshirani, R. J. (2023). Conformal prediction beyond exchangeability. *Annals of Statistics* 51(2), 816–845. DOI: `10.1214/23-AOS2276`
- `[baulch1997transfer]` Baulch, B. (1997). Transfer costs, spatial arbitrage, and testing for food market integration. *AJAE* 79(2), 477–487. DOI: `10.2307/1244145`
- `[biradar2026agrimarket]` Biradar, A. V., & Divyashree, N. (2026). AgriMarket AI: Intelligent market selection and profit prediction system for farmers using ML. *IJEDR* 14(3), 538–547.
- `[chatterjee2016six]` Chatterjee, S., & Kapur, D. (2017). Six puzzles in Indian agriculture. *India Policy Forum* 13(1), 185–229.
- `[chatterjee2023market]` Chatterjee, S. (2023). Market power and spatial competition in rural India. *Quarterly Journal of Economics* 138(3), 1649–1711. DOI: `10.1093/qje/qjad004`
- `[chow1970optimum]` Chow, C. K. (1970). On optimum recognition error and reject tradeoff. *IEEE Trans. Info. Theory* 16(1), 41–46. DOI: `10.1109/TIT.1970.1054406`
- `[courtois2015farmer]` Courtois, P., & Subervie, J. (2015). Farmer bargaining power and market information services. *AJAE* 97(3), 953–977. DOI: `10.1093/ajae/aau051`
- `[deka2026missing]` Deka, P. (2026). Reconstructing missing mandi prices in North-East India with regional factors. *arXiv:2610.39949*. DOI: `10.48550/arXiv.2610.39949`
- `[demiguel2009optimal]` DeMiguel, V., Garlappi, L., & Uppal, R. (2009). Optimal versus naive diversification: How inefficient is the 1/N portfolio strategy? *Rev. Financ. Stud.* 22(5), 1915–1953. DOI: `10.1093/rfs/hhm075`
- `[el_yaniv2010selective]` El-Yaniv, R., & Wiener, Y. (2010). On the foundations of noise-free selective classification. *JMLR* 11, 1605–1641.
- `[elmachtoub2022smart]` Elmachtoub, A. N., & Grigas, P. (2022). Smart "Predict, then Optimize". *Management Science* 68(1), 9–26. DOI: `10.1287/mnsc.2020.3922`
- `[fafchamps2012sms]` Fafchamps, M., & Minten, B. (2012). Impact of SMS-based agricultural information on Indian farmers. *WBER* 26(3), 383–414. DOI: `10.1093/wber/lhr056`
- `[franc2023optimal]` Franc, V., Prusa, D., & Voracek, V. (2023). Optimal strategies for reject option classifiers. *JMLR* 24(11), 1–49.
- `[geifman2017selective]` Geifman, Y., & El-Yaniv, R. (2017). Selective classification for deep neural networks. *NeurIPS* 30, 4878–4887.
- `[gibbs2021adaptive]` Gibbs, I., & Candès, E. J. (2021). Adaptive conformal inference under distribution shift. *NeurIPS* 34, 1660–1672.
- `[gigerenzer2011heuristic]` Gigerenzer, G., & Gaissmaier, W. (2011). Heuristic decision making. *Annual Review of Psychology* 62, 451–482. DOI: `10.1146/annurev-psych-120709-145346`
- `[goyal2010information]` Goyal, A. (2010). Information, direct access to farmers, and rural market performance in Central India. *AEJ: Applied Economics* 2(3), 22–45. DOI: `10.1257/app.2.3.22`
- `[gross2016usda66]` Gross, K. C., Wang, C. Y., & Saltveit, M. (2016). *The Commercial Storage of Fruits, Vegetables, and Florist and Nursery Stocks*. USDA ARS AH-66.
- `[guo2020mandi]` Guo, H., Woodruff, A., & Yadav, A. (2020). Improving lives of indebted farmers using deep learning. *AAAI-20* 34(08), 13294–13299. DOI: `10.1609/aaai.v34i08.7039`
- `[hersbach2020era5]` Hersbach, H., et al. (2020). The ERA5 global reanalysis. *QJRMS* 146(730), 1999–2049. DOI: `10.1002/qj.3803`
- `[holm1979simple]` Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics* 6(2), 65–70.
- `[horowitz2000nonparametric]` Horowitz, J. L., & Manski, C. F. (2000). Nonparametric analysis of randomized experiments with missing covariate and outcome data. *JASA* 95(449), 77–84. DOI: `10.1080/01621459.2000.10473902`
- `[hpeconsurvey2026]` Department of Economics and Statistics, GoHP (2026). *Economic Survey 2025–26: Himachal Pradesh*.
- `[jensen2007digital]` Jensen, R. (2007). The digital provide: Information, market performance, and welfare in the South Indian fisheries sector. *QJE* 122(3), 879–924. DOI: `10.1162/qjec.122.3.879`
- `[jha2015ciphet]` Jha, S. N., et al. (2015). *Report on Assessment of Quantitative Harvest and Post-Harvest Losses of Major Crops in India*. ICAR-CIPHET, MoFPI.
- `[jin2023selection]` Jin, Y., & Candès, E. J. (2023). Selection by prediction with conformal p-values. *JMLR* 24(244), 1–41.
- `[kader2002postharvest]` Kader, A. A. (Ed.) (2002). *Postharvest Technology of Horticultural Crops* (3rd ed.). UC ANR Pub. 3311.
- `[kallus2021minimax]` Kallus, N., & Zhou, A. (2021). Minimax-optimal policy learning under unobserved confounding. *Management Science* 67(5), 2870–2890. DOI: `10.1287/mnsc.2020.3699`
- `[ladhar2023ai]` Ladhar, R., et al. (2023). AI-based market intelligence systems for farmer collectives: A case study from India. *ACM JCSS* 1(1), 1–32. DOI: `10.1145/3609262`
- `[lakkaraju2017selective]` Lakkaraju, H., et al. (2017). The selective labels problem: Evaluating algorithmic predictions in the presence of unobservables. *ACM KDD '17*, 275–284. DOI: `10.1145/3097983.3098066`
- `[lei2018distribution]` Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018). Distribution-free predictive inference for regression. *JASA* 113(523), 1094–1111. DOI: `10.1080/01621459.2017.1307116`
- `[lekeufack2024conformal]` Lekeufack, J., et al. (2024). Conformal decision theory: Safe autonomous decisions from imperfect predictions. *IEEE ICRA*, 11668–11675. DOI: `10.1109/ICRA57147.2024.10610041`
- `[levi2020impact]` Levi, R., Rajan, M., Singhvi, S., & Zheng, Y. (2020). The impact of unifying agricultural wholesale markets on prices and farmers' profitability. *PNAS* 117(5), 2366–2371. DOI: `10.1073/pnas.1906854117`
- `[levi2025improving]` Levi, R., Rajan, M., Singhvi, S., & Zheng, Y. (2025). Improving farmers' income on online agri-platforms: Evidence from the field. *Manuf. Serv. Oper. Manag.* 27(6), 1683–1700. DOI: `10.1287/msom.2022.0437`
- `[luxen2011osrm]` Luxen, D., & Vetter, C. (2011). Real-time routing with OpenStreetMap data. *ACM SIGSPATIAL*, 513–516. DOI: `10.1145/2093973.2094062`
- `[ma2019price]` Ma, W., Nowocin, K., Marathe, N., & Chen, G. H. (2019). An interpretable produce price forecasting system for small and marginal farmers in India. *ICTD '19*, 1–11. DOI: `10.1145/3287098.3287100`
- `[madaan2019price]` Madaan, L., et al. (2019). Price forecasting & anomaly detection for agricultural commodities in India. *ACM COMPASS '19*, 52–64. DOI: `10.1145/3314344.3332488`
- `[mahajan2021covid]` Mahajan, K., & Tomar, S. (2021). COVID-19 and supply chain disruption: Evidence from food markets in India. *AJAE* 103(1), 35–52. DOI: `10.1111/ajae.12158`
- `[mandi2024dfl]` Mandi, J., et al. (2024). Decision-focused learning: Foundations, state of the art, benchmark and future opportunities. *JAIR* 80, 1623–1701. DOI: `10.1613/jair.1.15320`
- `[manimegalai2026mandicast]` Manimegalai, M., Sanjay, B., Siddarth, J., & Udayabhaarathi, K. (2026). Mandi Cast: AI-based crop price forecasting and sell advisory system. *IJRPR* 7(11), 1–5.
- `[manski1990bounds]` Manski, C. F. (1990). Nonparametric bounds on treatment effects. *American Economic Review* 80(2), 319–323.
- `[mitra2018asymmetric]` Mitra, S., Mookherjee, D., Torero, M., & Visaria, S. (2018). Asymmetric information and middleman margins: An experiment with Indian potato farmers. *REStat* 100(1), 1–13. DOI: `10.1162/rest_a_00699`
- `[nabcons2022phl]` NABCONS (2022). *Study to Determine Post-Harvest Losses of Agri Produces in India*. MoFPI, GoI (PIB `PRID=2151371`).
- `[negi2018farmers]` Negi, D. S., Birthal, P. S., Roy, D., & Khan, M. T. (2018). Farmers' choice of market channels and producer prices in India. *Food Policy* 81, 106–121. DOI: `10.1016/j.foodpol.2018.10.008`
- `[nitiaayog2021freight]` NITI Aayog & RMI (2021). *Fast Tracking Freight in India*. Government of India.
- `[nss77report587]` National Statistical Office (NSO), MoSPI, GoI (2021). *NSS Report No. 587: Situation Assessment of Agricultural Households* (PIB `PRID=1753856`).
- `[phipson2010permutation]` Phipson, B., & Smyth, G. K. (2010). Permutation p-values should never be zero. *Stat. Appl. Genet. Mol. Biol.* 9(1). DOI: `10.2202/1544-6115.1585`
- `[pib154554apmc]` Ministry of Consumer Affairs, Food and Public Distribution, GoI (2016). *14 States Deregulated Fruits & Vegetables Marketing from APMC* (PIB `relid=154554`).
- `[rbi2024top]` Roy, R., et al. (2024). *Vegetables Inflation in India: A Study of Tomato, Onion and Potato (TOP)*. RBI Working Paper Series No. 08/2024.
- `[rockafellar2000cvar]` Rockafellar, R. T., & Uryasev, S. (2000). Optimization of Conditional Value-at-Risk. *Journal of Risk* 2(3), 21–41. DOI: `10.21314/JOR.2000.038`
- `[romano2019conformalized]` Romano, Y., Patterson, E., & Candès, E. J. (2019). Conformalized quantile regression. *NeurIPS* 32, 3538–3548.
- `[rubin1976inference]` Rubin, D. B. (1976). Inference and missing data. *Biometrika* 63(3), 581–592. DOI: `10.1093/biomet/63.3.581`
- `[sekhar2012agricultural]` Sekhar, C. S. C. (2012). Agricultural market integration in India: An analysis of select commodities. *Food Policy* 37(3), 309–322. DOI: `10.1016/j.foodpol.2012.03.002`
- `[sparks2018nasapower]` Sparks, A. H. (2018). nasapower: A NASA POWER global meteorology, surface solar energy and climatology data client for R. *JOSS* 3(30), 1035. DOI: `10.21105/joss.01035`
- `[vargas2026mean]` Vargas, N., Klapp, M., & Mac Cawley, A. (2026). A mean-variance optimisation model for produce export distribution with postponed shipment and market allocation options. *Int. J. Prod. Res.* 64(1), 125–150. DOI: `10.1080/00207543.2025.2543493`
- `[ziegler2019fresh]` Ziegler, M., Garg, L., Tiwary, S., Vashistha, A., & Heimerl, K. (2019). Fresh insights: User research towards a market information service for Bihari vegetable farmers. *ICTD '19*, 1–11. DOI: `10.1145/3287098.3287115`
