# Curated Viva Questions & Verified Answers (`C2` Fixed)

> **See [`final/VIVA_QA.md`](../final/VIVA_QA.md) and [`final/CLAIM_MATRIX.md`](../final/CLAIM_MATRIX.md) for the complete scripted-verified Q&A.** All older 50-question unlagged Stage I/II scripts (with `cvar_10`, `forecaster_2024.pkl`, ERA5 features, and conformal claims) have been retired to prevent unverified citations during oral defense.

### Summary Reference of Core Viva Topics (Verified in Revision v4)
1. **Data Cleaning Funnel (`260,043 -> 259,284 -> 256,997 -> 248,302 -> 58,676` test):** Reconciled in `revision/results/cleaning_counts.json` (drops `759` out-of-range modals, deduplicates `2,287` exact dup excess & `8,695` variety consolidations).
2. **Strict `<= t - 1` Leakage Firewall (`R3`):** Proven by `tests/test_timing_and_leakage_r3.py` (bit-for-bit invariant shortlists under day `>= t*` adversarial price corruption) and exclusion of `98.64%` ERA5-identical weather.
3. **Payoff Economics (`M9`):** `35 + 0.45 * hp * road_km`, NABCONS 20°C spoilage, destination post-spoilage fee (`0` on intra-district or turn-backs), sequential no-lookahead wait/divert settlement.
4. **Equal-Menu & Equal-Age Baselines (`M4` / `R4`):** `B1_lagged_screen` (`₹397.87`, `45.21%` loss, `−₹641.26 ES10`), `B2_age_matched` (`₹433.56`, `26.72%`, `−₹525.25 ES10`), `B_simple_activity_matched` (`₹440.97`, `23.48%`, `−₹506.28 ES10`), `MG_matched` (`₹467.90`, `18.57%`, `−₹512.78 ES10`), **`RR_Abstain_matched` (`₹475.36`, `17.23%`, `−₹460.72 ES10`, Holm `p = 0.0020`)**.
5. **Preserved Failures & Boundaries (`R5`–`R7`):** Stage I `H2` inconclusive (`+₹6.13`, `p = 0.2699`), `MG` mean flips below `B1` at NITI Aayog bulk floor (`₹0.258/qtl-km`, `−₹14.23`), HP graded-apple `44.63%` conditional losses, and no untouched post-April-2026 multi-state panel (`exploratory: true`, Gate J = `BLOCKED`).
