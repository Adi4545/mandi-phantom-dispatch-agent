> Historical assessment at b399358. Later checks and dispositions appear in the [correction record](CORRECTIONS.md) and [independent review](reviews/corrections-qa.md).

# Novelty assessment

## What the prior literature already contains

Checked against Crossref, arXiv, publisher pages, or the paper PDF text on 2026-11-21.

- Spatial arbitrage and price dispersion: Jensen, QJE 2007, DOI `10.1162/qjec.122.3.879` (Kerala fisheries, phones reduce dispersion). Sekhar, Food Policy 2012, DOI `10.1016/j.foodpol.2012.03.002` (mandi integration). Chatterjee and Kapur, India Policy Forum, RePEc `v13y2017` (the bib year is 2017; there is no DOI). Negi et al., Food Policy 2018, DOI `10.1016/j.foodpol.2018.10.008`. Goyal, AEJ Applied 2010, DOI `10.1257/app.2.3.22`. Mitra et al., REStat 2018, DOI `10.1162/rest_a_00699` (potato middlemen; not a dispatch benchmark). Levi et al., PNAS 2020, DOI `10.1073/pnas.1906854117`.
- Mandi forecasting: Madaan et al., COMPASS 2019, DOI `10.1145/3314344.3332488`. Ma et al., ICTD 2019, DOI `10.1145/3287098.3287100`. Guo et al., AAAI 2020, DOI `10.1609/aaai.v34i08.7039`. Deka, arXiv:2610.39949 (exists; title matches; Crossref 404 was the capitalised DOI; lowercase `10.48550/arxiv.2610.39949` is the working form). Biradar and Divyashree, IJEDR 2026: the numbered byline is Biradar then Divyashree; the uppercase PDF URL returns HTML 404; `https://rjwave.org/ijedr/papers/IJEDR2603265.pdf` resolves. Manimegalai et al., IJRPR 7(11), 2026, pages 1–5: `https://ijrpr.com/uploads/V7ISSUE11/IJRPR72000.pdf`. These last two are short applied system papers, and Mandi Cast’s reported MAPE is on synthetic demo data.
- Selective labels: Lakkaraju et al., KDD 2017, DOI `10.1145/3097983.3098066`. That paper is about labels missing because a decision-maker did not treat the case. A missing AGMARKNET row is closer to non-reporting or censoring than to that mechanism. The citation is an analogy.
- Selective prediction: Chow, IEEE Trans. IT 1970, DOI `10.1109/TIT.1970.1054406`. Franc, Průša, and Voráček, JMLR 2023, `https://jmlr.org/papers/v24/21-0048.html` (no DOI in the bib; page returns 200).
- Conformal methods: Angelopoulos and Bates, FnT ML 2023, DOI `10.1561/2200000101`. Lei et al., JASA 2018, DOI `10.1080/01621459.2017.1307116`. Romano, Patterson, and Candès, NeurIPS 2019 (proceedings page 200). Gibbs and Candès, NeurIPS 2021 (proceedings page 200). Angelopoulos, Bates, Fisch, Lei, and Schuster, Conformal Risk Control, ICLR 2024, OpenReview `uPD0kqYEfS`. The live OpenReview HTML was bot-challenged from this machine; the bibliographic identity is the standard ICLR 2024 paper. Theorem 1 needs exchangeable scores and a loss whose calibration denominator does not depend on the chosen threshold in the way `(n_loss+1)/(n_dispatch(λ)+1)` does.
- Other bib checks: Hersbach et al., QJRMS 2020, DOI `10.1002/qj.3803`. Luxen and Vetter, SIGSPATIAL 2011, DOI `10.1145/2093973.2094062`. Sparks, JOSS 2018, DOI `10.21105/joss.01035`. Phipson and Smyth 2010, DOI `10.2202/1544-6115.1585`. Han, Buntine, and Shareghi, Findings of ACL 2024, DOI `10.18653/v1/2024.findings-acl.398`. Yao et al. and Kachuee et al. arXiv abstracts return 200. Mahajan and Tomar: Crossref `issued` year is 2020; the bib year 2021 matches the AJAE 103(1) issue label. Holm 1979 has no DOI in the bib. 37 keys are cited and 37 entries exist.

## Terminology

“Phantom spatial arbitrage” is a name for apparent portal spreads that do not survive variety match, quote timing, road cost, and a structural spoilage model. Jensen and the mandi-integration papers already study spreads that are not realizable. The name is useful packaging. It is not evidence of a new phenomenon.

## Narrowest defensible contribution

A public, time-ordered, multi-state retrospective **decision evaluation** of perishable dispatch rules on AGMARKNET, in which:

1. Stage I, with hypotheses frozen in git before the result CSV commit, finds a higher modeled mean than screen-chasing and a lower episode loss incidence than point-forecast dispatch, and does **not** find a significant mean gain over a same-day price plus road-cost rule.
2. The gain over screen-chasing is sensitive to the non-quote penalty. The stored Exp 15 zero-penalty cell has MandiGuard below B1 on the mean.
3. Stage II is an after-the-fact redesign on the same holdout. Its risk gate is an empirical validation rule, not conformal risk control.

That is an applied measurement and systems result suitable for an M.Tech defense if those three sentences are the claim. It is not a new estimator, not a theorem, and not a measured change in farmer income.
