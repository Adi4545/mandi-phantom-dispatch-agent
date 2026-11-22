# Viva Defense Q&A — Verified Claims Only (`VIVA_QA.md` — Agent `A15`)

> **Verification Guarantee (`R2` & `C2` Fix):** Every empirical number in this document traces automatically to `revision/results/` or documented Stage I outputs (`results/confirmatory_holm_summary.csv`, `results/exp3_hp_apple_grade_holdout.csv`) via `scripts/verify_traceability.py`. Zero stale quantile-mean `cvar_10`, Stage II conformal claims, or unverified numbers remain.

---

## 1. The 45-Second Examiner Pitch

> *"Sir/Ma'am, agricultural price portals like AGMARKNET tempt farmers with large spatial price gaps—say `₹500/qtl` higher at another mandi. Under a strict prior-day causal replay (`<= t - 1`) across `58,676` wholesale episodes (6 states, 4 crops) with sequential day-by-day settlement and destination-base APMC fees, chasing the top lagged spread loses money `45.21%` of the time with worst-10% shortfall `ES10 = −₹641.26/qtl`. Replacing black-box ML trees, leaked weather, and hard binary gates with **one calculator-simple formula (`RR-Abstain`)**—weighting expected open-market gain by yesterday's variety-reporting probability against a bounded return-freight loss—raises mean net gain to **`₹475.36/qtl`** (`+₹41.80` over age-matched road baselines, Holm `p = 0.0020`), cuts episode losses to **`17.23%`** (`−9.49 pp`, Holm `p = 0.0020`), and improves **`ES10` to `−₹460.72/qtl`** (`+₹64.54` over road baselines and `+₹52.06` over hard-gated heuristics, Holm `p = 0.0020`), holding across Onion, Potato, and Tomato and down to zero missing-quote penalty, while leaving Stage I `H2` inconclusive (`+₹6.13`, `p = 0.270`) and graded HP apples volatile (`44.63%` conditional loss rate)."*

---

## 2. First-Principles Definitions (Whiteboard Explanations)

### Q1. Why can't you use same-day `local_price` or build Top-5 shortlists from today's portal?
**First Principles (`R3`):** A dispatch truck must be booked in the morning (`day t`), *before* day-$t$'s terminal modal prices across destination yards are settled. Earlier commits (`b3bb46f`) leaked in two places: (a) Top-12 corridors came from a day-$t$ shortlist (`C1`), and (b) `lag_spread` subtracted same-day origin `local_price` (`M9`). In Revision v4, **both** origin and destination prices in the candidate menu and every scoring equation come strictly from dates $\le t - 1$, verified by a counterfactual perturbation test corrupting all prices on dates $\ge t^*$ with bit-for-bit invariant shortlists.

### Q2. Walk me through every rupee of your payoff equation on a whiteboard.
<!-- WORKED_EXAMPLE_START -->
Take an out-of-district **Madhya Pradesh Tomato** trip (`fee_rate = 1.5%`, `road_km = 200` km, `truck_hours = 6` h, $P_{\text{dest}} = ₹2,000$, $P_{\text{loc}, d0} = ₹1,500$):
1. **Road Freight:** $35.0 + 0.45 \times 200 = ₹125.00/\text{qtl}$.
2. **NABCONS 20°C Reference Spoilage (`w=0`):** $0.0325 \times (6/24) = 0.8125\% \implies$ $₹2,000 \times (1 - 0.008125) = ₹1,983.75$ gross surviving auction value.
3. **Destination Statutory APMC Fee (`M9` fix):** Charged on the surviving destination auction value ($1.5\% \times ₹1,983.75 = ₹29.76$), leaving $₹1,953.99/\text{qtl}$. (Zero fee on intra-district trips or turn-back diversions without a yard sale!)
4. **Net Gain:** $₹1,953.99 - ₹125.00 - ₹1,500.00 = +₹328.99/\text{qtl}$.
<!-- WORKED_EXAMPLE_END -->

### Q3. Why did hard-gated `MG_matched` fail to improve `ES10` significantly, and why did `RR-Abstain` succeed?
At matched dispatch (`~70%`), `MG_matched` applied fixed hard cutoffs (`rep14 >= 0.50`, `dow8 >= 0.35`) and still ranked surviving candidates solely by open-yard profit. So it treated a risky `52%`-reporting route identically to a `95%`-reporting route (`ES10` gain `+₹12.49`, CI `[−₹16.57, +₹39.97]`, Holm `p = 0.589`). Pre-registered `RR-Abstain` (`87a0b62`) fixes this with **one smooth convex combination**:
$$S_{\text{RR}} = \hat{p}_{\text{rep}}\,\widehat{\Delta}_{\text{open}} + (1 - \hat{p}_{\text{rep}})\,(-\kappa\,F_{\text{road}} - P_{\text{orig,lag}}\,s_{\text{ref,0}})$$
When a yard reports rarely ($\hat{p}_{\text{rep}}$ low), `(1 - p_rep)` prices the `-kappa * F` (`kappa* = 5.0`) return risk directly into the ranking and abstention decision—cutting `ES10` tail loss by `+₹64.54` over `B2_age_matched` (`−₹460.72` vs `−₹525.25`) and `+₹52.06` over `MG_matched` (`−₹512.78`, Holm `p = 0.0020`).

### Q4. Explain exact `ES10` vs your older `cvar_10` metric.
Earlier tables took the unweighted mean of points below the sample 10% quantile, which included too many or too few points when zeros tied at the threshold. Exact `ES10` sorts all `N` episode outcomes worst-first, takes total mass `m = 0.10 * N = k + f`, sums the worst `k` observations plus fraction `f` of `(k + 1)`, and divides by `m`. Abstentions count as `₹0`, so `ES10` measures the worst tenth of all decision days.

### Q5. Why is sequential arrival settlement critical instead of 3-day hindsight?
If day 0 shows no exact-variety row *and no other variety of that crop*, a real truck driver cannot peek at day +1/+2 to know an auction will appear tomorrow—they leave or divert immediately (`no_comm_divert_d0`, `27.99%` of `B1` trips). Scoring `B1` with 3-day hindsight drops its apparent loss rate artificially from `45.21%` to `31.35%`.

---

## 3. Tough Examiner Trap Questions (Honest Answers Only)

### Q6. *"Aren't your test results still post-hoc because June 2025–April 2026 was already on GitHub?"*
**Yes, wrt calendar exposure (`R5`).** We explicitly label the June 2025–April 2026 test window `exploratory` and rate Gate J (`untouched future multi-state fold`) as **BLOCKED (disclosed)**. What we *did* enforce strictly is pre-registering `RR-Abstain` (`final/PREREG_A10.md`, `87a0b62`) before writing `eval_a10.py`, and freezing all validation tuning on Jan–May 2025. True untouched prospective validation requires a field pilot.

### Q7. *"Didn't HP Apples fail in Stage I, and don't Apples drive everything?"*
In legacy Stage I (`results/exp3_hp_apple_grade_holdout.csv`), HP graded apples failed cleanly for `MG`, and even in Revision v4 (`a10_crop_splits.csv`), generic `Apple` `ES10` is statistically tied between `RR_Abstain` and `B2_age_matched` (`−₹1,537.30` vs `−₹1,533.29`, CI `[−₹209.47, +₹160.84]`), while HP graded apples (`N = 2,802`, `a10_hp_apple.csv`) still suffer `44.63%` conditional loss rate and `−₹2,165.73` `ES10` (`−₹3,453.18` in summer 2026). **Crucially, however, `RR-Abstain` is NOT apple-driven:** across the `52,207` non-apple episodes (`a10_crop_splits.csv`), `RR-Abstain` raises mean `+₹34.82` and improves `ES10` by **`+₹78.10`** (`Onion +₹101.93`, `Potato +₹88.91`, `Tomato +₹49.31`, all CIs strictly positive).

### Q8. *"What happens if your assumed ₹35 + ₹0.45/km freight or missing-quote `1.5×` penalty is wrong?"*
- **Missing quotes (`a10_missing_stability.csv`):** Even at **zero return penalty (`div = 0.0, disc = 0.00`)**, `RR_Abstain_matched` (`₹493.37` mean, `17.21%` loss, `−₹349.35 ES10`) still beats `B2_age_matched` (`₹475.80`, `26.67%`, `−₹359.17`) and `B1` (`₹461.57`, `45.07%`, `−₹535.08`). Under heterogeneous selective missingness (`div=2.0` on sporadic yards), `ES10` improves from `−₹499.07` (`B2_age_matched`) to `−₹388.55` (`RR_Abstain_matched`).
- **NITI Aayog heavy-truck floor (`tornado_sensitivity.csv`):** If a farmer accesses bulk national highway freight at NITI Aayog's `₹0.258/qtl-km` (`₹20` base), unmatched high-threshold `MG` (`41%` disp) trails `B1` by `−₹14.23/qtl`. For smallholder LCV freight (`₹0.45..₹1.20/qtl-km`) and `0%–6%` *arhtiya* commissions, selective rules stay strongly ahead of `B1` (`+₹21.67` to `+₹156.89/qtl`).

### Q9. *"How does your clustering handle destination shocks or market-wide holidays?"*
Every primary contrast `H_A10_1..4` passes Holm-Bonferroni at `p_holm = 0.0020` under **both** two-way `origin_x_2week` (`173` origins $\times$ `23` fortnights) and two-way `b2dest_or_origin_x_2week` (`336` destinations/origins $\times$ `23` fortnights) cluster bootstraps (`2,000` replicates).

### Q10. *"Did you invent a new conformal theorem or machine learning algorithm?"*
**No (`R7` & `A12`).** We dropped the pickled ML tree (`forecaster_2024.pkl`), dropped the "conformal risk control" claim, and reduced system difficulty from `4.3/5` to `1.6/5` (`final/DIFFICULTY.md`). The contribution is an audited benchmark, leak-free simulator, and the empirical discovery that a simple reporting-reliability linear expectation rule beats both price-imputing baselines and hard activity gates on worst-10% tail risk (`ES10`).
