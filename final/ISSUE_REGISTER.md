# Issue register

Reviews below are sequential passes by one agent, not independent reviewers.

| ID | Severity | Issue | Disposition |
|---|---|---|---|
| I1 | High | Abstract and README treated the 58.94% trap flag as arrival at a closed market. The flag is true whenever `wait_days > 0`, including 7,724 exact-variety sales after a wait. The no-quote “closed_yard_divert” branch is 8,026/63,040 (12.73%) and still means “no commodity row”, not a witnessed closure. | Fixed in manuscript, README, FINDINGS. New table `results/exp1b_b1_outcome_types.csv`. |
| I2 | High | Stage II (`Exp 16`) reports holdout diagnostics and `Exp 17` evaluates the redesigned rule on that same holdout. No later unused date range is in the shipped panels. | Left as post-hoc. Documented. Exp 18 is explicitly not untouched. |
| I3 | Medium | `forecaster_2024.pkl` needs scikit-learn 1.3.0 and does not load here. H1–H4, B3, B4, and MandiGuard were not resimulated. | Open. B1, B2, and Exp 14 were resimulated. Noted in REPRODUCIBILITY.md. |
| I4 | Medium | Rebuilt candidate parquet byte SHA ≠ manifest. Episode rows match exactly. B1/B2 metrics match within ₹0.02 (B1 mean ₹349.999 vs published ₹350.01). | Documented. Content check passes for payoff policies. Historical byte hash is writer-specific. |
| I5 | Medium | `(n_d = 0)` used to set CRC risk to 0, so a never-dispatch rule could pass the gate. | Fixed. Risk is 1 when there are no dispatches. Test added. Published λ = 0.15 has 56.6% validation dispatch in the stored CSV, so this branch was not the one that selected λ. Exp 17 was not rerun. |
| I6 | Medium | 2,296 extra duplicate rows in the 2024–2026 panel; 1,489 keys have more than one modal. Builder takes the median. 799 raw rows have modal outside [min, max]. | Documented. Not rewritten, because changing the panel would move the pre-registered numbers. |
| I7 | Medium | Bootstrap comment said the draws were centered under the null. The p-value is the percentile tail. | Comment corrected. `p_value_basic` added. Published Stage I p-values remain the percentile ones. |
| I8 | Low | README mixed H3’s −37.29 pp episode incidence with the 45.28% and 9.97% conditional loss-trip rates (difference 35.31 pp). | Fixed. Test locks the identity. |
| I9 | Low | Biradar author order reversed relative to the PDF byline; URL path case 404; Mandi Cast had no URL; Deka DOI capitalisation 404s on Crossref. | Bib updated. |
| I10 | Low | Pre-registration is a git author date. The runner script is in the same commit as the hypotheses. | Not repairable after the fact. Status CONDITIONAL. |
| I11 | Info | Mahajan and Tomar Crossref issued year 2020 vs bib year 2021. | Left. Issue year of AJAE 103(1) is 2021. |
| I12 | Info | Statutory fee is applied to the local modal, not the destination sale. Freight and spoilage are assumed. | Documented. Not recoded. |
