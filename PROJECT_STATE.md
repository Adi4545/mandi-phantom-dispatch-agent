# Project State — `MandiGuard`

**Last Updated:** 2026-11-17 (Complete End-to-End Pipeline Executed & Verified)  
**Active Project Directory:** `/Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent`  
**Status:** Phase A & Phase B Complete & Verified (`18/18` unit tests passing, `11/11` notebooks executed clean with zero errors including `<5 MB` `4.82 MB` Colab bundle, `8` 300-DPI figures visually verified, `Exp 1`–`Exp 13b` + updated `manuscript.md` + `viva/` suite complete). Pending final red-team audit sign-off and final Git commit.

---

## Completed Datasets & Provenance
1. **Official AGMARKNET 10-Year Panel (`2017-01-01`..`2026-04-13`) + HP Apple Grade Panel (`2025-11-07`..`2026-09-01`):** **`42,722,187` raw streamed CSV rows -> `883,406` balanced rows across `178` `2024`-ranked mandis** (`623,363` in `2017–2023` + `260,043` in `2024–2026`) + `4,427` grade-explicit HP Apple rows (`42` mandis) + `22` live Nov-2026 official API queries (`11/22` non-reporting 7d).
2. **OSRM Real Highway Matrix:** `220` district-validated geocoded mandis -> `8,147` intra-state road corridors (`15–500 km`, auction arrival lags `1–3 days`).
3. **Climate Dataset:** `141,955` daily rows (`2024–2026`, `145` `0.1°` grids, `0.0%` missing: `145/145` ERA5 + `102/145` Open-Meteo Historical NWP + `43` causal nowcasts) plus **`291,384` NASA POWER daily rows (`2017–2023`, `114` `0.5°` grids, `0.0%` missing)**.
4. **Verified GoI Central & State Surveys:** `8` archived `pib.gov.in` HTML/PDF releases + `GoHP Economic Survey 2025–26` -> `data/processed/state_apmc_and_loss_parameters.csv`.
5. **Episode & Candidate Panels:** `239,809` 6-state `2024–2026` episodes (`209,450` active shortlist, `1,457,515` candidate rows), `4,129` HP Apple grade episodes (`3,923` active shortlist, `33,090` candidate rows), and `2,735,166` candidate rows across `516,428` `2017–2023` episodes (`661,192` total matched decade episodes across `Exp 10`).

---

## Executed Validation, Decade & Creative Milestones
* **Pre-Registration Commit (`e421d15`):** Locked `research/hypotheses.md` and `Val_2025H1`-frozen `safety_margin_inr = ₹50.0/qtl` (`78.85%` empirical conformal coverage) strictly before touching holdout (`>= 2025-06-01`).
* **Confirmatory Holdout Outcomes (`N = 69,526` shortlisted episodes; `174` origin mandis $\times$ `23` 2-week blocks; $R = 5{,}000$ cluster bootstrap; `79.07%` holdout LCB coverage):**
  * `H1` (`MG > B1` Mean $\Delta\text{Net}$): **`+₹102.78/qtl`**, `95% CI [+48.66, +153.45]`, $p_{\text{Holm}} = 0.0012$ (`SUPPORTED`).
  * `H2` (`MG > B2` Mean $\Delta\text{Net}$): `+₹6.13/qtl`, `95% CI [-17.02, +25.02]`, $p_{\text{Holm}} = 0.2699$ (`NOT_SUPPORTED` — nearly halves `B2` phantom loss risk `18.11% -> 9.97%` and tail `CVaR_10%` `-₹436.67 -> -₹37.89/qtl`; beats `B2` by `+₹31.82/qtl` on the `4` native-NWP states).
  * `H3` (`MG < B3` Ep. Phantom Loss): **`-37.29 pp`**, `95% CI [-0.4019, -0.3424]`, $p_{\text{Holm}} = 0.0008$ (`SUPPORTED`).
  * `H4` (`MG` Calls `< 0.75 * B4` Calls): **`-3.05 calls`** (`8.75` vs `15.74` = `44.4%` reduction), `95% CI [-3.44, -2.69]`, $p_{\text{Holm}} = 0.0008$ (`SUPPORTED`).
* **Phase B Extensions (`Exp 10`–`Exp 13b`):** 6-regime decade stability (`Loss-Trip Rate 8.78%–12.03%`, `+₹165.14/qtl` El-Niño peak), `1-Yr` vs `8-Yr` scaling (`₹452.79 -> ₹454.94/qtl`), Modern AI & NeurIPS'21 `ACI` (`Direct_Quantile_GBDT_Q20` `₹459.02`, `Deep_MLP` HP Apple `₹615.34`, `ACI` `-27.6%` HP tail loss), `MandiGuard-ZeroCloud` + Satisficing (`3.84` live calls, `-75.6%` API spend), `FPO 90-qtl` Pooling (`₹477.28/qtl`), `Split Top-2` (`9.85%` traps), & Biological Spoilage Clock.
* **Verification:** `18/18` `pytest` tests passed; `00`–`09` + clean-room `colab_standalone_reproduction.ipynb` (`4.82 MB` `colab_data_pack.tar.gz`) executed cleanly (`Errors: []`); `8` 300-DPI PNG figures (`fig1`–`fig8`) generated and inspected.
