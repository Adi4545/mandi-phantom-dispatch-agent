> **Archival Note (Historical Stage-I/II Sign-Off):** Preserved for provenance (`R8`). Superseded by **Revision v5** (`Safe_EV_Sunk_m0`, `RT_2F_Min_m0`, `8.7/10` sign-off) in `final/AUDIT_V4.md` and `final/READINESS.md`.

# Final Independent Red-Team & Thesis Examiner Sign-Off (`06`)

## 1. Independent Multi-Agent Review Sign-Off Summary

Two independent post-remediation review agents completed three full adversarial verification rounds over code, raw/processed data manifests, CSV outputs, figures, BibTeX sources, manuscript, viva materials, and the HTML/PDF handbook inside `/Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent`:

| Reviewer Role | Conversation ID | Round 1 | Round 2 | Round 3 Final Verdict |
|:---|:---|:---|:---|:---|
| **Final Statistical & Anti-HARKing Red-Team Auditor** (`statistical_and_redteam_reviewer`) | `d7bd083c-1cc4-478c-9f18-22c7e4602428` | `BLOCK` | `BLOCK` *(2 blockers + 2 docs)* | **`PASS`** |
| **Final Thesis Examiner & Viva/PDF Auditor** (`academic_reviewer`) | `0c81b685-fe18-42cf-8880-f04930eade9a` | `BLOCK` | `BLOCK` *(3 surgical fixes)* | **`PASS`** |

---

## 2. Chronicle of Remediated Defects (Round 1 $\to$ Round 3)

1. **Chronological Validation & Leakage Firewall (`src/evaluation/run_mechanistic_autopsy_and_crc.py`):**
   - Enforced `arr_dt <= splits["val_end"]` (`2025-05-31`) inside both `run_exp16_mechanistic_autopsy` (`L82-86`) and `run_exp17_uncensored_crc` (`L192-196`), narrowing `Val_2025H1` strictly to `N = 42,794` settled H1 episodes (matching Stage I), and enforced `arr_dt <= "2026-05-31"` on `HP_Warmup` (`wu_ap`, `L146`).
   - Wired `assert_no_future_leakage_dates(tr_arr_clean, va, cfg)` into both `run_exp16_mechanistic_autopsy` (`L89`) and `run_exp17_uncensored_crc` (`L200`).
   - Exposed `policy_lambda_used` (`0.1` for `Rung2_UncensoredCRC_StrictT1`, `0.15` for `Rung3_MandiGuard_CRC`) inside `results/exp17_uncensored_crc_validation.csv`.
   - Re-executed `Exp 16`–`Exp 17` cleanly (`exit 0`): `MandiGuard-CRC` validation selection stayed $\lambda^* = 0.15$ (`Val_2025H1`: `56.60%` disp, `₹365.46/qtl`, `9.15%` cond LTR; `Rung 2`: $\lambda^* = 0.10$, `57.14%` disp, `₹358.52/qtl`, `9.34%` cond LTR) and `Holdout_2025_2026` (`N = 69,526`, `₹479.17/qtl`), `Matched_AllTopK_Observed_d0` (`N = 10,162`, `₹533.75/qtl`), and `HP_Apple_Grade_2026` (`N = 1,537`, `₹812.08/qtl`) remain unchanged.
2. **Code-to-Manuscript Alignment (`paper/manuscript.md` Section 7.8 & Appendix):**
   - Harmonized `Rung 1` (`L311`), `Rung 2` (`L312–314`), and `Rung 3` (`L315`) strictly with `src/models/uncensored_crc_forecaster.py` and `src/evaluation/run_mechanistic_autopsy_and_crc.py`: identical `screen_spread > ₹100/qtl` Step-0 candidate pool (`candidates_6state.parquet`, up to 12 candidates/episode) sorted descending by `1.20x` Euclidean freight-adjusted spread before `K_max = 5`; `274,296` settled 2024 post-`T1` (`static_net > 0`) training corridors; uncalibrated `HistGradientBoostingClassifier.predict_proba` loss head; $\lambda \in \{0.00, 0.05, \dots, 1.20\}$ first-feasible `break` at $\beta_{\text{target}} = 0.095$ (explicitly disclaiming Angelopoulos et al. 2024 Theorem 1 guarantees); and exact `fresh0 | strict` admission rule (`age == 0` exact-variety/grade quotes with `open_prob_14d >= 0.20` and `dow_open_rate >= 0.25`).
   - Updated `Table 8` and `Table 9` `Val_2025H1` rows (`N = 42,794`; `Q1` `32,290` `88.91%` vs `Q4` `32,281` `67.84%`, `-21.07 pp`; `MG_v1` `₹351.48` vs Sec 4.3 `₹351.36` documented in Table 9 footnote), added bold `Table 1` and `Table 2` captions, refined Tier-2 `L73` `2,082` vs `2,042` (`<= 2026-04-13` mirror window overlap), added `**Table 4** below` forward reference (`L179`), and fixed chronological figure ordering (`Figure 1..7`, `Figure 8A–B` [`Exp 16`] / `Figure 8C` [`Exp 17`], `Figure A1A–B` in Appendix).
3. **Primary-Source BibTeX, Registry, Viva, Visualization & Handbook PDF Polish:**
   - Verified `37/37` `paper/references.bib` entries against primary venues (`madaan2019price`, `ma2019price`, `guo2020mandi`, `franc2023optimal`, `biradar2026agrimarket` [`Divyashree, N. & Biradar, Anu Vittal`], `manimegalai2026mandicast`, `deka2026missing`, `kachuee2019opportunistic`), synced `research/literature_matrix.md`, and eliminated the duplicate `viva/02_35_viva_questions_and_answers.md` file and `README.md` link.
   - Regenerated `figures/fig4_tool_budget_pareto.png`, `figures/fig6_sensitivity_and_govt_fees.png`, and `figures/fig9_mechanistic_autopsy_and_uncensored_crc.png` (`width=0.66`, `q80:` label fit verified inside bars across Q1–Q4).
   - Fixed `+₹234.20` Tomato arithmetic, stripped stray raw markdown inside HTML, and rebuilt `docs/MandiGuard_First_Principles_and_Thesis_Defense_Handbook.pdf` (`5.41 MB`, 9 embedded figures, `Q1..Q50`, zero hype/stale terms).
   - Synchronized `88.91%–90.46%` vs `67.84%–67.80%` (`14.12–17.08%` vs `7.15–8.89%`) across `FINDINGS.md`, `NOVELTY_AUDIT.md`, `PROJECT_STATE.md`, `RESEARCH_DECISIONS.md`, `EXPERIMENT_REGISTRY.csv`, and `viva/`.

---

## 3. Verified Pre-Registration Separation & Integrity Checks

- **Stage-I CSV Immutability:** `git diff --name-only HEAD --` across `results/confirmatory_holm_summary.csv`, `results/exp1..exp13b*.csv`, and `results/exp15_missing_data_open_yard_sensitivity.csv` is empty — Stage I (`e421d15`) remains completely frozen.
- **Stage-II Boundary:** `Exp 16`–`Exp 17` and `MandiGuard-CRC` are quarantined as **`[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]`**, calibrated solely on `Val_2025H1` (`N = 42,794`) with zero holdout tuning and zero distribution-free exchangeability Theorem 1 claims.
- **Automated Test Suite:** `PYTHONPATH=. /Users/adityasharma/anaconda3/bin/python3 -m pytest -v tests` passed **`22/22`** cleanly (`results/pytest_execution.log`) after all code and documentation edits.
- **Citation, Size & Secret Checks:** `37/37` BibTeX parity (`missing=set()`, `unused=set()`), `9/9` figure paths resolve on disk, zero non-gitignored files `>= 10 MB` (`colab_data_pack.tar.gz` = `4.83 MB`, Handbook PDF = `5.41 MB`), and zero leaked tokens.
