# Findings Summary — MandiGuard Revision v4 (Synchronized With `AUDIT_V4.md`)

**Primary Benchmark (`revision/results/`):** Leak-free strictly-prior (`<= t - 1`) lagged test split (`2025-06-01..2026-04-08`, `N = 58,676` Top-5 shortlisted episodes, `exploratory: true`), validation selection strictly on `2025-01-01..2025-05-31` (`N = 36,398`), NABCONS 20°C reference spoilage, destination-base APMC statutory fees (`0` intra-district or divert), sequential arrival settlement, exact fractional `ES10`.

## 1. Headline Findings (`revision/results/a10_results.csv` & `a10_bootstrap.csv`)
- **RQ1 (Phantom Lagged Spreads):** Chasing the top lagged exact-variety gap (`B1_lagged_screen`, `100%` disp) loses money on **45.21%** of test episodes (mean `₹397.87/qtl`, `ES10 −₹641.26/qtl`); `28.98%` encounter no commodity trade on arrival and turn back sequentially (`outcome_mix.csv`). Scoring identical trips with 3-day hindsight drops apparent losses to `31.35%` (`settlement_compare.csv`).
- **RQ2 (`RR-Abstain` vs Equal-Age & Hard-Gated Baselines at Matched ~70% Dispatch):**
  - `B2_age_matched` (`lag 1..3`, `th = ₹200`): `72.03%` disp, Mean `₹433.56`, EpLoss `26.72%`, `ES10 −₹525.25`.
  - `MG_matched` (hard gates `T1..T4`): `69.51%` disp, Mean `₹467.90` (`+₹34.35`, `p_holm = 0.006`), EpLoss `18.57%` (`−8.16 pp`), `ES10 −₹512.78` (`+₹12.49`, CI `[−₹16.57, +₹39.97]`, `p_holm = 0.589` — insignificant on tail risk). Virtually all matched gain came from `T1` (`Abl_T1_T2_noT3` = `₹467.46`), whereas `euclid*1.2` matched OSRM within `₹0.40` (`₹467.50`) and 2024 climatology added `−₹0.05` (`₹467.85`).
  - Pre-registered **`RR_Abstain_matched`** (`87a0b62`, `kappa* = 5.0`, `m* = ₹3.73`): `69.02%` disp, Mean **`₹475.36/qtl`** (`+₹41.80` vs `B2_age_matched`, Holm `p = 0.0020`), EpLoss **`17.23%`** (`−9.49 pp`, Holm `p = 0.0020`), and exact **`ES10 −₹460.72/qtl`** (**`+₹64.54`** vs `B2_age_matched`, **`+₹52.06`** vs `MG_matched`, Holm **`p = 0.0020`** under BOTH `origin_x_2week` and `b2dest_or_origin_x_2week` clusterings). Zero-cutoff `RR_Abstain_m0` (`> 0`) gives `₹475.76/qtl` and `−₹461.74 ES10`.
- **RQ3 (Generalizability, Sensitivity & Preserved Failures):**
  - Non-Apple crops (`N = 52,207`): `RR_Abstain_matched` adds `+₹34.82` Mean and `+₹78.10 ES10` (Onion `+₹101.93`, Potato `+₹88.91`, Tomato `+₹49.31`). Generic `Apple` `ES10` is tied (`−₹1,537.30` vs `−₹1,533.29`).
  - Missing-quote stability: `RR_Abstain_matched` beats `B2_age_matched` & `B1` down to `div = 0.0, disc = 0.00` (`₹493.37`, `17.21%`, `−₹349.35 ES10`) and under heterogeneous selective missingness (`−₹388.55` vs `−₹499.07`).
  - Economic stability: `MG > B1` holds across smallholder freight (`₹0.45..₹1.20/qtl-km`) & `0–6%` *arhtiya*, flipping only at NITI Aayog bulk floor (`₹0.258/km`, `−₹14.23/qtl`).
  - Graded HP Apples (`N = 2,802` lagged): `44.63%` cond loss rate and `−₹2,165.73 ES10` remain unacceptably risky (`R6`).

## 2. Preserved Legacy Stage I Record (`results/confirmatory_holm_summary.csv`, `N = 69,526`)
Legacy same-day `H2` (`MandiGuard` vs same-day `B2` under old quantile-mean `cvar_10`, `hist_gbdt`, and coupled weather) stayed **inconclusive** (`+₹6.13/qtl`, 95% CI `[−₹17.02, +₹25.02]`, `p_holm = 0.2699`). See `results/ES10_NOTE.md` for why legacy `cvar_10_inr` differs from exact `ES10`.
