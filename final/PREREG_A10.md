# Pre-Registration: Agent A10 Minimal Extension (`RR-Abstain`)

**Pre-registered BEFORE writing or running `revision/eval_a10.py` (`R5`).**  
**Scope & Exposure Disclosure (`R5`):** Both the 6-state test window (`2025-06-01..2026-04-08`) and the Himachal Pradesh graded-apple file (`2025-11-21..2026-08-27`) were inspected in earlier commits of this repository. Therefore, evaluating `RR-Abstain` on those windows is strictly **exploratory with respect to calendar exposure**, while **confirmatory with respect to pre-registering the `A10` hypothesis, formula, parameter grid, and failure rules before implementation and execution**. All validation selection uses ONLY `2025-01-01..2025-05-31`.

---

## 1. Exact Mathematical Formulation (Strictly $\le t-1$ Inputs Only)

Candidate universe: identical Top-5 shortlisted menu from `revision/results/lagged_candidates.parquet` restricted to quote age $1 \le \text{dest\_lag\_age}(c, t) \le 3$ (matching `B2_age_matched`, `M4`).

For candidate corridor $c = (o \to d)$ on morning decision day $t$:

1. **Historical exact-variety reporting reliability** (strictly $\le t-1$):
   $$\hat{p}_{\text{rep}}(c, t) = 0.5\,\text{dest\_exact\_rep\_28d}(c, t) + 0.5\,\text{dest\_dow\_exact\_rep\_8w}(c, t) \in (0, 1)$$
2. **Expected open-quote net gain** (strictly $\le t-1$, Class-12 arithmetic):
   $$\widehat{\Delta}_{\text{open}}(c, t) = P_{\text{dest,lag}}(c, t)\,\big(1 - s_{\text{ref,0}}(c)\big)\,\big(1 - \tau_{\text{fee}}(c)\big) - P_{\text{orig,lag}}(o, t) - F_{\text{road}}(c)$$
3. **Worst-case bounded missing-quote loss** (parameterized by single scalar risk weight $\kappa \ge 0$):
   $$\widehat{\Delta}_{\text{miss}}(c, t; \kappa) = -\kappa\,F_{\text{road}}(c) - P_{\text{orig,lag}}(o, t)\,s_{\text{ref,0}}(c)$$
4. **Combined reporting-reliability-aware score (`RR-Abstain`):**
   $$S_{\text{RR}}(c, t; \kappa) = \hat{p}_{\text{rep}}(c, t)\,\widehat{\Delta}_{\text{open}}(c, t) + \big(1 - \hat{p}_{\text{rep}}(c, t)\big)\,\widehat{\Delta}_{\text{miss}}(c, t; \kappa)$$

Notice that NO ad-hoc separate thresholds (`rep14 >= 0.50`, `dow8 >= 0.35`, conformals, or trees) remain: `RR-Abstain` collapses activity filtering, destination statutory fee, 20°C spoilage, and missing-quote downside bounding into ONE linear expectation formula. When $\hat{p}_{\text{rep}} \to 1$, $S_{\text{RR}} \to \widehat{\Delta}_{\text{open}}$; when $\hat{p}_{\text{rep}} \to 0$, $S_{\text{RR}} \to -\kappa F_{\text{road}} - P_{\text{orig,lag}} s_{\text{ref,0}}$.

**Dispatch Decision:** Choose $c^*(t) = \arg\max_{c \in \text{age } \le 3} S_{\text{RR}}(c, t; \kappa^*)$ (deterministic tie-break smaller `road_km`, then lexicographic `dest_market`), and dispatch iff $S_{\text{RR}}(c^*(t), t; \kappa^*) > m^*$; else abstain ($\Delta\text{Net} = 0$).

---

## 2. Validation-Only Parameter Selection (`2025-01-01..2025-05-31` ONLY)

- **Risk-aversion grid:** $\kappa \in \{0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0\}$.
- **Primary fair matched-dispatch comparator (`RR_Abstain_matched`):** For each $\kappa$ in the grid, calibrate cutoff $m_{\text{match}}(\kappa)$ strictly on `val` quantiles to match `B2_age_matched`'s validation dispatch rate (`0.7071`), then pick $\kappa^*$ minimizing `val` **`ep_loss_rate`** (Wait: specify BOTH `min ep_loss_rate` and tie-break `max val ES10` OR `max val ES10` directly! Pre-register cleanly: pick $\kappa^*$ maximizing **`val` `ES10`** — i.e., least negative worst-10% loss — subject to `val mean >= val_mean(B2_age_matched) - 10.0`, fallback best `val ES10` overall).
- **Secondary unconstrained validation-tuned version (`RR_Abstain_val`):** Pick $(\kappa^\dagger, m^\dagger)$ over $\kappa \in \{0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0\} \times m \in \{0, 50, 100, 150, 200, 250, 300, 350, 400, 500\}$ minimizing `val` `cond_loss_rate` subject to `val dispatch_rate >= 0.25` (exact same objective as `B2_age_matched` & `MG_T1_T2_T3_T4`), plus at fixed standard hurdle `m = 100` / `m = 0` (`RR_Abstain_0`).

---

## 3. Declared Hypotheses & Failure Rules (Evaluated Once on Frozen `test`)

Primary Holm-Bonferroni family (`m = 4`, FWER $\alpha = 0.05$, tested under **both** `origin_x_2week` and `b2dest_or_origin_x_2week` 2,000-rep two-way cluster bootstrap):

1. **`H_A10_1` (Matched Tail Loss `ES10`):** Under val-calibrated matched dispatch (`~70%`), `ES10(RR_Abstain_matched) > ES10(B2_age_matched)`.
2. **`H_A10_2` (Matched Episode Loss Rate):** Under val-calibrated matched dispatch (`~70%`), `ep_loss_rate(RR_Abstain_matched) < ep_loss_rate(B2_age_matched)`.
3. **`H_A10_3` (Matched Mean Gain):** Under val-calibrated matched dispatch (`~70%`), `mean(RR_Abstain_matched) > mean(B2_age_matched)`.
4. **`H_A10_4` (Matched Tail Advantage over Hard-Gated `MG_matched`):** `ES10(RR_Abstain_matched) > ES10(MG_matched)`.

Additional mandatory stress diagnostics (reported in full even if negative):
- Performance across non-Apple crops (`Onion`, `Potato`, `Tomato`) separately and across missing-price scenarios (`div in {0.0, 0.5, 1.0, 1.5, 2.0}` and heterogeneous regimes).
- Zero-retuning evaluation on `lagged_hp_apple_candidates.parquet` (`N = 2,802` graded apple episodes).

**Failure Condition:** If any of `H_A10_1..4` fails to beat its comparator or fails Holm-Bonferroni (`p_holm >= 0.05` under either clustering scheme), it will be explicitly reported as `NOT_SUPPORTED` (or `MIXED` / `FAILED`) in `final/NOVELTY_V2.md`, `paper/manuscript.md`, and `final/CLAIM_MATRIX.md`, with zero post-hoc re-tuning.
