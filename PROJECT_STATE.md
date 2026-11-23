# Project State — MandiGuard (Revision v7)

- **Branch & Status:** `finalization` (PR #1; `main` untouched). Revision v7 + 16-Agent Finalization complete across pipeline (`revision/eval_v7.py`, `revision/eval_v7_stress_experiments.py`, `revision/make_figures.py`), manuscript (`paper/manuscript.md`), deliverables (`7` PDFs, `manuscript.tex`, `.docx`, `12` slides), tests, cleanroom audit (`scripts/a16_independent_audit.py`), and traceability gate (`scripts/verify_traceability.py`).
- **Author & Supervision:** Aditya Sharma (M.Tech Thesis Research, supervised by **Dr. Sonia**) — Shoolini University, Solan, Himachal Pradesh, India.
- **Primary Evaluation Panel:** Strict `2024`-selected zero-lookahead `171`-market panel (`N_val = 35,870`, `N_test = 57,634`, `166` clusters $\times$ `23` fortnights, exploratory calendar `2025-06-01..2026-04-08`).
- **Locked Pre-Registered Family:** `PREREG_A18.md` (`4` contrasts `H_A18_1..4`, exact `R = 2,000`) passes with `p_holm_2s_prereg4 = 0.0040` across all `3` clusterings; post-hoc `R = 5,000` (`1w/2w/4w`) stands separately at `p = 0.0024–0.0036`.
- **Headline Primary Numbers (`v7_main_171.csv`):**
  - `B1_lagged_screen`: `₹384.61` Mean, `45.07%` EpLoss, `−₹642.15` `ES10` (`28.67%` / `16,524` divert).
  - `B2_age_matched` (`71.73%`): `₹419.62` Mean, `26.43%` EpLoss, `−₹524.78` `ES10`, `−₹628.37` `cond_ES10`.
  - `Safe_EV_Sunk_m0` (`0` params, `63.23%`): `₹452.74` Mean (`+₹33.12`), `14.88%` EpLoss (`−11.56 pp`), **`−₹345.53` `ES10`** (`+₹179.24` vs `B2`; `+₹91.67` matched vs `RR`), **`−₹447.48` `cond_ES10`** (`+₹180.89`).
  - `Safe_EV_Phys_m0` (`0` params, `60.84%`): `₹449.52` Mean, `13.70%` EpLoss, `−₹334.80` `ES10` (`+₹189.97`), `−₹447.33` `cond_ES10`.
  - `RT_2F_Min_m0` (`0` params, `64.79%`): **`₹463.98` Mean** (`+₹44.36`), `16.21%` EpLoss, `−₹464.84` `ES10`, `−₹618.35` `cond_ES10`.
- **Clean `166`-Mkt `2018–2023` Archive (`N = 383,952`) & Phase 6 (`v7_exp1..5`):** Zero-retuning clean `166`-mkt `2018–2023` (`115`-mkt `N = 325,993`) yields `Safe_EV` `+₹169.27 ES10` & `+₹155.08 cond_ES10` (`p = 0.001`), winning `ES10`/`cond_ES10` in `6/6` years (`2020/2023` Mean NS); Phase 6 verifies `<= t-2` (`p = 0.001`), `S6_Frozen x Stoch_CondMAR_p1.00` (`+₹366.85 cond_ES10`), clean ML/OR Pareto, and SUTVA crowding (`k <= 2`).
- **Pre-Registration, Citations & Repo Hygiene:** `59/59` verified citations; `final/PREREG_A10.md` and `final/PREREG_A18.md` untouched (`Gate J = BLOCKED` prospectively); gitignored `data/interim/omega_lab_*.parquet` kept untracked on disk.
