# Corrected worst-decile payoff

An episode pays zero when the policy sells locally. Those zeros often straddle the tenth percentile. The historical routine averaged every observation at or below that percentile. When less than 10% of episodes lost money, including every tied zero could dilute losses severalfold.

The revised statistic averages exactly the worst tenth of episode probability mass. Let the finite simulated payoffs in ascending order be x₁, …, xₙ. Write n = 10k + r, where 0 ≤ r < 10. The signed lower-decile mean is (10 Σᵢ₌₁ᵏ xᵢ + r xₖ₊₁) / n. A negative value is a modeled shortfall in rupees per quintal. For 20 episodes with one ₹100 loss, 17 zeros and two gains, the lower-decile payoff is −₹50. A cohort without finite outcomes has no defined tail. This treatment of mass at the boundary follows the discrete-distribution definition. [Rockafellar and Uryasev, *Journal of Banking & Finance*, 2002](https://sites.math.washington.edu/~rtr/papers/rtr187-CVaR2.pdf)

All four experiment runners use [the shared implementation](../src/evaluation/tail_risk.py). The column names in their output files are retained for existing callers. [Regression tests](../tests/test_tail_risk.py) cover ties at zero, fractional boundary observations, fewer than ten observations, and missing values. The original CSV files and historical figures should be read according to the formula used by their generating commit.

[The audit comparison](exact-decile-audit.csv) includes both tail conventions for the policies in Exp 17. It covers the six-state validation and reused test periods, the historical 10,162-episode complete-screen cohort and HP apples, including the two reported grade subgroups. The experimental refit uses the historical eligibility and timing for comparability. [The independent HP payoff reconstruction](weather-and-apple-checks.json) provides full-precision checks on two baselines and the released v1 policy. Stage II results on the same inspected episodes remain exploratory.

The replay reproduced every archived non-tail field across all 42 Exp 17 rows, including the selected multipliers. The Exp 16 table and Exp 17 cluster-resampling table were byte-identical to the historical records. For file verification their SHA-256 digests are `e29f7b6fe46cbe7f0fb06ba0e532d86908665aff66418dbec2dfc2772ab15bc2` and `722538fbcf48992456cb4da5d407f7ff5f819e3966b815745866d85c2605466c`, respectively.

| Policy | Six-state exact lower-decile mean in ₹/qtl | HP apple exact lower-decile mean in ₹/qtl |
|---|---:|---:|
| B1, screen heuristic | −1,062.70 | −8,494.67 |
| B2, fresh-road heuristic | −436.69 | −2,069.03 |
| B3, point forecast | −1,097.84 | −8,061.01 |
| MandiGuard v1 | −212.93 | −876.47 |
| Stage II final policy | −223.19 | −929.66 |

Stage II improved mean simulated gain over v1 while the exact lower tail worsened in both cohorts. On the six-state holdout the corrected B2 and v1 tail means differ by ₹223.76/qtl. The legacy metric suggested a gap of ₹398.78/qtl.

To reproduce on a scratch checkout with the archived model and rebuilt six-state candidate table, run the command below from the repository root. The replay writes the experiment CSVs into that checkout's results directory.

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m src.evaluation.run_mechanistic_autopsy_and_crc
```

Join the new Exp 17 table to the historical version at commit `d20a0cb` on evaluation_scope, subgroup and policy. The audit's old and revised metrics correspond to the cvar_10_inr fields in those two versions. The four Stage I primary hypotheses use means, episode incidence or counted tool calls. Their estimands are unchanged by the expected-shortfall correction.
