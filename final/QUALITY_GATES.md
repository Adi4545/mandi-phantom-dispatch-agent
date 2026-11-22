# Quality gates (after the lagged revision)

| Gate | Result | Evidence |
|---|---|---|
| A. Pre-registration | PARTIAL | Original H1–H4 file is unchanged and H2 stays inconclusive. The lagged margin and the B2 cutoff were chosen on Jan–May 2025 by a rule written in `revision/eval_run.py` before the test printout. They are not the original four hypotheses. |
| B. Claim–evidence | PASS for the narrow claim | Manuscript table matches `revision/results/main_table.csv`. The review's ₹397 / 67,675 table is explicitly not a result. |
| C. Decision-time information | PASS | Quotes through \(t-1\) only. Live weather removed from the primary score. Forecast-versus-ERA5 counts are in `cleaning_counts.json`. |
| D. Settlement | PASS | Sequential is primary. Hindsight is a separate column and is much kinder. |
| E. Missing prices | PASS | Grid by crop and state. Loss rate stable, ES10 not. Wording is "no exact-variety price recorded." |
| F. ES10 | PASS | `revision/es10.py` and `tests/test_es10.py`. Old quantile means are bannered as deprecated. |
| G. Baselines at matched dispatch | PASS | B2 at ₹100 dispatches 73.95%; the cautious rule dispatches 73.73%. The curve is `risk_coverage.csv`. The cautious rule loses on loss rate and ES10. |
| H. Novelty | PASS at the narrow scope | Retrospective scoring under incomplete variety reports, an explicit settlement, and ES10. Not a new phenomenon and not a conformal method. Baulch, Fafchamps and Minten, Ma, and Madaan checked on Crossref. |
| I. Reproducibility of the old pickle | BLOCKED | `forecaster_2024.pkl` needs scikit-learn 1.3.0. No cp312 wheel. Not required for the new tables. |
| J. Untouched holdout | BLOCKED as a claim, disclosed | The paper says there is none. |

Readiness is a conditional pass for the simplified claim only. It is not a pass for the old conformal system or for the unreproduced ₹397 table.
