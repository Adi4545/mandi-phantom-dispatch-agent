# Reproducibility & Cleanroom Guide (`MandiGuard` Revision v4)

## 1. Pinned Environment (`environment/requirements.txt`)
- Tested cleanly on macOS `arm64` and Linux CI (`Python 3.11.5`):
  `numpy==1.24.3`, `pandas==2.0.3`, `pyarrow==11.0.0`, `scipy==1.11.1`, `scikit-learn==1.3.0`, `matplotlib==3.7.2`, `pytest==7.4.0`.
- **No ML Pickle Required:** Revision v4 replaces the brittle `scikit-learn 1.3.0` pickle (`data/interim/forecaster_2024.pkl`) with simple calculator equations (`RR-Abstain`), so `make reproduce` runs cleanly on any modern Python 3.11 environment without binary model dependencies.
- **No Gitignored Files Needed:** Does **not** read `data/processed/candidates_6state.parquet`. Every intermediate table is rebuilt cleanly from tracked `data/raw/` and static `osrm_corridor_matrix.parquet`.

## 2. One-Command Cleanroom Reproduction

```bash
pip install -r environment/requirements.txt
make reproduce
```

`make reproduce` executes in ~2 minutes:
1. `python3 -m revision.build_variant` -> builds strictly `<= t - 1` `lagged_candidates.parquet`, `cleaning_counts.json`, `feature_availability_table.csv`.
2. `python3 -m revision.build_hp_apple_lagged` -> builds `lagged_hp_apple_candidates.parquet` and `hp_apple_cleaning_counts.json`.
3. `python3 -m revision.eval_run` -> sequential & hindsight settlement, equal-menu baselines (`B1`, `B2_fresh`, `B2_age_matched`, `B_simple_activity`), `T1..T4` matched ablations, two-clustering bootstrap (`origin_x_2week` & `b2dest_or_origin_x_2week`), `risk_coverage.csv`, `by_crop_state.csv`, `hp_apple_lagged.csv`.
4. `python3 -m revision.sensitivity_a8` -> `epistemic_parameters.csv`, `tornado_sensitivity.csv`, `missing_sensitivity_heterogeneous.csv`.
5. `python3 -m revision.eval_a10` -> evaluates pre-registered `RR-Abstain` (`final/PREREG_A10.md`, `87a0b62`) -> `a10_*.csv`, `a10_summary.json`.
6. `python3 -m revision.make_figures` -> generates `figures/rev_fig1..4*.png`.
7. `python3 scripts/a16_independent_audit.py` -> independent zero-import re-derivation verifying `<= ₹0.01` agreement (`₹0.00`).
8. `python3 scripts/verify_traceability.py` -> verifies `0` untraceable empirical numbers in `paper/manuscript.md` & `viva/`.
9. `python3 -m pytest -v` -> runs all `32` tests including counterfactual `R3` leakage tests.

## 3. Google Colab Notebook
Run [`notebooks/10_finalization_reproduction.ipynb`](notebooks/10_finalization_reproduction.ipynb) directly after cloning branch `finalization` (`git clone -b finalization https://github.com/Adi4545/mandi-phantom-dispatch-agent.git`).

## 4. Verification Scope
Clean-clone reproduction certifies **deterministic code execution, chronological leakage immunity (`<= t - 1`), and internal figure traceability (`0` discrepancy)**—not field-measured farmer profits or physical yard lockouts (see `final/LIMITATIONS.md`). Legacy Stage I scripts live under `src/` for historical completeness.
