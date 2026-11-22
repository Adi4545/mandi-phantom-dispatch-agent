# Simplified Design Audit (`SIMPLIFIED_DESIGN.md` — Revision v5 Verified)

## A. How Complexity & Magic Constants Were Eliminated Across Audits

1. **Legacy Baseline (`4.3 / 5` Difficulty):** Relied on gitignored caches (`candidates_6state.parquet`), same-day price/weather leaks (`98.64%` ERA5 match), deprecated GBDT pickles (`scikit-learn 1.3.0`), pseudo-conformal theorems, unweighted quantile means (`cvar_10`), and unmatched baselines (`H2 +₹6.13`, `p = 0.2699`).
2. **Audit Remediation (`A10` `RR-Abstain`, `1.6 / 5`):** Fixed timing/fee/ES10/age-matching bugs cleanly, yet `A17` + `A18` uncovered remaining defects: a bare `dest_market` string-prefix bug (`336` split clusters instead of `172`), one-sided Holm labels, grid-wall collision at $\kappa^* = 5.0$, Sunday holiday pollution inside `rep28`, missing price-volatility defense (`cv28`), and `div = 0.0` hidden spoilage losses.
3. **Final Zero-Parameter Design (`PREREG_A18.md`, `1.2 / 5` Difficulty):** Removed **ALL** tuned thresholds, $\kappa$ grids, dual lookbacks, and Q10 biology parameters.

---

## B. The Minimal Zero-Parameter Formulas (`S > 0`, Zero Tuning)

Using strictly `<= t - 1` quotes (`dest_lag_age in 1..3`), plain fee-adjusted spread $G = P_{\text{dest,lag}}(1 - \tau_{\text{fee}}) - P_{\text{orig,lag}}$, 1-SD conservative spread $G_{\text{1SD}} = P_{\text{dest,lag}}(1 - \text{cv}_{28})(1 - \tau_{\text{fee}}) - P_{\text{orig,lag}}$, weekday reporting frequency $p_{\text{dow}} = \text{dest\_dow\_exact\_rep\_8w}$, and $p_{\min} = \min(\text{rep}_{28}, p_{\text{dow}})$:

- **`Safe_EV_Sunk_m0` (Scientific & Tail-Risk Champion, 0 Free Params):**
  $$S_{\text{Safe-EV}} = p_{\text{dow}}\cdot G_{\text{1SD}} - F_{\text{road}} > 0 \quad \Longleftrightarrow \quad \frac{G_{\text{1SD}}}{F_{\text{road}}} > \frac{1}{p_{\text{dow}}}$$
- **`RT_2F_Min_m0` (Class-8 4-Function Phone Calculator, NO `cv28`, NO Spoilage):**
  $$S_{\text{RT-2F-Min}} = p_{\min}\cdot G - 2\,F_{\text{road}} > 0$$

---

## C. Verified Headline Progression (`N = 58,676`, `exploratory: true`, Two-Sided Holm)

- **`B1_lagged_screen`** (`100.00%` disp): Mean `₹397.87/qtl`, EpLoss `45.21%`, `ES10 −₹641.26/qtl` (`28.98%` / `17,005` turn back sequentially).
- **`B2_age_matched`** (`72.03%` disp, `lag 1..3`, val `₹200`): Mean `₹433.56/qtl`, EpLoss `26.72%`, `ES10 −₹525.25/qtl`.
- **`MG_matched`** (`69.51%` disp, hard `T1..T4` gates): Mean `₹467.90/qtl`, EpLoss `18.57%`, `ES10 −₹512.78/qtl` (`p_holm_2s = 1.000` on `ES10` — fails tail risk).
- **`RR_Abstain_matched`** (`69.02%` disp, `kappa* = 5.0`, `m* = ₹3.73`): Mean `₹475.36/qtl`, EpLoss `17.23%`, `ES10 −₹460.72/qtl` (`p_holm_2s = 0.0040` origin/B2-dest, `0.0060` RR-dest; fails NS at `div=0` on `ES10`).
- **`Safe_EV_Sunk_m0`** (**`0` free params**, `63.27%` disp): Mean **`₹465.59/qtl`** (`+₹32.03` vs `B2`), EpLoss **`14.93%`** (`−11.79 pp`, `p_holm_2s = 0.0040`), **`ES10 −₹344.09/qtl`** (**`+₹181.17` vs `B2_age_matched`**, **`+₹168.69` vs `MG_matched`**, **`+₹116.63` vs `RR_Abstain_matched`**, `p_holm_2s = 0.0040` on all 3 schemes), dominates every state (`6/6`), all `36/36` tornado cells, `N = 88,014` unconditional origin panel (`−₹335.04` vs `−₹515.93`), `exact_zero_divert_payoff_0` (`+₹169.79`), and HP Graded Apples (`₹1,354.85 / −₹1,454.86`).
- **`RT_2F_Min_m0`** (**`0` free params**, NO `cv28`, `64.92%` disp): Mean **`₹478.38/qtl`** (`+₹44.82` vs `B2`, `p_holm_2s = 0.0040`), EpLoss `16.26%`, `ES10 −₹468.32/qtl`.
- **Open Disclosures (`R6`, `R7`):** Acts as 6 a.m. portal-alert triage before live *arhtiya* phone calls; under Open-MAR portal omissions, `B2` earns `+₹102.58` higher mean while `Safe_EV_Sunk_m0` keeps `+₹190.00` `ES10` gain; Gate J future holdout remains `BLOCKED (disclosed)`.
