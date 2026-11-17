# Statistical, Temporal Firewall & Manuscript Verification Audit (`MandiGuard` — Final Sign-Off)

**Auditor:** Statistical & Red-Team Reviewer  
**Project Root:** `/Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent`  
**Audit Date:** 2026-11-17  
**Overall Verdict:** **`PASS`** *(Zero temporal/conformal/weather leakage; Git pre-registration `e421d15` strictly precedes all holdout results; zero numeric discrepancies `> 0.1` and zero mechanistic inaccuracies across all 9 audited docs; `0` banned jargon hits, `31/31` BibTeX citations, `8/8` valid 300-DPI figures, `11/11` executed notebooks, `4.82 MB` Colab bundle, and `18/18` passing unit tests.)*

---

## Executive Summary Table

| Audit Pillar | Status | Key Verification Result |
|:---|:---|:---|
| **1. Zero-Leakage, Git Pre-Registration & Decade/Phase-B Authenticity** | **PASS** | Commit `e421d15` locked `research/hypotheses.md` & `configs/frozen_calibration.json` strictly prior to all `results/*`; `decade_agmarknet_manifest.json` (`42,722,187` raw -> `883,406` balanced rows) and `nasa_power_manifest.json` (`291,384` rows across `114` `0.5°` cells, `0.0%` missing) SHA-256 digests match 100%; `run_creative_decade_and_modern_experiments.py` (`Exp 10`–`Exp 13b`), `ACI` online maturation (`aci_diagnostics.json`), `Val`-frozen satisficing (`₹250/qtl`), and `sample_farmer_sms_cards.txt` strictly causal. |
| **2. Every-Number & Mechanistic Cross-Check (Zero `> 0.1` Discrepancies)** | **PASS** | All 8 prior rounding/wording items AND the `paper/manuscript.md:248` `ZeroCloud_Full` pre-ranking explanation (`src/agents/mandiguard_agent.py:56-75`) are verified exact. **Zero numeric discrepancies `> 0.1`** and **zero mechanistic inaccuracies** across all 9 audited docs (`paper/manuscript.md`, `FINDINGS.md`, `README.md`, `REPRODUCIBILITY.md`, `PROJECT_STATE.md`, `viva/01`–`03`, `EXPERIMENT_REGISTRY.csv`). |
| **3. Manuscript Formatting, Bibliography & Anti-Jargon (`paper/manuscript.md`)** | **PASS** | `0` Git hashes, `0` SHA-256 strings, `0` `pytest` mentions, `0` internal file paths in prose; `8/8` `../figures/fig*.png` links exist on disk; `31/31` BibTeX keys in `paper/references.bib` are cited by `\cite{...}` with `0` missing and `0` uncited; `H2 NOT_SUPPORTED`, `Exp 3` HP Apple LCB tradeoff, and `Exp 4` `No-T3` tradeoff disclosed candidly. |
| **4. Execution Proofs & Checksums** | **PASS** | Re-ran `PYTHONPATH=. /Users/adityasharma/anaconda3/bin/python3 -m pytest -v tests` after final manuscript edit -> **`18 passed in 2.74s`** (matching `results/pytest_execution.log`: `18 passed in 2.71s`); `11/11` notebooks executed with `errors=[]`; `data/processed/colab_data_pack.tar.gz` = `5,049,010` bytes (`4.82 MB < 10 MB`); `8/8` 300-DPI PNG figures (`fig1`–`fig8`) verified. |

---

## 1. Zero-Leakage, Git Pre-Registration & Decade/Phase-B Authenticity

### 1.1 Git Pre-Registration & Primary Firewall
- Verified via `git log --oneline -n 10` and `git status`:
  - Commit `e421d15` (`"Pre-register H1-H4 hypotheses and freeze Val_2025H1 calibration before holdout evaluation"`) remains the sole committed baseline (`Tue Nov 17 14:11:39 2026 +0530`), containing `research/hypotheses.md` and `configs/frozen_calibration.json` (`safety_margin_inr = 50.0`), with zero `results/*` outputs committed.
  - All Phase A (`exp1`–`exp9`, `confirmatory_holm_summary.csv`, `EXPERIMENT_REGISTRY.csv`) and Phase B (`exp10`–`exp13b`, `aci_diagnostics.json`, `sample_farmer_sms_cards.txt`) results sit strictly post-registration in the working tree.

### 1.2 Decade & NASA POWER Manifest SHA-256 Verification
- **`data/manifests/decade_agmarknet_manifest.json`:**
  - `total_raw_csv_rows_streamed_2017_2026` = **`42,722,187`**; `decade_panel_rows` = **`883,406`** (`623,363` across `2017–2023` + `260,043` across `2024–2026` in the fixed `178`-mandi `2024`-ranked panel).
  - Verified SHA-256 digest `d7b90cf7cf6f230d73e37ccc26f127f1afb085a78f2bb3083d81f4304cd4c928` against `data/raw/agmarknet_6state_decade_2017_2026.parquet` (`883,406` rows): **Exact match**.
- **`data/manifests/nasa_power_manifest.json`:**
  - `n_rows` = **`291,384`** daily rows across `n_grid_cells` = **`114`** `0.5°` grid cells (`2017-01-01..2023-12-31`), `raw_null_rates` = `0.0%` across all 4 meteorological variables (`era5_tmax`, `era5_tmin`, `era5_rain_mm`, `era5_rh_mean`).
  - Verified SHA-256 digest `b021f0aecbe48e7ac9aa82f7a5c61a57105b091ef045c00edb5adc7ed3092ca9` against `data/processed/nasa_power_climate_2017_2023.parquet`: **Exact match**.
- Verified `data/interim/candidates_2017_2023.parquet` contains **`2,735,166`** candidate rows across **`516,428`** episodes (matching `PROJECT_STATE.md:14`).

### 1.3 Causal Audit of Phase A & Phase B Pipelines
- **Primary Holdout Bootstrap (`R=5,000, seed=20261117, m=4` Holm):** Independently recomputed `H1` (`+102.7823`, `[48.6649, 153.4512]`, `p_holm = 0.0012`, `SUPPORTED`), `H2` (`+6.1303`, `[-17.0161, 25.0171]`, `p_holm = 0.269946`, `NOT_SUPPORTED`), `H3` (`-0.3729`, `[-0.4019, -0.3424]`, `p_holm = 0.0008`, `SUPPORTED`), `H4` (`-3.0548`, `[-3.4408, -2.6906]`, `p_holm = 0.0008`, `SUPPORTED`), plus `Val_Conformal_Cov` (`78.85%`) and `Holdout_Conformal_Cov` (`79.07%`) matching `results/confirmatory_holm_summary.csv` and `EXPERIMENT_REGISTRY.csv`.
- **`Exp 10` & `Exp 10b`:** Expanding training windows filter strictly `arr_dt <= tw1` prior to each evaluation regime (`2024_ElNino_Heatwave` trains strictly on `2017-01-01..2023-12-26`); exact matched episode counts (`31,997 + 145,972 + 139,032 + 178,197 + 96,468 + 69,526 = 661,192`) verified across `B1`, `B2`, and `MandiGuard_Expanding`.
- **`Exp 11` (Modern AI & Gibbs–Candès ACI):** All predictors fit/seeded strictly on `Train_2024`; `MandiGuard_ACI_NeurIPS21` updates `alpha_comm` (`adaptive_gamma = 0.005`, clipped `[0.02, 0.45]`) strictly upon causal maturation (`matured_dates_heap[0] <= date_t`). `results/aci_diagnostics.json` confirms final alphas (`Holdout_6State`: `Onion 0.244`, `Potato 0.270`, `Tomato 0.038`, `Apple 0.205`; `HP_Apple_2026`: `Apple 0.164`).
- **`Exp 12` & `Exp 13`/`13b`:** Satisficing hurdle (`₹250.0/qtl`) calibrated strictly on `Val_2025H1`; `ZeroCloud_Full` `+₹2.54/qtl` lift verified to arise from `zerocloud_mode=True` pre-ranking Step-0 candidates by `screen_spread - cached_f` prior to `k_max = 5` (`src/agents/mandiguard_agent.py:56-75`); `_exact_vectorized_freight_shift` algebraically verified (`< 1e-9`); `results/sample_farmer_sms_cards.txt` verified (4 real advisories `<= 160` chars).

---

## 2. Every-Number & Mechanistic Cross-Check

All figures across `paper/manuscript.md`, `FINDINGS.md`, `README.md`, `REPRODUCIBILITY.md`, `PROJECT_STATE.md`, `viva/01_plain_english_complete_guide.md`, `viva/02_35_viva_questions_and_answers.md`, `viva/03_spoken_pitches_1m_5m_15m.md`, and `EXPERIMENT_REGISTRY.csv` match `results/confirmatory_holm_summary.csv`, `results/exp1`–`results/exp13b`, `results/aci_diagnostics.json`, `results/sample_farmer_sms_cards.txt`, `configs/frozen_calibration.json`, `data/processed/state_apmc_and_loss_parameters.csv`, `data/raw/official_govt_survey_parameters.json`, and `data/manifests/*.json` with **`0` numeric discrepancies `> 0.1`** and **`0` factual/mechanistic inaccuracies** (`paper/manuscript.md:248` verified fixed).

---

## 3. Manuscript Formatting, Bibliography & Anti-Jargon Audit (`paper/manuscript.md`)

- **Anti-Jargon Audit:** `0` Git commit hashes (`e421d15`, `59bef3f`, or hex strings), `0` SHA-256 strings, `0` `pytest` mentions, and `0` internal paths/extensions (`.py`, `.parquet`, `.csv`, `.json`, `.ipynb`, `.pkl`, `.jsonl`, `.tar.gz`, `.txt`, `src/`, `configs/`, `data/`, `results/`, `notebooks/`) in prose.
- **Figure Links (`8/8` Verified on Disk):** `../figures/fig1_...png` through `../figures/fig8_...png` all exist (`172,886`–`401,299` bytes).
- **Bibliography (`paper/references.bib`):** **`31/31`** BibTeX keys cited by `\cite{...}` in `paper/manuscript.md` (`0` missing, `0` uncited).
- **Honest Scientific Disclosures:** `H2 NOT_SUPPORTED` (`L9, L162, L179`), Grade-Explicit HP Apple conservative LCB tradeoff (`L9, L207, L261`), `Exp 4` `No-T3` tradeoff (`L192, L197`), and `Exp 10b` diminishing multi-year scaling returns (`+₹2.15/qtl`, `L227`) all reported candidly.

---

## 4. Execution Proofs & Artifacts

- **Unit Tests:** Executed `PYTHONPATH=. /Users/adityasharma/anaconda3/bin/python3 -m pytest -v tests` after final manuscript edit -> **`18 passed in 2.74s`**, matching `results/pytest_execution.log` (`18 passed in 2.71s`).
- **Executed Notebooks (`11/11`):** `00`–`09` + `colab_standalone_reproduction.ipynb` all executed with `errors=[]`.
- **Colab Data Pack:** `data/processed/colab_data_pack.tar.gz` = **`5,049,010` bytes (`4.82 MB < 10 MB`)**.
- **Publication Figures (`8/8`):** `fig1`–`fig8` verified as valid 300-DPI RGBA PNGs (`fig1`: `3630x1409` ... `fig7`: `3977x1590`, `fig8`: `3984x1590`).
