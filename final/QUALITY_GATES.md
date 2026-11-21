> This document records the earlier analysis. Use the [correction record](CORRECTIONS.md) for the revised downside estimates, arrival-day diagnostics, weather control and reproduction commands.

# Quality gates

| Gate | Result | Evidence |
|---|---|---|
| A. Pre-registration integrity | PARTIAL | `e421d15` predates result CSVs in git author time and the hypothesis file is unchanged. The runner is inside `e421d15`. No external timestamp. |
| B. Claim–evidence trace | PARTIAL | `final/CLAIM_MATRIX.md`. B1/B2/Exp 14 recomputed. MG/B3/Exp 17 not recomputed. Closed-market wording contradicted and removed. |
| C. Data provenance and parity scope | PARTIAL | Panel SHA checks. Exp 14 rerun identical. Scope is a spot check plus HP apple. Duplicates documented. |
| D. Observed vs assumed economics | PASS | Limitations and manuscript §8–9 separate portal rows, derived medians, and the structural payoff. |
| E. Statistical conventions | PARTIAL | Denominators, CVaR, Holm family, and percentile vs basic bootstrap are stated. Basic p-values were not the pre-registered test and do not replace it. |
| F. Risk-gate assumptions | PASS | Manuscript calls Stage II an empirical gate. Theorem 1 is disclaimed. Zero-dispatch bug fixed and tested. |
| G. Leakage and baseline fairness | PARTIAL | Decision features are lagged or known at t; payoff weather is realized; code review only. B1 and B2 rerun on the same episodes. MG not rerun. |
| H. Novelty and citations | PASS | `final/NOVELTY_ASSESSMENT.md`. Contribution narrowed. Load-bearing DOIs resolved except the OpenReview bot-check, which is noted. |
| I. Reproducibility | PARTIAL | 23 tests pass. Candidate table rebuilds to the same episodes. Pickle does not load. Byte SHA of candidates differs. |
| J. Manuscript, viva, limitations | PASS | Stage I and Stage II are separated. H2 failure kept. Limitations are in the manuscript and in `final/LIMITATIONS.md`. |

No gate is BLOCKED after the wording and code fixes. Several remain PARTIAL because the Stage I model was not replayed and Stage II is post-hoc.
