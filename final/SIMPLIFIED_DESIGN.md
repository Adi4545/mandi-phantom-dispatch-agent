# Simplified design

## A. What was wrong

The external review scored a paper whose scripts (`revision/build_variant.py`, `build_run.py`, `eval_run.py`) and whose headline numbers (about 67,675 episodes; MG ₹397.24, B2 ₹371.38) were not in any branch of this repository. Those figures are not reproduced and are not used.

Separate defects in the older design:

- Decision rows often store a weather "forecast" that equals realized ERA5 rain (498,083 of 752,456 rows in 2025–26, 66%). ERA5 is not available the same morning, and lag-1 ERA5 is not a real-time feed either.
- Settlement could look ahead up to two days for an exact price.
- A missing exact-variety row was easy to describe as a closed market. It is not.
- The downside number was a mean of points below a quantile, not an exact worst-10% mass.
- The serious baseline was not tuned, and policies were not compared at matched dispatch rates.
- Stage I versus the road rule was inconclusive. Grade-explicit apples failed. The missing-price penalty moved the older mean ranking.

## B. The design a student can defend

Three questions only. RQ1: how often a lagged gap above ₹100 loses money under the stated payoff. RQ2: whether a margin rule reduces simulated losses versus road rules at a similar dispatch rate. RQ3: how settlement, the missing-price multiple, and the crop move the answer.

The rule uses a quote from yesterday, the day before, or the day before that. It subtracts road freight and the state fee. It dispatches if the remainder exceeds ₹200. That cutoff was frozen on January–May 2025. There is no live weather, no gradient-boosted model, and no conformal gate in the proposal.

## C. Information, settlement, missing prices

Decision prices stop at day \(t-1\). Settlement is sequential: sell if today's exact variety is recorded, wait a day only if some variety of the crop is recorded, otherwise return. Hindsight is a comparison, not the main score. The return multiple 1.5 and the 10% other-variety discount are assumptions. The grid shows that ES10 moves by hundreds of rupees and the loss rate does not, inside 0 to 1.5.

## D. What the new run actually says

Test N = 56,172. B1 loss rate 41.47%, mean ₹455.43, ES10 −₹530.85. Cautious rule: dispatch 73.73%, mean ₹490.52, loss rate 33.41%, ES10 −₹444.37. B2 at ₹100: dispatch 73.95%, mean ₹432.41, loss rate 30.82%, ES10 −₹419.36. Tuned B2 at ₹250: mean ₹424.23, loss rate 30.51%, ES10 −₹398.18. Paired mean gap versus tuned B2 is +₹66.29, interval about [+₹43, +₹94]. The road rules win on loss rate and on ES10. Straight-line versus road changes the cautious mean by ₹0.17. There is no untouched holdout.

## H. Difficulty to defend

| Piece | Original | Simplified |
|---|---|---|
| Claim of a new phenomenon | High. Reviewers hear Jensen and Baulch. | Low. It is a label for an untradable gap. |
| Mean versus the road rule | High. H2 interval crossed zero, and later text drifted. | Medium. The lagged mean gap is positive, and the tail comparison is negative. Both are in the table. |
| Weather as a causal input | High. Forecast column matches ERA5 too often. | Low. Primary score uses the 20°C reference only. |
| Settlement | High. Hindsight uses future quotes. | Medium. Sequential rule is simple; the penalty is still assumed. |
| Missing row described as closed | High. The flag was wrong. | Low. The wording is "no exact-variety price recorded." |
| ES10 | High. The old estimator was not exact 10% mass. | Low. One function, one test, one numeric example. |
| Conformal risk control | High. The theorem does not apply. | Dropped from the proposal. |
| Grade-explicit apples | High. The old rule lost to B2 and was not resimulated. | Still high if someone claims apples are solved. The paper says they are not. |
| Reproducing the review's ₹397 table | Impossible from this repo. | Not claimed. |
