# How much does the unobserved sale price matter?

B1 follows a headline spread. B2 requires a fresh exact-variety quote and accounts for road freight. This diagnostic holds both policies’ chosen destinations fixed. It varies the *net incremental payoff* assigned to a dispatched route with no matching price on arrival day or the next two days. “Matching” follows the historical panel’s normalized variety key and, in the HP panel, includes grade. Actual receipts for these hypothetical dispatches are unavailable.

Let `a` be a common adjustment in rupees per quintal to the baseline modeled payoff on every such unmatched dispatch. For `N` common shortlisted episodes, let `M_j` count those dispatches under policy `j`. The mean B1-minus-B2 contrast changes by exactly `a × (M₁ − M₂) / N`. Selling locally retains zero incremental payoff. The crossing reverses which fixed policy has the larger *mean simulated score*. It does not change an individual policy decision.

| Cohort | Episodes | B1 / B2 unmatched dispatches | Baseline B1 minus B2 (₹/qtl) | Contrast change for each +₹100/qtl adjustment | Adjustment that ties the means | Contrast at +₹500/qtl |
|---|---:|---:|---:|---:|---:|---:|
| Six states | 69,526 | 29,433 / 2,582 | −96.65 | +38.62 | +250.26 | +96.45 |
| HP grade-explicit apples | 1,537 | 1,412 / 60 | −309.25 | +87.96 | +351.57 | +130.57 |

For example, if every unobserved destination outcome in the six-state panel were worth ₹300/qtl more than its assigned fallback payoff, B1 would exceed B2 by about ₹19.21/qtl per shortlisted episode. The portal cannot determine the sign or size of that adjustment. It might vary by market, date, grade or alternative buyer.

A second calculation allows an episode-specific and destination-specific adjustment anywhere in `[−A, A]`. When both policies select the same missing route, they must receive the same adjustment. Those common routes cancel. The largest possible absolute change in the contrast is `A × (M₁ + M₂ − 2S) / N`, where `S` is the number of common unmatched choices. This expression is attained if adjustments take opposite extremes for the unmatched routes selected exclusively by the two policies. The smallest such radius admitting a tie is ₹228.84/qtl in the six-state panel and ₹331.46/qtl in HP. These are mathematical sensitivity limits for the observed policy choices. They supply neither confidence intervals nor evidence that the required adjustments are economically typical.

Run `python scripts/audit_payoff_crossover.py` after rebuilding the six-state candidates. The script checks the missing flags against the three raw destination price columns, matches chosen routes by episode and destination, verifies their scores and substitutes the break-even adjustment into both payoff vectors. The full unrounded results are in `final/payoff-crossover.csv`.
