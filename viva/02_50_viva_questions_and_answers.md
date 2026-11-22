# Curated Viva Questions & Verified Answers (`Revision v5` Synced)

> **See [`final/VIVA_QA.md`](../final/VIVA_QA.md) and [`final/CLAIM_MATRIX.md`](../final/CLAIM_MATRIX.md) for full scripted-verified Q&A.** All legacy quantile-mean proxies, GBDT pickles, ERA5 features, `336`-cluster keys, and tuned-threshold workarounds have been retired.

### Summary Reference of Core Viva Topics (`N = 58,676`, Two-Sided Holm)
1. **Data Cleaning Funnel (`260,043 -> 259,284 -> 256,997 -> 248,302 -> 58,676` test):** Drops `759` out-of-range quotes (`cleaning_counts.json`). Plus `N = 88,014` unconditional origin audit restoring `29,338` unreported day-$t$ origin episodes.
2. **Strict `<= t - 1` Leakage Firewall (`R3`):** Proven by `tests/test_timing_and_leakage_r3.py` counterfactual `>= t*` price-corruption invariance and exclusion of `98.64%` ERA5-identical weather.
3. **Payoff Economics (`M9`) & 3-Scheme Clustering:** Destination post-spoilage APMC fees (`0` intra-district/divert), sequential arrival settlement, `State|` prefixed cluster keys (`173` / `172` / `170–173` clusters, NOT `336`), strict two-sided Holm `p_holm_2s`.
4. **Baselines vs Zero-Parameter Rules:** `B1_lagged_screen` (`₹397.87`, `45.21%` loss, `−₹641.26 ES10`), `B2_age_matched` (`₹433.56`, `26.72%`, `−₹525.25`), `MG_matched` (`₹467.90`, `18.57%`, `−₹512.78`, `p_holm_2s = 1.000` on `ES10`), `RR_Abstain_matched` (`k*=5.0`: `₹475.36`, `17.23%`, `−₹460.72`), **`Safe_EV_Sunk_m0` (`0` params: `₹465.59`, `14.93%`, `−₹344.09`, `p_holm_2s = 0.0040`)**, **`RT_2F_Min_m0` (`0` params: `₹478.38`, `16.26%`, `−₹468.32`, `p_holm_2s = 0.0040`)**.
5. **Preserved Boundaries (`R5`–`R7`):** Open-MAR mean reversal (`B2 +₹102.58` mean vs `Safe_EV +₹190.00 ES10`), HP graded-apple `41.38%` cond loss (`−₹1,454.86` `ES10`), Stage I `H2` (`+₹6.13`, `p = 0.2699`), phone-call triage role, and `Gate J = BLOCKED (disclosed)`.
