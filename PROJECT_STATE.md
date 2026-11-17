# Project State — `MandiGuard`

**Last Updated:** 2026-11-17 (Complete End-to-End Pipeline Executed & Audited)  
**Active Project Directory:** `/Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent`  
**Status:** Core `Exp 1`–`Exp 10b` & `Exp 14`–`Exp 15` + Appendix Illustrations (`Exp 11`–`Exp 13b`, not main contributions) + audit updates complete (19/19 unit tests passing for deterministic execution/schema/split hygiene, 11/11 notebooks executed with zero errors including `4.82 MB` `colab_data_pack.tar.gz`, 8 300-DPI PNG figures, `paper/manuscript.md`, `paper/12th_class_easy_reading_edition.md`, and `viva/` suite).

---

## Completed Datasets & Provenance
1. **AGMARKNET 10-Year Archive Panel (2017-01-01 to 2026-04-13) + HP Apple Grade Panel (2025-11-07 to 2026-09-01):** 42,722,187 raw streamed CSV rows from a public archive mirror -> 883,406 balanced rows across 178 2024-ranked mandis (623,363 in 2017–2023 + 260,043 in 2024–2026) + 4,427 grade-explicit HP Apple rows (42 mandis) + 22 live Nov-2026 `agmarknet.gov.in` queries (11/22 non-reporting over 7 days) + single-day official `data.gov.in` Resource `9ef84268-d588-465a-a308-a864a43d0070` XML spot-check on 2023-10-18 (100.00% `Min_Price`/`Max_Price` and 99.42% `Modal_Price` parity across 172 matched core-panel keys).
2. **OSRM Real Highway Matrix:** 220 district-validated geocoded mandis -> 8,147 intra-state road corridors (15–500 km, auction arrival lags 1–3 days).
3. **Climate Dataset:** 141,955 daily rows (2024–2026, 145 `0.1°` grids, 0.0% missing: 145/145 ERA5 + 102/145 Open-Meteo Historical NWP + 43 causal nowcasts) plus 291,384 NASA POWER daily rows (2017–2023, 114 `0.5°` grids, 0.0% missing).
4. **GoI Central & State Survey Parameters:** 8 archived `pib.gov.in` HTML/PDF releases + GoHP Economic Survey 2025–26 -> `data/processed/state_apmc_and_loss_parameters.csv`.
5. **Episode & Candidate Panels:** 239,809 6-state 2024–2026 episodes (209,450 active shortlist, 1,457,515 candidate rows), 4,129 HP Apple grade episodes (3,923 active shortlist, 33,090 candidate rows), and 2,735,166 candidate rows across 516,428 2017–2023 episodes (661,192 total matched decade episodes across `Exp 10`).

---

## Executed Validation, Decade, Sensitivity & Appendix Milestones
* **Pre-Registration Commit (`e421d15`):** Locked `research/hypotheses.md` and `Val_2025H1`-frozen `safety_margin_inr = ₹50.0/qtl` (78.85% empirical conformal coverage) strictly before touching holdout (`>= 2025-06-01`).
* **View 1 — Confirmatory Holdout Outcomes (`N = 69,526` shortlisted episodes; 174 origin mandis $\times$ 23 2-week blocks; $R = 5{,}000$ cluster bootstrap; 79.07% holdout LCB coverage):**
  * `H1` (`MandiGuard > B1` Mean $\Delta\text{Net}$): **+₹102.78/qtl**, 95% CI [+₹48.66, +₹153.45], $p_{\text{Holm}} = 0.0012$ (`SUPPORTED`).
  * `H2` (`MandiGuard > B2` Mean $\Delta\text{Net}$): +₹6.13/qtl, 95% CI [-₹17.02, +₹25.02], $p_{\text{Holm}} = 0.2699$ (`NOT_SUPPORTED` — `H2` failed on mean profit; `MandiGuard` reduces loss-trip rate from 18.11% to 9.97% and `CVaR_10%` from -₹436.67 to -₹37.89/qtl; an exploratory 4-state NWP check yields +₹31.82/qtl).
  * `H3` (`MandiGuard < B3` Ep. Phantom Loss): **-37.29 pp**, 95% CI [-0.4019, -0.3424], $p_{\text{Holm}} = 0.0008$ (`SUPPORTED`).
  * `H4` (`MandiGuard` Calls `< 0.75 * B4` Calls): **-3.05 calls** (8.75 vs 15.74 = 44.4% reduction), 95% CI [-3.44, -2.69], $p_{\text{Holm}} = 0.0008$ (`SUPPORTED` — an expected design consequence of cheap-first ordering; helpful under tight query caps like `B = 6`, while direct rupee API savings are minor relative to crop profit).
* **View 2 — Fair Matched Complete-Observation Cohorts & Trap-Penalty Crossover (`Exp 15`):**
  * Fair matched guaranteed-open cohort (`6_Fair_Matched_AllTopK_Observed_d0`, `N = 10,162` identical episodes across all 4 policies, zero simulated trap rules): `MandiGuard` earns ₹510.89/qtl (6.82% LTR, -₹36.07 `CVaR_10%`), beating `B1` (₹472.51, +₹38.38) and `B2` (₹469.99, +₹40.91), while unfiltered point-ML `B3` earns ₹553.22/qtl (+₹42.33 higher) at 2.2x higher LTR (14.77%) and 10x deeper tail losses (-₹362.40). On `7_Fair_Matched_AllTopK_Observed_3d` (`N = 16,849`), `MandiGuard` earns ₹592.53/qtl (7.74% LTR) vs `B1` ₹581.06 (+₹11.47), `B2` ₹572.09 (+₹20.44), and `B3` ₹670.38 (15.02% LTR).
  * Trap-penalty crossover curve (`N = 69,526`, Regimes 1–5): `MandiGuard` leads `B1` and `B3` from `1.5x`/`10%` (+₹102.78 / +₹121.94), through `1.0x`/`10%` (+₹91.66 / +₹109.39) and `0.5x`/`5%` (+₹42.43 / +₹46.12), plus `₹0` break-even on missing-3d trips (+₹82.26 / +₹73.61), crossing below `B1`/`B3` on mean only at `0.0x` return freight and `0%` variety discount (-₹10.00 vs `B1`, -₹20.93 vs `B3`, while cutting LTR roughly three-fold to 6.09%).
* **Core Decade & Provenance Extensions (`Exp 10`, `Exp 10b`, `Exp 14`):** 6-regime decade stability (Loss-Trip Rate 8.78%–12.03%, +₹165.14/qtl over `B1` in 2024 El-Niño), 1-Yr vs 8-Yr scaling (₹452.79 -> ₹454.94/qtl), and `Exp 14` single-day `data.gov.in` Resource `9ef84268` XML spot-check (100.00% `Min_Price`/`Max_Price`, 99.42% `Modal_Price` across 172 matched keys).
* **Appendix Illustrations (`Exp 11`–`Exp 13b`, Exploratory — Not Main Contributions):** Plug-in predictors & NeurIPS'21 `ACI` (`Direct_Quantile_GBDT_Q20` ₹459.02, `Deep_MLP_Conformal` HP Apple ₹615.34, `MandiGuard_ACI` reducing HP Apple worst-10% loss from -₹102.76 to -₹74.42/qtl), `MandiGuard-ZeroCloud` + Satisficing (3.84–5.53 live calls, modeled API spend reduction up to 75.6% at ₹0.05/call), `FPO` 90-qtl pooling (₹477.28/qtl under 0.70x modeled freight), `Split_Top2_Portfolio` (9.85% traps), and $Q_{10}$ spoilage clock + SMS cards.
* **Verification Scope:** 19/19 `pytest` tests pass, verifying **deterministic code execution, schema/checksum parity, and chronological split hygiene—not real-world economic truth** (trucking costs, $Q_{10}$ spoilage, and closed-yard penalties lack field weighment receipts or farmer survey validation).
