> **Archival Note (Superseded by `final/PROGRESS.md`):** This earlier roadmap recorded an intermediate Review-2 draft before Revision v4 (`build_hp_apple_lagged.py`, `eval_a10.py`, `make_figures.py`, `scripts/verify_traceability.py`, `final/AUDIT_V4.md`). See `final/PROGRESS.md` for the completed pipeline.

# Roadmap (E)

Order is the order the revision was built. Effort is relative to this codebase, not calendar time. Importance is for the defense.

| Order | File | What it does | Effort | Importance |
|---|---|---|---|---|
| 1 | `revision/es10.py`, `tests/test_es10.py` | Exact worst-10% ES with a fractional boundary | Small | High. Removes a false downside number. |
| 2 | `revision/build_variant.py` | Lagged quotes (through \(t-1\)), cleaning counts, 2024 climatology | Medium | High. Decision-time prices. |
| 3 | `revision/eval_run.py` | Sequential vs hindsight settlement, no-weather payoff, validation-frozen cutoffs, risk-coverage, penalty grid, crop and state, two clusterings | Medium | High. The tables in the paper. |
| 4 | `revision/build_run.py` | Runs 2 then 3 | Small | High. The command the paper cites. |
| 5 | `revision/results/*` | Output of that command | — | High. Do not edit by hand. |
| 6 | `paper/manuscript.md` | 10–12 page plain-English paper on three questions | Medium | High. |
| 7 | `paper/references.bib` | Baulch 1997 DOI `10.2307/1244145`; Fafchamps and Minten 2012 DOI `10.1093/wber/lhr056`; Ma and Madaan already checked | Small | High. |
| 8 | `final/VIVA_QA.md` | Beginner answers | Small | Medium. |
| 9 | README, FINDINGS, viva banners | Stop quoting the old quantile-tail mean as ES10 | Small | Medium. |

Not done, and why:

- Replay of `forecaster_2024.pkl` (old MandiGuard, B3, B4, Exp 15–17). The file needs scikit-learn 1.3.0. This image is Python 3.12, and 1.3.0 has no wheel for it. A source build was stopped. The simplified paper does not use that model.
- The review's 67,675-episode table. The scripts were not in the repo. The rebuild does not recover those rupee figures. They are not in the paper.
- A grade-explicit lagged replay. The apple candidate file has no arrival-price columns. The old failure (about ₹605 vs ₹1,151) is reported as not resimulated.
