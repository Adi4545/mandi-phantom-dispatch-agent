> **Archival Note (Historical Stage-I/II Novelty Challenge):** Preserved for provenance (`R8`). Stage-II CRC/conformal claims were retired (`DIFFICULTY.md`); active surviving novelty is in `final/NOVELTY_V2.md` and `paper/manuscript.md`.

# Adversarial Literature & Novelty Challenge — Stage-II Mechanistic Findings (`MandiGuard-CRC`)

**Scope:** Bibliographic verification of the 6 primary Stage-II anchor citations and an adversarial prior-art challenge against **Finding A (Censored-Arrival Survivorship Bias)**, **Finding B (Heteroscedastic Coverage Illusion)**, and **Finding C (`MandiGuard-CRC`)**.  
**Evidence Anchors Audited:** `src/models/arrival_forecaster.py`, `src/models/uncensored_crc_forecaster.py`, `src/evaluation/run_mechanistic_autopsy_and_crc.py`, `src/evaluation/payoff_model.py`, `results/exp16_censored_bias_and_coverage_illusion.csv`, `NOVELTY_AUDIT.md`, and `paper/references.bib`.

---

## 1. Verified BibTeX Blocks for the 6 Primary Citations

Every field below (author list, exact title, journal/conference, year, volume/number/pages, and DOI/URL) was verified via web search against primary publisher, DBLP, OpenReview, and ACM/AEA/PNAS/T&F/NeurIPS records.

```bibtex
@inproceedings{romano2019conformalized,
  author    = {Romano, Yaniv and Patterson, Evan and Cand{\`e}s, Emmanuel J.},
  title     = {Conformalized Quantile Regression},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS)},
  year      = {2019},
  volume    = {32},
  pages     = {3538--3548},
  url       = {https://proceedings.neurips.cc/paper/2019/hash/5103c3584b063c431bd1268e9b5e76fb-Abstract.html},
  note      = {Preprint: arXiv:1905.03222, DOI: 10.48550/arXiv.1905.03222}
}

@article{lei2018distribution,
  author  = {Lei, Jing and G'Sell, Max and Rinaldo, Alessandro and Tibshirani, Ryan J. and Wasserman, Larry},
  title   = {Distribution-Free Predictive Inference for Regression},
  journal = {Journal of the American Statistical Association},
  year    = {2018},
  volume  = {113},
  number  = {523},
  pages   = {1094--1111},
  doi     = {10.1080/01621459.2017.1307116},
  url     = {https://doi.org/10.1080/01621459.2017.1307116}
}

@inproceedings{angelopoulos2024conformal,
  author    = {Angelopoulos, Anastasios N. and Bates, Stephen and Fisch, Adam and Lei, Lihua and Schuster, Tal},
  title     = {Conformal Risk Control},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2024},
  url       = {https://openreview.net/forum?id=uPD0kqYEfS},
  note      = {ICLR 2024 Spotlight; arXiv preprint arXiv:2208.02814, DOI: 10.48550/arXiv.2208.02814}
}

@inproceedings{lakkaraju2017selective,
  author    = {Lakkaraju, Himabindu and Kleinberg, Jon and Leskovec, Jure and Ludwig, Jens and Mullainathan, Sendhil},
  title     = {The Selective Labels Problem: Evaluating Algorithmic Predictions in the Presence of Unobservables},
  booktitle = {Proceedings of the 23rd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD '17)},
  year      = {2017},
  pages     = {275--284},
  doi       = {10.1145/3097983.3098066},
  url       = {https://doi.org/10.1145/3097983.3098066}
}

@article{levi2020impact,
  author  = {Levi, Retsef and Rajan, Manoj and Singhvi, Somya and Zheng, Yanchong},
  title   = {The impact of unifying agricultural wholesale markets on prices and farmers' profitability},
  journal = {Proceedings of the National Academy of Sciences},
  year    = {2020},
  volume  = {117},
  number  = {5},
  pages   = {2366--2371},
  doi     = {10.1073/pnas.1906854117},
  url     = {https://doi.org/10.1073/pnas.1906854117}
}

@article{goyal2010information,
  author  = {Goyal, Aparajita},
  title   = {Information, Direct Access to Farmers, and Rural Market Performance in Central India},
  journal = {American Economic Journal: Applied Economics},
  year    = {2010},
  volume  = {2},
  number  = {3},
  pages   = {22--45},
  doi     = {10.1257/app.2.3.22},
  url     = {https://doi.org/10.1257/app.2.3.22}
}
```

---

## 2. Adversarial Prior-Art Synthesis & Red-Line Audit

An external statistics, ML, or agricultural economics referee will challenge whether Findings A, B, and C rediscover well-known theorems or recycle classical econometric/conformal machinery. Below is the component-by-component adversarial challenge separating **mandatory concessions** from **genuinely defensible domain discoveries**.

### Challenge 1: Finding A — Censored-Arrival Survivorship Bias
* **Concede:** Complete-case omission (`dropna`) under MNAR outcomes is textbook sample selection (Heckman 1979) and selective-label missingness (Lakkaraju et al. 2017). Moreover, on missing-price rows (`no_exact_variety_3d`), `uncensored_ret` includes structurally modeled diversion/discount penalties (`payoff_model.py`).
* **Defend:** Exact empirical audit in `Exp 16` (`results/exp16_censored_bias_and_coverage_illusion.csv`): even *after* passing `T1`, `d0`-open rates fall monotonically across quote age from `89.10%` (`age_0d`) to `62.63%` (`age_3d` in `Train_2024`; `62.97%` in `Holdout_2025_2026`), causing complete-case arrival regression (`dropna(subset=["target_ret"])`, discarding `55.83%` of raw `Train_2024` corridors) to understate 20th-percentile downside drops by `1.82x–2.00x` in `Train_2024` (`-4.81%` vs `-9.62%` at `age_0d`, `-13.46%` vs `-26.08%` at `age_3d`) and up to **`2.54x`** on `Holdout_2025_2026` (`-10.55%` vs `-26.82%` at `age_3d`).

### Challenge 2: Finding B — Heteroscedastic Coverage Illusion
* **Concede:** Heteroscedastic conditional miscoverage of homoscedastic split conformal is textbook motivation for Lei et al. (2018) and Romano et al. (2019). We do **not** claim a new statistical discovery about conformal prediction.
* **Defend:** `Exp 16` measures the concrete operational manifestation inside Indian wholesale dispatch: commodity-pooled additive quantiles in `MandiGuard v1` produce a **21–23 pp conditional coverage collapse** from calm `Q1` markets (`88.93%` `Val` / `90.46%` `Holdout`) to volatile `Q4` markets (`67.73%` `Val` / `67.80%` `Holdout`, where true Q80 error `14.19%`–`17.08%` exceeds issued cushions `7.18%`–`8.89%` nearly twofold)—simultaneously starving calm corridors of viable dispatches while exposing high-ticket volatile corridors to tail shocks.

### Challenge 3: Finding C — `MandiGuard-CRC`
* **Concede:**
  1. `MandiGuard-CRC` is **NOT** a new theorem and does **not** inherit Theorem 1 finite-sample guarantees of Angelopoulos et al. (2024): daily agri-price series are non-exchangeable, and `(n_l + 1)/(n_d + 1) <= beta_target` calibrates a post-selection conditional dispatch loss rate whose denominator `n_d(lambda)` varies with `lambda`. We state plainly that `MandiGuard-CRC` **adapts the empirical `(n_l + 1)/(n_d + 1)` CRC calibration heuristic** on `Val_2025H1` (`lambda* = 0.15`), analogous to validation-tuned selective risk control (Chow 1970; Franc et al. 2023).
  2. `use_euclid_step0_sort` is elementary zero-call heuristic ranking, and `thin_grade_aware_t1` (`age == 0` fresh exception) is explicitly a **post-diagnostic Stage-II rule revision** motivated by `Exp 3` / `Exp 16` rather than a pre-registered Stage-I confirmation.
  3. Because `UncensoredCRCForecaster` trains on `real_delta_net_inr`, evaluation **must** verify gains on trap-free `Matched_AllTopK_Observed_d0` (`N = 10,162`) as well as the full `Holdout_2025_2026` (`N = 69,526`).
* **Defend:** Diagnoses and resolves why strict rolling `T1` (`open_prob >= 0.50`) suppressed active sub-grade HP Apple markets (`Exp 16`: `77.82%–82.75%` of `MG_v1` refusals on `B2`-dispatched lots came from `T1` rather than `T4`), bridges grade fragmentation insights (Levi et al. 2020; Goyal 2010) to spatial dispatch, and demonstrates strictly out-of-sample gains (`+₹26.38/qtl` over `MG_v1`, `+₹32.51/qtl` over `B2` at `N=69,526`; `+₹22.86/qtl` over `MG_v1` on trap-free `N=10,162`; and `+₹207.02/qtl` on graded HP Apple `2026`).

---

## 3. Thesis Red-Line Guardrails for Stage-II Writing

| Prohibited Overclaim | Defensible Replacement |
|:---|:---|
| *"We prove finite-sample CRC guarantees for dispatch."* | *"Inspired by Conformal Risk Control (Angelopoulos et al., 2024), we adapt the empirical `(n_l + 1)/(n_d + 1) <= beta` validation-tuning heuristic on `Val_2025H1` (`lambda* = 0.15`), auditing realized out-of-sample control directly on `Holdout_2025_2026` without claiming exchangeability-based Theorem 1 guarantees."* |
| *"We discover heteroscedastic miscoverage in split conformal."* | *"We measure how heteroscedastic miscoverage (Lei et al., 2018; Romano et al., 2019) drives a 21–23 pp coverage gap across Indian mandi volatility quartiles in Stage I."* |
| *"Exp 17 confirms pre-registered superiority on HP Apple 2026."* | *"`Exp 17` is strictly labeled a post-diagnostic, validation-calibrated Stage-II study (`lambda* = 0.15` frozen on `Val_2025H1`, zero holdout tuning) separating mechanistic fixes from pre-registered Stage-I commit `e421d15`."* |
