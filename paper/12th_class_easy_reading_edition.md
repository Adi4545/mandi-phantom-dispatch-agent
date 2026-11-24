# MandiGuard (Class-12 Pocket-Calculator Edition — Revision v7 Audited)

> **Verified Edition Note:** Synced to `paper/manuscript.md` (`Revision v7`, Aditya Sharma, supervised by Dr. Sonia, Shoolini University, Solan, HP; `59/59` verified citations and `0` untraceable numbers across `23/23` docs). Earlier black-box ML trees (`HistGradientBoostingRegressor`), pseudo-conformal theorems, leaked ERA5 weather in decisions, and tuned penalty cutoffs (`kappa* = 5.0`) have been retired in favor of zero-tuned-parameter lower-bound equations (`7` fixed structural choices) a student or FPO manager can verify with a pocket calculator (`final/DIFFICULTY.md`: complexity cut `4.3 -> 1.2 / 5`).

---

## 1. Why Yesterday's High Screen Price Tricks a Truck Driver

Imagine managing a tomato cooperative. At 6 a.m. (`<= t - 1` quotes only—never today's price!), yesterday's portal shows `₹1,500/qtl` at home vs `₹2,000/qtl` at another mandi `200 km` away. Across **`57,634`** test episodes on the zero-lookahead `2024`-selected `171`-market panel (`2025-06-01..2026-04-08`), blindly sending trucks to the top lagged gap (`B1_lagged_screen`) loses money on **`45.07%`** of days (`ES10 −₹642.15/qtl`), and **`28.67%`** (`16,524` trips) arrive on a day with zero uploaded commodity trade (`no_comm_divert`).

Three real costs explain why:
1. **Road Freight (`F`):** Loading (`₹35`) plus `₹0.45 * hp * road_km` (`hp = 1.45` in Himachal Pradesh due to `91.59%` single-lane roads; stylized `30 qtl` load assumption).
2. **Stylized Regulatory Fees & Operational Decay:** Stylized destination seller-fee tiers (`0.5%–1.5%`, `0` inside the same district or if diverted unsold) anchored qualitatively to state APMC deregulation regimes (PIB `relid=154554`), plus operational 24-hour transit decay (`0.86%–3.25%`) calibrated from NABCONS cumulative `"Total loss in market level"` shares (PIB `PRID=2151371`).
3. **Monday–Sunday Closing Gaps & Price Swings:** Mandis closed on Sundays still look open under a 28-day rolling average, while volatile markets bounce sharply (`dest_price_cv_28d`).

---

## 2. Two Zero-Tuned-Parameter Pocket-Calculator Rules (NO Magic Tuning!)

Both rules work on identical `1..3`-day lagged quotes without live weather, ML pickles, or `kappa` grid searches:

### Option A (`Safe_EV_Sunk_m0` — Scientific & Tail-Risk Champion, 0 Free Params)
- Count how often in the last 8 same-weekdays (`dow8`) the destination posted your exact variety: `p_dow = (k + 1) / 10`.
- Compute the 1-SD conservative spread subtracting recent price volatility `cv28`: `G_1SD = P_dest*(1 - cv28)*(1 - fee) - P_orig`.
- **Rule:** Dispatch **only if** `p_dow * G_1SD - F > 0` (ratio form: `G_1SD / F > 1 / p_dow`). (Its settlement-matched sibling `Safe_EV_Phys_m0` uses `1.5F` return cost with zero tuned parameters.)

### Option B (`RT_2F_Min_m0` — Class-8 4-Function Phone Calculator, NO `cv28`, NO Spoilage!)
- Take `p_min = min(rep28, dow8)` (worse of last 28 days and last 8 same-weekdays) and plain fee-adjusted spread `G = P_dest*(1 - fee) - P_orig`.
- **Rule:** Dispatch **only if** `p_min * G - 2 * F > 0` (*"Multiply your gain by the chance the mandi reports; make sure it beats round-trip freight (`2F`)!"*).

<!-- WORKED_EXAMPLE_START -->
> **Worked Arithmetic Example (10 Seconds on a Phone Calculator):**  
> Take a `200 km` Madhya Pradesh tomato route (`fee = 1.5%`, `F = 35 + 0.45 * 200 = ₹125`), `P_orig = ₹1,500`, `P_dest = ₹2,000`, recent price swing `cv28 = 0.15`:
> - Plain fee-adjusted spread: `G = 2,000 * 0.985 - 1,500 = +₹470/qtl`.
> - 1-SD conservative spread: `G_1SD = 2,000 * (1 - 0.15) * 0.985 - 1,500 = +₹174.50/qtl`.
> - **Steady Weekday Yard (`dow8 = 0.90`, `p_min = 0.85`):**  
>   - `Safe_EV_Sunk_m0`: `0.90 * 174.50 - 125 = +₹32.05 > 0` -> **DISPATCH!**  
>   - `RT_2F_Min_m0` (needs no `cv28`): `0.85 * 470 - 250 = +₹149.50 > 0` -> **DISPATCH!**
> - **Sunday-Closed / Sporadic Yard (`dow8 = 0.20`, `p_min = 0.20`):** Road baseline `B2` gives identical `+₹345` (`470 - 125`) and dispatches blindly! Both zero-param rules abstain immediately: `0.20 * 174.50 - 125 = −₹90.10 < 0` and `0.20 * 470 - 250 = −₹156.00 < 0` -> **STAY HOME!**
<!-- WORKED_EXAMPLE_END -->

---

## 3. Verified Results (`171`-Mkt Primary `N = 57,634` + Clean `166`-Mkt `2018–2023` `N = 383,952`)

| Policy (`171`-Mkt Equal Menu, `20°C` Closed-Yard) | Free Params | Dispatch (%) | Mean Net (₹/qtl) | Ep. Loss (%) | Exact `ES10` / `cond_ES10` (₹/qtl) |
|---|---:|---:|---:|---:|---:|
| **`B1_lagged_screen`** (`spread > 100`, `1..7`d) | 1 | `100.00%` | `₹384.61` | `45.07%` | `−₹642.15` / `−₹642.15` |
| **`B2_age_matched`** (`road + fee > ₹200`, `1..3`d) | 1 | `71.73%` | `₹419.62` | `26.43%` | `−₹524.78` / `−₹628.37` |
| **`MG_matched`** (Hard gates `T1–T2`, ML-stripped, `₹133.03`) | 4 | `69.16%` | `₹454.07` | `18.35%` | `−₹508.72` / `−₹638.55` |
| **`RR_Abstain_matched`** (Tuned `kappa* = 5.0`, `₹5.40`) | 2 | `68.75%` | `₹461.41` | `17.07%` | `−₹459.46` / `−₹584.66` |
| **`Safe_EV_Sunk_m0`** (`p_dow * G_1SD > F`) | **0** | **`63.23%`** | **`₹452.74`** | **`14.88%`** | **`−₹345.53` / `−₹447.48`** |
| **`Safe_EV_Phys_m0`** (`1.5F`, `0` tuned params) | **0** | `60.84%` | `₹449.52` | **`13.70%`** | **`−₹334.80` / `−₹447.33`** |
| **`RT_2F_Min_m0`** (`p_min * G > 2F`) | **0** | `64.79%` | **`₹463.98`** | `16.21%` | `−₹464.84` / `−₹618.35` |

- **Locked `PREREG_A18.md` Four-Test Inference (`R = 2,000`, `p_holm_2s_prereg4 = 0.0040`):** Across all three clustering schemes (`166` origin, `166` B2-dest, `165–166` policy-dest $\times$ `23` fortnights), `Safe_EV_Sunk_m0` improves `ES10` over `B2_age_matched` by **`+₹179.24/qtl`** (`−₹345.53` vs `−₹524.78`) and conditional dispatched **`cond_ES10` by `+₹180.89/qtl`** (`−₹447.48` vs `−₹628.37`), cuts losses by **`−11.56 pp`**, beats tuned `RR` (`+₹91.67` matched), and Class-8 **`RT_2F_Min_m0`** raises Mean by **`+₹44.36/qtl`**. Holds under realized ERA5 settlement (`+₹187.80/qtl` `ES10`), `<= t-2` portal lag (`N = 57,047`: `Safe_EV p = 0.001` vs `RT_2F cond_ES10 p = 0.9805` NS), coupled `S6_Frozen x Stoch_CondMAR_p1.00` (`+₹366.85 cond_ES10`), retrained ML/OR Pareto, and `N = 86,054` unconditional origins (`−₹336.19` vs `−₹513.75`).
- **Clean `166`-Mkt `2018–2023` Archive (`N = 383,952`, Zero Retuning):** Removing all `7` post-`2024` lookahead markets leaves `166` clean markets (`+₹35.00` Mean, `−12.57 pp` loss, `+₹169.27 ES10`, **`+₹155.08 cond_ES10`**, `+₹174.27` vs equal-dispatch `B2_eq_SafeM0`, `p = 0.001`; `115`-mkt `N = 325,993` `+₹159.83 ES10`; NASA POWER `₹330.84` vs `₹291.41`), beating `B2` on `ES10` & `cond_ES10` in **`6/6` years** while `2020` (`p = 0.208`) and `2023` (`p = 0.077`) Means are NS.
- **Exact Silent-Market Break-Even:** `B2` catches `Safe_EV_Sunk_m0` on Mean only if silent arrival markets average **`+₹348.61/qtl` above turn-back** (or **`+₹117.97/qtl`** flat profit, or **`25.45%`** Open-MAR share; `26.65%` under ERA5).

---

## 4. Honest Boundaries for Field Defense (`R6` & `R7`)

1. **Automated 6 a.m. Alert Filter Before Phone Calls (`A17`):** Under free turn-back (`div = 0.0` or literal `₹0`), `Safe_EV` Mean gain (`+₹12.03` / `+₹11.21`, `p = 0.220–0.256`) is non-significant while `ES10` keeps `+₹174.40`/`+₹169.82`. Under Open-MAR, `B2` earns `+₹97.01/qtl` higher Mean while `Safe_EV` keeps `+₹189.97` `ES10`; under `hindsight_3d`, `B2` earns `₹549.81` vs `Safe_EV ₹533.14` Mean; coupled Manski `Supp1..3` Means turn negative (`−₹124.95` to `−₹325.40`), and `10%` SUTVA crowding lowers `Safe_EV` Mean to `−₹5.31`.
2. **Subgroup Fragility & Graded Apples (`R6`):** `Safe_EV` wins unconditional `ES10` in `6/6` states & `5/5` slices vs `B2` (trails `RR` by `−₹17.20` on Potato `ES10`), yet **HP (`B = 12`) fails significance on `cond_ES10` (`p = 0.1239`)**, Apple is borderline (`p = 0.0550`), and Mean CIs cross zero in GJ, MH, UP, Tomato, and Apple. On HP Graded Apples (`N = 2,802`), `41.38%` of dispatched trips lose money and `cond_ES10` (`p = 0.0940`) is NS.
3. **No Live Field Telemetry Yet (`Gate J = BLOCKED`):** Bulk AGMARKNET stops `2026-04-13`; a prospective FPO truck-slip & call-log pilot is the next phase.
