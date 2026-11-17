# 35 M.Tech Viva Questions & Crisp Examiner-Ready Answers — `MandiGuard`

## Group A — Motivation, Novelty & Agricultural Economics (Q1–Q9)

1. **Q: In one sentence, what is "Phantom Spatial Arbitrage"?**  
   **A:** It is an apparent cross-mandi profit spread shown on price boards that turns negative or fails to execute once real highway freight, state mandi charges, variety/grade mismatches, closed destination yards, ambient spoilage, and arrival-day price drops are included. On our 6-state holdout (`63,040` naive dispatches), headline spreads average `₹1,330.49/qtl` yet **`58.94%`** hit closed/missing-variety traps and **`40.46%` lose money outright**.

2. **Q: Why didn't you just predict tomorrow's mandi price like dozens of existing ML papers?**  
   **A:** Because we directly tested an unconstrained ML point forecaster (`B3_MLPointDispatch`) on `69,526` real holdout episodes—and it performed **worse than naive price-board chasing**: `45.28%` of its dispatched trucks lost money and `65.65%` hit closed-yard or missing-variety traps (`₹330.85/qtl` vs naive `₹350.01/qtl` and `MandiGuard`'s `₹452.79/qtl`). Accurate regression MSE does not fix operational execution traps or downside asymmetry.

3. **Q: Why is `MandiGuard` a real scientific AI contribution and not "just simple `if-else` business rules"?**  
   **A:** Three empirical proofs settle this directly against our ablations and comparators: (1) our heuristic verbal rule router `B6_HeuristicBucketRouter` underperforms `MandiGuard` (`₹431.94` vs `₹452.79/qtl`, higher traps `21.59%` vs `16.17%`, and uses `34.9%` more tool calls); (2) removing causal Conformal `80%` LCB (`No_T4`) **increases phantom loss risk by `69.4%`** (`9.97% -> 16.89%`) and worsens worst-10% tail losses **10.5x** (`-₹37.89 -> -₹397.19/qtl`); and (3) `MandiGuard`'s sequential cascade traces a provably superior utility–API-budget Pareto curve (`+₹104.54/qtl` over upfront verification `B4` at `B = 6` calls/episode).

4. **Q: Wait — what happened to your earlier multi-ensemble `EVA-Mandi` attempt (`H1, H2, H4, H5` rejected)? Why did you pivot?**  
   **A:** In `EVA-Mandi` v1, stacking 9 ensembles, Duan smearing, Knowledge-Gradient integrals, and delayed conformal rules over small HP Apple subsets failed 4 of 5 pre-registered hypotheses and lost to a simple staleness filter. Following first-principles scientific rigor, we preserved that archive untouched, pivoted cleanly to multi-state physical arbitrage (`MandiGuard`), kept the math transparent (1st-year engineering economics + single HGBR + empirical conformal LCB), and got `3/4` confirmatory hypotheses strongly supported (`H1, H3, H4`, all $p_{\text{Holm}} \le 0.0012$) with rich, honest insights on `H2`.

5. **Q: Why is your local market sale option (`REFUSE_PHANTOM_SPREAD`) justified theoretically?**  
   **A:** By Chow (1970) optimal reject theory and Franc et al. (2023): dispatching a perishable load creates asymmetric risk (sunk freight + spoilage + diversion cost up to `-₹1,062.66/qtl` worst-10% tail), whereas refusing an uncertain spread yields deterministic local realization (`ΔNet = ₹0`). An agent must predict *lower confidence bounds*, not point averages.

6. **Q: How is a farmer's truckload size and income impact grounded, rather than made up?**  
   **A:** Directly in **MoSPI NSO *NSS Report No. 587* (77th Round Situation Assessment Survey)** (`PIB PRID 1753856`): average harvested quantity per selling household is `2,933 kg` (`29.33 qtl`) for Potato and `3,873 kg` (`38.73 qtl`) for Onion—grounding our **`30-quintal` mini-truckload**—while average household net crop income is **`₹3,798/month`**. Thus our `+₹102.78/qtl` gain (`+₹3,083.5` per load) represents **81.2% of a household's monthly net crop income** on a single trip.

7. **Q: How do recent papers like *AgriMarket AI* (2026) and *Mandi Cast* (2026) differ from `MandiGuard`?**  
   **A:** Both compute point net gains using Euclidean Haversine distances or weather-covariate regressions without exact variety/grade matching, arrival-weekday openness checks, transit biological $Q_{10}$ heat decay, or selective conformal refusal—they are exact archetypes of our failing baselines `B1` and `B3`.

8. **Q: Which of the 4 crops suffers the worst phantom arbitrage, and why?**  
   **A:** **Onion** (`48.69%` phantom loss rate under `B1`, averaging only `+₹53.61/qtl` net gain on a `₹704.50/qtl` headline spread), because onion varieties (`Red`, `Puna`, `Local`, `Standard`) fluctuate quickly in tight margin bands where `₹138/qtl` freight and arrival drops wipe out gains. **Apple** has the largest absolute spread erosion (`₹3,499.80/qtl` screen -> `₹1,982.36/qtl` lost to traps/reversion), and **Tomato** has the highest transit spoilage (`3.25%` NABCONS base).

9. **Q: Why did `MandiGuard` do especially well across Onion and Potato, while naive `B1` had a slightly higher mean on Tomato (`₹547.64` vs `₹522.48`)?**  
   **A:** Because tomato spreads occasionally hit rare massive scarcity spikes that inflate naive average revenue even while **`32.38%` of naive tomato episodes lose money**! `MandiGuard` trades away a sliver of lottery upside (`-₹25.16/qtl` vs `B1`, while still beating `B2` Fresh+OSRM by **`+₹37.84/qtl`**!) to cut tomato episode losses more than 6-fold (`32.38% -> 5.09%`).

---

## Group B — Data Authenticity, Official Government Surveys & Physical Model (Q10–Q19)

10. **Q: How do we know none of your mandi price data is synthetic or scraped against website terms?**  
    **A:** We archived SHA-256 checksums for every streamed raw 2024–2026 AGMARKNET archive file (`14,443,770` rows), quarantined and excluded synthetic files from prior workspace experiments, used zero CAPTCHA bypassing, executed only unauthenticated open AGMARKNET API `lastweek` queries for Nov 2026 verification (`HTTP 200`), and fetched all Open-Meteo / OSRM / `.gov.in` records cleanly with polite backoffs.

11. **Q: How did you avoid "survivorship bias" when picking top mandis?**  
    **A:** Picking the most active markets over the full `2024–2026` range peaks into the future (markets that shut down in 2025 wouldn't be picked). We strictly ranked the top 30 markets per state using **only calendar `2024` trading days** (`>= 20` days in 2024, `>= 80` total -> `178` core mandis across 6 states).

12. **Q: Where did your base crop spoilage percentages come from? Did you tune them?**  
    **A:** Zero tuning! We took them directly from **MoFPI / NABCONS (2022) Annexure-II Table-2** (tabled in Rajya Sabha, `PIB PRID 2151371`, `01 Aug 2025`), using the official **market-level handling and transport loss rates**: Tomato `3.25%`, Onion `1.96%`, Apple `1.64%`, Potato `0.86%`.

13. **Q: Wait—AGMARKNET doesn't publish truck-level spoilage receipts! Isn't your spoilage calculation a simulation?**  
    **A:** Yes, we state this limitation openly (`Section 8` and `NOVELTY_AUDIT.md`): prices, yard availability, road hours (`OSRM`), and corridor heat/rain (`ERA5`) are 100% observed ground truth, while per-shipment biological shrinkage uses a standard food-engineering $Q_{10}$ curve anchored to official NABCONS (2022) rates. To ensure our conclusions don't hinge on spoilage weights, our $3\times 3$ sensitivity test (`Exp 6`) sweeps spoilage `[0.5x, 1.0x, 1.5x]` and freight `[0.75x, 1.0x, 1.25x]`: `MandiGuard` beats `B1` in all `9/9` regimes (`+₹82.62` to `+₹121.42/qtl`).

14. **Q: Why do cross-district mandi charges differ across your 6 states?**  
    **A:** Because Indian agricultural marketing is a State subject (`PIB Release ID 154554`): Karnataka and Gujarat exempted market fees on fruits and vegetables (leaving ~`0.5%` user/handling fees); Himachal Pradesh exempted all F&V **except Apple** (`0.5%` veg vs `1.0%` Apple); Maharashtra deregulated direct outside-yard F&V sales (`1.0%` inside APMC supervision); while Madhya Pradesh (`notified yards`) and Uttar Pradesh maintain regulated yard levies (`1.5%`). Swapping uniform `1.5%` fees for these authentic state rules unlocks `+₹7.12/qtl` real net spatial margin (`Exp 6`).

15. **Q: Why does Himachal Pradesh carry a `1.45x` per-km road freight multiplier?**  
    **A:** Confirmed directly by official Public Works Department statistics in the **Government of Himachal Pradesh *Economic Survey 2025–26* (Table 28)**: out of `43,091 km` of motorable roads, **`39,465 km` (`91.59%`) are single-lane hill roads** (plus `1,337 km` jeepable), causing higher fuel burn and slow speeds relative to plains highways.

16. **Q: What happened when Open-Meteo hit its daily forecast request limit on `43` northern grid cells? Did that cause future leakage?**  
    **A:** No—we obeyed the API quota (`HTTP 429`) strictly rather than bypassing it. All `145/145` (`100%`) ground-truth `ERA5` cells finished first, alongside `102/145` (`70.3%`) native Open-Meteo historical forecasts (`100%` of `GJ, KA, MP, MH` + `8` UP cells). For the `43` remaining cells, we fit a Ridge nowcaster **strictly on `2024` overlap data using only causal day-`<= t` ERA5 inputs** (validated via a unit test perturbing `t+1..t+3` with `0.0` effect on `<= t`)—AND proved in `Exp 2b` that across the **`42,766` episodes in the 4 states with `100%` native NWP forecasts**, `MandiGuard` beats *both* `B1` (`+₹59.53/qtl`) and `B2` (`+₹31.82/qtl`)!

17. **Q: How did you prevent geocoding errors like matching a Maharashtra village to Rajasthan?**  
    **A:** In early audits, raw geocoders matched `"Neemuch"` to Rajasthan and `"Gonda"`/`"Ahmadnagar"` to distant homonym villages (`300–400 km` off). We enforced `admin2` district-alias validation and a hard `<= 110 km` Haversine check against verified District HQ coordinates across all `220` mandis (enforced automatically by `pytest`).

18. **Q: How do you handle clerks entering `"Onion"`, `"Other"`, and `"FAQ"` interchangeably for variety?**  
    **A:** We canonicalize generic commodity-name / `"Other"` / `"FAQ"` entries into `"Standard"` and unify spelling variants (`"Deshi"` -> `"Desi"`), while strictly preserving distinct cultivars (`"Red"`, `"Hybrid"`, `"Royal Delicious"`, `"Badshah"`, etc.). That eliminates false mismatch noise while catching real cultivar traps.

19. **Q: What does the Live November 2026 AGMARKNET check prove?**  
    **A:** Querying 22 real benchmark corridors against the live official API on `November 17, 2026` revealed that **`11/22` (`50.0%`)** of benchmark APMC series (including major yards like Lasalgaon Onion and Bengaluru Tomato) reported zero trading across the entire preceding 7 days—proving that Tool `T1` market-vitality gating solves an active real-time problem today.

---

## Group C — Machine Learning, Conformal Intervals, Statistics & Limitations (Q20–Q35)

20. **Q: Explain Conformal Prediction (`T4`) in plain English for an examiner.**  
    **A:** Imagine checking how badly your weather or price app lied to you over the last 400 settled trips (`actual return minus predicted return`). You find the **80th percentile worst downside mistake**—say your model was over-optimistic by `7%` or more in `20%` of past trips. So today, instead of trusting the model's raw guess (`pred_ret`), you subtract that historical `7%` mistake buffer (`lcb_ret = pred_ret - 0.07`). You only send the truck if profit still clears `+₹50/qtl` *even after suffering an 80th-percentile bad surprise*!

21. **Q: Doesn't Conformal Prediction assume data is i.i.d. / exchangeable—which prices violate?**  
    **A:** Yes! We disclose this candidly: agricultural prices exhibit seasonality and monsoon shocks, so theoretical finite-sample exchangeability bounds are approximate, not exact theorems. That is why we maintain a **strictly causal sliding buffer** updated only once arrival dates mature (`arrival_date <= t`), and **empirically verify** actual coverage: **`78.85%`** in `Val_2025H1` and **`79.07%`** across `468,816` holdout candidate pairs—within `1%` of the nominal `80%` target!

22. **Q: Why train on `2024` only (`Train_2024`) and never refit monthly on `2025–2026`?**  
    **A:** Keeping the base forecaster weights 100% frozen in `2024` guarantees zero model overfitting to holdout price regimes and provides a tough out-of-time robustness stress test (`15` months ahead!). Only the scalar 400-sample conformal residual window adapts causally on matured arrivals.

23. **Q: How was `safety_margin_inr = ₹50/qtl` chosen? Was it tuned on holdout?**  
    **A:** Strictly **no holdout access**. It was swept over `{50, 100, 150, 200, 250}` on `Val_2025H1` (`Jan–May 2025`), frozen in `configs/frozen_calibration.json`, and locked into Git (`commit e421d15`) **before** holdout experiments ever ran. Notice `50` maximized validation net utility while keeping phantom loss below `10%` (`9.68%` in val -> `9.97%` in holdout!).

24. **Q: Why did Hypothesis `H2` (`MandiGuard > B2_FreshRoadGreedy` in Mean $\Delta\text{Net}$) fail statistical significance (`p_holm = 0.2699`)? Should we be worried?**  
    **A:** Quite the opposite—it is the hallmark of an honest thesis! `MandiGuard` edges out `B2` by `+₹6.13/qtl` overall (`₹452.79` vs `₹446.66/qtl`) and beats `B2` by `+₹31.82/qtl` across the 4 native-NWP states, while `B2` relies on risky high-variance same-day spreads (`18.11%` losing dispatches, `-₹436.67/qtl` `CVaR_10%`). Because our Two-Way Mandi $\times$ Block bootstrap accounts for correlated market & calendar shocks across 23 two-week clusters, `+₹6.13/qtl` is inside sampling noise, whereas **reducing risk (`PLR 18.11% -> 9.97%`) and improving tail `CVaR_10%` 11.5-fold (`-₹436.67 -> -₹37.89/qtl`)** is `MandiGuard`'s undeniable engineering edge over `B2`!

25. **Q: Why use Two-Way Origin-Mandi $\times$ 2-Week-Block Cluster Bootstrap (`R = 5,000`) instead of a standard paired `t`-test?**  
    **A:** Treating `69,526` episodes as independent draws violates independence doubly: consecutive days from the same origin mandi are serially correlated, and mandis across a state share regional monsoon/harvest price shocks in the same week. Our two-way cluster bootstrap resamples both `174` origin mandis AND `23` two-week blocks simultaneously, yielding honest wide confidence intervals (`[+48.66, +153.45]` for `H1` instead of artificially narrow i.i.d. CIs) with Phipson–Smyth exact finite-sample $p$-values and Holm–Bonferroni FWER control.

26. **Q: Look at `Exp 4`: why does removing weather tool `T3` slightly *increase* unconditional mean gain by `₹2.46/qtl` (`₹455.25` vs `₹452.79`)?**  
    **A:** Very intuitive: `T3` and `T4` stack conservatively (`spoilage` haircut + `80% LCB` price haircut). On `1.52%` of episodes (`50.18% -> 48.66%` dispatch), weather pruning blocks marginally hot/rainy corridors whose spot prices happened to jump enough to overcome spoilage. However, **keeping `T3` protects vulnerable extreme heat/rain shipments**, reducing heat/rain Phantom Loss Rate from `11.39% -> 10.10%` and improving heat/rain `CVaR_10%` from `-₹67.49 -> -₹57.11/qtl`.

27. **Q: Why did `MandiGuard` get lower mean net gain (`₹605.06/qtl`) than `B2` (`₹1,150.83/qtl`) on Grade-Explicit HP Apple 2026 (`Exp 3`)?**  
    **A:** Domain transfer under grade granularity! `forecaster_2024.pkl` trained on ungraded `2024` AGMARKNET data (`Standard` apples). When evaluated in `2026` against premium `Grade A` auctions (`~₹10,000+/qtl`), historical ungraded volatility inflated the `80%` conformal error buffer, causing `MandiGuard` to dispatch only `5.39%` of `Grade A` lots! Meanwhile on `Grade B` (lower buffer, huge `92.73%` naive trap hazard), `MandiGuard` crushed naive chasing (`+₹833.70/qtl` vs `-₹427.54/qtl`), cutting overall Apple traps **7x** (`94.14% -> 13.24%`) and tail losses **82x** (`-₹8,487.24 -> -₹102.76/qtl`). Recalibrating grade-specific quantiles is straightforward future work.

28. **Q: Does `MandiGuard` require any LLM API at runtime? Why didn't you run GPT-4 on every mandi?**  
    **A:** No LLM is required at decision time—making inference deterministic, millisecond-fast, zero-token-cost, and usable via lightweight rural SMS/IVR or state extension portals without cloud LLM latency or hallucinations! The "AI Agent" property comes from **sequential, uncertainty-gated tool orchestration (`T1 -> T2 -> T3 -> T4`) under partial observability and explicit abstention**, exactly following Kachuee et al. (2019) and UALA (Han et al., 2024).

29. **Q: Why did the 3-agent system (`B5_MultiAgentCoordinator`) perform worse (`₹437.39/qtl`) than single-agent `MandiGuard` (`₹452.79/qtl`)?**  
    **A:** Empirical refutation of unnecessary multi-agent bloat! When Scout -> Logistics/Weather -> RiskGate communicate over coarse quantized margin tiers (`₹150/qtl` buckets), boundary precision gets lost near the cutoff (`₹15.40/qtl` penalty) without reducing tool calls (`8.76` vs `8.75`). Keeping one unified continuous cascade wins cleanly.

30. **Q: Can your model generalize to a brand-new state it never saw in training?**  
    **A:** Yes—proven by our **Leave-One-State-Out (LOSO) diagnostic (`Exp 9`)**. Training strictly on `5` states in `2024` and predicting the held-out `6th` state in `2025–2026` beat `B1` in all `6/6` unseen states (`+₹424.19/qtl` in HP, `+₹122.79/qtl` in MP, etc.), keeping arrival-price drops under `10%` (`3.34%–9.72%` vs `45.3%–55.7%` naive).

31. **Q: What are the top rejection reasons in `MandiGuard`?**  
    **A:** Out of `69,526` shortlisted episodes (`Exp 7`): `48.66%` (`33,828`) dispatch after clearing LCB (`12.30` avg calls), **`25.48%` (`17,713`) are pruned early by `T1` (`VARIETY_OR_STALE`, averaging just `3.64` calls)**, `17.58%` (`12,222`) are refused by `T4` (`ARRIVAL_REVERSION_RISK`), `5.34%` by `T1` (`CLOSED_YARD_RISK`, `3.04` calls), `2.24%` by `T2` freight, and `0.71%` by `T3` weather spoilage.

32. **Q: Why allow waiting `+1` or `+2` days at destination (`detention = ₹25/day`) instead of immediate rejection?**  
    **A:** Real Indian truckers reaching an auction yard closed for a mid-week holiday either wait 1–2 mornings (paying parking/waiting detention and suffering extra heat decay) or divert/dump. Modeling `w in {0, 1, 2}` plus 3-day closure diversion reflects real agricultural truck economics accurately.

33. **Q: What happens if fuel prices spike +25% or refrigerated vans halve spoilage (`0.5x`)?**  
    **A:** Across our full $3\times 3$ matrix (`Exp 6`), `MandiGuard` beats `B1` in **every single cell (`+₹82.62` to `+₹121.42/qtl`)**. Against `B2`, `MandiGuard` wins at `1.0x` and `1.5x` spoilage (`+₹5.27` to `+₹14.50/qtl`), while matching `B2` within `-₹0.02` to `-₹1.52/qtl` if refrigeration halves decay to `0.5x`.

34. **Q: Could interstate corridors (`> 500 km` or across state borders) change the story?**  
    **A:** Our corridors cover intra-state distances `[15, 500] km`, reflecting typical smallholder truckloads (`30 qtl`, 1–3 days). Long-haul interstate rail/corridors (`1,500+ km`, e.g., Nashik->Delhi) operate via large multi-trader aggregators rather than individual farmers and involve state e-way permits; extending to inter-state FPO corridors is a natural next step.

35. **Q: How can someone verify your entire thesis results in 3 minutes on their own laptop?**  
    **A:** Open `notebooks/colab_standalone_reproduction.ipynb` alongside the self-contained `< 5 MB` (`4.82 MB`) `colab_data_pack.tar.gz` bundle in Google Colab and click **Run all**—it unpacks the frozen `2024` model, stratified holdout panel, verified GoI survey table, and source code to reproduce the benchmark, `ZeroCloud`, `FPO Pooling`, and cluster bootstrap cleanly in under 3 minutes!

---

## Group D — 10-Year Scale, Edge-AI `ZeroCloud`, Modern AI & Creative Farmer Solutions (Q36–Q40)

36. **Q: Does `MandiGuard` still hold up across COVID-19, GST transition, export curbs, and El-Niño—beyond 2024–2026?**  
    **A:** Yes! We streamed **all `42,722,187` raw AGMARKNET records (`2017-01-01`..`2026-04-13`)** (`883,406` rows in our 178-mandi panel) and aligned **`291,384` official US Govt NASA POWER agroclimatology rows (`2017–2023`, `114` `0.5°` grids)** (`Exp 10`, `661,192` matched episodes across 6 macro regimes). Across *every* regime (`2017H2 GST`, `2018–19`, `2020–21 COVID`, `2022–23 Inflation/Export Curb`, `2024 El-Niño Heatwave`, `2025–26`), `B1` suffers `39.18%–44.29%` Loss-Trip Rates and `-₹786.52` to `-₹1,289.28/qtl` tail crashes, whereas causally expanding `MandiGuard` holds Loss-Trip Rate to **`8.78%–12.03%`** and peaks at **`+₹165.14/qtl` over `B1` during `2024 El-Niño`** (`₹387.91` vs `₹222.77/qtl`).

37. **Q: Does training on 8 years of data (`2017–2024`, `3.44M` rows) dramatically beat 1 year (`2024`, `702k` rows)?**  
    **A:** Honest, super interesting finding (`Exp 10b`): `1-Yr` gets `₹452.79/qtl`, `3-Yr` (`1.67M` rows) gets `₹454.74/qtl`, and `8-Yr` (`3.44M` rows) gets `₹454.94/qtl`—just **`+₹2.15/qtl` improvement**. Agricultural mandi spread cycles shift over time, proving that **fresh recent calibration (`2024`) + causal conformal guardrails** beat brute-forcing decade-old price regimes!

38. **Q: How does `MandiGuard` compare against Quantile GBDT, Deep Neural MLPs, Contextual Bandits, and NeurIPS'21 Adaptive Conformal Inference (`ACI`)?**  
    **A:** In our `Exp 11` showdown (`Holdout_2025_2026` + `HP_Apple_Grade_2026`): `Direct_Quantile_GBDT_Q20` edges `MandiGuard_Standard` slightly on 6-state mean (`₹459.02` vs `₹452.79/qtl`, `9.40%` LTR), while on high-shift `HP Apple 2026`, `Deep_MLP_Conformal` leads mean (`₹615.34/qtl`, `18.15%` LTR) and **`MandiGuard_ACI`** (Gibbs & Candès 2021) shrinks Apple's adaptive $\alpha$ from `0.200 -> 0.164`, cutting **Worst-10% Loss by `27.6%`** (`-₹102.76 -> -₹74.42/qtl`). Notice any modern forecaster plugs cleanly into `MandiGuard`'s 4-tool cascade!

39. **Q: How did you make `MandiGuard` radically money-efficient for real deployment (`ZeroCloud`)?**  
    **A:** Highways don't move weekly (`T2`), and our lightweight forecaster runs on CPU in `0.099 ms/query` (`T4`)—so **`MandiGuard-ZeroCloud`** caches `T2` + runs `T4` locally, querying only live yard vitality (`T1`) and weather (`T3`). That cuts live external API spend **`64.9%`** vs `B4` (`₹2,764` vs `₹7,868` per `10k` queries at `5.53` calls/query) while actually *raising* mean profit to **`₹455.33/qtl`**! Adding a `Val`-frozen `₹250/qtl` **satisficing early-exit** stops scanning extra yards once a verified winner exceeds `₹250/qtl`, cutting API spend **`75.6%`** (`3.84` calls = **`₹1,922` per `10k` queries**) while keeping `97.3%` of standard utility (`₹440.48/qtl`).

40. **Q: What are your most creative out-of-the-box farmer features (`FPO Pooling`, `Split-Lot Portfolio`, `Spoilage Clock`)?**  
    **A:** First, pooling three `30-qtl` smallholders into a shared **`90-qtl` FPO truck (`0.70x` freight)** raises profit to **`₹477.28/qtl`** (`+₹24.49/qtl` over solo `30-qtl` and `+₹67.75/qtl` over `10-qtl` marginal growers). Second, a **50/50 Top-2 Split-Lot Portfolio** cuts `Closed Trap Rate` **`39%` relative (`16.17% -> 9.85%`)**. Third, our **$Q_{10}$ Biological Spoilage Clock** computes exact safe transit hours before `15%` decay (`Tomato`: `110.8h` at `20°C` down to **`24.1h` at `42°C`**) and translates every dispatch/refusal into real `<= 160`-character farmer SMS cards (`sample_farmer_sms_cards.txt`).
