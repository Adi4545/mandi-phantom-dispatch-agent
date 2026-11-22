# Locked Exploratory Follow-Up Specification (`PREREG_A18.md` — Agents `A17` & `A18`)

> **Strict Honest Disclosure (`R5` & `A17` #9):** Because calendar `2025-06-01..2026-04-08` and the HP Apple CSV were previously exposed in repository commits, **ALL evaluations under this specification remain strictly EXPLORATORY (`exploratory: true`)**—not confirmatory prospective inference. Following `R5`, this specification is frozen in git **before** implementing or running `revision/eval_a18.py`.

---

## 1. Why Zero-Parameter Simplification Was Needed (`A17` + `A18` Diagnosis)

On validation (`2025-01-01..2025-05-31`, `N = 36,398`, test untouched by `A18`), two flaws remained in `A10` (`RR-Abstain`):
1. **Unexplained ceiling constant $\kappa^* = 5.0$:** Hit the upper wall of `KAPPAS = [0..5]`, lacked physical equality to return freight (`1.5×`), and relied on mixing `rep28` with `dow8` (over-predicting Sunday holiday openings) plus Q10 biology `spoil_ref_0` (`+₹0.44` effect).
2. **No volatility protection:** Treating destination modal price as deterministic ignored daily auction dispersion (`dest_price_cv_28d`), leaving graded apples and missing-neutral counterfactuals exposed.

---

## 2. Locked Zero-Hyperparameter Rules (Discovered Strictly on `val`, Zero Magic Constants)

All rules use the identical equal-age candidate menu (`dest_lag_age in 1..3`) with strictly `<= t - 1` features. Define:
- Plain fee-adjusted spread: $G(c, t) = P_{\text{dest,lag}}(1 - \tau_{\text{fee}}) - P_{\text{orig,lag}}$
- One-standard-deviation conservative spread: $G_{\text{1SD}}(c, t) = P_{\text{dest,lag}}(1 - \text{cv}_{28})(1 - \tau_{\text{fee}}) - P_{\text{orig,lag}}$
- Reliability probabilities: $p_{\text{dow}} = \text{dest\_dow\_exact\_rep\_8w} = \frac{k+1}{10}$, $\quad p_{\min} = \min(\text{dest\_exact\_rep\_28d},\; p_{\text{dow}})$

Frozen scoring rules (all **ZERO free tuned parameters**, `S > 0` primary cutoff; plus val-calibrated `70.71%` matched versions):
1. **`Safe_EV_Sunk` (`M1` Primary Scientific Champion):**
   $$S_{\text{Safe-EV}}(c, t) = p_{\text{dow}}\cdot G_{\text{1SD}}(c, t) - F_{\text{road}}(c) > 0 \quad \Longleftrightarrow \quad \frac{G_{\text{1SD}}}{F_{\text{road}}} > \frac{1}{p_{\text{dow}}}$$
2. **`Safe_EV_Phys` (`M3` Exact Physical `div = 1.5` Counterpart):**
   $$S_{\text{Safe-EV-Phys}}(c, t) = p_{\text{dow}}\cdot(G_{\text{1SD}}(c, t) - F_{\text{road}}(c)) - (1 - p_{\text{dow}})\cdot 1.5\,F_{\text{road}}(c) > 0$$
3. **`RT_2F_Min` (`M2b` Class-8 Keypad-Calculator Rule, NO `cv28`, NO `spoil`):**
   $$S_{\text{RT-2F-Min}}(c, t) = p_{\min}\cdot G(c, t) - 2\,F_{\text{road}}(c) > 0$$
4. **`RT_2F_Dow` (`M2a` Single-Lookback 4-Function Calculator Rule):**
   $$S_{\text{RT-2F-Dow}}(c, t) = p_{\text{dow}}\cdot G(c, t) - 2\,F_{\text{road}}(c) > 0$$
5. **`EV_RT_Min` (`M4` Exact 2-State Round-Trip EV):**
   $$S_{\text{EV-RT-Min}}(c, t) = p_{\min}\cdot G(c, t) - (2 - p_{\min})\,F_{\text{road}}(c) > 0$$

---

## 3. Locked Four-Hypothesis Family (`H_A18_1..4`, Two-Sided Holm-Bonferroni)

All four primary contrasts are evaluated via `2,000`-replicate two-way cluster bootstrap (`seed = 20261117`) across **three** clustering schemes (`origin_x_2week`, corrected `b2dest_or_origin_x_2week`, and `policy_dest_or_origin_x_2week`), using **two-sided Holm-Bonferroni (`p_holm_2s`)**:
- **`H_A18_1`:** `ES10(Safe_EV_Sunk_m0) − ES10(B2_age_matched)` (two-sided)
- **`H_A18_2`:** `ES10(Safe_EV_Sunk_matched) − ES10(RR_Abstain_matched)` at validation-matched `70.71%` rate (two-sided)
- **`H_A18_3`:** `EpLoss(Safe_EV_Sunk_m0) − EpLoss(B2_age_matched)` (two-sided)
- **`H_A18_4`:** `Mean(RT_2F_Min_m0) − Mean(B2_age_matched)` (two-sided)

---

## 4. Mandatory `A17` Adversarial Audits Included in `eval_a18.py`

1. Full **Manski / Missing-Quote Regimes**: `div in {0.0_spoil_only, 0.5, 1.0, 1.5, 2.0}`, literal zero-loss `exact_zero_divert_payoff_0`, **open-yard MAR (`open_yard_MAR_lagged_price`)**, **realized open-auction subset (`realized_exact_d0_only`)**, and all three heterogeneous scenarios (including `het_adversarial_lowrep_ok_highrep_harsh`), plus `div = 0.0_spoil_only` and `exact_zero_divert_payoff_0` cluster bootstrap CIs.
2. Full **18-scenario Tornado** across `B1`, `B2`, `MG_matched`, `RR_Abstain_matched`, `Safe_EV_Sunk_m0`, and `RT_2F_Min_m0` under BOTH frozen and re-scored decisions.
3. **Fair Feature & Dispatch-Matched Ablations**: `val-ES10`-tuned hard-gate `MG` (`rep28/dow8` grid), `RR_rep14_only`, `B2_dist_penalty_only`, `Safe_EV_fixed10pct` (fixed 10% haircut vs adaptive `1 - cv28`), `Safe_EV_euclid120`, `Safe_EV_clim2024`, and test-matched `B2`/`RR`.
4. **Structural & Leakage Stress Slices**: Exact-geocoded corridors (`58.29%`, excluding centroids), excluding `3,096` conflicting-duplicate episodes, `origin_lag_age in 1..3` only, **unconditional origin panel** (`~41,603` dropped unreported day-$t$ origin days restored via `origin_lag_price`), full **6-state** & **5-crop** splits with CIs, settlement comparison (`sequential`, `hindsight`, `outside_origin_lag`), risk-coverage bands, and zero-retuning **HP Graded Apples (`N = 2,802`)**.
