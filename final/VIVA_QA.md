# Viva questions and answers

Short answers. Use the files named in each answer if asked for the number.

**What is actually new?** A time-ordered comparison of dispatch rules on six states and four perishable crops. The defensible result is empirical: under a structural cost model, a road-and-fresh-price rule is not beaten on mean profit by the pre-registered cascade (H2), while screen-chasing and unfiltered point forecasts look worse on the stored holdout. “Phantom spatial arbitrage” is a name for unrealized portal spreads, not a new phenomenon. See `final/NOVELTY_ASSESSMENT.md`.

**Does a missing price mean the market was closed?** No. Exp 1b: of 63,040 B1 dispatches, 41.06% have an exact arrival-day quote, 12.25% sell the exact variety one or two days later, 29.59% are priced with another variety’s minimum under a 10% model discount, 4.37% have no row for that commodity while another commodity is quoted, and 12.73% have no commodity row that day. Only the last branch is named `closed_yard_divert`, and it is still “no row”, not a visit that found the gate shut.

**Is the profit real?** No. It is a retrospective score: sale quote, if any, minus local modal, minus assumed freight, fee, spoilage, and a penalty when the quote is missing. The fee uses the local modal. There are no farmer receipts. The ₹3,083 versus NSS ₹3,798 line is a scale comparison for one 30-qtl trip, not a measured income gain.

**Why a deterministic cascade instead of an LLM?** The decision is a threshold on public numbers: quote age, road cost, a weather spoilage term, and a lower bound or risk score. An LLM would add an unlogged policy and would not identify freight or spoilage. The cascade is also what makes H4 a statement about call order rather than about intelligence.

**How does MandiGuard compare with the road heuristic?** Stored H2: +₹6.13/qtl, 95% interval about −₹17 to +₹25, Holm p = 0.27, not supported. MandiGuard dispatches less often in that table (48.66% vs 62.11%) and has a lower conditional loss rate (9.97% vs 18.11%) and a milder episode CVaR. Those are different estimands from the mean. Exp 18, which does not include MandiGuard, shows the road heuristic itself loses to screen-chasing on mean in the last 9,886 episodes of the holdout (₹340.61 vs ₹453.67).

**Why did H2 fail?** The fresh same-day quote plus road cost already removes most of the bad screen trades. The extra gates abstain on trips whose mean contribution is small relative to cluster noise. The design spent its mean advantage on fewer loss trips. That can be a reasonable safety choice, and it is still a failed mean test.

**Is the Stage II gate conformal risk control?** No. Calibration uses `(n_loss+1)/(n_dispatch(λ)+1) ≤ 0.095` on validation. Daily prices are not exchangeable, and the denominator moves with λ. Angelopoulos et al. (2024) Theorem 1 does not apply. Call it an empirically calibrated risk gate. It was also fit after the holdout had been inspected (Exp 16), then scored on that holdout (Exp 17).

**How sensitive is this to trucking and spoilage?** Exp 6 varies freight and spoilage multipliers. Exp 15 varies the non-quote penalty down to zero. In the stored zero-penalty cell, MandiGuard’s mean falls below B1 (about −₹10/qtl) while the loss-trip rate stays lower. Mean rank is an assumption about the penalty. Tail comparisons move less, and they still use the same model.

**What field trial would you run?** Pre-register one primary endpoint before the season: farmer-level net receipt per quintal from weighment and payment slips, MandiGuard or the road heuristic versus the farmer’s own choice, randomized by farmer or by week within mandi, with refusal allowed. Record whether the destination traded that variety, separately from the portal row. Do not use the modeled payoff as the primary endpoint. Power on clusters of farmers, not on portal-days. Keep a frozen rule; do not retune λ on the trial outcomes. A pilot in one crop and two states is enough to learn whether the portal-missing cases are closures.
