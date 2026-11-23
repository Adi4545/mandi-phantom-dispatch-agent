# MandiGuard — Viva Q&A (Revision v7)

**Author / Thesis Framing:** Aditya Sharma (M.Tech Thesis Research, supervised by Dr. Sonia) — Shoolini University, Solan, Himachal Pradesh, India.

This sheet prepares concise, traceable answers to the ten hardest questions an external examiner or venue referee can ask about Revision v7.

---

## Q1. What changed between earlier drafts (`v6`) and final Revision `v7`?
Revision v7 resolves every methodological, statistical, stress-test, citation, and disclosure issue identified across external review and the 16-agent adversarial audit while keeping `PREREG_A10.md` and `PREREG_A18.md` unmodified:
1. **Primary panel switched to zero-lookahead `171` markets (`N = 57,634`):** Filtered strictly on pre-test `2024` activity (`>= 80` days, `<= 30`/state), removing future market-survival lookahead.
2. **Pre-registered `4`-test `R = 2,000` family & `cond_ES10` pairing:** `PREREG_A18.md` passes at `p_holm_2s_prereg4 = 0.0040` across `3` clusterings, paired directly with dispatched conditional `cond_ES10` (`−₹447.48` vs `B2 −₹628.37` = `+₹180.89`).
3. **Clean `166`-Mkt `2018–2023` Archive (`N = 383,952` & `115`-Mkt `N = 325,993`):** Drops all `7` post-`2024` lookahead yards from the legacy `173`-mkt (`389,357`) extract. Frozen `Safe_EV_Sunk_m0` gains `+₹169.27 ES10` and `+₹155.08 cond_ES10` (`+₹174.27` vs equal-dispatch `B2_eq_SafeM0`, `p = 0.001`), holds under NASA POWER climate, and wins `ES10` & `cond_ES10` in all `6/6` years while disclosing NS `2020/2023` Means.
4. **Phase 6 Adversarial Stress (`v7_exp1..5`):** Verifies `<= t-2` latency (`Safe_EV` `p = 0.001`), coupled `S6_Frozen x Stoch_CondMAR_p1.00` (`+₹366.85 cond_ES10`), Manski bounds, clean ML/OR Pareto, and SUTVA crowding (`k <= 2`).

## Q2. Were the zero-parameter rules designed after seeing `2024` data?
- **Honest acknowledgement:** Yes — `Safe_EV_Sunk_m0`, `Safe_EV_Phys_m0`, and `RT_2F_Min_m0` were specified after Stage I (`2024`) inspection, so the `2025–2026` panel (`N = 57,634`) is explicitly labeled exploratory even with `m = 0` tuned parameters.
- **Retrospective out-of-period check:** Evaluating the frozen rules verbatim across clean `166`-mkt `2018–2023` (`N = 383,952`) yields `+₹169.27 ES10` and `+₹155.08 cond_ES10` (`p = 0.001`), winning `ES10` & `cond_ES10` in all `6` years (`2020/2023` Means NS).

## Q3. Does zero-parameter `Safe_EV_Sunk_m0` beat properly retrained ML and OR models without weather leaks?
Yes, on conditional tail risk (`cond_ES10`), which was benchmarked head-to-head in `v7_exp4` after removing weather leaks and purging `939` overlapping validation episodes: `Safe_EV_Sunk_m0` (`cond_ES10 −₹447.48`, EpLoss `14.88%`) outperforms retrained `Ridge` (`−₹530.30`), `HGBR_EV_TV_age13` (`−₹523.53`), `HGBR_RiskAverse_L500` (`−₹512.43`), `OR_Vargas_MeanVar_g0002` (`−₹496.76`), and `MG_Intact_matched` (`−₹531.66`), while remaining zero-parameter.

## Q4. Isn't unconditional `ES10` artificially inflated because `Safe_EV` abstains more (`36.8%` vs `28.3%`) and puts ₹0 zeros into the bottom decile?
That is why Revision v7 pairs every `ES10` result with **conditional `cond_ES10` among dispatched trips only** (where ₹0 abstentions are excluded!). Among dispatched trips (`N = 36,441` vs `41,342`), `Safe_EV_Sunk_m0` improves `cond_ES10` from `−₹628.37` (`B2`) to `−₹447.48/qtl` (`+₹180.89`), beats equal-dispatch `B2_eq_SafeM0` by `+₹174.27` in `166`-mkt `2018–2023` (`p = 0.001`), and matches `Safe_EV_Phys_m0` (`−₹447.33/qtl`) within `₹0.15/qtl`.

## Q5. What happens if portals actually have a 2-day publication lag (`<= t - 2`)?
Tested directly in `v7_exp1` (`N = 57,047`, `t2_age_2_3`, `th = ₹300.0`): `Safe_EV_Sunk_m0` retains statistically significant gains over `B2` on Mean (`+₹37.69`, `p = 0.001`), `ES10` (`−₹364.48` vs `−₹508.36`, `p = 0.001`), and `cond_ES10` (`−₹484.32` vs `−₹672.39`, `+₹188.07`, `p = 0.001`), whereas Class-8 `RT_2F_Min_m0` loses both `ES10` (`p = 0.3628`) and `cond_ES10` (`p = 0.9805`) significance under 2-day staleness.

## Q6. What if every blank AGMARKNET day is actually an open yard (`MAR`), or physical frictions hit smallholder worst-cases simultaneously?
1. **Manski Break-Even & Envelopes (`v7_breakeven_171`, `v7_exp3`):** On `171` markets, `B2` overtakes `Safe_EV` on Mean if `>= 25.45%` of silent yards clear at full lagged prices (`26.65%` under ERA5), leading by `+₹97.01/qtl` at `100%` MAR (`₹698.17` vs `₹601.16`). Yet even under coupled `S6_Smallholder_4pctArh_USDA_ERA5_Frozen x Stoch_CondMAR_p1.00` (`v7_exp2`), `Safe_EV_Sunk_m0` still improves `cond_ES10` by `+₹366.85` (`−₹595.27` vs `−₹962.12`). Worst-case Manski `Supp1..3` coupled Mean shifts (`−₹124.95`, `−₹199.51`, `−₹325.40`) are disclosed openly.
2. **Negative/NS Mean Regimes:** Under `div = 0.0` (`p = 0.2199–0.2559`), `hindsight_3d` (`B2 ₹549.81` vs `₹533.14`), `PreChoice_ExactD0` (`−₹20.74` Mean, `+₹260.20 ES10`), and `2020/2023` (`p = 0.208/0.077`), Mean differences vanish or reverse while `ES10` tail protection persists.

## Q7. Are your `ES10` / `cond_ES10` results fragile in small states like HP (`B = 12`) or crops like Apple?
We test small-cluster robustness via `CGM`, `t(B-1)`, studentized percentile, and `Webb-6` wild cluster bootstrap (`v7_exp_summary.json`): main `PREREG_A18` passes (`H_A18_2` `p_cgm_gstar = 0.0470 orig / 0.0659 b2dest`), whereas **HP (`B = 12`) fails significance on `cond_ES10` (`+₹250.82`, `p = 0.1239`) and `p_stud` (`0.1864`) / `p_cgm_gstar` (`0.2879`)**, and **Apple is borderline on `cond_ES10` (`p = 0.0550`, `p_stud = 0.0585`)**. In the separate HP Graded Apple panel (`N = 2,802`), `cond_ES10` (`p = 0.0940`) is non-significant and `41.38%` of dispatched trips still lose money.

## Q8. What are the limits of your PIB APMC fee, NABCONS spoilage, and SUTVA price-taker assumptions?
- `PIB relid=154554` documents qualitative state APMC deregulation rather than exact percentage rates, and NABCONS `PIB PRID=2151371` reports cumulative marketing-level loss shares (`0.86%–3.25%` market level; `5.96%–11.62%` total); both, plus `30 qtl` load size, are stylized model calibrations stress-tested across `36` tornado cells and coupled `S6_Frozen`.
- On fleet crowding (`v7_exp5`), `5%`/`10%` extra-truck price impact drops `Safe_EV` Mean to `₹86.06` / `−₹5.31` (vs `B2 ₹17.26` / `−₹75.37`), while a `k <= 2` cap limits dispatch to `31.29%` (`₹207.00` Mean, `ES10 −₹230.30`).

## Q9. What exact novelty do you claim vs DeMiguel et al. (2009), Gigerenzer & Gaissmaier (2011), and Vargas et al. (2026)?
We claim **applied problem, evaluation, and operational synthesis novelty** — never a mathematical theorem or novel optimization algorithm (`final/NOVELTY_V2.md`). We formalize how sequential wholesale execution converts AGMARKNET non-reporting into structured tail risk, show why `m = 0` domain rules beat tuned ML/OR models (`Ridge`, `HGBR`, `OR_Vargas`) on `cond_ES10`, and bound all conclusions with exact Manski partial identification.

## Q10. Why not just call the destination trader instead of running a filter, and what is your next milestone?
Live trader phone calls (`Jensen 2007`; `Ziegler et al. 2019`) remain indispensable. MandiGuard filters dozens of noisy AGMARKNET spreads at `6 a.m.` *before* human confirmation calls (`PreChoice_ExactD0` still preserves `+₹260.20 ES10` on open days). Because bulk public feeds end `2026-04-13` (`Gate J = BLOCKED`), the immediate next milestone is a prospective single-season FPO field pilot logging real *arhtiya* phone confirmations, truck bills, and auction slips.
