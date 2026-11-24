# 50 Examiner Viva Questions & Scripted-Verified Answers (`Revision v8 — Honest Candidate C Synthesis`)

**Author & Supervision:** Aditya Sharma (M.Tech Thesis Research, supervised by **Dr. Sonia**) — Shoolini University, Solan, Himachal Pradesh, India.
Every number below traces directly to `revision/results/v7_*.csv`, `v7_exp1..5*.csv`, `v7_summary.json`, and `v7_exp_summary.json` (`0` untraceable claims).

---

## Theme I — Research Problem, Literature (`59` Citations) & Novelty (Q1–Q10)

**Q1. What core real-world failure does MandiGuard diagnose?**
Blindly chasing top `<= t - 1` AGMARKNET spreads `> ₹100/qtl` (`B1_lagged_screen`) across `57,634` zero-lookahead `171`-market episodes averages `₹384.61/qtl` with **`45.07%`** episode losses and **`ES10 −₹642.15/qtl`**, largely because `28.67%` (`16,524` trips: `15,960 d0 + 364 d1 + 200 d2`) encounter zero uploaded destination commodity trade sequentially.

**Q2. How do you position your novelty without misrepresenting prior agricultural economics?**
We explicitly distinguish **problem/evaluation novelty** from **methodological novelty** (`final/NOVELTY_V2.md`). We do **not** claim prior economists assumed quotes are `MAR`, we do **not** claim zero-parameter rules beat all ML, nor do we claim a statistical theorem or novel OR optimizer. We formalize how sequential wholesale execution interacts with AGMARKNET non-reporting and benchmark zero-tuned-parameter domain triage honestly against full-season `17m` ML and fixed heteroscedastic Split-CQR models.

**Q3. How do DeMiguel et al. (2009) and Gigerenzer & Gaissmaier (2011) relate to your zero-tuned-parameter rules?**
DeMiguel et al. (2009) proved naive `1/N` heuristics can rival or outperform sample-optimized portfolios when estimation variance dominates, and Gigerenzer & Gaissmaier (2011) formalized less-is-more heuristics under low signal-to-noise. Together they explain why `m = 0` `Safe_EV_Sunk_m0` transfers across `166` clean markets (`2018–2023`) and captures `~98.8%` of `17m MeanQ10` Mean and `~94%` of `cond_ES10` tail protection with zero training history (`v7_exp4`).

**Q4. How does MandiGuard differ from Madaan et al. (2019), Ma et al. (2019), and `mandi2024dfl` (2024)?**
Madaan et al. forecast prices, Ma et al. impute missing AGMARKNET entries statistically, and `mandi2024dfl` (*JAIR* 80) surveys Decision-Focused Learning (`DFL`) benchmarks and differentiable combinatorial optimization (never mandi procurement). None evaluate sequential spatial truck dispatch with day-`0` missing-quote censoring (`16,524` diversions) or benchmark conditional tail shortfall `cond_ES10` alongside full-season `17m` ML and zero-tuned-parameter triage (`v7_exp4`).

**Q5. How does MandiGuard compare to Vargas, Klapp & Mac Cawley (2026, *IJPR*)?**
Vargas et al. (2026) formulate mean-variance produce distribution with postponed shipment. We benchmark `OR_Vargas_MeanVar` directly (`v7_exp4`): because of its quadratic $\text{INR}^2$ penalty, at `gamma = 0.0002` it reaches `Mean ₹430.53/qtl` and `cond_ES10 −₹511.42/qtl`, trailing `Safe_EV_Sunk_m0` (`₹452.74/qtl`, `cond_ES10 −₹447.48/qtl`); switching to scale-invariant IQR dispersion (`OR_Stylized_MeanSD_17m_valmatch`, `EV - 0.35*IQR`, `61.40%`) improves OR to `Mean ₹443.57/qtl` and `cond_ES10 −₹439.77/qtl`.

**Q6. What role do Jensen (2007), Fafchamps & Minten (2012), and Ziegler et al. (2019) play?**
Fafchamps & Minten (2012) and Mitra et al. (2018) explain why raw public prices fail to generate frictionless arbitrage; Jensen (2007) and Ziegler et al. (2019) show Indian farmers/traders rely on simple morning phone calls to *arhtiyas*. MandiGuard acts purely as a `6 a.m.` pre-call portal filter before dialing.

**Q7. Why use Rockafellar & Uryasev (2000) `ES10` instead of VaR alone, and Manski (1990) bounds?**
Exact fractional `ES10` coherently averages worst-decile ruin (augmented by conditional `cond_ES10`), while Manski (1990) nonparametrically brackets silent day-`0` quotes between closed-yard diversion and optimistic `Open-MAR` without unverifiable imputation.

**Q8. Are all `59` citations in `paper/references.bib` verified and matched across formats?**
Yes — `scripts/verify_traceability.py` enforces a strict `59/59` 4-way bijection across `paper/references.bib`, `paper/manuscript.md` body cites, `## References`, and `deliverables/manuscript.tex` `\citep` calls.

**Q9. What is the conceptual progression from Stage I (`4.3/5`) to Revision v8 (`1.2/5`)?**
Stage I relied on weather-leaking GBDT (`H2` `+₹6.13/qtl` NS); `A10` tested tuned regret (`RR_Abstain` hit ceiling `kappa* = 5.0`); Revision v8 establishes zero-parameter rules (`m = 0`, `9` fixed structural choices incl. `z = 1.0`) reducing complexity `4.3 -> 1.6 -> 1.2 / 5` while transparently contrasting them against fixed heteroscedastic Split-CQR and full-season `17m` ML (`v7_exp4`).

**Q10. What happens if someone already knows a yard is open (`PreChoice_AllCandidates_ExactD0`)?**
In `v7_exp3` across `N = 24,654` open-only episodes, `Safe_EV_Sunk_m0` trails `B2` slightly on Mean (`−₹20.74/qtl`: `₹457.48` vs `₹478.23`) yet still gains **`+₹260.20/qtl` on `ES10`** (`−₹184.60` vs `−₹444.80`) because avoiding high-variance volatile spikes remains valuable even on open yards.

---

## Theme II — Mathematics, Formulas & Worked Examples (Q11–Q20)

**Q11. Why does `Safe_EV_Sunk_m0` carry literally zero fitted parameters (`m = 0`), and what are its `9` structural choices?**
`p_dow = (k + 1)/(n + 2)` is a textbook uniform Laplace success rate over the prior 8 same-weekdays, `G_1SD` deducts `z = 1.0` rolling 28-day standard deviation of volatility (`1 - cv28`, `0.05` fallback when `cnt28 < 2`) and deterministic stylized fees across `age 1..3`, `spread > 100`, `top_k = 5`, and `threshold = 0` (`9` fixed structural choices incl. `z = 1.0`). Zero weights, multipliers, or cutoffs are fitted on validation or test outcomes.

**Q12. What is the algebraic relationship between `Safe_EV_Sunk_m0` (`p_dow * G_1SD > F`) and `Safe_EV_Phys_m0`, and what does `2×2` orthogonal decomposition show?**
Using the exact algebraic identity **`p_dow * G_1SD - F == p_dow*(G_1SD - F) + (1 - p_dow)*(-1.0*F)`**, `Safe_EV_Sunk_m0` treats closure payoff as sunk outbound freight (`-1.0F`, not literal `0`!), whereas `Safe_EV_Phys_m0` aligns the lower bound with `1.5F` physical settlement (`p_dow * (G_1SD - F) - (1 - p_dow) * 1.5 * F > 0`, lowering EpLoss `14.88% -> 13.70%` and `ES10 −₹345.53 -> −₹334.80` while matching `cond_ES10 −₹447.33` vs `−₹447.48`). In the closed-yard `2×2` orthogonal decomposition (`v7_exp4`), `Ortho_Pure_cv28_only` (`71.91%`, matched to `B2` `71.73%`: `Mean ₹421.62`, `ES10 −₹387.46`, `cond_ES10 −₹447.13`) shows **`cv28` alone drives ~100% of `cond_ES10` truncation**, whereas `Ortho_Pure_pdow_only` (`84.10%`, `Mean ₹466.68`, `ES10 −₹546.75`, `cond_ES10 −₹607.18`) shows **`p_dow` drives Mean lift & diversion avoidance** (`ScaleInv_Safe_EV_24tau`: `53.19%`, `₹431.30 / 11.33% / −₹288.61 / −₹421.27`).

**Q13. Explain `RT_2F_Min_m0` (`p_min * G > 2F`) on an ordinary 4-function phone calculator.**
Multiply plain fee-adjusted spread `G = P_dest*(1 - fee) - P_orig` by conservative reporting frequency `p_min = min(rep28, p_dow)`, and dispatch only if it beats round-trip freight `2F`. It needs no volatility `cv28` or biological decay, leading Mean payoff at `₹463.98/qtl` (`+₹44.36` vs `B2`), though weaker on tail protection (`cond_ES10 −₹618.35`).

**Q14. Walk through the exact 10-second arithmetic example from Section 3.**
<!-- WORKED_EXAMPLE_START -->
Route `200 km` in MP (`F = 35 + 0.45*200 = ₹125`, fee `1.5%`, `P_orig = ₹1,500`, `P_dest = ₹2,000`, `cv28 = 0.15`): `G = ₹470`, `G_1SD = 2,000*(0.85)*(0.985) - 1,500 = +₹174.50`. On a steady Tuesday (`p_dow = 0.90`, `p_min = 0.85`): `Safe_EV = 0.90*174.50 - 125 = +₹32.05` (Dispatch) and `RT_2F = 0.85*470 - 250 = +₹149.50` (Dispatch). On a Sunday-closed yard (`0.20`): `B2` gives `+₹345` (blind Dispatch), while `Safe_EV = −₹90.10` and `RT_2F = −₹156.00` (Abstain).
<!-- WORKED_EXAMPLE_END -->

**Q15. Is `p_dow * G_1SD - F > 0` equivalent to `G_1SD / F > 1 / p_dow` under corridor selection (`argmax`)?**
The accept/abstain decision boundary is mathematically identical (`F > 0`, `p_dow > 0`), **but** selecting the best corridor by INR surplus (`argmax (p_dow * G_1SD - F)`) vs dimensionless ratio (`argmax (G_1SD / F - 1 / p_dow)`) is not rank-invariant: `v7_exp4` shows ratio argmax switches `5,113` (`14.03%`) test destinations (`Mean ₹437.28`, `ES10 −₹329.26`), so the paper selects corridors explicitly by INR net surplus.

**Q16. How many test observations hit the sparse volatility fallback `cnt28 < 2`, and what about `cv28 == 0`?**
`cnt28 < 2` triggers on only `77 / 36,441` (`0.21%`) dispatched test rows (`0.05` floor). Extending the `0.05` guard to exact `cv28 == 0` rows affects `5,274` candidate rows (`v7_exp4`) and yields nearly identical performance (`Mean ₹452.10`, `ES10 −₹345.52`, `cond_ES10 −₹447.65`).

**Q17. What happens if `K <= 5` candidate shortlist truncation (`top_k = 5`) or `> ₹100` spread pre-filter is removed?**
In `v7_exp4`, setting `top_k = None` across all `307,242` (`> ₹100`) or `414,880` (`> ₹0`, `N = 63,683`) corridor rows raises `Safe_EV_Sunk_m0` slightly (`Mean ₹454.37`, `ES10 −₹344.47`; all-spreads `ES10 −₹324.19` vs `B2 −₹497.41`), proving conclusions are not artifacts of top-5 truncation.

**Q18. Check worked Example 1 and Worked Example 2 for algebraic accuracy.**
<!-- WORKED_EXAMPLE_START -->
In Example 1 (`F = ₹125`, `0.8125%` 9h spoilage -> `₹1,983.75`, dest `1.5%` fee -> `₹1,953.99`): `+₹1,953.99 - ₹1,500 - ₹125 = +₹328.99/qtl`. In Example 2 (blind 2-day diversion when `d0, d1 = 0` & `d2 = ₹1,450`): sequential turn-back gives `−₹199.69/qtl`, vs false 3-day hindsight `+₹239.97/qtl` (computed with `0` waiting cost). Exact hand parity confirmed (`a16_independent_audit.py`).
<!-- WORKED_EXAMPLE_END -->

**Q19. Why test a `Beta(0.5, 0.5)` Jeffreys prior and `z = 0.5` / `1.5` volatility multipliers?**
In `v7_exp4`, swapping Laplace `(k+1)/(n+2)` for Jeffreys `(k+0.5)/(n+1)` shifts Mean slightly (`₹453.58`, `ES10 −₹343.46`). Adjusting `z` trades Mean vs tail (`z = 0.5`: `Mean ₹471.44 / cond_ES10 −₹528.38`; `z = 1.5`: `Mean ₹417.23 / cond_ES10 −₹417.55`), showing `z = 1.0` wasn't cherry-picked for extrema.

**Q20. Could a reader claim `z = 1.0`, `lag in 1..3`, or `spread > 100` are hidden tuned parameters?**
`z = 1` (`G_1SD`) and `2F` are standard uncalibrated 1-SD and round-trip baselines fixed a priori across `171` markets and clean `166`-mkt `2018–2023`, and we show sensitivity across `z = 0.5..1.5`, `<= t-2` (`lag 2..3`), and `spread > 0` (`top_k = None`) in `v7_exp1` & `v7_exp4`.

---

## Theme III — Dataset Provenance, Causal Firewall & Hygiene (Q21–Q30)

**Q21. Walk through the `171`-market cleaning funnel (`257,576 -> 57,634`).**
Raw `257,576` records drop `759` invalid rows (`modal` outside `[min, max]`) leaving `256,817`; raw-key dedup keeps `254,533` (`1,481` conflicting duplicate groups dropped); variety consolidation keeps `245,838`; shortlist forms `93,504` (`35,870` val through `2025-05-31`, `57,634` test `2025-06-01..2026-04-08`).

**Q22. Why switch from `178` markets to `171` primary and `173 -> 166` Clean `2018–2023`, and what is reverse-survivorship?**
The earlier `178` markets filtered across the full `2024–2026` span (post-`2024` lookahead). Restricting selection strictly to `2024` (`>= 80` days, `<= 30`/state) gives zero-lookahead `171` markets (`−₹13.26` `B1` shift; `−₹31.16` total with ERA5 `−₹17.90`). Intersecting the legacy `173`-mkt extract (`N = 389,357`) with `171` removes all `7` post-`2024` lookahead yards, producing **clean `166` markets (`N = 383,952`)** and **`115` `2017`-active markets (`N = 325,993`)** — explicitly conditioned on `2018–2023` reverse-survivorship (`481/647` historical yards absent from the `2024` frame).

**Q23. How do you prove zero `>= t*` future price leakage (`R3`), and what cannot be proven without upload timestamps?**
Counterfactual `pytest` mutates `>= t*` destination & origin prices to absurd constants and asserts zero change in prior candidate scores or selections. True portal upload timestamps are unavailable historically, which we stress directly via `<= t - 2` latency in `v7_exp1`.

**Q24. How did Stage I leak ERA5 weather (`98.64%`), and how is ERA5 handled now?**
Audit `N1` discovered historical daily ERA5 predictors matched settlement-day arrival weather on `66,222 / 67,135` (`98.64%`) records. Zero weather features enter decision scoring now; arrival-only ERA5 (`100.0%` coverage in `171`, plus `NASA POWER` in `166`-mkt `2018–2023`) is evaluated strictly in outcome settlement (`Safe_EV +₹187.80 ES10` under `171` ERA5; `Mean ₹328.15` vs `₹284.26`, `ES10 −₹363.00` vs `−₹567.71`, `cond_ES10 −₹507.15` vs `−₹693.39` in `166` NASA POWER × Sched #7).

**Q25. What happens if conflicting duplicates, numeric outliers, or missing-grade rows are dropped cleanly?**
Dropping `369` raw outlier prices (`N = 57,521` in `v7_exp5`) leaves `Safe_EV_Sunk_m0` at `Mean ₹453.78`, `ES10 −₹344.17` (`p = 0.001`), `cond_ES10 −₹445.20` (`p = 0.001`). Restricting to explicit grade records (`N = 54,858`) keeps `−₹329.55` vs `−₹504.55 ES10`.

**Q26. How sensitive are results to district-centroid geocoding (`40.5%` raw) and sub-yard coordinate collisions (`v7_exp5`)?**
Raw geocoding labeled `59.50%` (`N = 40,263`; `19,362` raw all-5 exact: `Safe_EV ₹563.22` vs `B2 ₹539.04`, `ES10 −₹395.22` vs `−₹667.35`, `p = 0.001`). Auditing coordinate uniqueness uncovered **`56/171` collided markets (`33/171` falsely `"market_exact"`)**; `clean_market_query` is fixed in `src/data/build_road_network.py` (prioritizing parenthetical sub-yards), leaving **`35.23%` true non-collided exact row coverage**. On **`PureAll5_NonCollided_Exact_N6605`** (`N = 6,605`), `Safe_EV_Sunk_m0` (`34.56%` disp) earns `Mean ₹194.97` vs `B2 ₹200.37`, cuts `EpLoss` **`8.30%` vs `17.38%`**, strengthens **`ES10` `−₹231.27` vs `−₹449.14` (`p = 0.001`)**, and strengthens **`cond_ES10` `−₹497.57` vs `−₹687.18` (`p = 0.019`)**. Replacing OSRM road km with `1.20 * euclid_km` yields `₹452.35/qtl`.

**Q27. What happens when we restore the `28,420` episodes dropped by day-`t` origin quote conditioning?**
Evaluating the `N = 86,054` unconditional origin panel preserves `Safe_EV` `ES10 −₹336.19` vs `B2 −₹513.75` (`v7_robustness_171.csv`), and symmetric open-origin fallback (`v7_exp3`) yields `+₹34.92/qtl` Mean and `+₹175.19/qtl` `ES10`.

**Q28. Did validation window leakage across 3-day arrivals affect `th_b2`?**
Purging the final `939` validation episodes intersecting early test settlement days (`v7_exp4`) keeps `th_b2 = ₹200.00` unchanged (`m_mg = 133.56` vs `133.03`, `m_rr = 5.68` vs `5.40`).

**Q29. Does `p_dow` still fail or degrade on Monday/Sunday holiday patterns?**
Using `8`-week exact weekday Laplace reporting (`dest_dow_exact_rep_8w`) directly catches yards closed every Sunday even when 28-day average `rep28` exceeds `75%` — the exact mechanism creating Worked Example Case B.

**Q30. Why keep `omega_lab_*.parquet` untracked on disk?**
It holds legacy external Stage-I scratch tables (`~462 MB`); rule `R8` keeps it gitignored and completely excluded from all `Revision v8` code paths and clean-clone `make` reproduction (`0.0` diff parity without it).

---

## Theme IV — Economics, Biology, Missing Data (`Manski`) & SUTVA (Q31–Q40)

**Q31. Do `PIB relid=154554` and `NABCONS (PIB PRID=2151371)` literally report your percentage fees and 24h spoilage rates?**
No — Revision v8 discloses this explicitly (`epistemic_parameters.csv`): `PIB relid=154554` reports qualitative state F&V deregulation/user-charge status (not exact percentage seller tariffs), while NABCONS Annexure-II Table-2 reports cumulative marketing-level loss shares (`Tomato 3.25%`, `Onion 1.96%`, `Apple 1.64%`, `Potato 0.86%`; cumulative stage totals `5.96%–11.62%`). We adopt both as stylized calibration anchors alongside `30 qtl` truck loads and test `0%–6%` commission, `0%` fees, `0.5–2x` decay, and coupled extremes.

**Q32. How do all methods behave under worst-case coupled smallholder costs (`S6_Frozen`, `v7_exp2`)?**
Under fixed `_spoil_return_leg` `S6_Smallholder_4pctArh_USDA_ERA5_Frozen` (4% commission + USDA/ERA5 stress + frozen `m=0`), `Safe_EV_Sunk_m0` maintains higher closed Mean (`₹307.39` vs `B2 ₹247.15`), higher `ES10` (`−₹576.57` vs `−₹832.00`), and higher `cond_ES10` (`−₹725.73` vs `−₹969.71`).

**Q33. What if we couple `S6_Frozen` with 100% conditional-MAR open arrivals (`Stoch_CondMAR_p1.00`)?**
In `v7_exp2`, `B2` overtakes `Safe_EV_Sunk_m0` on Mean (`₹473.48` vs `₹432.71`), **yet `Safe_EV` preserves a `+₹366.85/qtl` advantage on `cond_ES10` (`−₹595.27` vs `−₹962.12`) and `−₹407.13` vs `−₹754.09` on `ES10`**!

**Q34. What is the exact Manski–MAR break-even point (`v7_breakeven_171`)?**
Under linear closure-vs-MAR mixtures on `171` markets, `B2` catches `Safe_EV_Sunk_m0` on Mean at **`25.45%` Open-MAR** (`26.65%` ERA5) — equivalent to silent arrivals averaging `+₹348.61/qtl` above turn-back (`+₹117.97` flat profit). Under the coupled 2D thick/thin liquidity surface (`v7_exp_summary.json`), `theta_thin` break-even is `29.78%` when `theta_thick = 0%` (or `12.76%` when `theta_thick = 100%`).

**Q35. When does cross-crop evidence point to true closures vs thin-market reporting lag (`CrossCrop`) & coupled Manski `cond_ES10`?**
In `v7_exp3`, treating days where *zero* other crops traded (`b2_blackout = 8,933`) as physical closures while other-crop-open days (`other = 2,517`) clear at lagged price keeps `Safe_EV_Sunk_m0` positive on both Mean (`+₹9.88` to `+₹24.38`) and `ES10` (`+₹188.56` to `+₹207.04`). Under adversarial Manski `Supp1..3` coupled bounds, worst-case Mean shifts turn deeply negative (`−₹124.95`, `−₹199.51`, `−₹325.40/qtl`), while **exact coupled Manski `cond_ES10` stays strictly positive in `Supp1` (`[+₹152.20, +₹328.28]`) and `Supp2` (`[+₹105.96, +₹394.89]`, vs decoupled `−₹0.51`)**.

**Q36. Why do Mean gains disappear under `div = 0.0` free return and `hindsight_3d`?**
If turn-backs cost ₹0 return freight (`div = 0.0`), abstaining saves zero diversion loss (`+₹12.03` / `+₹11.21`, `p = 0.220–0.256` NS). Under clairvoyant `3`-day hindsight (`hindsight_3d`), a truck waits costlessly knowing future rebounds (`B2 ₹549.81` vs `Safe_EV ₹533.14`). In both cases `Safe_EV` retains `+₹169.82` to `+₹308.41 ES10`.

**Q37. How does a non-clairvoyant 1- or 2-day "blind wait" affect settlement (`v7_exp2`)?**
Unlike clairvoyant hindsight, waiting unconditionally `1` or `2` days (`Causal_BlindWait_1d/2d_ExactV7_20C`) yields `Safe_EV_Sunk_m0` `Mean ₹509.84` / `₹529.53` (vs `B2 ₹512.49` / `₹540.65`), still strictly outperforming `B2` on `ES10` (`−₹348.32` vs `−₹643.23` at `1d`; `−₹315.33` vs `−₹666.55` at `2d`) and `cond_ES10` (`−₹497.92` vs `−₹788.18` at `1d`; `−₹488.11` vs `−₹828.73` at `2d`).

**Q38. What happens if many FPO trucks use MandiGuard simultaneously (`SUTVA` crowding, `v7_exp5`)?**
Modeling `5%` / `10%` per-extra-truck price impact drops `Safe_EV_Sunk_m0` Mean from `₹452.74` to **`₹86.06`** and **`−₹5.31/qtl`** (while `B2` collapses further to `₹17.26` and `−₹75.37`). Under a `k <= 2` destination-day truck cap, `Safe_EV` dispatches `31.29%` at `Mean ₹207.00/qtl` and `ES10 −₹230.30/qtl` (vs `B2 ₹176.11`, `−₹380.51`).

**Q39. Why isn't `NITI Aayog / RMI ₹0.258/qtl-km` used directly instead of `₹35 + 0.45 * km`, and what about Outsider LCV/`Min_Price` stress?**
We benchmark `₹0.258/qtl-km` as a line-haul floor (`sensitivity_a8`), add terminal loading (`₹35`) + short-haul/empty backhaul allowance (`₹0.45/qtl-km`), and verify `Safe_EV` wins across `0.75x–1.50x` freight shifts and `36/36` tornado cells (`+₹15.03` to `+₹61.22` Mean; `+₹114.97` to `+₹263.60 ES10`; `+₹172.97` to `+₹322.24 cond_ES10`). Under heavy outsider friction (`LCV` freight + `4%` *arhtiya* commission + `Min_Price` discrimination, `v7_exp5`), `Outsider_Mid_LCV_4pctArh` gives `Safe_EV ₹212.28 / −₹668.22 / −₹842.50` (vs `B2 ₹152.37 / −₹926.53 / −₹1,094.88`) and `Outsider_MinPrice_LCV_4pctArh` gives `Safe_EV ₹102.62` (`34.29%` loss, `cond_ES10 −₹1,290.83`) vs `B2 ₹33.86 / −₹1,573.13`.

**Q40. What makes HP graded apples lose `41.38%` of dispatched trips (`Scale Non-Invariance`, `v7_exp5`)?**
Graded HP varieties across `42` yards (`N = 2,802` episodes) have high lot-quality dispersion (`A+` vs cull grades) AND severe **freight scale non-invariance**: `F/G_1SD < 0.10` on **`79.52%`** of HP dispatches, so `Safe_EV_Sunk_m0`'s freight screen drops out (`67.45%` disp, `Mean ₹1,354.85`, `41.38%` cond. loss, `ES10 −₹1,454.86`, `cond_ES10 −₹2,003.68`, **`p = 0.094` NS**). Adding explicit 24-hour spoilage in `ScaleInv_Safe_EV_24tau` cuts `ep_loss` `27.91% -> 17.92%` (`cond_loss 34.93%`, `ES10 −₹958.08`, `cond_ES10 −₹1,616.08` at `51.28%` / `₹1,287.44`), and `Safe_EV_Sunk_pFloor50` achieves `15.17%` `ep_loss` (`Mean ₹1,036.94`, `ES10 −₹1,011.73`, `cond_ES10 −₹1,759.81`), while live buyer calls remain mandatory.

---

## Theme V — Statistics, Baseline Fairness, Reproducibility & Defense (Q41–Q50)

**Q41. Summarize `PREREG_A18.md` specification-locked exploratory results, `D_S ∩ D_B`, and UP's `q10=0` atom.**
All four specification-locked exploratory `PREREG_A18` hypotheses at exact `R = 2,000` (`H_A18_1..4`: `Safe_EV` `ES10`, `Safe_EV_matched` vs `RR` `ES10` `+₹91.67`, `Safe_EV` EpLoss `−11.56 pp`, `RT_2F` Mean `+₹44.36`) pass simultaneously at **`p_holm_2s_prereg4 = 0.0040`** across all `3` clusterings (`166` orig, `166` B2-dest, `165–166` pol-dest $\times$ `23` fortnights). `H_A18_2` also holds joint `val+test` (`[+₹34.81, +₹158.11]`, `p = 0.0020`). Note UP exhibits an unconditional `q10 = 0` atom (`7.28% < 10%` loss rate), making `cond_ES10` essential; on `CommonIntersection_DS_cap_DB` (`n = 33,398`), `Safe_EV` outperforms `B2` (`₹773.38` vs `₹707.72`, `+₹65.66` Mean, `+₹53.40 ES10`: `−₹464.82` vs `−₹518.22`), while pruning `7,944` `B2`-only trips (`₹68.96`, `58.60%` loss, `ES10 −₹1,018.70`).

**Q42. How do finite-sample `CGM G/(G-1)`, `t(B-1)`, studentized percentile, and `p_wild_webb6_1w_block_only` behave on `H_A18` and subgroups?**
Overall `PREREG_A18` passes (`H_A18_1 p_cgm_gstar = 0.00511` `orig` / `0.01001` `b2dest`, `p_stud = 0.0010` / `0.0035`, `p_wild_webb6_1w_block_only = 0.0005`; `H_A18_2` `p_cgm_gstar = 0.04887` `orig` / `0.06800` `b2dest`, `p_stud = 0.01199` / `0.05697`, `p_wild_webb6_1w_block_only = 0.0005` — noting `p_wild_webb6_1w_block_only` is 1-way block-only). However, in **HP (`B = 12`, `g_star_block = 1.535` warning)**, `cond_ES10` fails significance (`+₹250.82`, `p = 0.1239`, `p_stud = 0.18791`, `p_cgm_gstar = 0.29947`), and in **Apple**, `cond_ES10` is borderline (`p = 0.0550`, `p_cgm_gstar = 0.07443`, `p_stud = 0.05947`).

**Q43. Where do `Safe_EV_Sunk_m0` Mean gains fail across states and crops, and when does `RT_2F` or `RR` lead?**
`Safe_EV_Sunk_m0` wins unconditional `ES10` in all `6` states and `5` crop slices vs `B2`, **but its Mean CIs cross zero in GJ (`p = 0.940`), MH (`0.160`), UP (`0.116`), Tomato (`0.877`), and Apple (`0.143`)**. `RT_2F_Min_m0` wins Mean in all `11` slices (`p = 0.001–0.032`) while failing `cond_ES10` across multiple slices. On Potato (`N = 14,723`), tuned `RR` leads `ES10` (`−₹224.80` vs `−₹242.00`).

**Q44. Compare clean `166`-mkt `2018–2023` (`383,952`) vs legacy `173`-mkt (`389,357`) and year-by-year results.**
Reverse-survivorship leaves `481/647` historical yards absent from the `2024` frame and drops `7` post-`2024` lookahead yards (`171 ∩ 173`) to yield **`166` clean markets (`N = 383,952`)** and **`115` `2017`-active markets (`N = 325,993`)**, where frozen `Safe_EV_Sunk_m0` earns `+₹35.00` Mean, `−12.57 pp` loss, `+₹169.27 ES10` (`−₹304.29` vs `−₹473.56`), **`+₹155.08 cond_ES10`** (`−₹421.35` vs `−₹576.44`, `+₹174.27` vs equal-dispatch `B2_eq_SafeM0`, `p = 0.001`), holds under realized NASA POWER × Sched #7 (`₹328.15` vs `₹284.26`, `ES10 −₹363.00` vs `−₹567.71`, `cond_ES10 −₹507.15` vs `−₹693.39`), wins `ES10` & `cond_ES10` in all **`6/6` individual years (`p = 0.001`)**, while **`2020` (`+₹12.93`, `p = 0.208`) and `2023` (`+₹20.35`, `p = 0.077`) Means are NS** and `RT_2F` `cond_ES10` turns NS (`p = 0.079` `b2dest`; `2020/21/23 p = 0.265–0.528`).

**Q45. How does `Safe_EV_Sunk_m0` compare fairly at matched dispatch volume (`B2_eq_SafeM0`, `B2_test_matched`, `val-ES10 MG`)?**
Matched to `Safe_EV`'s `63.23%` dispatch on `171` markets (`th = ₹295.00`), `B2_test_matched` stays at `−₹501.23 ES10` (`Safe_EV +₹155.70` better); in `166`-mkt `2018–2023`, `Safe_EV_Sunk_m0` beats equal-dispatch `B2_eq_SafeM0` by **`+₹174.27 cond_ES10` (`p = 0.001`)**. Retuning `MG` directly for `val-ES10` (`₹352.73`) reduces `B2` parity gap (`v7_ablations_171.csv`).

**Q46. Why not deploy `Ridge`, `HGBR`, Split-CQR, or full-season `17m` ML (`v7_exp4`) instead of `Safe_EV_Sunk_m0`?**
We explicitly retire any claim that zero-parameter beats all ML or that `safe_ev_feat` boosts `17m` ML! Earlier ML failures reflected `5m` off-season starvation (`ML_Ridge_EV_m0` `85.00%` `Mean ₹467.15` `cond_ES10 −₹542.58`; `ML_HGBR_EV_TV_age13_m0 −₹543.57`; `ML_HGBR_RiskAverse_L500 −₹537.57`), quadratic INR² penalty (`OR_Vargas_MeanVar_g0002 −₹511.42`), and homoscedastic CQR (`0` switches). Once fixed, `5m` heteroscedastic Split-CQR (`s80 = 0.53`, `8,848` destination switches) gets `MG_T1_T2_T3_T4_Intact_matched`: `66.32%`, `Mean ₹356.78`, `ES10 −₹323.41`, **`cond_ES10 −₹414.44`**, and `5m` `ML_5m_HGBR_Q20_matched63` (`58.80%`) hits `₹361.90 / −₹283.43 / −₹403.95` (`ML_HGBR_Q20_m0` `33.67%`, `₹286.72 / −₹162.15 / −₹441.94`). Under full-season `17m` leak-free training (`2024-02..2025-05`, `n = 113,374`): `ML_17m_MeanQ10_Hybrid_eq63` (`63.23%`) reaches `Mean ₹455.83`, `EpLoss 14.94%`, `ES10 −₹320.02`, `cond_ES10 −₹420.57` (`valmatch` `61.39%`: `₹454.20 / −₹315.38 / −₹422.52`), `ML_17m_MeanQ10_NoSafeEV_eq63` reaches `Mean ₹458.27`, `EpLoss 14.87%`, `ES10 −₹321.73`, `cond_ES10 −₹423.88` (`+₹2.44` Mean *higher* when removing `safe_ev_feat`!), `ML_17m_CQR80_valmatch` (`s80 = 0.52`, `8,115` switches) gets `57.30%`, `₹364.03 / −₹261.29 / −₹367.09`, and `OR_Stylized_MeanSD_17m_valmatch` gets `61.40%`, `₹443.57 / −₹324.93 / −₹439.77`. Rather than beating `17m` ML, `Safe_EV_Sunk_m0` (`0` fitted params, `63.23%`, `₹452.74 / 14.88% / −₹345.53 / −₹447.48`) captures **`~98.8%` of `17m MeanQ10` Mean and `~94%` of `cond_ES10` tail protection with zero training history and pocket-calculator portability**.

**Q47. What independent checks guarantee every reported number is authentic and bug-free?**
Three automated gates: (1) `scripts/a16_independent_audit.py` independently recomputes settlements & `cond_ES10` to `<= ₹0.01` parity; (2) `scripts/verify_traceability.py` verifies `0` untraceable numbers across `23` docs plus `59/59` citation bijection; (3) `pytest -v` tests counterfactual leakage, immutable pre-registrations, `<= 15`-page paper PDF & `12` slides; plus a clean-clone `make reproduce` yielding `0.0` CSV discrepancy.

**Q48. What critical runtime and math bugs were caught and fixed during Revision v7/v8 audits?**
`eval_v7_stress_experiments.py` resolved `AttributeError` (`numpy.ndarray.between`), `KeyError: origin_market`, `sort=True` misalignment, `_spoil_return_leg` return-leg spoilage in `S6_Frozen` and `Decade166_NASA_POWER`, homoscedastic vs heteroscedastic Split-CQR scaling (`8,848` switches), and `clean_market_query` parenthetical sub-yard priority in `src/data/build_road_network.py` plus finite-sample `CGM G/(G-1)` scaling in `revision/stats_utils.py`.

**Q49. Why keep `PREREG_A10.md` and `PREREG_A18.md` untouched even after discovering new weaknesses?**
Amending pre-registrations after observing outcomes invalidates confirmatory discipline. We leave both locked verbatim (`git diff` empty), label `PREREG_A18` honestly as **specification-locked exploratory inference**, and separate `R = 5,000` checks, clean `166`-mkt `2018–2023`, and Phase 6 `v7_exp1..5` stress experiments transparently.

**Q50. Why is `Gate J` blocked and what is the single highest-value follow-up study?**
Bulk public AGMARKNET archives stop `2026-04-13` and contain neither phone-call outcomes nor household auction receipts (`Gate J = BLOCKED`; note `PhoneCall_TopK_Open` confirms `Safe_EV ₹501.09 / −₹204.98 / −₹355.07` & `Pure_cv28 ₹517.49 / −₹249.12 / −₹396.59` still curb tail risk over `B2 ₹527.55 / −₹440.72 / −₹691.79` even when phone calls screen out closures). A one-season prospective FPO field trial logging `200–500` real `6 a.m.` *arhtiya* confirmation calls, truck freights, and sale *pattis* directly measures the empirical silent-open rate against our `25.45%` Manski threshold.
