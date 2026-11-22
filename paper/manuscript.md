# When Online Mandi Prices Mislead: A Leak-Free Audit and Zero-Parameter Risk-Aware Dispatch Rules for Indian Wholesale Markets

## Abstract

Farmers and farmer producer organizations (FPOs) routinely compare local harvest prices against wholesale prices posted on government portals such as AGMARKNET before hiring a truck. On a portal screen, a ₹500 per quintal price difference between an origin mandi and a neighboring yard looks like immediate cash. It is not. This paper audits Indian daily wholesale records for onion, potato, tomato, and apple across 178 core markets (plus 42 graded-apple yards) in six states from 1 January 2024 to 1 September 2026 under a strict chronological timing firewall (`<= t - 1`) and a realistic sequential day-by-day arrival settlement model.

Across 58,676 lagged test episodes (1 June 2025 to 8 April 2026) showing a raw `<= t - 1` price gap above ₹100 per quintal, naive screen-chasing (`B1_lagged_screen`, `100.00%` dispatch) loses money on **45.21%** of trips (`mean ₹397.87/qtl`, exact worst-10% expected shortfall **`ES10 = −₹641.26/qtl`**). Conditioning on sequential portal arrivals is crucial: under baseline missing-quote return assumptions (`div = 1.5`), **28.98%** (`17,005` trips) find zero commodity trading recorded on arrival and turn back; scoring the identical trips with 3-day hindsight drops apparent loss incidence to 31.35%.

Building up from fair age-matched road baselines (`B2_age_matched`, `lag 1..3`) and pre-registered tuned reliability-weighted abstention (`RR_Abstain_matched`, $\kappa^* = 5.0$), we discover an **even simpler, zero-hyperparameter rule (`Safe_EV_Sunk_m0`)**: multiply the 1-standard-deviation conservative spread ($G_{\text{1SD}}$) by the yard's historical arrival-weekday reporting frequency ($p_{\text{dow}}$), and dispatch iff $p_{\text{dow}} G_{\text{1SD}} - F_{\text{road}} > 0$ (equivalently, safe spread-to-freight ratio $G_{\text{1SD}} / F_{\text{road}} > 1 / p_{\text{dow}}$). Without tuning ANY threshold or $\kappa$ grid, **`Safe_EV_Sunk_m0`** (`63.27%` dispatch) achieves `mean ₹465.59/qtl` (+₹32.03 vs `B2_age_matched`), cuts episode loss incidence to **`14.93%`** (−11.79 pp, two-sided Holm `p = 0.0040`), and strengthens **`ES10` to `−₹344.09/qtl`**—a **+₹181.17/qtl tail improvement over `B2_age_matched`** (`p_holm_2s = 0.0040`), **+₹168.69/qtl over hard-gated `MG_matched`**, and **+₹116.63/qtl over tuned `RR_Abstain_matched`** across all three spatiotemporal clustering schemes (170–173 market clusters $\times$ 23 fortnights) and **every single state and crop** including graded apples (`−₹1,454.86` vs `−₹2,392.12` on HP apples). A stripped 4-function phone-calculator rule dropping volatility (`RT_2F_Min_m0`, $p_{\min} G > 2 F_{\text{road}}$) raises mean net gain to **`₹478.38/qtl`** (+₹44.82 vs `B2`, `p_holm_2s = 0.0040`) with zero free parameters. Across strict counterfactual tests, `Safe_EV_Sunk_m0` maintains strong `ES10` and loss reductions even when diversion penalties vanish (`exact_zero_divert_payoff_0`: +₹169.79/qtl `ES10`, `p_2s = 0.002`) and under open-yard Missing-At-Random portal omissions (`+₹190.00/qtl` `ES10`), though `B2` earns higher mean payoff (+₹102.58/qtl) when blank portal rows represent unrecorded open sales—establishing that algorithmic triage helps FPOs filter screen noise prior to live trader confirmation, while not replacing phone verification or field trials. All results remain exploratory wrt prior calendar exposure (`make reproduce`, `0` untraceable numbers).

---

## 1. Three Research Questions and Honest Methodological Scope

Indian wholesale agricultural markets (*mandis*) publish daily minimum, modal, and maximum prices by variety on AGMARKNET. A widely held premise in agricultural informatics is that surfacing remote portal prices unlocks spatial arbitrage for farmers [jensen2007digital, goyal2010information]. In practice, four operational barriers stand between an online spread and cash in hand:

1. **Decision-Time Reporting Lag:** At 6 a.m. dispatch time $t$—when FPO managers decide whether to load a truck or suppress an alert—same-day auction prices are not settled, and thin yards publish intermittently (`1..7` days late).
2. **Transfer, Statutory Destination Fees, and Spoilage:** Road freight, hill terrain, out-of-district APMC seller fees levied on destination auction value, and ambient transit decay shrink paper spreads [baulch1997transfer, nabcons2022phl].
3. **Price Dispersion and Arrival Execution Risk:** A single high lagged modal quote on a volatile yard (`dest_price_cv_28d`) frequently reverts toward mean on arrival day $t + \tau$, and an empty arrival board (`settle_any_min_dw = NaN`) means no transaction record exists in the portal [deka2026missing].
4. **Role of Automated Triage vs Live Phone Calls:** Farmers hauling a 30-quintal truck typically confirm live yard openings via a 30-second phone call to a destination *arhtiya* (commission agent) [jensen2007digital]. Automated dispatch scoring serves as a **6 a.m. alert-triage filter** preventing FPO managers from chasing hundreds of noisy portal spreads before dialing traders.

We ask three focused questions across six Indian states (Maharashtra, Uttar Pradesh, Karnataka, Madhya Pradesh, Gujarat, Himachal Pradesh) and four crops (Onion, Potato, Tomato, Apple):

- **RQ1 (Screen-Chasing Loss Incidence):** Under a `<= t - 1` price firewall and non-anticipative sequential arrival settlement, how often do attractive lagged price spreads (`> ₹100/qtl`) lose money, and how severely do 3-day hindsight settlement and ex-post day-$t$ origin conditioning distort perceived performance?
- **RQ2 (Can Zero-Parameter Expected-Value Rules Beat Both Fair Baselines and Tuned Heuristics?):** On equal candidate menus and equal quote ages (`1..3` days), can threshold-free, zero-hyperparameter rules (`Safe_EV_Sunk_m0` and 4-function calculator `RT_2F_Min_m0`) improve episode loss incidence and worst-10% `ES10` compared with age-matched road rules (`B2_age_matched`), hard-gated heuristics (`MG_matched`), and our tuned `kappa*=5.0` extension (`RR_Abstain`)?
- **RQ3 (Identification Bounds, Subgroup Generalizability, and Structural Robustness):** How sensitive are conclusions across full Manski/MAR missing-quote regimes (`open_yard_MAR_lagged_price`, `exact_zero_divert_payoff_0`, `div = 0..2`), frozen vs re-scored freight/commission tornados, exact-geocoded corridors vs district centroids, unconditional origin panels restoring unreported day-$t$ origin rows, all six states, individual crops, and high-dispersion Himachal Pradesh graded apples?

### Explicit Protocol Chronology (`Stage I` -> `A10` -> `A18` Zero-Parameter Evolution)
1. **Stage I Legacy Baseline (`e421d15`):** An unlagged gradient-boosted tree system (`HistGradientBoostingRegressor`) with ERA5 weather and conformal bands proved **inconclusive against same-day road dispatch `B2`** on confirmatory `H2` (+₹6.13/qtl, 95% CI [−₹17.02, +₹25.02], Holm `p = 0.2699`) and failed on HP graded apples. We preserve those negative results cleanly.
2. **Audit Remediation (`A10`, Commit `87a0b62`):** Eliminated all day-$t$ shortlist/origin price leaks, removed `98.64%` ERA5-identical forecast weather, fixed APMC fee bases (`M9`), fixed quantile-mean `ES10` math, and tested reliability-weighted `RR-Abstain`. However, critical re-examination revealed four structural issues: a destination cluster-key string mismatch (`336` split clusters instead of `172` physical markets), one-sided unlabeled Holm p-values, hitting the validation grid ceiling at $\kappa^* = 5.0$ (disguising an implicit threshold shift rather than a true `m=0` zero-parameter rule), and missing subgroup/sensitivity coverage for `RR`.
3. **Final Zero-Parameter Simplification (`PREREG_A18.md`, Commit `4cbb02d`):** Strictly keeping test outcomes quarantined during rule design on validation (`2025-01-01..2025-05-31`), we committed five zero-hyperparameter closed-form formulas plus the full `A17` stress suite before running `revision/eval_a18.py`. Because calendar `2025-06-01..2026-04-08` and HP apples appeared earlier in repo history, **all post-Stage-I tests remain strictly exploratory (`exploratory: true`) wrt calendar exposure** [R5].

---

## 2. Data Provenance, Cleaning Funnel, and Causal Information Audit

### 2.1 Tracked Official Data Sources (Zero Gitignored Files Required)
All tables and figures build deterministically from six tracked repository artifacts:
1. **AGMARKNET 6-State 4-Crop Panel (`data/raw/agmarknet_6state_top_apple_2024_2026.parquet`):** Cleaned daily market-variety-grade records from Government of India AGMARKNET releases spanning 1 January 2024 to 13 April 2026 (`260,043` rows, `178` core markets, Open Govt Data NDSAP license). Verified against official XML parity records in legacy `Exp 14` (`100.0%` modal parity on graded apples).
2. **HP Grade-Explicit Apple Panel (`data/raw/hp_apple_daily_2025_2026.csv`):** `4,427` official daily records across `42` Himachal Pradesh yards (7 November 2025 to 1 September 2026) with explicit commercial grades.
3. **Static OSRM Corridor Matrix (`data/processed/osrm_corridor_matrix.parquet`):** `8,147` directed corridors (`15.19` km to `499.43` km) across `220` yards (`150` exact market geocodes, `70` district centroids, OSM ODbL; `1.35x` truck speed, `1.25x` hill speed, `+4`h buffer) [luxen2011osrm]. Exact-geocoded corridors cover `58.29%` of shortlisted test rows (`41.71%` touch at least one centroid endpoint—explicitly tested in Section 4.3).
4. **Statutory Fee & NABCONS Decay Schedules (`data/processed/state_apmc_and_loss_parameters.csv`):** Seller market fees from PIB `relid=154554` (`0.5%` KA/GJ/HP-veg, `1.0%` MH/HP-apple, `1.5%` MP/UP; `0%` intra-district) and 24-hour market-level decay rates from MoFPI / NABCONS (2022) Annexure-II Table-2 (PIB `PRID=2151371`: Tomato `3.25%`, Onion `1.96%`, Apple `1.64%`, Potato `0.86%`) [nabcons2022phl].
5. **Pre-Split Weather Audit (`data/processed/mandi_weather_2024_2026.parquet`):** Auditing `67,135` rows (`2025-01-01..2026-04-08`) showed `fc_rain_mm == era5_rain_mm` on `66,222` rows (`98.64%`) and humidity within 1% on `67,091` rows (`99.93%`) [hersbach2020era5]. Live/ERA5 weather is completely excluded from primary analysis (`none_20C_reference` primary), with `< 2025-01-01` 2024 state-month averages tested only as sensitivity.
6. **Government Economic Benchmarks:** Heavy-truck corridor floor `₹2.58/tonne-km` (`₹0.258/qtl-km`) from NITI Aayog & RMI (2021) [nitiaayog2021freight], smallholder `30`-quintal reference loads and `₹3,798/mo` net crop income from MoSPI NSS Report 587 (`PRID=1753856`), HP `91.59%` single-lane hill road share (`39,465 / 43,091` km) from GoHP Economic Survey 2025–26, and *arhtiya* commission ranges from RBI Working Paper 08/2024 [rbi2024top].

### 2.2 Reconciled Cleaning Funnel & Day-$t$ Origin Conditioning Disclosure
Table 1 traces every row from raw portal files through canonical variety consolidation (`Modal = median`, `Min = min`) and strictly `<= t - 1` shortlisting. Earlier docs under-reported or failed to drop `759` out-of-range quotes (`Modal < Min` or `Modal > Max`), which are now cleanly removed before episode construction.

| Pipeline Stage | 6-State Panel Count | HP Graded Apple Count | Exact Integer Check / Disclosure |
|---|---:|---:|---|
| Raw daily records | `260,043` | `4,427` | `2024-01-01..2026-04-13` (6-state); `2025-11-07..2026-09-01` (HP) |
| Dropped: invalid (`Modal < Min` or `Modal > Max`) | `759` | `0` | `0` nonpositive/NaN prices |
| Valid cleaned records retained | `259,284` | `4,427` | `260,043 - 759 = 259,284` |
| Raw 7-column key deduplication (`median` modal, `min` floor) | `256,997` | `4,427` | `2,287` excess duplicate rows (`2,254` groups, `1,484` conflicting modals) |
| Canonical `(State, Market, Commodity, Variety_Key, Date)` rows | `248,302` | `4,427` | `8,695` variant/grade merges (`259,284 - 10,982 = 248,302`) |
| Origin variety-days inside evaluation window | `131,366` | `4,165` | `2025-01-01..2026-04-08` (ensures `[t+tau, t+tau+2] <= 2026-04-13`) |
| With strictly prior origin quote (`origin_lag_age` 1–7d) | `129,023` | `3,921` | `98.22%` origin coverage strictly `<= t - 1` |
| Reachable `(origin, dest)` corridors (`15–500` km) | `3,942,896` | `250,958` | Inner join with `osrm_corridor_matrix.parquet` |
| Candidate pairs with strictly prior dest quote (`1–7`d) & `lag_spread > 100` | `518,467` | `8,442` | Across `95,074` (6-state) / `2,802` (HP) episodes |
| **Top-5 shortlisted candidate rows (`val` + `test`)** | **`324,992`** | **`7,753`** | Tie-broken deterministically by `(-lag_spread, road_km, dest_market)` |
| **Validation / Test episodes (`2025-01..05` / `2025-06..2026-04`)** | **`36,398` / `58,676`** | `0` / **`2,802`** | Exploratory wrt prior calendar exposure |
| *Unconditional test origin panel (without day-$t$ origin filter)* | **`88,014`** *(test)* | — | Restores **`29,338`** test episodes lacking day-$t$ origin upload (Section 4.3) |

**Ex-Post Day-$t$ Origin Conditioning Disclosure (`A17`):** Constructing primary episodes on observed day-$t$ origin records (`settle_local_price_d0` present) excludes active origin days whose local exact-variety modal failed to publish on day $t$ (`29,338` out of `88,014` unconditional shortlisted test episodes) and leaves abstention with `0%` non-reporting risk versus `~28%` on dispatched trips. In Section 4.3 we explicitly evaluate the full `88,014`-episode unconditional panel (`unconditional_orig_panel_d0_or_lag`—where `origin_lag_price` serves symmetrically as the local benchmark when `settle_local_price_d0` is missing, alongside `outside_origin_lag` everywhere) to prove that primary conclusions hold without day-$t$ sample selection. Moreover, filtering on `lag_spread > 100` creates classic winner's curse reversion: across `origin_lag_age in 1..7`, `origin_lag` prices sit slightly below day-$t$ local prices while stale `dest_lag` prices fall sharply by arrival day; keeping `origin_lag_age` up to 7d affects `2,028` test episodes, tested directly in Section 4.3.

### 2.3 Causal Timing Firewall and Feature Availability
At morning decision time $t$, **every** feature entering scoring or shortlisting predates day $t$ (`dest_quote_date < date`, `origin_quote_date < date`). Realized `settle_local_price_d0` and arrival columns `settle_dest_modal_d0..d2`, `settle_any_min_d0..d2` exist exclusively for payoff settlement. `tests/test_timing_and_leakage_r3.py` corrupts *all* prices on days $\ge t^*$ (inserting ₹99,999/qtl at excluded yards, halving day-$t^*$ local prices, and deleting active candidates on days $\ge t^*$) and asserts bit-for-bit equality of the candidate menu and all decision features on $t \le t^*$.

---

## 3. Payoff Physics, Sequential Settlement, and Decision Rules (With Numeric Examples)

### 3.1 Physical Freight, Statutory Destination Fee (`M9`), and Spoilage
For corridor $c = (o \to d)$ in state $s$ and commodity $k$:

$$\text{Freight}_{\text{road}}(c) = 35.0 + 0.45 \cdot h_s \cdot \text{road\_km}(c)$$

where $h_s = 1.45$ in Himachal Pradesh (`91.59%` single-lane roads) and $1.0$ elsewhere. Reference 20°C / 65% RH biological decay over transit `truck_hours` plus waiting days $w \in \{0, 1, 2\}$ is:

$$s(k, w) = \min\!\left(0.55,\; b_k \cdot \frac{\max(1,\; \text{truck\_hours} + 24 w)}{24}\right)$$

with NABCONS 24h rates $b_k \in \{0.0325 \text{ Tomato},\; 0.0196 \text{ Onion},\; 0.0164 \text{ Apple},\; 0.0086 \text{ Potato}\}$ [nabcons2022phl]. Statutory APMC seller fees $\tau_{\text{fee}}(c) \in \{0, 0.005, 0.010, 0.015\}$ (`0` if `same_district`) apply strictly to **post-spoilage destination gross sales**, and equal `0` if the truck returns home unsold.

<!-- WORKED_EXAMPLE_START -->
> **Worked Example 1 (Physical Freight, Spoilage & Destination-Base Statutory Fee):**  
> Consider an out-of-district **Tomato** trip in **Madhya Pradesh** (`fee_rate = 1.5%`, $h_s = 1.0$) with `road_km = 200` km, `truck_hours = 6` hours, and immediate arrival sale ($w = 0$) at `sale_price = ₹2,000/qtl`, vs local `settle_local_price_d0 = ₹1,500/qtl`:
> 1. Freight: $F = 35.0 + 0.45 \times 1.0 \times 200 = ₹125.00/\text{qtl}$.
> 2. 20°C spoilage: $s(0) = 0.0325 \times (6 / 24) = 0.008125$ ($0.8125\%$).
> 3. Post-spoilage gross auction revenue: $₹2,000 \times (1 - 0.008125) = ₹1,983.75/\text{qtl}$.
> 4. Net after 1.5% statutory fee: $₹1,983.75 \times 0.985 = ₹1,953.99/\text{qtl}$.
> 5. Modeled net dispatch gain: $₹1,953.99 - ₹125.00 - ₹1,500.00 = +₹328.99/\text{qtl}$.
<!-- WORKED_EXAMPLE_END -->

### 3.2 Sequential Non-Anticipative Settlement vs Hindsight Lookahead
Starting at $w = 0$ on arrival day $t_{\text{arr}} = t + \tau$ (`tau_days in 1..3`), settlement advances day by day without future knowledge:
- **Sell exact:** If exact-variety `Modal_Price` is reported on day $w$, sell: $\Delta\text{Net}_{\text{sell}}(w) = P_{\text{sale}}(1 - s(k, w))(1 - \tau_{\text{fee}}) - F - 25 w - P_{\text{loc}, d0}$.
- **Wait ($w < 2$):** If exact variety is missing on day $w$ but another variety of the crop trades (`settle_any_min_dw > 0`), wait 1 day (`₹25/qtl-day` detention + 24h decay).
- **Turn back / distress fallback:** If no variety of the commodity is recorded on day $w$, divert home with zero APMC fee: $\Delta\text{Net}_{\text{divert}}(w) = -\text{div}\cdot F - P_{\text{loc}, d0}\cdot s(k, w) - 25 w$ (baseline `div = 1.5`; if day $w = 2$ still shows another variety, sell at `0.90 * settle_any_min_d2` after fee and `₹50` detention).

By contrast, **3-day hindsight settlement** peeks ahead across `d0..d2` even when day 0 shows zero commodity trade.

<!-- WORKED_EXAMPLE_START -->
> **Worked Example 2 (Sequential No-Lookahead vs 3-Day Hindsight):**  
> On our MP Tomato trip ($F = ₹125$, $P_{\text{loc}, d0} = ₹1,500$), suppose destination Tomato is completely absent on arrival day 0 (`settle_any_min_d0 = NaN`), though exact-variety trades at `₹2,000` on day +1:
> - **Sequential (realistic):** Seeing an empty tomato auction on day 0, the truck diverts at $w = 0$ (zero fee): $\Delta\text{Net} = -1.5 \times 125 - 1,500 \times 0.008125 = -₹199.69/\text{qtl}$.
> - **3-day hindsight:** Clairvoyant waiting ($w = 1$, $s(1) = 0.040625$, detention `₹25`) records $+₹239.97/\text{qtl}$—a ₹439.66/qtl hindsight distortion.
<!-- WORKED_EXAMPLE_END -->

### 3.3 Equal-Menu Baselines, `RR-Abstain`, and Zero-Parameter Simplification (`Safe-EV` & `RT-2F`)
Every rule evaluates the same Top-5 lagged menu (`lag_spread > 100`) and selects at most one corridor (else abstain with $\Delta\text{Net} = 0$). Baselines match `dest_lag_age in 1..3` (`R4`):
1. **`B1_lagged_screen`:** Highest raw `lag_spread` across `age 1..7` (`100%` dispatch).
2. **`B2_age_matched`:** Road-adjusted score $G(c, t) - F_{\text{road}}(c) > ₹200/\text{qtl}$ (where $G = P_{\text{dest,lag}}(1 - \tau_{\text{fee}}) - P_{\text{orig,lag}}$, tuned on validation `70.71%` dispatch).
3. **`B_simple_activity_matched` & `MG_matched`:** Adds 14-day reporting (`rep14 >= 0.50`) or dual hard gates (`rep14 >= 0.50 & dow8 >= 0.35`) plus 20°C spoilage, matched to validation `70.71%` dispatch (`m_mg_match = ₹131.26`).
4. **Tuned `RR_Abstain` (`A10`, Commit `87a0b62`):** Mixes open-market payoff $\widehat{\Delta}_{\text{open}}$ and a bounded loss $-\kappa F_{\text{road}} - P_{\text{orig,lag}} s_{\text{ref},0}$ weighted by $\hat{p}_{\text{rep}} = 0.5\,\text{rep}_{28} + 0.5\,\text{dow}_8$. **Critical Limitation Caught by `A17`/`A18`:** `val` optimization hit the grid wall $\kappa^* = 5.0$ ($3.33\times$ physical diversion `1.5`), compensating for two missing signals: `rep28` over-predicted Sunday mandi closures, and `RR` omitted auction price volatility. Raising $\kappa$ further up to `20.0` drives the matched cutoff down to `−₹328.99/qtl` (showing $\kappa = 5.0$ acted as an implicit grid-tuned threshold shift, NOT a pure threshold-free constant).

To eliminate $\kappa$ tuning, `rep28` holiday pollution, and Q10 spoilage lookups simultaneously, **Agent `A18`** designed and locked (`PREREG_A18.md`, **0 free parameters, fixed `S > 0`**):
5. **`Safe_EV_Sunk_m0` (Zero-Parameter Scientific Champion):** Combines weekday-specific Laplace reporting frequency $p_{\text{dow}} = \text{dest\_dow\_exact\_rep\_8w} \in \{\frac{1}{10}, \dots, \frac{9}{10}\}$ with 1-standard-deviation conservative price spread $G_{\text{1SD}}(c, t) = P_{\text{dest,lag}}(1 - \text{cv}_{28})(1 - \tau_{\text{fee}}) - P_{\text{orig,lag}}$ against sunk one-way freight $F_{\text{road}}$:
   $$S_{\text{Safe-EV}}(c, t) = p_{\text{dow}}(c, t) \cdot G_{\text{1SD}}(c, t) - F_{\text{road}}(c) > 0 \quad \Longleftrightarrow \quad \frac{G_{\text{1SD}}}{F_{\text{road}}} > \frac{1}{p_{\text{dow}}}$$
   *(And its exact physical counterpart `Safe_EV_Phys_m0` using simulator `div = 1.5`: $p_{\text{dow}}(G_{\text{1SD}} - F) - (1 - p_{\text{dow}}) 1.5 F > 0$, zero tuning!)*
6. **`RT_2F_Min_m0` & `RT_2F_Dow_m0` (Class-8 Phone-Calculator Rule, NO `cv28`, NO `spoil`):** Using plain fee-adjusted spread $G$ and $p_{\min} = \min(\text{rep}_{28}, p_{\text{dow}})$ (or $p_{\text{dow}}$ alone), dispatch iff expected revenue clears **round-trip freight (`2F`)**:
   $$S_{\text{RT-2F-Min}}(c, t) = p_{\min}(c, t) \cdot G(c, t) - 2\,F_{\text{road}}(c) > 0 \quad \Longleftrightarrow \quad \frac{G}{2\,F_{\text{road}}} > \frac{1}{p_{\min}}$$

<!-- WORKED_EXAMPLE_START -->
> **Worked Example 3 (Zero-Parameter `Safe_EV_Sunk_m0` and Class-8 `RT_2F_Min_m0` in 10 Seconds):**  
> Take our MP Tomato route ($P_{\text{orig,lag}} = ₹1,500$, $P_{\text{dest,lag}} = ₹2,000$, $\tau_{\text{fee}} = 1.5\%$, $F_{\text{road}} = ₹125$, `cv28 = 0.15`), so $G = 2,000(0.985) - 1,500 = +₹470.00/\text{qtl}$ and 1-SD safe spread $G_{\text{1SD}} = 2,000(0.85)(0.985) - 1,500 = +₹174.50/\text{qtl}$.
> - **Steady Yard A (`dow8 = 0.90`, `rep28 = 0.85`, so $p_{\min} = 0.85$):**
>   - `Safe_EV_Sunk`: $0.90 \times 174.50 - 125 = +₹32.05 > 0 \implies$ **DISPATCH** (Ratio $174.5/125 = 1.40 > 1/0.90 = 1.11$).
>   - `RT_2F_Min` (no SD needed): $0.85 \times 470.00 - 250 = +₹149.50 > 0 \implies$ **DISPATCH**.
> - **Sunday / Thin Yard B (`dow8 = 0.20`, `rep28 = 0.60`, $p_{\min} = 0.20$):** Notice `B2_age_matched` scores Yard B `+₹345` (`+₹470 - ₹125`) identically to Yard A and dispatches! Yet both zero-parameter rules abstain instantly: `Safe_EV_Sunk`: $0.20 \times 174.50 - 125 = -₹90.10 < 0$; `RT_2F_Min`: $0.20 \times 470 - 250 = -₹156.00 < 0 \implies$ **STAY HOME**.
<!-- WORKED_EXAMPLE_END -->

### 3.4 Exact Tail Shortfall (`ES10`) and Corrected Three-Scheme Two-Way Cluster Inference
Following Acerbi–Tasche expected shortfall at $\alpha = 0.10$ (`revision/es10.py`), we sort all $n$ episode outcomes $x_{(1)} \le \dots \le x_{(n)}$ (`0` on abstention) with fractional mass $m = 0.10 n = k + f$ ($k = \lfloor m \rfloor$, $f = m - k$):

$$\text{ES10}(x) = \frac{1}{m}\left(\sum_{i=1}^{k} x_{(i)} + f \cdot x_{(k+1)}\right)$$

<!-- WORKED_EXAMPLE_START -->
> **Worked Example 4 (Exact Fractional `ES10`):** On $\{1, 2, \dots, 11\}$, $m = 1.1$ ($k = 1, f = 0.1$), giving $\text{ES10} = (1 + 0.1 \times 2)/1.1 = 1.2/1.1 \approx 1.09$, unlike unweighted below-quantile averaging (`1.50`).
<!-- WORKED_EXAMPLE_END -->

After fixing a key-prefixing bug uncovered during adversarial review (bare `dest_market` previously lacked `State|` and split physical markets into `336` artificial clusters instead of `172`), **all CIs and tests use `2,000`-replicate paired two-way cluster bootstraps across ALL THREE corrected schemes** (`23` 2-week blocks; Phipson–Smyth $+1$ correction [phipson2010permutation]):
1. **`origin_x_2week`:** `173` origin `State|Market` clusters;
2. **`b2dest_or_origin_x_2week`:** `172` State-prefixed `B2` destination (or origin) clusters;
3. **`policy_dest_or_origin_x_2week`:** `170–173` policy-specific chosen destination (or origin) clusters.

Crucially, **all Holm-Bonferroni FWER adjustments (`p_holm_2s`) reported throughout this paper are standard TWO-SIDED p-values** [holm1979simple] (`p_value_two_sided`), never unlabeled one-sided p-values.

---

## 4. Results

### 4.1 RQ1: Screen-Chasing Loss Incidence and Arrival Outcomes
Across `N = 58,676` test episodes, blindly chasing top lagged spreads > ₹100 (`B1_lagged_screen`, `100.00%` dispatch) loses money on **45.21%** of all episodes (`mean ₹397.87/qtl`, `ES10 −₹641.26/qtl`, Table 2). `a18_outcome_mix.csv` confirms that `69.47%` (`40,765` trips) sell exact variety on arrival day 0, `0.49%` wait 1–2 days to sell, `1.05%` sell another variety on day 2, and **28.98%** (`17,005` trips) encounter zero recorded trade of the commodity (`27.99%` day 0, `0.64%` day 1, `0.35%` day 2) and incur the return branch. Scoring identical trips with 3-day hindsight drops `B1` loss incidence artificially from `45.21%` to `31.35%` (`mean ₹538.96/qtl`).

| Policy (`N = 58,676` Test Episodes) | Free Params | Dispatch (%) | Mean Net (₹/qtl) | Ep. Loss (%) | Cond. Loss (%) | Exact `ES10` (₹/qtl) | Loss Given Loss | Mean km |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **`B1_lagged_screen`** (`lag 1..7`, spread `> 100`) | 1 | `100.00%` | `₹397.87` | `45.21%` | `45.21%` | `−₹641.26` | `−₹271.24` | `224.33` |
| **`B2_age_matched`** (`lag 1..3`, val `₹200`) | 1 | `72.03%` | `₹433.56` | `26.72%` | `37.10%` | `−₹525.25` | `−₹293.73` | `206.80` |
| **`B_simple_activity_matched`** (`rep14>=0.5`, `₹168.04`) | 2 | `70.73%` | `₹440.97` | `23.48%` | `33.20%` | `−₹506.28` | `−₹298.77` | `206.83` |
| **`MG_matched`** (hard `T1..T4`, val `₹131.26`) | 4 | `69.51%` | `₹467.90` | `18.57%` | `26.71%` | `−₹512.78` | `−₹331.27` | `204.08` |
| **`RR_Abstain_matched`** (`k*=5.0`, `m*=₹3.73`) | 2 | `69.02%` | `₹475.36` | `17.23%` | `24.96%` | `−₹460.72` | `−₹308.18` | `182.69` |
| **`RR_Abstain_m0`** (`k*=5.0`, `S_RR > 0`) | 1 | `69.52%` | `₹475.76` | `17.43%` | `25.07%` | `−₹461.74` | `−₹306.48` | `182.67` |
| **`RR_Abstain_phys15_matched`** (`k=1.5`, `₹87.63`) | 1 | `69.75%` | `₹477.95` | `18.82%` | `26.98%` | `−₹483.69` | `−₹311.14` | `193.42` |
| **`Safe_EV_Sunk_m0`** *(0-param champion)* | **0** | **`63.27%`** | **`₹465.59`** | **`14.93%`** | **`23.61%`** | **`−₹344.09`** | **`−₹260.05`** | `196.29` |
| **`Safe_EV_Sunk_matched`** (val-match `70.71%`) | 1 | `70.90%` | `₹469.94` | `18.51%` | `26.11%` | `−₹366.41` | `−₹243.04` | `194.46` |
| **`Safe_EV_Phys_m0`** (`1.5F`, 0 tuned params) | **0** | `60.85%` | `₹462.16` | `13.73%` | `22.57%` | `−₹333.57` | `−₹264.64` | `194.59` |
| **`Safe_EV_Phys_matched`** (val-match `70.71%`) | 1 | `70.54%` | `₹469.68` | `17.98%` | `25.49%` | `−₹360.29` | `−₹241.32` | `193.00` |
| **`RT_2F_Min_m0`** *(Class-8 keypad, NO `cv28`)* | **0** | `64.92%` | **`₹478.38`** | `16.26%` | `25.05%` | `−₹468.32` | `−₹325.70` | `177.24` |
| **`RT_2F_Dow_m0`** *(1-lookback, NO `cv28`)* | **0** | `67.36%` | `₹476.72` | `17.52%` | `26.01%` | `−₹484.97` | `−₹321.75` | `179.37` |
| **`EV_RT_Min_m0`** *(exact 2-state round-trip)* | **0** | `77.20%` | `₹484.82` | `20.46%` | `26.50%` | `−₹515.77` | `−₹308.52` | `190.91` |

### 4.2 RQ2: Zero-Parameter `Safe_EV_Sunk_m0` & `RT_2F_Min_m0` vs Fair Baselines, Hard Gates & Tuned `RR-Abstain`
Tables 2, 3, and 4 establish a clean progression across complexity reduction and statistical rigor:
1. **Hard-Gated `MG_matched` Fails Tail Risk (`p_holm_2s = 1.000`):** At matched `~70%` dispatch, `MG_matched` lifts mean over `B2_age_matched` (`+₹34.34/qtl`, two-sided Holm `p = 0.0120` origin / `0.0550` B2-dest) and cuts episode losses (`−8.15 pp`, `p_holm_2s = 0.0120`), **but worst-10% `ES10` does not improve** (`−₹512.78` vs `−₹525.25`, diff `+₹12.48/qtl`, CI `[−₹16.57, +₹39.97]`, `p_holm_2s = 1.000`). Even tuning `MG`'s hard gates directly for validation `ES10` (`rep28 >= 0.75, dow8 >= 0.35`) reaches only `ES10 −₹445.92` at a severe mean crash (`₹358.44/qtl`, `a18_fair_ablations.csv`).
2. **Tuned `RR_Abstain` Improves `ES10`, Yet Exposes Ceiling Artifact & Severity-When-Wrong:** `RR_Abstain_matched` (`k*=5.0`) improves `ES10` (`−₹460.72`: `+₹64.54` vs `B2_age_matched` and `+₹52.06` vs `MG_matched`, `p_holm_2s = 0.0040` origin/B2-dest and `0.0060` RR-dest), **yet hits the grid ceiling `kappa = 5.0`**, shows worse average severity on losing trips (`loss_given_loss −₹308.18` vs `B1 −₹271.24` and `B2 −₹293.73`), and fails to reach statistical significance on its `+₹7.46` mean gap vs `MG_matched` (`p_2s = 0.241..0.477`) while leaving `H_A10` Apple `ES10` tied. Extending `kappa` up to `20.0` drives `val ES10` to `−₹371.53` only by forcing `m_val = −₹328.99` and losing `₹24.14/qtl` test mean (`₹475.36 -> ₹451.22`).
3. **Zero-Parameter `Safe_EV_Sunk_m0` Crushes `ES10` Without Tuning Anything (Table 3):** By replacing tuned `kappa=5.0` with `p_dow` weekday reliability and adaptive price-drop protection `1 - cv28` against sunk freight `F` (where the `< 2`-observation `0.05` `cv28` fallback affects only `86 / 37,122 = 0.23%` of dispatched rows), **`Safe_EV_Sunk_m0` (`0` free params) strengthens `ES10` to `−₹344.09/qtl` (+₹181.17/qtl over `B2_age_matched`, `p_holm_2s = 0.0040` on all 3 schemes), cuts episode loss to `14.93%` (`−11.79 pp`, `p_holm_2s = 0.0040`), lifts mean gain by `+₹32.03/qtl` (`₹465.59`), and cuts losing-trip severity below every baseline (`loss_given_loss −₹260.05` vs `−₹293.73` `B2` / `−₹308.18` `RR`)!** At equal validation-matched `70.90%` dispatch, `Safe_EV_Sunk_matched` beats `RR_Abstain_matched` by **`+₹94.31/qtl` on `ES10`** (`p_holm_2s = 0.0040` on ALL 3 cluster schemes).
4. **Class-8 Phone-Calculator `RT_2F_Min_m0` Leads on Mean Without `cv28` or Spoilage:** Dropping volatility `cv28` and NABCONS spoilage completely leaves `p_min * G > 2F`, delivering **`₹478.38/qtl` mean** (`+₹44.82/qtl` vs `B2_age_matched`, `p_holm_2s = 0.0040` on all 3 schemes—beating `RR_Abstain_matched` `₹475.36`) and `16.26%` losses!
5. **Fair Feature, Volatility, and Exact Test-Dispatch Controls (Table 4 & Figure 2):** Against `B2` forced to **identical test dispatch (`63.27%`)** (`ES10 −₹500.75`, `ep_loss 23.27%`), `Safe_EV_Sunk_m0` STILL gains **`+₹156.66/qtl` `ES10` and `−8.34 pp` losses**, proving zero dependence on abstention drift. Against a static 10% haircut (`Safe_EV_fixed10pct_m0`, `ES10 −₹444.75`), adaptive `1 - cv28` adds **`+₹100.66/qtl` `ES10`**. Substituting `1.20 * euclid_km` alters `Safe_EV_Sunk_m0` mean by just `−₹0.39` (`₹465.20`) and adding 2024 climatology shifts mean by `−₹2.93` (`₹462.66`, `ES10 −₹335.36`).

| Pre-Registered Hypothesis / Contrast (`N = 58,676`) | Estimate | `origin_x_2week` (`173×23`) CI (`p_holm_2s`) | `b2dest_or_origin` (`172×23`) CI (`p_holm_2s`) | `policy_dest_or_origin` (`171–173×23`) CI (`p_holm_2s`) |
|---|---:|---|---|---|
| **`H_A18_1`:** `ES10(Safe_EV_Sunk_m0) − ES10(B2)` | **+₹181.17** | `[+₹124.77, +₹252.29]` (**0.0040**) | `[+₹109.76, +₹296.29]` (**0.0040**) | `[+₹122.97, +₹265.45]` (**0.0040**) |
| **`H_A18_2`:** `ES10(Safe_EV_matched) − ES10(RR_matched)` | **+₹94.31** | `[+₹41.96, +₹158.72]` (**0.0040**) | `[+₹32.30, +₹201.07]` (**0.0040**) | `[+₹38.55, +₹172.92]` (**0.0040**) |
| **`H_A18_3`:** `EpLoss(Safe_EV_Sunk_m0) − EpLoss(B2)` | **−11.79 pp** | `[−13.47, −10.20] pp` (**0.0040**) | `[−14.78, −9.28] pp` (**0.0040**) | `[−14.38, −9.51] pp` (**0.0040**) |
| **`H_A18_4`:** `Mean(RT_2F_Min_m0) − Mean(B2)` | **+₹44.82** | `[+₹30.35, +₹60.62]` (**0.0040**) | `[+₹21.89, +₹72.88]` (**0.0040**) | `[+₹25.20, +₹67.97]` (**0.0040**) |
| Secondary: `Mean(Safe_EV_Sunk_m0) − Mean(B2)` | **+₹32.03** | `[+₹11.71, +₹52.00]` (`p_2s=0.004`) | `[+₹2.41, +₹66.89]` (`p_2s=0.043`) | `[+₹5.67, +₹62.82]` (`p_2s=0.014`) |
| Secondary: `ES10(Safe_EV_Sunk_m0) − ES10(RR_matched)` | **+₹116.63** | `[+₹63.41, +₹181.36]` (`p_2s=0.001`) | `[+₹53.88, +₹223.03]` (`p_2s=0.001`) | `[+₹62.28, +₹194.04]` (`p_2s=0.001`) |

| Fair Control Ablation (`a18_fair_ablations.csv`) | Disp (%) | Mean (₹/qtl) | Ep. Loss (%) | Exact `ES10` (₹/qtl) | Control Question Answered |
|---|---:|---:|---:|---:|---|
| `B2_test_matched_to_SafeM0` (`th=₹298.92`) | `63.27%` | `₹427.08` | `23.27%` | `−₹500.75` | `Safe_EV_Sunk_m0` beats equal-test-dispatch `B2` by **`+₹156.66 ES10`** |
| `B2_dist_penalty_3F_matched` (no `p_rep`) | `72.98%` | `₹438.01` | `26.67%` | `−₹489.25` | Distance penalty alone achieves `₹489.25`, far short of `−₹344.09` |
| `MG_val_es10_tuned_matched` (`rep28>=0.75`) | `66.55%` | `₹358.44` | `17.91%` | `−₹445.92` | Even `val-ES10`-tuned hard gates crash Mean (`−₹107` vs `Safe_EV`) |
| `RR_rep14_only_matched` (equal 14d info) | `68.94%` | `₹457.63` | `19.86%` | `−₹461.32` | `RR` drops `−₹17.73` mean when restricted to 14d window |
| `Safe_EV_fixed10pct_m0` (`drop = 10%`) | `63.63%` | `₹467.87` | `16.84%` | `−₹444.75` | Adaptive `1 - cv28` outperforms static 10% haircut by **`+₹100.66 ES10`** |
| `Safe_EV_euclid120_m0` (`1.20 * euclid_km`) | `64.32%` | `₹465.20` | `15.52%` | `−₹353.68` | Simple straight-line `×1.20` preserves Mean within `₹0.39/qtl` |

![Risk-coverage curves with 95% cluster confidence bands across B2_age_matched, hard-gated MG, RR_Abstain, and zero-parameter Safe_EV_Sunk alongside B1 and RT_2F_Min](../figures/rev_fig1_risk_coverage_ci.png)

![Fair ablations against Safe_EV_Sunk_m0 and RT_2F_Min_m0 (left) and worst-10% ES10 comparison across Onion, Potato, Tomato, NonApple, and Apple subsets (right)](../figures/rev_fig2_ablations_and_crops.png)

### 4.3 RQ3: Identification Bounds, Subgroup Generalizability, and Stress Audits
1. **Full Manski & Missing-Quote Regimes (`A17` Fix — Table 5 & Figure 3 Right):** Earlier drafts inaccurately called `div = 0.0` "zero missing-quote penalty" even though code still charged `-local * spoil < 0`. Under `div_0.0_spoil_only`, `RR_Abstain_matched`'s `ES10` diff over `B2` collapses to statistically insignificant noise (`+₹9.81`, CI `[−₹23.70, +₹45.94]`, `p_2s = 0.603`), trailing `B_simple_activity` (`−₹349.35` vs `−₹347.95`). Under literal `exact_zero_divert_payoff_0`, `RR` has *worse* episode loss than `B2` (`7.40%` vs `6.55%`, `p_2s = 0.032`). **By contrast, zero-parameter `Safe_EV_Sunk_m0` thrives across EVERY non-MAR missingness regime** (`+₹173.65 ES10` at `div_0.0_spoil_only`; `+₹169.79 ES10` and `4.52%` vs `6.55%` losses at `exact_zero_divert_payoff_0`, both `p_2s = 0.002`). Importantly, under the upper Manski bound where every blank portal row clears as an open auction at `dest_lag_price` (`open_yard_MAR_lagged_price`), we disclose openly that **`B2_age_matched` earns +₹102.58/qtl higher mean** (`₹722.66` vs `₹620.08`, `p_2s = 0.002`)—while `Safe_EV_Sunk_m0` STILL lowers loss incidence (`4.78%` vs `7.08%`) and boosts `ES10` by **+₹190.00/qtl** (`−₹191.91` vs `−₹381.91`, `p_2s = 0.002`). Similarly, restricted purely to realized open `exact_d0` auctions (`n=30,831` `Safe_EV` vs `30,062` `B2`), `Safe_EV_Sunk_m0` cuts `ES10` in half (`−₹307.70` vs `−₹623.62`) and nearly matches `B2`'s mean (`₹924.65` vs `₹930.65`), whereas `RR` trails `B2` by `−₹94.44`.

| Missing-Quote Counterfactual Regime (`a18_missing_regimes.csv`) | `B2_age` (Mean / EpL / `ES10`) | `RR_matched` (Mean / EpL / `ES10`) | `Safe_EV_Sunk_m0` (Mean / EpL / `ES10`) | `RT_2F_Min_m0` (Mean / EpL / `ES10`) |
|---|---|---|---|---|
| `div_2.0_disc_0.10` *(Harsh diversion)* | `₹419.73` / `26.72%` / `−₹593.52` | `₹469.43` / `17.23%` / `−₹506.17` | `₹458.92` / **`14.93%`** / **`−₹400.99`** | **`₹472.57`** / `16.26%` / `−₹513.26` |
| `div_1.5_disc_0.10_base` *(Baseline)* | `₹433.56` / `26.72%` / `−₹525.25` | `₹475.36` / `17.23%` / `−₹460.72` | `₹465.59` / **`14.93%`** / **`−₹344.09`** | **`₹478.38`** / `16.26%` / `−₹468.32` |
| `div_0.0_spoil_only` *(Still `-loc*sp`)* | `₹475.80` / `26.67%` / `−₹359.17` | `₹493.37` / `17.21%` / `−₹349.35` *(NS)* | `₹485.92` / **`14.92%`** / **`−₹185.52`** | **`₹496.01`** / `16.25%` / `−₹352.72` |
| `exact_zero_divert_payoff_0` *(Literal `₹0`)* | `₹477.14` / `6.55%` / `−₹349.01` | `₹494.14` / `7.40%` / `−₹343.03` *(NS)* | `₹486.50` / **`4.52%`** / **`−₹179.22`** | **`₹496.73`** / `6.58%` / `−₹346.08` |
| `open_yard_MAR_lagged_price` *(MAR open)* | **`₹722.66`** / `7.08%` / `−₹381.91` | `₹641.41` / `7.71%` / `−₹359.16` | `₹620.08` / **`4.78%`** / **`−₹191.91`** | `₹630.70` / `6.87%` / `−₹361.51` |
| `realized_exact_d0_dispatched_only` *(Open)* | **`₹930.65`** / `12.10%` / `−₹623.62` | `₹836.21` / `12.33%` / `−₹563.99` | `₹924.65` / **`8.31%`** / **`−₹307.70`** | `₹900.16` / `11.74%` / `−₹608.10` |
| `het_adversarial_lowrep_ok_highrep_harsh` | `₹435.33` / `26.69%` / `−₹569.44` | `₹470.54` / `17.23%` / `−₹503.84` | `₹463.12` / **`14.93%`** / **`−₹385.31`** | **`₹474.43`** / `16.26%` / `−₹508.53` |

2. **All 6 Individual States & All 5 Crop Slices (`a18_crop_and_state_splits.csv`):** Unlike `RR_Abstain_matched` (whose `ES10` CIs cross zero in Maharashtra `[−₹68.87, +₹68.33]` and HP `[−₹19.98, +₹169.84]`), **`Safe_EV_Sunk_m0` achieves strictly positive 95% `ES10` CIs in EVERY ONE of all 6 states**: Gujarat `[+₹138.05, +₹369.11]`, HP `[+₹59.18, +₹637.28]`, Karnataka `[+₹58.23, +₹184.08]`, MP `[+₹139.94, +₹303.97]`, Maharashtra `[+₹48.71, +₹303.07]`, and UP `[+₹48.00, +₹139.86]`, and across **all 5 crop slices** (`NonApple` `N = 52,207`: `+₹135.58` CI `[+₹108.37, +₹165.94]`; Onion `+₹123.49`; Potato `+₹72.31`; Tomato `+₹195.65`; generic Apple `N = 6,469`: `+₹561.37` CI `[+₹172.22, +₹1,216.91]`). Transparently, on **mean net gain** vs `B2_age_matched`, `Safe_EV_Sunk_m0`'s 95% CIs cross zero in Gujarat (`₹344.63` vs `₹346.29`, CI `[−₹49.29, +₹36.56]`), Maharashtra (`CI [−₹5.58, +₹36.32]`), UP (`CI [−₹3.18, +₹27.00]`), Tomato (`₹461.42` vs `₹462.27`, CI `[−₹34.58, +₹28.50]`), and Apple (`CI [−₹24.81, +₹245.04]`) due to conservative high-volatility abstention—whereas zero-parameter **`RT_2F_Min_m0`** beats `B2`'s point mean in all 6 states and all 5 crop slices (`Tomato ₹504.35`).
3. **18-Scenario Frozen & Re-Scored Tornado (`a18_tornado.csv`):** Across all 18 scenarios (`NITI ₹0.258/km` floor, LCV `₹0.75/km`, steep `₹1.20/km`, HP `1.00–1.75`, *arhtiya* `2–6%`, `buyer_paid_0%`, `spoil 0.5–2x`, `detention 0–100`, `joint_optimistic`, `joint_harsh`, `outside_origin_lag`) under BOTH frozen decisions and re-scored policies (`36` cells), **`Safe_EV_Sunk_m0` beats `B2_age_matched` in 36 of 36 cells on BOTH Mean (`+₹13.31` to `+₹61.11`) AND `ES10` (`+₹144.94` to `+₹329.37`)**, with ZERO sign flips.
4. **Structural Integrity & Unconditional Origin Panel (`a18_settlement_and_robustness.csv`):** `Safe_EV_Sunk_m0` dominates `B2_age_matched` across `exact_geocode_corridors_only` (`N = 40,690` episodes retaining exact-geocoded corridors after dropping centroid candidates: `ES10 −₹364.46` vs `−₹556.97`, ep_loss `13.33%` vs `24.38%`; all-5 exact episodes `N = 18,189` behave similarly), `non_conflicting_dup_episodes_only` (`N = 56,857`: `−₹343.85` vs `−₹520.66`), `origin_lag_age_1_3_only` (`N = 56,648`: `−₹339.91` vs `−₹522.40`), `hindsight_3d` (`−₹281.99` vs `−₹591.16`), and critically on the **`N = 88,014` unconditional origin panel** restoring all `29,338` unreported day-$t$ origin episodes (`Safe_EV_Sunk_m0`: Mean `₹483.03` vs `₹445.37`, EpLoss `15.22%` vs `28.10%`, **`ES10 −₹335.04` vs `−₹515.93`**; `RT_2F_Min_m0`: Mean **`₹493.15`**).
5. **HP Graded Apples (`a18_hp_apple.csv` — `R6` Stress Check):** Across `N = 2,802` lagged HP graded-apple episodes (`2025-11..2026-08`), zero-parameter **`Safe_EV_Sunk_m0` (`67.45%` disp) resolves `MG_matched` vs `RR` tradeoffs cleanly**: it achieves Mean **`₹1,354.85`** (vs `B2` `₹1,199.31`, `MG_matched` `₹1,028.05`, `RR` `₹1,318.60`) and cuts `ES10` to **`−₹1,454.86`** (`+₹937.26` over `B2` `−₹2,392.12`, `+₹498.34` over `MG_matched` `−₹1,953.20`, `+₹710.87` over `RR` `−₹2,165.73`—and `Safe_EV_Phys_m0` hits `−₹1,376.71`), holding into June–August 2026 (`₹2,010.20` mean, `−₹2,479.28` vs `B2 −₹4,071.95` and `MG −₹2,720.72`). Still, `41.38%` of dispatched HP apple trips lose money (`−₹1,454.86` tail), so high-variance graded apples require live buyer confirmation before dispatch.

![Re-scored parameter sensitivity tornado across 10 freight/commission scenarios (left) and ES10 across complete missing-quote and Open-MAR identification bounds (right)](../figures/rev_fig3_sensitivity_tornado_and_missing.png)

![ES10 across sequential, hindsight, exact-geocode, and N=88,014 unconditional origin panels (left) and lagged HP graded-apple holdout performance (right)](../figures/rev_fig4_settlement_and_hp_apple.png)

---

## 5. Related Work and Surviving Novelty Claim

Prior agricultural economics literature established that spreads below transfer costs yield no arbitrage [baulch1997transfer] and that raw price SMS blasts frequently underdeliver when transport or intermediary barriers bind [fafchamps2012sms, mitra2018asymmetric, mahajan2021covid], whereas real-time phone coordination reduces price waste [jensen2007digital]. Applied agricultural CS studies forecast portal prices [madaan2019price, guo2020mandi] or impute blank rows via matrix/factor models [ma2019price, deka2026missing], minimizing forecast RMSE without pricing sequential non-reporting arrival risk or tail expected shortfall. Reject-option classification [chow1970optimum, franc2023optimal], partial identification bounds [manski1990bounds, horowitz2000nonparametric, kallus2021minimax], and cost-sensitive operational optimization [ban2019bigdata] provide the underlying mathematical building blocks, while conformal selection/CRC methods [jin2023selection, angelopoulos2024conformal] require exchangeable data and action-independent risk denominators absent here.

**Minimal Surviving Applied Contribution (`A18` + `A12`):** Claiming zero new mathematical theorems or neural architectures, this study proves in a leak-free (`<= t - 1`), sequentially settled retrospective audit (`N = 58,676`, plus `N = 88,014` unconditional origin robustness) that **replacing black-box trees, hard activity cutoffs, and tuned penalties with two zero-hyperparameter expected-value rules—weekday-reliability-weighted 1-SD spread minus sunk freight (`Safe_EV_Sunk_m0`, $p_{\text{dow}} G_{\text{1SD}} > F$) and round-trip spread rule (`RT_2F_Min_m0`, $p_{\min} G > 2F$)—eliminates tuning parameters while cutting `ES10` losses by `+₹181.17/qtl` over equal-age road dispatch (`p_holm_2s = 0.0040`) and `+₹116.63/qtl` over tuned `RR-Abstain` across every state and crop**.

---

## 6. Explicit Limitations and Non-Claims (`R6` & `R7`)

Eight binding boundaries govern interpretation and deployment:
1. **Modeled Payoffs $\ne$ Farmer Cash Income (`R7`):** Zero physical freight bills, weighment losses, or mandi auction *patti* slips exist in AGMARKNET; freight, loading (`₹35`), detention (`₹25`), and `Q10` decay are survey-anchored approximations (`NITI Aayog`, `NABCONS`, `GoHP`), not household cash profits.
2. **A Missing Portal Quote $\ne$ A Locked Yard (`R7`):** Blank arrival rows show no uploaded record, not physical closure. Under upper-bound Open-MAR upload omissions, `B2` earns `+₹102.58/qtl` higher mean than `Safe_EV_Sunk_m0`, though `Safe_EV` still cuts losses (`4.78%` vs `7.08%`) and boosts `ES10` (`+₹190.00`).
3. **Alert-Triage Scope Prior to Phone Confirmation (`A17` #10):** Because a 30-second phone call to a destination *arhtiya* can resolve whether a yard is trading before departure—leaving pure open-market price risk where `B2` and `Safe_EV_Sunk_m0` earn similar open-auction means (`₹930.65` vs `₹924.65`, though `Safe_EV` cuts open `ES10` in half)—our rules act as an **upstream portal-alert filter**, not a substitute for human trader confirmation.
4. **Exploratory Calendar Exposure (`Gate J = BLOCKED`):** Bulk official archives end `2026-04-13` (`api.agmarknet.gov.in` exposes only a 7-day rolling modal snippet), so `PREREG_A10.md` and `PREREG_A18.md` are **locked exploratory follow-up protocols** on a previously exposed 2025–2026 calendar, not untouched prospective trials.
5. **Day-$t$ Origin Conditioning Disclosed:** Primary tables condition on day-$t$ origin publication (`58,676` of `88,014` unconditional shortlisted test episodes); we report the full `88,014`-episode unconditional panel cleanly alongside primary results (`Safe_EV_Sunk_m0` `ES10 −₹335.04` vs `−₹515.93`).
6. **Residual Graded-Apple & Tomato Volatility (`R6`):** Although `Safe_EV_Sunk_m0` slashes HP Apple `ES10` from `−₹2,392.12` to `−₹1,454.86`, `41.38%` of dispatched apple trips still lose money; on `Tomato`, `Safe_EV_Sunk_m0` leaves mean flat (`₹461.42` vs `₹462.27`) while slashing tail risk (`+₹195.65 ES10`).
7. **District Centroids, Conflicts, & Partial Equilibrium:** `41.71%` of rows touch district-centroid coordinates and `3,096` episodes touch conflicting duplicates (verified stable when restricted to exact geocodes and clean keys); mass simultaneous FPO coordination would also induce price slippage not modeled here.
8. **Validation Calibration / Zero-Param Heuristic $\ne$ Conformal Guarantee (`R7`):** Zero conformal coverage guarantees are claimed (`Stage I H2` inconclusive at `+₹6.13`, `p_holm = 0.2699`).

---

## 7. Conclusion and Full Cleanroom Reproducibility

Tempting online mandi spreads lose money nearly half the time (`45.21%`) under strict lagged decision timing and sequential arrival settlement. Stripping away black-box pickles, weather leaks, conformal overclaims, and tuned `kappa` multipliers yields **`Safe_EV_Sunk_m0`** ($p_{\text{dow}} G_{\text{1SD}} > F$) and Class-8 **`RT_2F_Min_m0`** ($p_{\min} G > 2F$)—zero-hyperparameter rules verifiable on any calculator that reduce worst-10% tail losses (`+₹181.17/qtl`, `p_holm_2s = 0.0040`) across all six states and crops under **1-command clean-clone reproduction (`make reproduce`, `0.0000` numeric discrepancy, `0` untraceable numbers)**, ready for prospective FPO field piloting.

---

## References
- `[baulch1997transfer]` Baulch, B. (1997). Transfer costs, spatial arbitrage, and testing for food market integration. *AJAE* 79(2), 477–487. DOI: `10.2307/1244145`
- `[jensen2007digital]` Jensen, R. (2007). The digital provide: Information, market performance, and welfare in the South Indian fisheries sector. *QJE* 122(3), 879–924. DOI: `10.1162/qjec.122.3.879`
- `[goyal2010information]` Goyal, A. (2010). Information, direct access to farmers, and rural market performance in Central India. *AEJ: Applied Economics* 2(3), 22–45. DOI: `10.1257/app.2.3.22`
- `[fafchamps2012sms]` Fafchamps, M., & Minten, B. (2012). Impact of SMS-based agricultural information on Indian farmers. *WBER* 26(3), 383–414. DOI: `10.1093/wber/lhr056`
- `[mitra2018asymmetric]` Mitra, S., Mookherjee, D., Torero, M., & Visaria, S. (2018). Asymmetric information and middleman margins: An experiment with Indian potato farmers. *REStat* 100(1), 1–13. DOI: `10.1162/rest_a_00699`
- `[mahajan2021covid]` Mahajan, K., & Tomar, S. (2021). COVID-19 and supply chain disruption: Evidence from food markets in India. *AJAE* 103(1), 35–52. DOI: `10.1111/ajae.12158`
- `[madaan2019price]` Madaan, L., et al. (2019). Price forecasting & anomaly detection for agricultural commodities in India. *ACM COMPASS '19*, 52–64. DOI: `10.1145/3314344.3332488`
- `[ma2019price]` Ma, W., et al. (2019). An interpretable produce price forecasting system for small and marginal farmers in India. *ICTD '19*, 1–11. DOI: `10.1145/3287098.3287100`
- `[guo2020mandi]` Guo, H., Woodruff, A., & Yadav, A. (2020). Improving lives of indebted farmers using deep learning. *AAAI-20*, 34(08), 13294–13299. DOI: `10.1609/aaai.v34i08.7039`
- `[deka2026missing]` Deka, P. (2026). Reconstructing missing mandi prices in North-East India with regional factors. *arXiv:2610.39949*. DOI: `10.48550/arxiv.2610.39949`
- `[chow1970optimum]` Chow, C. K. (1970). On optimum recognition error and reject tradeoff. *IEEE Trans. Info. Theory* 16(1), 41–46. DOI: `10.1109/TIT.1970.1054406`
- `[franc2023optimal]` Franc, V., Prusa, D., & Voracek, V. (2023). Optimal strategies for reject option classifiers. *JMLR* 24(11), 1–49. URL: `https://jmlr.org/papers/v24/21-0048.html`
- `[manski1990bounds]` Manski, C. F. (1990). Nonparametric bounds on treatment effects. *AER* 80(2), 319–323. URL: `https://www.jstor.org/stable/2006592`
- `[horowitz2000nonparametric]` Horowitz, J. L., & Manski, C. F. (2000). Nonparametric analysis of randomized experiments with missing covariate and outcome data. *JASA* 95(449), 77–84. DOI: `10.1080/01621459.2000.10473902`
- `[ban2019bigdata]` Ban, G.-Y., & Rudin, C. (2019). The big data newsvendor: Practical insights from machine learning. *Operations Research* 67(1), 90–108. DOI: `10.1287/opre.2018.1757`
- `[kallus2021minimax]` Kallus, N., & Zhou, A. (2021). Minimax-optimal policy learning under unobserved confounding. *Management Science* 67(5), 2870–2890. DOI: `10.1287/mnsc.2020.3699`
- `[jin2023selection]` Jin, Y., & Candès, E. J. (2023). Selection by prediction with conformal p-values. *JMLR* 24(244), 1–41. URL: `https://jmlr.org/papers/v24/22-1176.html`
- `[angelopoulos2024conformal]` Angelopoulos, A. N., et al. (2024). Conformal risk control. *ICLR 2024*. URL: `https://openreview.net/forum?id=uPD0kqYEfS`
- `[nabcons2022phl]` NABCONS (2022). *Post-Harvest Losses of Agri Produces in India*. MoFPI, GoI (PIB `PRID=2151371`).
- `[nitiaayog2021freight]` NITI Aayog & RMI (2021). *Fast Tracking Freight in India*. Government of India.
- `[rbi2024top]` Roy, R., et al. (2024). *Vegetables Inflation in India: A Study of Tomato, Onion and Potato (TOP)*. RBI Working Paper Series No. 08/2024.
- `[kader2002postharvest]` Kader, A. A. (Ed.) (2002). *Postharvest Technology of Horticultural Crops* (3rd ed.). UC ANR Pub. 3311.
- `[gross2016usda66]` Gross, K. C., Wang, C. Y., & Saltveit, M. (2016). *The Commercial Storage of Fruits, Vegetables, and Florist and Nursery Stocks*. USDA ARS AH-66.
- `[hersbach2020era5]` Hersbach, H., et al. (2020). The ERA5 global reanalysis. *QJRMS* 146(730), 1999–2049. DOI: `10.1002/qj.3803`
- `[luxen2011osrm]` Luxen, D., & Vetter, C. (2011). Real-time routing with OpenStreetMap data. *ACM SIGSPATIAL*, 513–516. DOI: `10.1145/2093973.2094062`
- `[phipson2010permutation]` Phipson, B., & Smyth, G. K. (2010). Permutation p-values should never be zero. *Stat. Appl. Genet. Mol. Biol.* 9(1). DOI: `10.2202/1544-6115.1585`
- `[holm1979simple]` Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scand. J. Stat.* 6(2), 65–70.
