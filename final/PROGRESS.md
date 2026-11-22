# Progress Log — MandiGuard Finalization (`finalization`, PR #1)

## Step 1: Recon + Baseline Snapshot (`A1` PI) — Completed on `b3bb46f`
- Branch `finalization` checked out tracking `origin/finalization` at `b3bb46f8fee131218d6154898f4d0659b3018fa4` (`main`/`omega-research-lab`/`omega-x-scientific-audit` untouched).
- Python `3.11.5`, `numpy 1.24.3`, `pandas 2.0.3`, `scikit-learn 1.3.0`, `scipy 1.11.1`, `pyarrow 11.0.0`, `pytest 7.4.0`. Legacy `forecaster_2024.pkl` loads cleanly in sklearn `1.3.0`.
- Baseline `pytest -v`: **25 passed, 1 failed** (`M7` stale `## 9. Conclusion` lookup in `test_creative_decade_results_files_non_empty`).

## Step 2: Data Forensics & Timing Firewall (`A2`/`A3`) — Commit `f08c875`
- Rebuilt `revision/build_variant.py` and `revision/build_hp_apple_lagged.py` strictly from tracked primary files (`agmarknet_6state_top_apple_2024_2026.parquet`, `hp_apple_daily_2025_2026.csv`, `osrm_corridor_matrix.parquet`, `state_apmc_and_loss_parameters.csv`, `mandi_coordinates.parquet`, `mandi_weather_2024_2026.parquet` strictly `< 2025-01-01`). Zero dependence on gitignored `candidates_6state.parquet` (`C1`, `M5/M6` fixed).
- Reconciled exact cleaning funnel (`260,043 -> 759 dropped -> 259,284 -> 256,997 -> 248,302 -> 95,074` Top-5 episodes: `36,398` val, `58,676` test; HP Apple `2,802` episodes) and audited `98.64%` ERA5-identical weather leak.
- Fixed `M7` & added `tests/test_timing_and_leakage_r3.py` -> **30 passed**.

## Steps 3 & 4: Sequential Settlement, Matched Ablations, Inference & Sensitivity (`A4`–`A8`) — Commit `19ae655`
- Implemented destination-gross-sale fees (`0` intra-district or divert, `M9` fixed), equal quote-age baselines (`B2_age_matched`, `B_simple_activity`), matched-dispatch `T1`–`T4` ablations, paired two-way cluster bootstrap for Mean/EpLoss/`ES10` across `origin_x_2week` and `b2dest_or_origin_x_2week` with Holm FWER, crop/state splits, HP Apple lagged table, and primary-source `A8` sensitivity (`NITI Aayog 2021`, `RBI WP 08/2024`, `NABCONS 2022`, `GoHP Economic Survey 2025–26`, `PIB 154554`).

## Step 5: Pre-Registered `RR-Abstain` (`A9`–`A12`) — Commits `87a0b62` (Pre-Reg) & `5bf43cf` (Eval + `NOVELTY_V2`)
- Verified 9 new DOIs/URLs via Crossref/JSTOR/JMLR and committed `final/PREREG_A10.md` + `paper/references.bib` at **`87a0b62`** BEFORE writing `revision/eval_a10.py`.
- Executed `eval_a10.py` ONCE (`5bf43cf`): `kappa* = 5.0`, `m*_matched = ₹3.73/qtl` (zero-cutoff `m=0` matches `₹475.76`). On `test` (`N=58,676`, `exploratory: true`), `RR_Abstain_matched` (`69.02%`) reached Mean `₹475.36` (`+₹41.80` vs `B2_age`), EpLoss `17.23%` (`−9.49 pp`), `ES10 −₹460.72` (`+₹64.54` vs `B2_age`, `+₹52.06` vs `MG_matched`, `p_holm = 0.0020` both clusterings), Non-Apple `+₹78.10 ES10`, holds down to `div = 0.0`. Completed `final/NOVELTY_V2.md`; `31/31` pytest passed.

## Step 6: Code Figures & Clean-Clone Reproducibility (`A13`) — Commit `93cb333`
- Built `revision/make_figures.py` (`rev_fig1..4*.png`), updated `revision/build_run.py`, `environment/requirements.txt`, `Makefile`, `.github/workflows/ci.yml`, `notebooks/10_finalization_reproduction.ipynb`.
- Clean-clone reproduction in `/tmp/mandiguard_clean_repro` (zero `candidates_6state.parquet`): `CLEAN_CLONE_MAX_ABS_DIFF = 0.0`, `31/31` pytest passing.

## Step 7: Plain-English Manuscript, Verified Viva & Traceability Gate (`A14`, `A15`, `R2`) — Commit `69c6704`
- Rewrote `paper/manuscript.md` (with worked numeric examples for every equation), `final/VIVA_QA.md`, `final/DIFFICULTY.md` (`4.3 -> 1.6 / 5`), and `viva/00..03*.md` (`C2` fixed).
- Built `scripts/verify_traceability.py` + `revision/results/verified_numbers.json` -> `0` untraceable numbers across all 6 documents; `32/32` pytest passed.

## Step 8: Independent Audit (`A16`), `final/*` & Top-Level Sync (`M8`) — Commit `73439b8`
- Fixed `Min_Price` canonical market-minimum aggregation inside `scripts/a16_independent_audit.py` -> exact **`₹0.00`** discrepancy across all headline metrics (`B1`, `B2_age_matched`, `RR_Abstain_matched`, `RR_Abstain_m0`).
- Generated `final/AUDIT_V4.md`, `CLAIM_MATRIX.md`, `ISSUE_REGISTER.md`, `RESPONSE_TO_REVIEW_3.md`, `LIMITATIONS.md`, `QUALITY_GATES.md`, `READINESS.md`, synchronized `README.md`, `FINDINGS.md`, `PROJECT_STATE.md`, `REPRODUCIBILITY.md`.

## Step 9: Final Adversarial Loop, Clean-Clone Check & PR #1 Push
- Converted `paper/manuscript.md` figure links to repo-relative `../figures/rev_fig*.png` and spotlighted threshold-free `RR_Abstain_m0` (`S_RR > 0`, 1 scalar parameter).
- Rewrote `final/SLIDE_OUTLINE.md`, `final/SIMPLIFIED_DESIGN.md`, and `paper/12th_class_easy_reading_edition.md` to Revision v4 verified truth, and added archival banners to superseded pre-v4 logs (`M8`).
- Expanded `scripts/verify_traceability.py` across all `9/9` active documents (`0` untraceable numbers) and locked portability (zero local user paths), figure-target existence, BibTeX key sync, and `R5` pre-registration git commit order in pytest (`33/33` passing).
- Executed final clean-clone `make reproduce` (`CLEAN_CLONE_MAX_ABS_DIFF = 0.0`) and pushed `finalization` to `origin` (PR #1).
