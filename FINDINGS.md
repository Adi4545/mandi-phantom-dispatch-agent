# Findings Summary — MandiGuard Revision v5 (Zero-Parameter Simplification & `A17` Verified)

**Primary Benchmark (`revision/results/`):** Strictly `<= t - 1` lagged test split (`2025-06-01..2026-04-08`, `N = 58,676`, `exploratory: true`), validation split `2025-01-01..2025-05-31` (`N = 36,398`), NABCONS 20°C spoilage, destination gross-sale APMC fees (`0` intra-district/divert), sequential arrival settlement, exact `ES10`, corrected `State|` clustering (`170–173` clusters), strict two-sided Holm `p_holm_2s`.

## 1. Headline Findings (`revision/results/a18_results.csv` & `a18_bootstrap.csv`)
- **RQ1 (Screen-Chasing Loss Incidence):** Top lagged spread-chasing (`B1_lagged_screen`, `100%` disp) loses money on **45.21%** of test episodes (`mean ₹397.87/qtl`, `ES10 −₹641.26/qtl`); `28.98%` (`17,005` trips) divert sequentially under blank commodity trade. Scoring identical trips with 3d hindsight drops losses to `31.35%`.
- **RQ2 (Hard Gates & Tuned `RR` vs Zero-Parameter `Safe_EV_Sunk_m0` & `RT_2F_Min_m0`):**
  - `B2_age_matched` (`lag 1..3`, `th = ₹200`): `72.03%` disp, Mean `₹433.56`, EpLoss `26.72%`, `ES10 −₹525.25`.
  - `MG_matched` (`69.51%`): lifts Mean (`₹467.90`), fails `ES10` (`−₹512.78`, `p_holm_2s = 1.000`).
  - `RR_Abstain_matched` (`69.02%`, `kappa* = 5.0`, `m* = ₹3.73`): reaches `₹475.36` Mean & `−₹460.72 ES10`, yet collides with `kappa=5.0` ceiling and drops to NS on `div=0` `ES10` (`p_2s=0.603`).
  - **`Safe_EV_Sunk_m0` (`0` free params, `p_dow * G_1sd > F`):** `63.27%` disp, Mean **`₹465.59`** (`+₹32.03`), EpLoss **`14.93%` (`−11.79 pp`, `p_holm_2s = 0.0040`)**, **`ES10 −₹344.09`** (**`+₹181.17` vs `B2`**, **`+₹168.69` vs `MG`**, **`+₹116.63` vs `RR`**, `p_holm_2s = 0.0040` across ALL 3 clusterings). Beats equal-test-dispatch `B2` (`63.27%`) by `+₹156.66 ES10` and fixed-10% haircut by `+₹100.66 ES10`.
  - **`RT_2F_Min_m0` (`0` free params, `p_min * G > 2F`, NO `cv28`/spoil):** `64.92%` disp, Mean **`₹478.38`** (`+₹44.82` vs `B2`, `p_holm_2s = 0.0040`), EpLoss `16.26%`, `ES10 −₹468.32`.
- **RQ3 (Full Stress & Boundary Record):**
  - **6/6 States & All Crops:** `Safe_EV_Sunk_m0` earns strictly positive 95% `ES10` CIs in every single state, NonApple (`+₹135.58`), Apple (`+₹561.37`), all 36/36 frozen+rescored tornado scenarios, exact-geocodes (`N = 40,690`), non-conflict (`N = 56,857`), and the **`N = 88,014` unconditional origin panel** (`ES10 −₹335.04` vs `−₹515.93`).
  - **HP Graded Apples (`N = 2,802`):** `Safe_EV_Sunk_m0` beats both `B2` and `MG_matched` (`₹1,354.85`, `−₹1,454.86 ES10`), while `41.38%` cond losses remain high (`R6`).
  - **Open-MAR & Open-Auction Bounds:** `Safe_EV_Sunk_m0` dominates `exact_zero_divert_payoff_0` (`+₹169.79 ES10`, `p_2s=0.002`) and cuts Open-MAR `ES10` (`+₹190.00`), while `B2` wins Open-MAR Mean (`₹722.66` vs `₹620.08`)—clarifying upstream 6 a.m. alert-filter scope ahead of phone calls.

## 2. Preserved Legacy Stage I Record (`results/confirmatory_holm_summary.csv`, `N = 69,526`)
Stage I `H2` stays inconclusive (`+₹6.13/qtl`, 95% CI `[−₹17.02, +₹25.02]`, `p_holm = 0.2699`).
