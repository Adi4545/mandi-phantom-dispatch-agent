> This document records the earlier analysis. Use the [correction record](../final/CORRECTIONS.md) for the revised downside estimates, arrival-day diagnostics, weather control and reproduction commands.

# M.Tech Viva Questions & Crisp Examiner-Ready Answers — `MandiGuard` & `MandiGuard-CRC` (50 Examiner Q&As)

## Group A — Motivation, Novelty & Agricultural Economics (Q1–Q9)

1. **Q: In one sentence, what is "Phantom Spatial Arbitrage"?**  
   **A:** It is an apparent cross-mandi profit spread shown on price boards that turns negative or fails to execute once real highway freight, state mandi charges, variety or grade mismatches, closed destination yards, ambient spoilage, and arrival-day price drops are included. On our 6-state holdout (63,040 naive `B1` dispatches), headline spreads average ₹1,330.49/qtl yet 58.94% hit closed or missing-variety traps and 40.46% lose money outright.

2. **Q: Why didn't you just predict tomorrow's mandi price like most existing ML papers?**  
   **A:** When all candidate yards are open on arrival day (`N = 10,162` matched cohort, `Exp 15`), point-ML (`B3`) indeed earns higher mean profit (₹553.22/qtl), though with 14.77% losing trips and -₹362.40/qtl worst-10% tail loss. Across the full holdout market (69,526 episodes), however, `B3` performs worse than naive screen chasing: 45.28% of its dispatched trucks lose money and 65.65% hit closed-yard or missing-variety traps (₹330.85/qtl vs naive ₹350.01/qtl and `MandiGuard`'s ₹452.79/qtl). Price forecasting works when yards are open; it fails on the full market because it lacks `T1` openness checks and `T4` safety cushions.

3. **Q: Why is `MandiGuard` a scientific decision-support contribution rather than "just simple `if-else` business rules"?**  
   **A:** Three empirical comparisons distinguish it from ad-hoc thresholds: (1) our heuristic verbal rule router `B6_HeuristicBucketRouter` underperforms `MandiGuard` (₹431.94 vs ₹452.79/qtl, higher traps 21.59% vs 16.17%, and 34.9% more tool calls); (2) removing causal Conformal 80% LCB (`No_T4_ConformalLCB`) raises loss-trip rate from 9.97% to 16.89% and worsens worst-10% tail losses from -₹37.89 to -₹397.19/qtl; and (3) `MandiGuard`'s sequential cascade traces a stronger utility–API-budget tradeoff (+₹104.54/qtl over upfront verification `B4` at a strict `B = 6` calls/episode cap).

4. **Q: What happened to your earlier multi-ensemble `EVA-Mandi` attempt (`H1, H2, H4, H5` rejected)? Why did you pivot?**  
   **A:** In `EVA-Mandi` v1, stacking 9 ensembles, Duan smearing, Knowledge-Gradient integrals, and delayed conformal rules over small Himachal Pradesh Apple subsets failed 4 of 5 pre-registered hypotheses and trailed a simple staleness filter. Following scientific discipline, we preserved that archive untouched, pivoted cleanly to multi-state physical arbitrage (`MandiGuard`), kept the math transparent (first-year engineering economics + single HGBR + empirical conformal LCB), and saw 3 of 4 confirmatory hypotheses supported (`H1`, `H3`, `H4`, all p_Holm ≤ 0.0012) alongside transparent reporting on `H2`.

5. **Q: Why is your local market sale option (`REFUSE_PHANTOM_SPREAD`) justified theoretically?**  
   **A:** By Chow (1970) optimal reject theory and Franc et al. (2023): dispatching a perishable load creates asymmetric downside risk (sunk freight + spoilage + diversion cost up to -₹1,062.66/qtl worst-10% tail), whereas refusing an uncertain spread yields deterministic local realization (ΔNet = ₹0). A dispatch decision-support system must evaluate lower confidence bounds, not point averages.

6. **Q: How are a farmer's truckload size and income impact grounded rather than assumed arbitrarily?**  
   **A:** Directly in **MoSPI NSO *NSS Report No. 587* (77th Round Situation Assessment Survey)** (`PIB PRID 1753856`): average harvested quantity per selling household is 2,933 kg (29.33 qtl) for Potato and 3,873 kg (38.73 qtl) for Onion—grounding our 30-quintal mini-truckload—while average household net crop income is ₹3,798/month. Thus our +₹102.78/qtl gain (+₹3,083.5 per load) represents 81.2% of a household's monthly net crop income on a single trip.

7. **Q: How do recent papers like *AgriMarket AI* (2026) and *Mandi Cast* (2026) differ from `MandiGuard`?**  
   **A:** Both compute point net gains using Euclidean/Haversine distances or weather-covariate regressions without exact variety/grade matching, arrival-weekday openness checks, transit biological Q10 heat decay, or selective conformal refusal—putting them directly in the family of baselines `B1` and `B3`.

8. **Q: Which of the 4 crops suffers the highest phantom-loss rate, and why?**  
   **A:** **Onion** (48.69% loss-trip rate under `B1`, averaging +₹53.61/qtl conditional net gain on a ₹704.50/qtl headline spread), because onion varieties (Red, Puna, Local, Standard) fluctuate within tight margin bands where ₹138.07/qtl freight, ₹484.23/qtl traps/reversion, and arrival drops absorb most of the spread. **Apple** has the largest absolute spread erosion (₹3,499.80/qtl screen → ₹1,982.36/qtl lost to traps/reversion), and **Tomato** has the highest base market spoilage (3.25% NABCONS rate).

9. **Q: Why did `MandiGuard` perform strongly on Onion and Potato, while naive `B1` had a slightly higher mean on Tomato (₹547.64 vs ₹522.48/qtl)?**  
   **A:** Because tomato spreads occasionally hit rare scarcity price spikes that raise naive average revenue even while 32.38% of naive tomato episodes lose money. `MandiGuard` trades away a sliver of lottery upside (-₹25.16/qtl vs `B1`, while still beating `B2` Fresh+OSRM by +₹37.84/qtl) to cut tomato episode losses from 32.38% down to 5.09%.

---

## Group B — Data Authenticity, Official Benchmarks & Physical Model (Q10–Q19)

10. **Q: Where did your 10-year mandi price data come from, and how closely does it match official `data.gov.in` / AGMARKNET 2.0 (`Exp 14`)?**  
    **A:** Our bulk 2017–2026 CSVs came from a public AGMARKNET archive mirror (42,722,187 raw rows streamed, with SHA-256 checksums saved, synthetic workspace files excluded, and no CAPTCHA bypassing). `Exp 14` audits parity across two official tiers: **Tier 1** spot-checks `2023-10-18` against official `data.gov.in` Resource `9ef84268-d588-465a-a308-a864a43d0070` XML (`6,434` all-India rows, `172` matched core-panel keys: `100.00%` `Min`/`Max` and `99.42%` `Modal` parity); **Tier 2** audits a **149-day direct official AGMARKNET 2.0 export** (`2025-11-07` to `2026-04-13`, `2,042` matched market–variety–grade–day keys), achieving **`100.00%` (`2,042/2,042`) exact rupee parity across all three price fields**, alongside 22 live Nov-2026 `agmarknet.gov.in` queries.

11. **Q: How did you avoid survivorship bias when selecting top mandis?**  
    **A:** Picking the most active markets over the full 2024–2026 range peeks into the future (markets that shut down in 2025 wouldn't be picked). We strictly ranked the top 30 markets per state using **only calendar 2024 trading days** (≥ 20 days in 2024, ≥ 80 total → 178 core mandis across 6 states).

12. **Q: Where did your base crop spoilage percentages come from? Did you tune them?**  
    **A:** No tuning: we took them directly from **MoFPI / NABCONS (2022) Annexure-II Table-2** (tabled in Rajya Sabha, `PIB PRID 2151371`, 01 Aug 2025), using the official market-level handling and transport loss rates: Tomato 3.25%, Onion 1.96%, Apple 1.64%, Potato 0.86%.

13. **Q: Wait—AGMARKNET doesn't publish truck-level spoilage receipts! Don't you lack live field validation for freight, rot, and diversion penalties?**  
    **A:** Yes, we state this limitation openly (`Section 8` and `NOVELTY_AUDIT.md`): we have **no live farmer receipts, weighment slips, or field interviews yet**, so truck freight (₹35 + ₹0.45/km), Q10 biological rot anchored to NABCONS (2022), and closed-yard diversion penalties are modeled rather than field-measured, whereas daily prices, yard reporting gaps, OSRM road hours, and ERA5 weather are observed or routed public records. Notably, NABCONS spoilage averages ₹68.76/qtl of naive erosion compared with ₹714.90/qtl from observed AGMARKNET price drops and missing-yard episodes, `MandiGuard` stays ahead of `B1` across all 9/9 `[0.5×..1.5×]` freight × spoilage sensitivity cells (+₹82.62 to +₹121.42/qtl), and `Exp 15` evaluates both the full trap-penalty crossover curve and fair matched complete-observation cohorts.

14. **Q: Why do cross-district mandi charges differ across your 6 states?**  
    **A:** Because Indian agricultural marketing is a State subject (`PIB Release ID 154554`): Karnataka and Gujarat exempted market fees on fruits and vegetables (leaving ~0.5% user/handling fees); Himachal Pradesh exempted all F&V except Apple (0.5% veg vs 1.0% Apple); Maharashtra deregulated direct outside-yard F&V sales (1.0% inside APMC supervision); while Madhya Pradesh (notified yards) and Uttar Pradesh maintain regulated yard levies (1.5%). Replacing uniform 1.5% fees with these state rules increases realized net spreads by ₹7.12/qtl (`Exp 6`).

15. **Q: Why does Himachal Pradesh carry a 1.45× per-km road freight multiplier?**  
    **A:** Grounded directly in official Public Works Department statistics from the **Government of Himachal Pradesh *Economic Survey 2025–26* (Table 28)**: out of 43,091 km of motorable roads, 39,465 km (91.59%) are single-lane hill roads (plus 1,337 km jeepable), causing higher fuel burn and slower transit than plains highways.

16. **Q: What happened when Open-Meteo hit its daily forecast request limit on 43 northern grid cells? Did that cause future leakage?**  
    **A:** No—we respected the API quota (`HTTP 429`) strictly rather than bypassing it. All 145/145 realized ERA5 cells completed first, alongside 102/145 (70.3%) native Open-Meteo historical forecasts (all cells in Gujarat, Karnataka, MP, Maharashtra plus 8 in UP). For the 43 remaining cells, we fit a Ridge nowcaster strictly on 2024 overlap data using only causal day `<= t` ERA5 inputs (verified by unit tests perturbing `t+1..t+3` with zero effect on `<= t`), and checked exploratory `Exp 2b` across the 42,766 episodes in the 4 states with full native NWP forecasts (+₹59.53/qtl vs `B1`, +₹31.82/qtl vs `B2`).

17. **Q: How did you prevent geocoding errors like matching a Maharashtra village to Rajasthan?**  
    **A:** In early audits, raw geocoders matched "Neemuch" to Rajasthan and "Gonda"/"Ahmadnagar" to distant homonym villages (300–400 km off). We enforced `admin2` district-alias validation and a hard ≤ 110 km Haversine check against verified District HQ coordinates across all 220 mandis (checked automatically by `pytest`).

18. **Q: How do you handle market reporters entering `"Onion"`, `"Other"`, and `"FAQ"` interchangeably for variety?**  
    **A:** We canonicalize generic commodity-name, `"Other"`, and `"FAQ"` entries into `"Standard"` and unify spelling variants (`"Deshi"` → `"Desi"`), while preserving distinct cultivars (`"Red"`, `"Hybrid"`, `"Royal Delicious"`, `"Badshah"`, etc.). That reduces false mismatch noise while catching real cultivar traps.

19. **Q: What does the Live November 2026 AGMARKNET check (`Exp 8`) show?**  
    **A:** Querying 22 benchmark corridors against the live official API on November 17, 2026 showed that 11/22 (50.0%) of benchmark APMC series (including major yards like Lasalgaon Onion and Bengaluru Tomato) reported zero trading across the entire preceding 7 days—indicating that intermittent reporting and inactive-yard risk remain active issues today.

---

## Group C — Machine Learning, Conformal Intervals, Statistics & Limitations (Q20–Q35)

20. **Q: Explain Conformal Prediction (`T4`) in plain English for an examiner.**  
    **A:** Imagine checking how badly your forecast missed over the last 400 settled trips (actual return minus predicted return). You find the 80th-percentile worst downside mistake—say your model was over-optimistic by 7% or more in 20% of past trips. Today, instead of trusting the model's raw point prediction (`pred_ret`), you subtract that historical 7% mistake buffer (`lcb_ret = pred_ret - 0.07`), and dispatch only if profit still clears +₹50/qtl after accounting for that 80th-percentile downside shortfall.

21. **Q: Doesn't Conformal Prediction assume data is i.i.d. / exchangeable—which prices violate?**  
    **A:** Yes, we disclose this candidly: agricultural prices exhibit seasonality and weather shocks, so finite-sample exchangeability bounds are approximate rather than exact guarantees. We maintain a strictly causal sliding buffer updated only once arrival dates mature (`arrival_date <= t`) and empirically check actual coverage: 78.85% in `Val_2025H1` and 79.07% across 468,816 holdout candidate pairs—close to the nominal 80% target.

22. **Q: Why train on 2024 only (`Train_2024`) and never refit monthly on 2025–2026?**  
    **A:** Freezing the base forecaster weights in 2024 prevents model fitting on holdout price regimes and provides an out-of-time robustness test (15 months ahead). Only the scalar 400-sample conformal residual window adapts causally on matured arrivals.

23. **Q: How was `safety_margin_inr = ₹50/qtl` chosen? Was it tuned on holdout?**  
    **A:** Never tuned on holdout. It was swept over `{50, 100, 150, 200, 250}` on `Val_2025H1` (Jan–May 2025), frozen in `configs/frozen_calibration.json`, and locked into Git (`commit e421d15`) before holdout experiments ran. A ₹50 threshold maximized validation net utility while keeping loss-trip rate below 10% (9.68% in val → 9.97% in holdout).

24. **Q: Why did Hypothesis `H2` (`MandiGuard > B2_FreshRoadGreedy` in Mean ΔNet) fail statistical significance (p_Holm = 0.2699)?**  
    **A:** We admit cleanly that `B2` ties `MandiGuard` on overall mean profit (₹446.66 vs ₹452.79/qtl; the +₹6.13/qtl difference is within sampling noise under our Two-Way Mandi × Block bootstrap across 23 two-week clusters). `MandiGuard` differs from `B2` in its risk–return profile: it declines high-variance same-day spreads to halve loss trips (9.97% vs 18.11%) and limit worst-10% tail losses (-₹37.89 vs -₹436.67/qtl). The 4-state native-NWP subgroup (+₹31.82/qtl over `B2`, `Exp 2b`) is exploratory context only, not a confirmatory rescue.

25. **Q: Why use Two-Way Origin-Mandi × 2-Week-Block Cluster Bootstrap (`R = 5,000`) instead of a standard paired *t*-test?**  
    **A:** Treating 69,526 episodes as independent draws violates independence doubly: consecutive days from the same origin mandi are serially correlated, and mandis across a state share regional monsoon/harvest price shocks in the same week. Our two-way cluster bootstrap resamples both 174 origin mandis and 23 two-week blocks simultaneously, yielding conservative wide confidence intervals (`[+₹48.66, +₹153.45]` for `H1` instead of artificially narrow i.i.d. CIs) with Phipson–Smyth finite-sample *p*-values and Holm–Bonferroni FWER control.

26. **Q: Look at `Exp 4`: why does removing weather tool `T3` slightly *increase* unconditional mean gain by ₹2.46/qtl (₹455.25 vs ₹452.79)?**  
    **A:** Because `T3` and `T4` stack conservatively (spoilage haircut + 80% LCB price haircut). On 1.52% of episodes (50.18% → 48.66% dispatch), weather pruning blocks marginally hot/rainy corridors whose spot prices jumped enough to offset spoilage. Keeping `T3` protects vulnerable extreme heat/rain shipments, lowering heat/rain loss rate from 11.39% to 10.10% and improving heat/rain worst-10% loss from -₹67.49 to -₹57.11/qtl.

27. **Q: Why did `B2` earn higher mean net gain (₹1,150.83/qtl) than Stage-I `MandiGuard` (₹605.06/qtl) on Grade-Explicit HP Apple 2026 (`Exp 3`), and what did `Exp 16` prove really happened?**  
    **A:** Initially we suspected wide conformal intervals (`T4`) suppressed scarce 2026 `Grade A` auctions (~₹10,000+/qtl). Our Stage-II diagnostic `Exp 16` overturned that guess empirically: on lots where `B2` dispatched and Stage-I `MandiGuard` refused, **`77.82%` on holdout** (`N = 275`, `B2` mean `+₹3,511.16/qtl`) and **`82.75%` in warmup** (`N = 458`, `B2` mean `+₹1,004.66/qtl`) were actually rejected at **gate `T1`** (`open_prob_14d < 0.50` because splitting apple arrivals into rare `Grade A`/`Range-1` tags makes per-grade series look sparse), whereas only `22.18%` (`16.59%` warmup) failed at `T4`. Stage-I `MandiGuard` still cut traps 7x (94.14% → 13.24%) and tail loss to -₹102.76/qtl, and adding Stage-II grade-aware `T1` liquidity (`MandiGuard-CRC`, `Exp 17`) lifts HP Apple mean by **+34.2% to ₹812.08/qtl** (`Grade A` `₹205.46 → ₹477.56/qtl`).

28. **Q: Is `MandiGuard` an autonomous LLM agent, and why didn't you run GPT-4 at decision time?**  
    **A:** No—`MandiGuard` is **not an autonomous LLM agent**; it is a deterministic, **risk-gated dispatch decision-support system** structured as a four-step verification cascade (`T1` → `T2` → `T3` → `T4`) with explicit abstention. Running without runtime LLMs keeps inference deterministic, under 0.1 ms/query, zero-token-cost, and usable via lightweight rural SMS/IVR or extension portals without cloud latency or hallucinations, following selective prediction and uncertainty-aware tool invocation (Kachuee et al., 2019; Han et al., 2024).

29. **Q: Why did the 3-module coordinator `B5_MultiAgentCoordinator` earn less (₹437.39/qtl) than unified `MandiGuard` (₹452.79/qtl)?**  
    **A:** When Scout → Logistics/Weather → RiskGate communicate over coarse quantized margin tiers (₹150/qtl buckets), boundary precision is lost near the ₹50/qtl cutoff (-₹15.40/qtl difference) without saving tool calls (8.76 vs 8.75). Keeping one unified continuous cascade preserves precision.

30. **Q: Can your model generalize to a state it never saw in training?**  
    **A:** Yes—evaluated in our **Leave-One-State-Out (LOSO) diagnostic (`Exp 9`)**. Training strictly on 5 states in 2024 and predicting the held-out 6th state in 2025–2026 beat `B1` in all 6/6 unseen states (+₹424.19/qtl in HP, +₹122.79/qtl in MP, etc.), keeping arrival-price drops under 10% (3.34%–9.72% vs 45.3%–55.7% under `B1`).

31. **Q: What are the top rejection reasons in `MandiGuard`?**  
    **A:** Out of 69,526 shortlisted episodes (`Exp 7`): 48.66% (33,828) dispatch after clearing LCB (12.30 avg calls), 25.48% (17,713) are pruned early by `T1` (`VARIETY_OR_STALE`, averaging 3.64 calls), 17.58% (12,222) are refused by `T4` (`ARRIVAL_REVERSION_RISK`), 5.34% by `T1` (`CLOSED_YARD_RISK`, 3.04 calls), 2.24% by `T2` freight, and 0.71% by `T3` weather spoilage.

32. **Q: Why allow waiting +1 or +2 days at destination (`detention = ₹25/day`) instead of immediate rejection?**  
    **A:** Indian truckers reaching an auction yard closed for a mid-week holiday either wait 1–2 mornings (paying parking/waiting detention and taking extra heat decay) or divert. Modeling waiting `w in {0, 1, 2}` plus 3-day closure diversion reflects standard truck logistics.

33. **Q: What happens if fuel prices spike +25% or refrigerated vans halve spoilage (0.5×)?**  
    **A:** Across our 3 × 3 sensitivity matrix (`Exp 6`), `MandiGuard` beats `B1` in all 9/9 cells (+₹82.62 to +₹121.42/qtl). Against `B2`, `MandiGuard` leads at 1.0× and 1.5× spoilage (+₹5.27 to +₹14.50/qtl), while matching `B2` within -₹0.02 to -₹1.52/qtl if refrigeration halves decay to 0.5×.

34. **Q: Could interstate corridors (> 500 km or across state borders) change the findings?**  
    **A:** Our corridors cover intra-state distances [15, 500] km, reflecting typical smallholder truckloads (30 qtl, 1–3 days). Long-haul interstate corridors (1,500+ km, e.g., Nashik → Delhi) operate via large multi-trader aggregators and involve state e-way permits; extending to inter-state FPO corridors is future work.

35. **Q: How can someone reproduce your computational results on their own machine?**  
    **A:** Open `notebooks/colab_standalone_reproduction.ipynb` alongside the 4.83 MB `colab_data_pack.tar.gz` bundle in Google Colab and click **Run all**—it unpacks the frozen 2024 Stage-I and Stage-II models, holdout panel, benchmark schedules, and source code to reproduce the Stage-I benchmark, Stage-II `MandiGuard-CRC` autopsy/bootstrap, Dual-Tier `Exp 14`, and Appendix illustrations in under 3 minutes.

---

## Group D — 10-Year Scale (`Exp 10`–`10b`) & Appendix Illustrations (`Exp 11`–`13b`, Not Main Contributions) (Q36–Q40)

36. **Q: Does `MandiGuard` hold up across COVID-19, GST transition, export curbs, and El-Niño—beyond 2024–2026?**  
    **A:** Yes. We streamed 42,722,187 raw AGMARKNET mirror rows (2017-01-01..2026-04-13; 883,406 rows in our 178-mandi panel) and aligned 291,384 NASA POWER daily agroclimatology rows (2017–2023, 114 0.5° grids) (`Exp 10`, 661,192 matched episodes across 6 macro regimes). Across every regime (2017H2 GST, 2018–19, 2020–21 COVID, 2022–23 Inflation/Export Curb, 2024 El-Niño Heatwave, 2025–26), `B1` suffers 39.18%–44.29% loss-trip rates and -₹786.52 to -₹1,289.28/qtl worst-10% tail losses, whereas causally expanding `MandiGuard` holds loss-trip rates to 8.78%–12.03%, limits worst-10% losses to -₹20.93 to -₹37.89/qtl, and gains +₹165.14/qtl over `B1` during the 2024 El-Niño (₹387.91 vs ₹222.77/qtl).

37. **Q: Does training on 8 years of data (2017–2024, 3.44M rows) beat 1 year (2024, 702k rows)?**  
    **A:** In `Exp 10b`, 1-Yr gets ₹452.79/qtl, 3-Yr (1.67M rows) gets ₹454.74/qtl, and 8-Yr (3.44M rows) gets ₹454.94/qtl—only +₹2.15/qtl difference. Because agricultural spread regimes shift over time, recent calibration (2024) plus causal conformal guardrails captures nearly all the benefit of 8 years of data.

38. **Q: (Appendix Illustration `Exp 11`) How does `MandiGuard` compare against Quantile GBDT, Deep MLPs, Contextual Bandits, and NeurIPS'21 Adaptive Conformal Inference (`ACI`)?**  
    **A:** In our exploratory Appendix illustration (`Exp 11`, not a main thesis contribution): `Direct_Quantile_GBDT_Q20` edges `MandiGuard_Standard` slightly on 6-state mean (₹459.02 vs ₹452.79/qtl, 9.40% LTR), while on high-shift HP Apple 2026, `Deep_MLP_Conformal` leads mean (₹615.34/qtl, 18.15% LTR) and `MandiGuard_ACI` (Gibbs & Candès, 2021) adapts Apple α from 0.200 → 0.164, reducing worst-10% loss by 27.6% (-₹102.76 → -₹74.42/qtl).

39. **Q: (Appendix Illustration `Exp 12`) What does offline `ZeroCloud` caching illustrate for deployment API budgets?**  
    **A:** Treated strictly as an Appendix illustration (`Exp 12`, not a main contribution) using illustrative ₹0.05/call pricing: since highway distances don't change weekly (`T2`) and our lightweight forecaster runs on CPU in 0.099 ms/query (`T4`), caching `T2` + running `T4` locally cuts live external API spend 64.9% vs `B4` (₹2,764 vs ₹7,868 per 10k queries at 5.53 calls/query) while reaching ₹455.33/qtl. Adding a validation-frozen ₹250/qtl satisficing early-exit lowers live calls to 3.84/query (₹1,922 per 10k queries, 75.6% lower API cost) while keeping 97.3% of standard utility (₹440.48/qtl).

40. **Q: (Appendix Illustration `Exp 13`/`13b`) What cooperative and advisory extensions are shown in the Appendix?**  
    **A:** Evaluated strictly as exploratory Appendix illustrations (`Exp 13`/`13b`, not main contributions): first, under an illustrative 0.70× truck factor, pooling three 30-qtl smallholders into a shared 90-qtl FPO truck lifts net gain to ₹477.28/qtl (+₹24.49/qtl over solo 30-qtl and +₹67.75/qtl over 10-qtl marginal growers). Second, a 50/50 Top-2 Split-Lot Portfolio lowers closed traps from 16.17% to 9.85%. Third, our Q10 Biological Spoilage Clock computes safe transit hours before 15% decay (Tomato: 110.8h at 20°C down to 24.1h at 42°C) and formats illustrative ≤ 160-character SMS cards (`sample_farmer_sms_cards.txt`).

---

## Group E — Tough Examiner Probes: `H4`, `Exp 14`, Dual-View `Exp 15`, & Test Scope (Q41–Q44)

41. **Q: Isn't `H4` (44.4% fewer tool calls than `B4`) true simply by construction?**  
    **A:** Yes—we agree directly that fewer average calls (8.75 vs 15.74) follow by design from ordering `T1`–`T4` cheapest-first rather than querying all tools upfront. The empirical payoff appears under tight query caps (`Exp 5`): at `B = 6` calls/episode, `MandiGuard` earns ₹403.85/qtl (5.05 calls) vs `B4`'s ₹299.31/qtl (5.75 calls), a +₹104.54/qtl advantage.

42. **Q: How reliable is your AGMARKNET mirror, and what exactly did Dual-Tier `Exp 14` verify?**  
    **A:** We state the exact scope cleanly: the bulk 2017–2026 CSVs came from a public AGMARKNET archive mirror, audited across two official benchmarks in `Exp 14`: **Tier 1** spot-checks `2023-10-18` (`172` matched core-panel keys from `6,434` all-India official `data.gov.in` Resource `9ef84268-d588-465a-a308-a864a43d0070` XML rows: `100.00%` `Min`/`Max`, `99.42%` `Modal` parity); **Tier 2** cross-checks a direct **149-day official AGMARKNET 2.0 export** (`2025-11-07..2026-04-13`, `2,042` matched market–variety–grade–day rows) at **`100.00%` exact parity on all three price columns (`Min_Price`, `Max_Price`, `Modal_Price`)**, supplemented by 22 live Nov-2026 `agmarknet.gov.in` queries.

43. **Q: (`Exp 15`) How do you defend `MandiGuard` if missing 3-day entries have smaller diversion penalties—or when ALL candidate yards are strictly observed open?**  
    **A:** We present both views openly from `results/exp15_missing_data_open_yard_sensitivity.csv`:
    * **View 1 — Trap-Penalty Crossover Curve (`All_Shortlisted_Episodes`, N = 69,526):** From baseline 1.5× diversion freight / 10% variety discount (`MandiGuard` ₹452.79 vs `B1` ₹350.01, +₹102.78) through 1.0× / 10% (+₹91.66: ₹454.27 vs ₹362.61) and 0.5× / 5% (+₹42.43: ₹456.00 vs ₹413.57, 9.97% vs 38.01% LTR), `MandiGuard` leads `B1`. It crosses below `B1` on mean only at the zero-cost 0.0× / 0% boundary (`MandiGuard` ₹458.17 vs `B1` ₹468.17, -₹10.00; vs `B2` ₹456.09, +₹2.08; vs `B3` ₹479.09, -₹20.93), while still holding loss-trip rate at 6.09% (vs 18.52% `B1`, 20.40% `B3`) and worst-10% loss at -₹28.70 (vs -₹877.41 `B1`, -₹851.02 `B3`). Under break-even ₹0.00 return for missing 3-day arrivals (`5_ZeroTrap_BreakEven0_Missing3d`), `MandiGuard` (₹459.03, 5.96% LTR) leads `B1` (₹376.77, +₹82.26), `B2` (₹457.24, +₹1.79), and `B3` (₹385.42, +₹73.61).
    * **View 2 — Fair Matched Complete-Observation Cohorts (identical episodes across ALL 4 policies, zero simulated traps, zero selection bias):**
      * `Matched_AllTopK_Observed_d0` (N = 10,162 identical episodes where every top-5 candidate has observed arrival-day `d0` price): `MandiGuard` (₹510.89, 47.31% disp, 6.82% LTR, -₹36.07 CVaR10) beats `B1` (₹472.51, 74.78% disp, 19.84% LTR, -₹694.72; **+₹38.38**) and `B2` (₹469.99, 64.38% disp, 15.09% LTR, -₹94.70; **+₹40.91**), while point-ML `B3` earns +₹42.33/qtl higher mean (₹553.22, 73.47% disp) at 2.2× higher loss-trip rate (14.77%) and 10× deeper tail loss (-₹362.40).
      * `Matched_AllTopK_Observed_3d` (N = 16,849 identical episodes where every top-5 candidate trades exact variety in `d0..d2`): `MandiGuard` (₹592.53, 54.31% disp, 7.74% LTR, -₹48.25 CVaR10) beats `B1` (₹581.06, 81.45% disp, 20.63% LTR, -₹829.21; **+₹11.47**) and `B2` (₹572.09, 70.97% disp, 15.81% LTR, -₹588.86; **+₹20.44**), while `B3` earns ₹670.38 (79.16% disp; `MG - B3` = -₹77.85) at 15.02% LTR and -₹464.35 CVaR10.
    * **Takeaway:** *Price forecasting works when yards are open; it fails on the full market because it lacks `T1` openness checks and `T4` safety cushions.*

44. **Q: What do your 22/22 `pytest` tests actually verify, and what remains unvalidated in the field?**  
    **A:** All 22/22 automated tests pass, and we state their scope candidly: they verify code reproducibility, data manifest integrity, Dual-Tier `Exp 14` parity, Stage-II `Exp 16`–`17` artifact consistency, coordinate sanity, bootstrap/Holm arithmetic, and temporal leakage guards (including `arrival_date + 2d <= 2024-12-31` settlement firewalls and causal weather features)—they do **not** validate field economics. Live farmer truck receipts, weighment spoilage measurements, and field interviews remain essential next-step validation before real deployment.

---

## Group F — Stage-II `[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]` Mechanistic Autopsy & `MandiGuard-CRC` (Q45–Q50)

45. **Q: What is Censored-Arrival Survivorship Bias (`Exp 16`, Finding A), and how much did it distort Stage I?**  
    **A:** In Stage I, `CausalArrivalForecaster` called `dropna(subset=["target_ret"])`, discarding **55.83%** of raw `Train_2024` corridors (and **12.64%** even after passing `T1`) whenever the destination yard did not report an exact-variety price on arrival day. Across quote age `0d -> 3d` post-`T1`, exact `d0` open rate drops monotonically from `89.10%` to `62.63%` in `Train_2024` (`86.90% -> 62.97%` on `Holdout_2025_2026`). Dropping those missing/closed days understated true uncensored 20th-percentile (`Q20`) downside losses by **1.82x–2.00x** in `Train_2024` (`-4.81%` vs `-9.62%` at `0d`; `-13.46%` vs `-26.08%` at `3d`) and up to **2.54x** on `Holdout` (`-10.55%` vs `-26.82%` at `3d`). This is the market-logistics analogue of the Selective Labels problem (Lakkaraju et al., 2017).

46. **Q: What is the Heteroscedastic Coverage Illusion (`Exp 16`, Finding B) in Stage-I conformal bounds?**  
    **A:** Even though Stage-I marginal conformal coverage hit ~79% (`78.85%` val, `79.07%` holdout), splitting by 14-day destination volatility quartile (`dest_vol_14d`) reveals a **21–23 pp conditional coverage collapse** (Lei et al., 2018; Romano et al., 2019). On `Holdout_2025_2026`, Stage-I `MandiGuard` covers **90.46%** in calm `Q1` markets (issuing a `6.04%` cushion against a `1.98%` true Q80 error—unnecessarily suppressing profitable safe trips) yet drops to **67.80%** in volatile `Q4` markets (`88.91% -> 67.84%`, `-21.07 pp` in `Val_2025H1`; issuing an `8.89%` cushion against a `17.08%` true Q80 error—barely half the needed downside margin).

47. **Q: How does Stage-II `MandiGuard-CRC` score routes, how was $\lambda^* = 0.15$ chosen, and why don't you claim Angelopoulos et al. (2024) Theorem 1 guarantees?**  
    **A:** Stage-II trains two frozen 2024 gradient-boosted estimators on the `274,296` settled post-`T1` (`static_net > 0`) **uncensored** full payoffs `Y_full` (`arrival_date + 2d <= 2024-12-31`): expected net gain $\hat{\mu}(x)$ and raw `HistGradientBoostingClassifier` tail-loss risk probability $\hat{p}_{\text{loss}}(x) \approx \mathbb{P}(Y_{\text{full}} < 0)$. It ranks pre-shortlisted candidates by $1.20\times$ Euclidean-adjusted spread and gates them by $\text{Score}_{\text{CRC}}(m) = \hat{\mu}(m) - \lambda^* \cdot P_{\text{loc}} \cdot \hat{p}_{\text{loss}}(m)$ (> ₹50/qtl and $\hat{\mu} > ₹50$). Sweeping $\lambda \in \{0.00, 0.05, \dots, 1.20\}$ strictly on clean `Val_2025H1` (`N = 42,794`, `arr_dt <= 2025-05-31`, zero holdout tuning) and stopping at the first feasible grid point (`break`) satisfying $(n_{\text{loss}}+1)/(n_{\text{disp}}+1) \le \beta_{\text{target}} = 0.095$ freezes **`lambda* = 0.15`** for `MandiGuard-CRC` (`₹365.46/qtl`, `9.15%` LTR in val; `Rung 2` strict `T1` freezes at `lambda* = 0.10`, `₹358.52/qtl`, `9.34%` LTR). **Crucially:** we explicitly state we do **not** claim Angelopoulos et al. (2024) Theorem 1 distribution-free guarantees because agricultural crop prices are non-exchangeable across monsoon regimes and the dispatch denominator $n_{\text{disp}}(\lambda)$ varies with $\lambda$; we use `(n_l+1)/(n_d+1) <= 0.095` strictly as an empirical validation heuristic audited out-of-sample on untouched holdout.

48. **Q: Why keep Stage I (`₹452.79/qtl`) frozen instead of replacing it with Stage II (`₹479.17/qtl`) as your headline pre-registered result?**  
    **A:** Strict scientific integrity and anti-HARKing discipline (Nosek et al., 2018): commit `e421d15` pre-registered `H1`–`H4` for Stage-I `MandiGuard` v1 prior to unblinding `Holdout_2025_2026`. Discovering `Exp 16` after holdout means any corrective fix must be clearly marked `[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]` rather than retroactively passed off as pre-registered. Keeping both Stage I (frozen) and Stage II (`MandiGuard-CRC`, $\lambda^* = 0.15$ frozen on `Val_2025H1`, zero holdout tuning, evaluated via causal 3-rung ablations + `R = 5,000` 2-way cluster bootstrap) makes the research both 100% honest and stronger (`+₹32.51/qtl` over `B2`, $p = 0.0016$; `+₹26.38/qtl` over `MG_v1`, $p = 0.0002$).

49. **Q: Could `MandiGuard-CRC`'s gain on `Holdout_2025_2026` (`₹479.17/qtl`) just be an artifact of overfitting to simulated closed-yard diversion penalties in `Y_full`?**  
    **A:** We test that exact counter-hypothesis directly on `Matched_AllTopK_Observed_d0` (`N = 10,162` identical episodes where every top-5 candidate yard is guaranteed open on arrival day `d0` and zero simulated trap penalties apply). `MandiGuard-CRC` earns **₹533.75/qtl** (`₹16,012.5` per 30-qtl truck) at **7.14% LTR** and **-₹35.00 `CVaR_10%`**—outperforming `MG_v1` (`₹510.89`, `+₹22.86`), `B1` (`₹472.51`, `+₹61.24`), and `B2` (`₹469.99`, `+₹63.76`), while halving `B3`'s loss-trip rate (`14.77% -> 7.14%`) and shrinking tail loss ten-fold (`-₹362.40 -> -₹35.00`).

50. **Q: Why did Stage-II `MandiGuard-CRC` rise `+34.2%` on HP Graded Apples (`₹605.06 -> ₹812.08/qtl`) yet still trail `B2` (`₹1,150.83/qtl`) on mean return?**  
    **A:** Grade-aware `T1` liquidity (`fresh0 | strict`, admitting `age == 0` arrivals with `open_prob_14d >= 0.20` and `dow_open_rate >= 0.25`) unlocked the `77.82%` false `T1` blocks caused by sparse sub-grade reporting, doubling `Grade A` realized return (`₹205.46 -> ₹477.56/qtl` while cutting `Grade A` LTR from `20.00%` to `11.54%`) and lifting `Grade B` to `₹852.01/qtl`. The remaining gap vs `B2` (`22.84%` vs `33.64%` dispatch) reflects a genuine risk–return preference: `B2` achieves higher average Apple revenue at `28.43%` LTR and `-₹272.50/qtl` `CVaR_10%` (`-₹4,472.90` on `Grade B`), whereas `MandiGuard-CRC` limits `CVaR_10%` to **`-₹113.40/qtl`** (`-₹142.46` on `Grade B`)—a limitation we still highlight candidly.
