> Historical assessment at b399358. Later checks and dispositions appear in the [correction record](CORRECTIONS.md) and [independent review](reviews/corrections-qa.md).

# Progress log

Base commit at start: `d20a0cb25827b73688e4ced19948ac5c01e49f6b` on `main`.
Work branch: `finalization` (not merged).

1. Read README, PROJECT_STATE, RESEARCH_DECISIONS, FINDINGS, NOVELTY_AUDIT, EXPERIMENT_REGISTRY, REPRODUCIBILITY, hypotheses, manuscript, payoff, bootstrap, CRC, manifests.
2. Baseline tests on this machine: 22 passed before new tests (Python 3.12.3). Environment was missing pytest; installed user-site scientific stack (pytest 9.2.0, numpy 2.5.5, pandas 3.1.1).
3. Pre-registration: `e421d15` author date 2026-11-17 14:11 +0530. `hypotheses.md` and `frozen_calibration.json` are unchanged since then. Result CSVs first appear in `2663e42` at 15:33 +0530. The holdout runner was already in `e421d15`. No external registry.
4. Rebuilt gitignored `candidates_6state.parquet`. Episode frame equals the tracked parquet. Byte SHA does not equal the manifest (`1750397d…` vs `ea5ac38a…`).
5. Recomputed `B1` and `B2` on the holdout. Means, loss rates, trap flag, and CVaR match the published CSV within ₹0.02. Outcome-type split written to `results/exp1b_b1_outcome_types.csv`.
6. Exp 14 parity function rerun: CSV byte-identical; manifest timestamp restored.
7. `forecaster_2024.pkl` is scikit-learn 1.3.0. Load failed on current scikit-learn (`__pyx_unpickle_CyHalfSquaredError`). A source build of 1.3.0 was stopped before it finished. `MandiGuard`, `B3`, and `B4` were not resimulated.
8. Exp 18 is a split of the already-used holdout at 2026-02-12 for `B1`/`B2` only. An untouched Stage II test is not feasible from shipped dates.
9. Code fixes kept: zero-dispatch risk gate no longer scores as 0; bootstrap return value distinguishes percentile and basic p-values; tests now 23 passed.
10. Prose and citation fixes: missing quote is not a closure; H3 denominator; Biradar byline and URL; Mandi Cast URL; Deka DOI case.
11. Stopped the unfinished scikit-learn 1.3 source build. Restarted from the payoff path only.
12. Exp 1b and Exp 18 written. B1/B2 mismatches versus published summaries: none above ₹0.02. Late slice B2 − B1 = −₹113.06 (N = 9,886).
13. Pytest after the new tests: 23 passed. Deliverables under `final/`.
