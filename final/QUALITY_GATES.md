# Verification & Quality Gates (Revision v8 — Honest Candidate C Synthesis)

| Gate | Requirement | Status | Evidence |
|---|---|---|---|
| **Gate A** | Zero day-`t` leak & zero weather features in decision scoring (`R3`) | **PASS** | `pytest -v` (`test_timing_and_leakage_r3.py` counterfactual corruption tests) |
| **Gate B** | Zero-lookahead `2024` primary market selection (`171` mkts, `N = 57,634`) | **PASS** | `v7_summary.json`, `v7_main_171.csv`, `v7_era5_and_reconcile.csv` |
| **Gate C** | Specification-locked exploratory `PREREG_A18` `4`-test `R = 2,000` (`p_holm_2s <= 0.0040`), `cond_ES10`, `D_S ∩ D_B`, & `CGM G/(G-1)` | **PASS** | `v7_bootstrap_prereg_2000.csv` (`3` clusterings, `H_A18_2` `+₹91.67`), `CommonIntersection_DS_cap_DB` (`n = 33,398`), UP `q10=0` (`7.28%`), `p_wild_webb6_1w_block_only`, `HP g_star_block = 1.535` |
| **Gate D** | Clean non-lookahead `166`-mkt `2018–2023` (`N = 383,952`) & `115`-mkt (`N = 325,993`), `481/647` reverse-survivorship disclosed | **PASS** | `v7_decade_2018_2023.csv`, `v7_decade_by_year*.csv` (`6/6` yrs `ES10`/`cond_ES10`; `2020/2023` Mean NS noted), updated NASA POWER × Sched #7 (`₹328.15` vs `₹284.26`) |
| **Gate D2** | Phase 6 stress suite (`<= t-2`, fixed `_spoil_return_leg` `S6`, coupled Manski `cond_ES10`, `17m` ML/CQR + `2×2` ortho, `clean_market_query`, `PhoneCall_TopK_Open`, `Outsider`, `HP_Apple_ScaleNonInv`, SUTVA `k <= 2`) | **PASS** | `v7_exp1..5*.csv`, `v7_exp_summary.json`, `src/data/build_road_network.py` |
| **Gate E** | Cleanroom independent recomputation (`<= ₹0.01` on `171` & clean `166`-mkt panels) | **PASS** | `scripts/a16_independent_audit.py` + `n_clusters <= 178` invariant |
| **Gate F** | `23`-doc numeric traceability (`0` untraceable numbers) & `59/59` citation bijection | **PASS** | `scripts/verify_traceability.py` |
| **Gate G** | Pre-registration immutability (`R5`) & cache hygiene (`R8`) | **PASS** | `PREREG_A10.md` & `PREREG_A18.md` unmodified; `omega_lab_*.parquet` untracked |
| **Gate H** | Presentation (`7` PDFs, `manuscript.tex`, `DOCX`, `59` `(Author, Year)`, `<= 15`p, `12` slides) | **PASS** | `scripts/build_*.py`, `pytest -v` deliverable assertions & visual inspection |
| **Gate I** | Clean-clone reproduction (`0.0` max abs CSV diff) | **PASS** | `Makefile` `reproduce` target verified in clean temp clone |
| **Gate J** | Prospective post-April-2026 live FPO phone-confirmation trial | **BLOCKED** | Public bulk archives stop `2026-04-13`; next research phase |
