# Review 3 — reproducibility

Role: reproducibility examiner. Pass 3 of 3, same agent, after the novelty pass. Not independent.

## What reran

- `pytest`: 23 passed on Python 3.12.
- Exp 14 parity function: output CSV identical to the committed file.
- Candidate rebuild: episode table identical; candidate byte hash different.
- B1 and B2 on 69,526 episodes: match published summaries within ₹0.02.
- Exp 18 B1/B2 split: new file, labeled as a slice of the used holdout.

## What did not rerun

`data/interim/forecaster_2024.pkl` records `sklearn_version` 1.3.0. Unpickling on the installed scikit-learn fails. A from-source install of 1.3.0 was stopped because this image was compiling it without a finished result. MandiGuard, B3, B4, coverage, and Exp 15–17 were therefore not regenerated. Their numbers in the paper are the committed CSVs, not a second execution.

Figures were not redrawn. The CSVs behind fig1–fig9 were not changed. New tables are CSV only.

`candidates_6state.parquet` is gitignored and about 77 MB. A clone does not contain it. The rebuild script reproduces episodes. Metric replay of MandiGuard still needs the old sklearn pickle.

## Verdict

A reader can check tests, parity, and the screen and road baselines. A reader on a current scikit-learn cannot replay the confirmatory MandiGuard column without installing 1.3.0. That is a PARTIAL reproducibility gate, and it is why the readiness verdict is not a clean pass.
