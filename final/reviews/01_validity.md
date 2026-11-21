# Review 1 — validity

Role: statistical examiner. This is pass 1 of 3 by the same agent, in sequence. It is not an independent review.

## Findings

The stored Stage I tests answer the questions written in `research/hypotheses.md`. H2’s interval includes zero. That result has to stay in the abstract, and it does.

H3’s −37.29 percentage points are episode incidence (4.85 − 42.14), not the conditional loss-trip rates. The README had mixed them. That is fixed, and a test now fails if the two differences are treated as equal.

The 58.94% figure does not count closed markets. Exp 1b separates delayed exact sales, other-variety prices, and two non-quote penalties. Using it as evidence that trucks “arrive at a closed market” is invalid. The manuscript no longer says that.

CVaR is a lower-tail mean of the episode distribution. Selective rules put mass at 0. Comparing −₹37.89 with −₹436 is a comparison of those mixtures, not of losses on trucks that actually left.

The cluster bootstrap keeps origin mandis and two-week blocks. It does not recenter under the null. The added basic p-value for B2 − B1 (0.0022 vs percentile 0.0012) does not change the sign. It was not computed for H1–H4, because MandiGuard actions were not resimulated.

Stage II p-values are not in the Holm family. Exp 16 used the holdout to describe the failure, and Exp 17 scored a fix chosen with that knowledge. Those p-values do not confirm a pre-specified superiority over B2.

Exp 18 shows B2’s advantage over B1 reverses after 2026-02-11 inside the same holdout. That is a validity warning about pooling the whole window. It is not a new test of MandiGuard.

## Verdict

Stage I mean-superiority over the road heuristic is not established. Stage I comparisons with B1 and B3 remain only as strong as the stored run plus the structural payoff. Stage II is exploratory.
