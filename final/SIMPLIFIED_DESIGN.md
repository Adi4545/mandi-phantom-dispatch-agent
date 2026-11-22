# Simplified Design Audit (`SIMPLIFIED_DESIGN.md` — Revision v4 Sync)

## A. What Was Fixed From Legacy Baseline & External Review 3

Previous repository revisions and earlier drafts suffered from six core defects (`C1`, `C2`, `M3`–`M9`, `N1`–`N3`):

- **Day-$t$ Shortlist & Same-Day Origin Leaks (`C1`, `M9`):** Candidate menus depended on a gitignored parquet built using arrival-day prices and subtracted same-day `local_price`.
- **ERA5 Weather Leakage (`N1`):** Stored forecast rain equaled realized ERA5 rain on `66,222 / 67,135` (`98.64%`) 2025–2026 rows.
- **Unfair Comparisons (`M3`, `M4`):** Hard-gated `MG` (`lag 1..3`) was compared against `B2_fresh` (`lag = 1`) at unmatched dispatch rates, and the `H2` Stage I test had crossed zero (`+₹6.13`, `p_holm = 0.2699`).
- **Imprecise `ES10` & Incorrect Statutory Fee Base (`M9`):** Prior `cvar_10` took unweighted means below quantile cutoffs; fees were charged on `local_price` and diversion turns.
- **Over-Engineered Black Boxes (`A15`):** Deprecated GBDT pickles (`scikit-learn 1.3.0`), pseudo-conformal theorems (`(n_loss+1)/(n_disp+1)`), and weather pipelines increased viva difficulty (`4.3 / 5`) without outperforming simple cost arithmetic.

---

## B. The Pocket-Calculator Revision v4 Design (`1.6 / 5` Difficulty)

Three focused research questions only:
1. **RQ1:** How often does chasing a strictly lagged screen gap above `₹100/qtl` lose money once road freight, statutory destination fees, reference spoilage, and sequential settlement apply?
2. **RQ2:** Does weighting expected open-market gain against bounded return risk by past exact-variety reporting reliability (`RR-Abstain`, pre-registered `87a0b62`) cut loss frequency and worst-10% shortfall (`ES10`) against age- and dispatch-matched baselines?
3. **RQ3:** How sensitive is that advantage to missing-quote diversion cost (`div`), freight/commission assumptions, sequential vs hindsight settlement, and crop splits (staple vegetables vs graded apples)?

**The Minimal Operational Rule (`RR_Abstain_m0` / `RR_Abstain_matched`):**  
Every morning uses ONLY prices dated `<= t - 1` (`dest_lag_age in 1..3`) and prior reporting rates `p_rep = 0.5 * rep28 + 0.5 * dow8`. Open-market net gain subtracts road freight (`35 + 0.45 * hp * km`), statutory destination fee (`0.5%–1.5%`, `0` if intra-district or diverted), and 20°C `NABCONS` reference spoilage. Missing-quote risk charges `-kappa * F - P_orig * s`. The convex score is:

$$S_{\text{RR}}(c, t) = \hat{p}_{\text{rep}}\,\widehat{\Delta}_{\text{open}} + (1 - \hat{p}_{\text{rep}})\,(-\kappa\,F - P_{\text{orig}}\,s)$$

Zero live weather, zero pickled trees, and zero conformal theorem claims. Even in its **zero-threshold form (`RR_Abstain_m0`: dispatch iff $S_{\text{RR}} > 0$ with `kappa* = 5.0`)**, it requires only one parameter and pocket-calculator arithmetic.

---

## C. Verified Headline Outcomes (`N = 58,676`, `exploratory: true`)

- **`B1_lagged_screen`** (`100.00%` disp): Mean `₹397.87/qtl`, EpLoss `45.21%`, `ES10 −₹641.26/qtl` (`28.98%` / `17,005` trips return without commodity trade).
- **`B2_age_matched`** (`72.03%` disp, `lag 1..3`, val `₹200`): Mean `₹433.56/qtl`, EpLoss `26.72%`, `ES10 −₹525.25/qtl`.
- **`MG_matched`** (`69.51%` disp, hard `T1..T4` gates): Mean `₹467.90/qtl`, EpLoss `18.57%`, `ES10 −₹512.78/qtl` (`+₹12.49` `ES10` vs `B2_age_matched`, CI `[−₹16.57, +₹39.97]`, `p_holm = 0.589` — **not significant**).
- **`RR_Abstain_matched`** (`69.02%` disp, val `m* = ₹3.73`): Mean **`₹475.36/qtl`** (`+₹41.80`), EpLoss **`17.23%`** (`−9.49 pp`), `ES10` **`−₹460.72/qtl`** (**`+₹64.54` vs `B2_age_matched`**, **`+₹52.06` vs `MG_matched`**, Holm `p = 0.0020` under both `origin_x_2week` and `b2dest_or_origin_x_2week`). Zero-cutoff **`RR_Abstain_m0`** achieves **`₹475.76/qtl`**, `17.43%` EpLoss, `−₹461.74` `ES10`.
- **Disclosed Non-Claims & Open Risk (`R6`, `R7`):** Non-Apple crops gain `+₹78.10/qtl` `ES10` (`N = 52,207`), while lagged HP graded apples (`N = 2,802`) still suffer `44.63%` conditional losses (`−₹2,165.73` `ES10`), and Gate J future bulk holdout remains `BLOCKED (disclosed)`.
