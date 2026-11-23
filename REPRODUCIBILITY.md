# Reproducibility & Cleanroom Guide (`MandiGuard` Revision v6)

## 1. Pinned Environment (`environment/requirements.txt`)
- Tested cleanly on macOS `arm64` and Linux CI (`Python 3.11.5`):
  `numpy==1.24.3`, `pandas==2.0.3`, `pyarrow==11.0.0`, `scipy==1.11.1`, `scikit-learn==1.3.0`, `matplotlib==3.7.2`, `pytest==7.4.0`.
- **Zero ML Pickles & Zero Gitignored Files Required:** `Safe_EV_Sunk_m0`, `Safe_EV_Phys_m0`, and `RT_2F_Min_m0` require zero ML models or checkpoints, rebuilding cleanly solely from tracked raw data (`data/raw/` and `data/processed/`).

## 2. One-Command Cleanroom Reproduction

```bash
pip install -r environment/requirements.txt
make reproduce
```

`make reproduce` executes end-to-end:
1. `revision.build_variant` & `revision.build_hp_apple_lagged` -> strictly `<= t - 1` `lagged_candidates.parquet`, `cleaning_counts.json`, `feature_availability_table.csv`, `lagged_hp_apple_candidates.parquet`.
2. `revision.eval_run` -> baselines, ablations, fixed `State|` cluster keys (`172`/`173` clusters), two-sided Holm `p_holm_2s`, sequential vs hindsight settlement.
3. `revision.sensitivity_a8` -> `epistemic_parameters.csv`, `tornado_sensitivity.csv`, `missing_sensitivity_heterogeneous.csv`.
4. `revision.eval_a10` -> `PREREG_A10.md` (`87a0b62`) + `kappa 0..20` ceiling diagnostic (`a10_summary.json`).
5. `revision.eval_a18` -> locked zero-parameter `Safe_EV_Sunk_m0`, `Safe_EV_Phys_m0` & `RT_2F_Min_m0` (`PREREG_A18.md`, `4cbb02d`) + 3-scheme bootstrap, 36-cell frozen/rescored tornado, Open-MAR/`exact_zero_divert` Manski regimes, `N = 88,014` unconditional origin panel, exact-geocode/non-conflict/`olag 1..3` robustness, 6-state splits, and lagged HP graded apples -> `a18_*.csv`, `a18_summary.json`.
6. `revision.eval_v6` -> strict `2024`-only `171`-market panel (`N = 57,634`), `100.0%`-covered realized ERA5 arrival-weather settlement (zero weather in decisions, closed & open-MAR), exact algebraically verified break-even silent-market thresholds (`resid = 0.0`), and `R = 5,000` paired cluster bootstraps across all 3 `State|` clusterings + 1-, 2-, and 4-week calendar blocks -> `v6_upgrades.csv`, `v6_breakeven.csv`, `v6_bootstrap_5000.csv`, `v6_summary.json`.
7. `revision.make_figures` -> generates `figures/rev_fig1..4*.png`.
8. `scripts/a16_independent_audit.py` -> independent zero-import cleanroom verification within `<= ₹0.01` across all 8 headline policies (`₹0.00`) + `n_clusters <= 178`.
9. `scripts/verify_traceability.py` -> verifies `0` untraceable empirical numbers across all `23/23` active docs.
10. `pytest -v` -> runs all `36` automated unit, leakage, portability, `49/49` citation parity, `R5` commit-order, `v6` break-even/ERA5/`171`-market, and compiled-deliverable integrity tests.

## 3. Google Colab Notebook & Verification Scope
Run [`notebooks/10_finalization_reproduction.ipynb`](notebooks/10_finalization_reproduction.ipynb) or [`notebooks/colab_standalone_reproduction.ipynb`](notebooks/colab_standalone_reproduction.ipynb) directly after cloning branch `finalization`. Clean-clone reproduction certifies **deterministic execution, chronological `<= t - 1` integrity, and internal numerical traceability**—not observed farm-gate income (see [`final/LIMITATIONS.md`](final/LIMITATIONS.md)).
