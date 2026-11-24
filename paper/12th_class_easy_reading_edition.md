# MandiGuard (Class-12 Pocket-Calculator Edition — Revision v8 Audited)

> **Verified Edition Note:** Synced to `paper/manuscript.md` (`Revision v8 — Honest Candidate C Synthesis`, **Aditya Sharma (M.Tech Thesis Research, supervised by Dr. Sonia) — Shoolini University**, Solan, HP; `59/59` verified citations and `0` untraceable numbers across `23/23` docs). Earlier black-box ML prototypes leaked ERA5 weather or failed from 5-month off-season training starvation, quadratic $\text{INR}^2$ penalties, and homoscedastic conformal widths; Revision v8 shows both fixed heteroscedastic Split-CQR and full-season 17-month ML perform strongly, while our **zero-tuned-parameter lower-bound equations (`9` fixed structural choices incl. `z = 1.0`)** capture `~98.8%` of full-season `17m` ML Mean and `~94%` of `cond_ES10` tail protection with zero training history so a student or FPO manager can compute them on a pocket calculator (`final/DIFFICULTY.md`: complexity cut `4.3 -> 1.2 / 5`).

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
- **Rule:** Dispatch **only if** `p_dow * G_1SD - F > 0` (algebraically identical to `p_dow * (G_1SD - F) + (1 - p_dow) * (-1.0 * F) > 0`, treating closure payoff as sunk outbound freight `-1.0F` rather than literal `0`; ratio threshold: `G_1SD / F > 1 / p_dow`). (Its settlement-matched sibling `Safe_EV_Phys_m0` uses `1.5F` return cost with zero tuned parameters.)

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

- **Specification-Locked Exploratory `PREREG_A18.md` Four-Test Inference (`R = 2,000`, `p_holm_2s_prereg4 = 0.0040`):** Across all three clustering schemes (`166` origin, `166` B2-dest, `165–166` policy-dest $\times$ `23` fortnights), `Safe_EV_Sunk_m0` improves `ES10` over `B2_age_matched` by **`+₹179.24/qtl`** (`−₹345.53` vs `−₹524.78`), conditional dispatched **`cond_ES10` by `+₹180.89/qtl`** (`−₹447.48` vs `−₹628.37`), and the common dispatched intersection `D_S ∩ D_B` (`n = 33,398`) by `+₹65.66` Mean (`₹773.38` vs `₹707.72`) and `+₹53.40` `ES10` (`−₹464.82` vs `−₹518.22`, while pruning `7,944` `B2`-only trips averaging `₹68.96` / `58.60%` loss / `−₹1,018.70 ES10`). `Safe_EV_Sunk_m0` cuts losses by **`−11.56 pp`**, beats tuned `RR` (`+₹91.67` matched), and Class-8 **`RT_2F_Min_m0`** raises Mean by **`+₹44.36/qtl`**. In the `2×2` orthogonal decomposition (`v7_exp4`), `cv28` volatility filtering alone (`Ortho_Pure_cv28_only`, `71.91%`, `₹421.62 / −₹387.46 / −₹447.13`) drives ~100% of `cond_ES10` truncation, whereas `p_dow` (`Ortho_Pure_pdow_only`, `84.10%`, `₹466.68 / −₹546.75 / −₹607.18`) drives Mean lift and diversion avoidance. Holds under realized ERA5 settlement (`+₹187.80/qtl` `ES10`), `<= t-2` portal lag (`N = 57,047`: `Safe_EV p = 0.001` vs `RT_2F cond_ES10 p = 0.9805` NS), coupled `S6_Frozen` (`₹307.39 / −₹576.57 / −₹725.73` vs `B2 ₹247.15 / −₹832.00 / −₹969.71`; `Stoch_CondMAR_p1.00` `+₹366.85 cond_ES10`: `−₹595.27` vs `−₹962.12`), non-collided exact geocode (`35.23%` true exact coverage after fixing `56/171` collided / `33/171` falsely `"market_exact"` yards; `N = 6,605`: `₹194.97` vs `₹200.37`, `8.30%` vs `17.38%` loss, `ES10 −₹231.27` vs `−₹449.14`, `p = 0.001`; `cond_ES10 −₹497.57` vs `−₹687.18`, `p = 0.019`), and `N = 86,054` unconditional origins (`−₹336.19` vs `−₹513.75`). Meanwhile, fixed heteroscedastic Split-CQR (`MG_Intact_matched`, `s80 = 0.53`, `8,848` switches) reaches `cond_ES10 −₹414.44` (`66.32%`, `₹356.78`), `5m Q20_matched63` hits `−₹403.95` (`58.80%`), and full-season `17m` (`n = 113,374`) `MeanQ10_Hybrid` reaches `₹455.83 / −₹420.57` (`NoSafeEV` `₹458.27 / −₹423.88` without `safe_ev_feat`), while `Safe_EV_Sunk_m0` matches `~98.8%` of `17m` Mean and `~94%` of `cond_ES10` with zero training data.
- **Clean `166`-Mkt `2018–2023` Archive (`N = 383,952`, Zero Retuning):** Reverse-survivorship removes `481/647` historical yards absent from the `2024` frame plus `7` post-`2024` lookahead markets, leaving `166` clean markets (`+₹35.00` Mean, `−12.57 pp` loss, `+₹169.27 ES10`, **`+₹155.08 cond_ES10`**, `+₹174.27` vs equal-dispatch `B2_eq_SafeM0`, `p = 0.001`; `115`-mkt `N = 325,993` `+₹159.83 ES10`; NASA POWER × Sched #7 `₹328.15` vs `₹284.26`, `ES10 −₹363.00` vs `−₹567.71`, `cond_ES10 −₹507.15` vs `−₹693.39`), beating `B2` on `ES10` & `cond_ES10` in **`6/6` years** while `2020` (`p = 0.208`) and `2023` (`p = 0.077`) Means are NS.
- **Exact Silent-Market Break-Even:** `B2` catches `Safe_EV_Sunk_m0` on Mean only if silent arrival markets average **`+₹348.61/qtl` above turn-back** (or **`+₹117.97/qtl`** flat profit, or **`25.45%`** Open-MAR share; `26.65%` under ERA5).

---

## 4. Honest Boundaries for Field Defense (`R6` & `R7`)

1. **Automated 6 a.m. Alert Filter Before Phone Calls (`A17`):** Under `PhoneCall_TopK_Open` (`Safe_EV ₹501.09 / −₹204.98 / −₹355.07`, `Pure_cv28 ₹517.49 / −₹249.12 / −₹396.59`, `B2 ₹527.55 / −₹440.72 / −₹691.79`), pre-screening alerts ahead of trader calls protects tails cleanly. Under free turn-back (`div = 0.0` or literal `₹0`), `Safe_EV` Mean gain (`+₹12.03` / `+₹11.21`, `p = 0.220–0.256`) is non-significant while `ES10` keeps `+₹174.40`/`+₹169.82`. Under Open-MAR, `B2` earns `+₹97.01/qtl` higher Mean while `Safe_EV` keeps `+₹189.97` `ES10`; under `hindsight_3d`, `B2` earns `₹549.81` vs `Safe_EV ₹533.14` Mean; coupled Manski `Supp1..3` Means turn negative (`−₹124.95` to `−₹325.40`, while coupled `cond_ES10` stays positive in `Supp1` `[+₹152.20, +₹328.28]` & `Supp2` `[+₹105.96, +₹394.89]`), `Outsider_MinPrice_LCV_4pctArh` drops Mean to `₹102.62` (`34.29%` loss, `cond_ES10 −₹1,290.83` vs `B2 ₹33.86 / −₹1,573.13`), and `10%` SUTVA crowding lowers `Safe_EV` Mean to `−₹5.31`.
2. **Subgroup Fragility, UP `q10=0` Atom, & Graded Apple Scale Non-Invariance (`R6`):** `Safe_EV` wins unconditional `ES10` in `6/6` states & `5/5` slices vs `B2` (trails `RR` by `−₹17.20` on Potato `ES10`; UP `7.28% < 10%` loss rate creates an unconditional `q10 = 0` atom requiring `cond_ES10`), yet **HP (`B = 12`, `g_star_block = 1.535` warning) fails significance on `cond_ES10` (`p = 0.1239`, `p_cgm_gstar = 0.29947`, `p_stud = 0.18791`)**, Apple is borderline (`p = 0.0550`, `p_cgm_gstar = 0.07443`, `p_stud = 0.05947`), and Mean CIs cross zero in GJ, MH, UP, Tomato, and Apple. On HP Graded Apples (`N = 2,802`), `F/G_1SD < 0.10` on `79.52%` of dispatches so `Safe_EV_Sunk_m0` loses leverage (`41.38%` cond. loss, `cond_ES10 −₹2,003.68`, `p = 0.0940` NS); explicit 24-hour spoilage `ScaleInv_Safe_EV_24tau` cuts `ep_loss` `27.91% -> 17.92%` (`cond_ES10 −₹1,616.08`).
3. **No Live Field Telemetry Yet (`Gate J = BLOCKED`):** Bulk AGMARKNET stops `2026-04-13`; a prospective FPO truck-slip & call-log pilot is the next phase.
