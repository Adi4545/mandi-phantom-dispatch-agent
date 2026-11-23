# MandiGuard — Leak-Free Agricultural Arbitrage & Zero-Parameter Dispatch Triage (Revision v7)

**Author:** Aditya Sharma (M.Tech Thesis Research, supervised by **Dr. Sonia**) — Shoolini University, Solan, Himachal Pradesh, India.

## What This Project Does
Online wholesale price portals (AGMARKNET) routinely display `> ₹100/qtl` cross-market spreads across India. Under a strict `<= t - 1` chronological firewall and non-anticipative sequential arrival settlement across a **zero-lookahead `2024`-selected `171`-market panel (`N = 57,634` test episodes)** in `6` states and `4` crops (`Onion`, `Potato`, `Tomato`, `Apple`), chasing top raw lagged spreads (`B1_lagged_screen`) loses money on **`45.07%`** of dispatches (`ES10 = −₹642.15/qtl`, with `28.67%` encountering zero recorded destination commodity trade on arrival).

After eliminating Stage I ERA5 weather leaks, pickled GBDT models (`H2` inconclusive at `+₹6.13/qtl`), and grid-edge penalty tuning (`κ* = 5.0`), Revision v7 establishes **three zero-hyperparameter expected-value rules (`m = 0`)**:
- **`Safe_EV_Sunk_m0` (`p_dow * G_1SD > F_road`):** `63.23%` dispatch, **`₹452.74/qtl`** Mean (`+₹33.12` vs `B2_age_matched`), **`14.88%`** episode loss (`−11.56 pp`), **`ES10 −₹345.53/qtl`** (`+₹179.24` vs `B2`), and conditional **`cond_ES10 −₹447.48/qtl`** (`+₹180.89` vs `B2 −₹628.37`), clearing all four locked `PREREG_A18.md` hypotheses (`p_holm_2s_prereg4 = 0.0040`, `R = 2,000` across `3` clusterings).
- **`Safe_EV_Phys_m0` (`1.5F`):** `60.84%` dispatch, `₹449.52/qtl` Mean, **`13.70%`** episode loss, **`ES10 −₹334.80/qtl`** (`+₹189.97` vs `B2`), **`cond_ES10 −₹447.33/qtl`**.
- **`RT_2F_Min_m0` (`p_min * G > 2 * F_road`, NO `cv28`, NO decay):** `64.79%` dispatch, **`₹463.98/qtl`** Mean (`+₹44.36` vs `B2`), `16.21%` loss, `ES10 −₹464.84/qtl`, keeping strictly positive 95% Mean CIs across all `6` states and all `5` crop slices (`p = 0.001–0.032`; note loss of `ES10`/`cond_ES10` significance under `<= t - 2` latency `p = 0.363`/`0.981`).
- **Clean `166`-Mkt `2018–2023` Validation (`N = 383,952`) & Phase 6 Stress Suite (`v7_exp1..5`):** Dropping all `7` post-`2024` lookahead yards (`171 ∩ 173`) yields `N = 383,952` (`115`-mkt `N = 325,993`), where frozen `Safe_EV_Sunk_m0` gains `+₹169.27 ES10` & **`+₹155.08 cond_ES10`** (`+₹174.27` vs equal-dispatch `B2_eq_SafeM0`, `p = 0.001`), holds under NASA POWER × Sched #7 (`₹330.84` vs `₹291.41`), and wins `ES10`/`cond_ES10` in all `6/6` years. Phase 6 stress runs verify `<= t-2` latency (`Safe_EV p = 0.001`), coupled `S6_Frozen x Stoch_CondMAR_p1.00` (`+₹366.85 cond_ES10`), and superior `cond_ES10` over retrained `Ridge/HGBR/OR_Vargas` (`v7_exp4`).

## Key Boundaries (Disclosed Upfront)
1. **Exploratory `2025–2026` Scope & Alert-Triage Role:** Bulk public AGMARKNET feeds stop at `2026-04-13` (`Gate J = BLOCKED` prospectively); rules operate strictly as 6 a.m. portal triage filters ahead of live *arhtiya* phone verification, claiming applied/evaluation novelty rather than a mathematical theorem (`59/59` verified citations).
2. **Negative / NS Mean & Small-Cluster Limits:** Mean vs `B2` turns non-significant under `div = 0.0` (`p = 0.2199–0.2559`), reverses under Open-MAR (`B2 +₹97.01`, break-even `25.45%`), reverses under `hindsight_3d` (`B2 ₹549.81` vs `₹533.14`), `PreChoice_ExactD0` (`−₹20.74`), `Manski Supp1..3` (`−₹124.95` to `−₹325.40`), `2020/2023` (`p = 0.208/0.077`), and `SUTVA 10%` (`−₹5.31`). **HP (`B = 12`) fails significance on `cond_ES10` (`p = 0.1239`)** and **HP Graded Apples (`N = 2,802`)** keep `41.38%` loss & NS `cond_ES10` (`p = 0.0940`).

## Quick Verification Commands
```bash
pytest -v
python3 scripts/a16_independent_audit.py
python3 scripts/verify_traceability.py
```
Build deliverables with `make deliverables` (or clean-clone verification via the `reproduce` target in `Makefile`).
