# MandiGuard (Revision v4): Audited Spatial Dispatch and Reporting-Reliability-Aware Abstention (`RR-Abstain`) for Indian Wholesale Markets

[![Python 3.11.5](https://img.shields.io/badge/Python-3.11.5-blue.svg)](environment/requirements.txt)
[![Tests](https://img.shields.io/badge/pytest-32%20passed-brightgreen.svg)](Makefile)

**`MandiGuard` Revision v4** (branch `finalization`, PR #1) audits when online Indian AGMARKNET price spreads between wholesale yards (*mandis*) fail under realistic transport costs, destination-base APMC statutory fees, NABCONS 20°C post-harvest decay, and strictly sequential arrival settlement across six states (`Maharashtra`, `Uttar Pradesh`, `Karnataka`, `Madhya Pradesh`, `Gujarat`, `Himachal Pradesh`) and four commodities (`Onion`, `Potato`, `Tomato`, `Apple`).

## Verified Current Results (`make reproduce` — Strictly `<= t - 1`, `N = 58,676` Test Episodes)

Everything in [`paper/manuscript.md`](paper/manuscript.md) and [`revision/results/`](revision/results/) builds deterministically from **tracked primary files only** (zero reliance on gitignored `candidates_6state.parquet`, zero live/ERA5 weather leaks, zero pickled ML trees, zero conformal overclaims). Calendar test split `2025-06-01..2026-04-08` was previously exposed in repo commits (`exploratory: true`), while **`RR-Abstain`** (`A10`) was strictly pre-registered in [`final/PREREG_A10.md`](final/PREREG_A10.md) (`87a0b62`) before coding [`revision/eval_a10.py`](revision/eval_a10.py).

| Policy (`N = 58,676`, Sequential 20°C) | Dispatch Rate | Mean Net (₹/qtl) | Episode Loss Rate | Exact `ES10` (₹/qtl) | Source |
|---|---:|---:|---:|---:|---|
| **`B1_lagged_screen`** (`lag_spread > ₹100`, 1–7d) | `100.00%` | `₹397.87` | `45.21%` | `−₹641.26` | [`revision/results/a10_results.csv`](revision/results/a10_results.csv) |
| **`B2_age_matched`** (`lag 1–3`d, val `₹200`) | `72.03%` | `₹433.56` | `26.72%` | `−₹525.25` | [`revision/results/a10_results.csv`](revision/results/a10_results.csv) |
| **`B_simple_activity_matched`** (`rep14>=0.5`, val-match) | `70.73%` | `₹440.97` | `23.48%` | `−₹506.28` | [`revision/results/a10_results.csv`](revision/results/a10_results.csv) |
| **`MG_matched`** (hard gates `T1..T4`, val-match) | `69.51%` | `₹467.90` | `18.57%` | `−₹512.78` | [`revision/results/a10_results.csv`](revision/results/a10_results.csv) |
| **`RR_Abstain_matched`** (`kappa*=5.0`, val-match `₹3.73`) | **`69.02%`** | **`₹475.36`** | **`17.23%`** | **`−₹460.72`** | [`revision/results/a10_results.csv`](revision/results/a10_results.csv) |
| **`RR_Abstain_m0`** (`kappa*=5.0`, zero cutoff `S_RR > 0`) | `69.52%` | `₹475.76` | `17.43%` | `−₹461.74` | [`revision/results/a10_results.csv`](revision/results/a10_results.csv) |

- **Statistical Inference (`a10_bootstrap.csv`):** `RR_Abstain_matched` beats `B2_age_matched` on Mean (`+₹41.80`, Holm `p = 0.0020`), EpLossRate (`−9.49 pp`, Holm `p = 0.0020`), and `ES10` (`+₹64.54`, Holm `p = 0.0020`), and beats `MG_matched` on `ES10` (`+₹52.06`, Holm `p = 0.0020`) across both `origin_x_2week` and `b2dest_or_origin_x_2week` clusterings.
- **Generalizability & Prominent Limitations (`R6`–`R7`):** Non-apple crops (`N = 52,207`) gain `+₹78.10 ES10` (Onion, Potato, Tomato all positive); `RR_Abstain` beats `B2`/`B1` down to `div = 0.0`; however, legacy Stage I `H2` stays inconclusive (`+₹6.13`, `p = 0.2699`), HP graded apples (`N = 2,802`) remain volatile (`44.63%` cond. loss rate), NITI Aayog bulk freight flips unmatched `MG`, and no untouched post-April-2026 fold exists (Gate J = `BLOCKED`, disclosed). Modeled payoffs $\ne$ observed farmer cash income; missing quotes $\ne$ physical yard locks.

## Quick Cleanroom Reproduction (`make reproduce`)

```bash
pip install -r environment/requirements.txt
make reproduce
```

Runs `revision.build_variant`, `revision.build_hp_apple_lagged`, `revision.eval_run`, `revision.sensitivity_a8`, `revision.eval_a10`, `revision.make_figures`, independent cleanroom re-derivation [`scripts/a16_independent_audit.py`](scripts/a16_independent_audit.py) (`₹0.00` discrepancy), scripted traceability check [`scripts/verify_traceability.py`](scripts/verify_traceability.py) (`0` untraceable numbers), and `pytest -v` (`32/32` passing).

## Repository Map
- **`paper/`**: Plain-English 10–12pp thesis manuscript [`manuscript.md`](paper/manuscript.md) and verified BibTeX [`references.bib`](paper/references.bib).
- **`revision/`**: Self-contained leak-free builder, sequential evaluator, `A8` sensitivity, pre-registered `RR-Abstain` (`eval_a10.py`), `make_figures.py`, and CSV/JSON outputs in [`revision/results/`](revision/results/).
- **`final/`**: Independent audit [`AUDIT_V4.md`](final/AUDIT_V4.md), [`PREREG_A10.md`](final/PREREG_A10.md), [`CLAIM_MATRIX.md`](final/CLAIM_MATRIX.md), [`NOVELTY_V2.md`](final/NOVELTY_V2.md), [`ISSUE_REGISTER.md`](final/ISSUE_REGISTER.md), [`RESPONSE_TO_REVIEW_3.md`](final/RESPONSE_TO_REVIEW_3.md), [`DIFFICULTY.md`](final/DIFFICULTY.md), [`VIVA_QA.md`](final/VIVA_QA.md), [`LIMITATIONS.md`](final/LIMITATIONS.md), [`QUALITY_GATES.md`](final/QUALITY_GATES.md), [`READINESS.md`](final/READINESS.md), [`PROGRESS.md`](final/PROGRESS.md).
- **`viva/`**: Verified oral defense guides [`00`–`03`](viva/00_career_defense_master_sheet.md) (`0` untraceable numbers).
- **`tests/`**: `32` automated unit & counterfactual `R3` property tests ([`test_timing_and_leakage_r3.py`](tests/test_timing_and_leakage_r3.py)).
- **`notebooks/10_finalization_reproduction.ipynb`**: Colab-ready reproduction notebook from tracked files only.
- **`results/`, `src/`**: Archived Stage I / II historical pipeline & outputs preserved cleanly for provenance (`H2` inconclusive retained).
