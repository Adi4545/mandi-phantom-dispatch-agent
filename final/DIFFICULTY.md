# Complexity & Difficulty Reduction Audit (`DIFFICULTY.md` — Agents `A15` & `A18`)

Every formula, feature, parameter, and defense argument was ruthlessly simplified across two rounds of difficulty reduction—first removing legacy black-box trees (`4.3 -> 1.6 / 5`), and then eliminating ALL tuned cutoffs, $\kappa$ grids, dual lookbacks, and Q10 biology tables via `PREREG_A18.md` (**`1.6 -> 1.2 / 5`**).

## 1. Three-Stage Complexity & Difficulty Scorecard (`1` = Class-8/10 Pocket Calculator, `5` = Brittle Specialization)

| Dimension | Legacy Baseline (`b3bb46f`) | Intermediate `A10` (`RR-Abstain`) | Final Revision v6 (`Safe_EV_Sunk_m0` & `RT_2F_Min_m0`) | Net Gain |
|---|---:|---:|---:|---|
| **1. Conceptual Framing** | **4.5 / 5** | **1.5 / 5** | **1.1 / 5** | Plain alert filter ahead of trader calls: *"spread after volatility × weekday reliability vs sunk freight"*. |
| **2. Mathematics & Equations** | **4.0 / 5** | **1.5 / 5** | **1.0 / 5** | Zero-parameter linear inequalities (`p_dow * G_1SD > F` and `p_min * G > 2F`) verified in 10 seconds on a phone calculator. |
| **3. Hyperparameters & Tuning** | **4.5 / 5** | **2.0 / 5** | **1.0 / 5** | Eliminated `kappa* = 5.0` grid wall, `m* = ₹3.73`, dual lookbacks, and Q10 decay tables (**0 free parameters**). |
| **4. Reproducibility & Hygiene** | **4.5 / 5** | **1.5 / 5** | **1.3 / 5** | 1-command `make reproduce` (`0.0` clean-clone diff), `State|` cluster keys fixed (`171–173`), two-sided Holm `p_holm_2s` (`R = 5,000`). |
| **5. Oral Viva Defensibility** | **4.5 / 5** | **1.5 / 5** | **1.4 / 5** | Zero sign flips across 36/36 tornado checks, all 6 states, exact-geocodes (`N=40.7k`), and `N=88.0k` unconditional origin panel; `0` untraceable numbers. |
| **Overall Mean Difficulty** | **4.3 / 5** | **1.6 / 5** | **1.2 / 5** | **Net cut: −3.1 points (−72% difficulty)** while boosting `ES10` by **+₹116.63/qtl over tuned `RR-Abstain`** (`+₹181.17` over `B2`). |

---

## 2. Specific Magic Constants & Redundant Components Removed (`A18`)

| Removed Component | Where It Hurt (`A17` Finding) | Zero-Parameter Replacement | Measured Impact on Test (`N = 58,676`) |
|---|---|---|---|
| **Tuned Multiplier `kappa* = 5.0` (`RR-Abstain`)** | Hit grid upper bound `5.0`, had no equality to `1.5×` return cost, shifted threshold to `−₹328.99` at `kappa=20`. | **`Safe_EV_Sunk_m0`** (`S = p_dow * G_1SD - F > 0`, **0 tuned params**) | `ES10` jumps from `−₹460.72` to **`−₹344.09/qtl` (`+₹116.63/qtl`)** with ZERO grid search. |
| **`0.5*rep28 + 0.5*dow8` Sunday Mix** | `rep28` averaged ~`0.75` on yards closed every Sunday, causing overconfident weekend dispatches. | **Weekday-only `dow8`** (`p_dow = (k+1)/10`, exact weekday frequency) | Brier prediction error strictly beaten by `dow8` alone; fixes Sunday closure blindness. |
| **Deterministic Price Assumption (`G_open`)** | Ignored daily auction crash variance (`cv28`), leaving `Apple` tied and `div = 0` `ES10` insignificant (`p_2s=0.603`). | **1-SD conservative spread** `G_1sd = P_d*(1-cv28)*(1-fee) - P_o` | Beats fixed 10% haircut by `+₹100.66 ES10`, improves `Apple ES10` (`+₹561.37`), holds at `exact_zero_divert_payoff_0` (`+₹169.79`). |
| **NABCONS Q10 Spoilage Inside Decision Score** | Added biological parameters (`3.25%`..`0.86%`, Q10, hours) for only `+₹0.44` matched effect (`matched_dispatch.csv`). | **Omitted cleanly** inside both `Safe_EV_Sunk_m0` & `RT_2F_Min_m0` decision rules (retained in simulator!) | Zero biological lookup needed by a farmer at 6 a.m., zero performance loss. |
| **Class-8 Ultra-Minimal Field Option** | Even `cv28` can feel abstract in rural kiosks without standard-deviation telemetry. | **`RT_2F_Min_m0` (`p_min * G > 2F`)** (0 free params, 4-function arithmetic) | Delivers **`₹478.38/qtl` mean** (`+₹44.82` vs `B2`, `p_holm_2s = 0.0024` at `R = 5,000`) and `16.26%` EpLoss with NO `cv28`. |
