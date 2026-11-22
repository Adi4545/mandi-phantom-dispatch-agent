# MandiGuard Revision v5 — Plain-English Complete Guide (Class-12 Level)

> **Note (`C2` & `R2`):** This guide aligns strictly with `paper/manuscript.md` (`Revision v5`). All legacy `cvar_10`, ML pickles, leaked weather, and even tuned `kappa*=5.0` formulas have been replaced by **zero-parameter Class-10 arithmetic**.

## 1. The Everyday Problem
Imagine checking AGMARKNET at 6 a.m.: local Tomato pays `₹1,500/qtl`, while a mandi `200 km` away listed `₹2,000/qtl` yesterday (`<= t - 1`). Yet across **`58,676`** test episodes (`2025-06-01..2026-04-08`), blindly chasing top spreads (`B1_lagged_screen`) loses money **`45.21%`** of the time (`mean ₹397.87/qtl`, worst-10% `ES10 −₹641.26/qtl`) because of road freight (`₹35 + ₹0.45 * hp * km`), destination APMC fees (`0.5%–1.5%`), transit spoilage, price swings (`dest_price_cv_28d`), and **`28.98%`** (`17,005` trips) encountering zero uploaded commodity trade on arrival day.

## 2. Two Zero-Parameter Pocket-Calculator Solutions (No Tuning Needed!)
1. **`Safe_EV_Sunk_m0` (Scientific Tail-Risk Champion, 0 Free Params):** Take yesterday's destination price minus 1 standard deviation of recent swings (`1 - cv28`), subtract statutory fee and local price to get safe spread $G_{\text{1SD}}$, multiply by how often the yard reported on that exact weekday (`dow8`), and go **only if** $p_{\text{dow}} G_{\text{1SD}} > F_{\text{road}}$.
2. **`RT_2F_Min_m0` (Class-8 4-Function Calculator, NO `cv28`, NO Spoilage):** Multiply plain fee-adjusted spread $G$ by conservative reporting chance $p_{\min} = \min(\text{rep}_{28}, \text{dow}_8)$ and go **only if** $p_{\min} G > 2 F_{\text{road}}$ (*"Expected spread beats round-trip freight!"*).

## 3. Verified Results (`N = 58,676`, `exploratory: true`, Two-Sided Holm `p_holm_2s`)
- **Zero-Parameter `Safe_EV_Sunk_m0` vs `B2_age_matched` (`72.03%` disp):** Cuts episode losses from `26.72%` to **`14.93%`** (`−11.79 pp`, `p_holm_2s = 0.0040`), raises mean from `₹433.56` to `₹465.59/qtl` (`+₹32.03`), and slashes **`ES10` from `−₹525.25` to `−₹344.09/qtl`** (**`+₹181.17` vs `B2`**, **`+₹168.69` vs hard gates `MG`**, **`+₹116.63` vs tuned `RR`**, `p_holm_2s = 0.0040` on all 3 corrected `170–173` clusterings).
- **Zero-Parameter `RT_2F_Min_m0` (`64.92%` disp):** Delivers highest simple mean (**`₹478.38/qtl`**, `+₹44.82` vs `B2`, `p_holm_2s = 0.0040`).
- **Generalizes across ALL 6 states, all crops on `ES10` (`NonApple +₹135.58`, `Apple +₹561.37`), all 36 tornado scenarios, `exact_zero_divert_payoff_0` (`+₹169.79 ES10`), and the `N = 88,014` unconditional origin panel (`ES10 −₹335.04` vs `−₹515.93`)**.
- **Honest Boundaries (`R6`, `R7`):** Acts as an upstream 6 a.m. portal alert triage filter prior to live *arhtiya* phone verification (under `open_yard_MAR_lagged_price`, `B2` earns higher Mean `+₹102.58` while `Safe_EV` still wins on EpLoss and `ES10`); HP Graded Apples (`41.38%` cond loss) remain volatile; Stage I `H2` stays inconclusive (`+₹6.13`, `p = 0.2699`); Gate J = `BLOCKED (disclosed)`.
