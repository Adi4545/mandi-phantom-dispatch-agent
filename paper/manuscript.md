# Phantom Spatial Arbitrage in Indian Agricultural Mandis: A Climate-, Road-, and Freshness-Aware Verification Agent (`MandiGuard`)

## Abstract

Digital agricultural portals broadcast daily wholesale prices across hundreds of Indian Agricultural Produce Market Committee (*mandi*) yards so farmers can choose where to sell. Yet on untouched official daily records spanning `69,526` inter-market dispatch opportunities across six major Indian states (`Maharashtra`, `Uttar Pradesh`, `Karnataka`, `Madhya Pradesh`, `Gujarat`, and `Himachal Pradesh`) and four perishable crops (`Onion`, `Potato`, `Tomato`, and `Apple`; June 2025–April 2026), we show that a farmer or dashboard chasing the highest recent price board falls into **phantom spatial arbitrage**: headline spreads average `₹1,330.49/qtl`, yet **`58.94%`** of those dispatches arrive at a closed yard or miss the exact crop variety across three consecutive auction days, and **`40.46%` lose money outright** once highway freight, statutory mandi charges, ambient heat/rain spoilage, and arrival-day price drops are counted. Even an unconstrained machine-learning point forecaster (`B3`) performs worse than naive screen chasing, losing money on `45.28%` of dispatches (`65.65%` physical traps).

To solve this decision problem without black-box complexity, we present **`MandiGuard`**, a four-step sequential verification agent combining an explicit **local-sale refusal (`REFUSE_PHANTOM_SPREAD`)** option with a cost-ordered cascade of four metered checks: `(T1)` same-variety yard activity & weekday auction schedule, `(T2)` Open Source Routing Machine (OSRM) highway freight with state-specific statutory charges grounded in Government of India (GoI) APMC deregulation notifications, `(T3)` day-of-dispatch weather spoilage calibrated to Ministry of Food Processing Industries (MoFPI) NABCONS (2022) market-level loss benchmarks, and `(T4)` a causal `2024`-trained arrival-return forecaster wrapped in a causal `80%` conformal lower confidence bound frozen prior to holdout evaluation. Extending static graph lookup and CPU inference to edge hardware (**`MandiGuard-ZeroCloud`**) plus validation-calibrated satisficing early exit further trims external API demand to `3.84` live calls per query (`-75.6%` API cost vs upfront evaluation).

Across `69,526` shortlisted holdout episodes evaluated with paired two-way origin-mandi $\times$ 2-week-block cluster bootstrap (`5,000` draws) and Holm–Bonferroni correction ($m=4$), `MandiGuard` satisfies three of four pre-registered confirmatory hypotheses: it outperforms naive screen chasing by **`+₹102.78/qtl`** (`+₹3,083.5` per 30-quintal smallholder truckload; `95% CI [+₹48.66, +₹153.45]`, $p_{\text{Holm}} = 0.0012$), cuts episode phantom losses relative to point-forecast ML by **`37.29 percentage points`** ($p_{\text{Holm}} = 0.0008$), and matches an upfront all-tools oracle (`₹452.79/qtl`) using **`44.4%` fewer tool calls** (`8.75` vs `15.74`, $p_{\text{Holm}} = 0.0008$). On our fourth confirmatory test against a fresh same-day OSRM baseline (`B2`), the unconditional mean gain of `+₹6.13/qtl` is positive but statistically non-significant (`95% CI [-₹17.02, +₹25.02]`, $p_{\text{Holm}} = 0.2699$), reflecting an explicit risk–return tradeoff: `MandiGuard` sacrifices borderline high-variance lottery upsides in exchange for **nearly halving** dispatched phantom loss risk (`9.97%` vs `18.11%`) and reducing worst-10% tail losses (**$\text{CVaR}_{10\%}$**) **11.5-fold** (`-₹37.89/qtl` vs `-₹436.67/qtl`), while beating `B2` by `+₹31.82/qtl` across the four states with native historical weather forecast grids. Stress-testing backward over nearly a decade of official AGMARKNET archives (`2017–2026`, `42,722,187` raw rows, `661,192` matched episodes across six macro regimes) confirms persistent `8.78%–12.03%` loss-trip rates (vs `39.18%–44.29%` naive) peaking at `+₹165.14/qtl` advantage during the `2024 El-Niño Heatwave`, while cooperative `90-qtl` truck pooling lifts realized farmer profit further to `₹477.28/qtl`. An auxiliary holdout validation over `1,537` grade-explicit Himachal Pradesh Apple auctions (`June–August 2026`) confirms seven-fold physical trap reduction (`13.24%` vs `94.14%` naive) while revealing conservative under-dispatching on scarce top grades (`Grade A`)—where adaptive conformal inference (`MandiGuard_ACI`) cuts worst-10% tail risk by `27.6%`.

---

## 1. Introduction: Why Looking Up the Highest Mandi Price Can Bankrupt a Smallholder

Economists have long established that transparent price information reduces spatial waste and boosts producer incomes when perishables can flow to nearby deficit markets—most famously in Robert Jensen's study of Kerala coastal fishermen \cite{jensen2007digital}. Yet inland Indian agricultural markets behave very differently from open-coast fish landings. Macro-econometric studies consistently document persistent inter-mandi price wedges and fragmented market cointegration across India \cite{sekhar2012agricultural, chatterjee2016six}, while field experiments with West Bengal potato farmers demonstrate that broadcasting daily wholesale prices without usable outside dispatch mechanisms fails to raise average farmgate realizations \cite{mitra2018asymmetric}. Survey work likewise confirms that transport and communication frictions push rural producers toward low-margin local buyers \cite{negi2018farmers}.

Consider a concrete smallholder decision grounded directly in national household data. According to the National Statistical Office (*NSS Report No. 587*, 77th Round Situation Assessment Survey) \cite{nss77report587}, Indian agricultural households cultivating potatoes or onions harvest on average `29.33–38.73 quintals` per season—roughly one **30-quintal mini-truckload**—while earning **`₹3,798/month`** in net crop income (`50.2%` of households carrying an average debt of `₹74,121`). If a tomato or onion grower checks India's AGMARKNET price portal and spots a distant wholesale yard displaying **`₹700/qtl` higher modal price** than the local yard, sending one 30-quintal load appears to promise `+₹21,000` (over five months of net crop income).

In practice, four physical and institutional realities frequently turn that tempting headline spread into a devastating **phantom arbitrage loss**:

1. **Variety & Grade Heterogeneity:** Official portals aggregate or display the top recent headline quote, whereas an arriving farmer carries a specific cultivar (`Red`, `Desi`, `Hybrid`) or apple grade (`Grade A`, `Grade B`, `Medium`). Arriving when the destination yard does not trade that exact variety triggers steep distress discounts.
2. **Closed-Yard & Non-Reporting Hazards:** Regional mandis rotate auction days by weekday, suspend trade on local market holidays, or experience gaps in AGMARKNET reporting \cite{guo2020mandi, deka2026missing}. Dispatching a perishable truck onto a 4-day-old stale screen quote risks idling overnight (incurring demurrage) or diverting back empty.
3. **Actual Highway Geometry vs. Straight-Line Intuition:** India's rural and mountain road topology differs sharply from crow-flies geometry \cite{luxen2011osrm}. As documented by the *Himachal Pradesh Economic Survey 2025–26* \cite{hpeconsurvey2026}, `91.59%` of motorable roads in Himachal Pradesh (`39,465` of `43,091 km`) are single-lane hill roads, magnifying transit hours and fuel surcharge beyond plain-terrain rules.
4. **Ambient Heat, Heavy Rain & Statutory State Fees:** Unlike grain, fresh tomatoes, apples, and onions respire and spoil along open-truck highways under Indian summer heat (`>= 35°C`) and monsoon rains (`>= 35 mm/day`). Meanwhile, statutory mandi fee regimes vary across state boundaries \cite{pib154554apmc}: Karnataka and Gujarat exempt fruits and vegetables from market fees (charging nominal yard user fees), Himachal Pradesh exempts vegetables *except apples*, and Uttar Pradesh maintains regulated mandi yard levies.

Recent applied AI recommender prototypes predict mandi prices with standard regressions (`XGBoost`, `SARIMA`, `CNN`) or rank markets using Euclidean Haversine distances and raw point predictions \cite{madaan2019price, ma2019price, biradar2026agrimarket, manimegalai2026mandicast}. These tools optimize symmetric price-forecast accuracy rather than **cost-sensitive operational dispatch** \cite{chow1970optimum, franc2023optimal}, exposing smallholders to severe downside risk whenever an apparent spread collapses in transit.

### Summary of Contributions
Rather than proposing complex opaque neural ensembles or speculative multi-agent heuristics, **`MandiGuard`** makes four focused, verifiable M.Tech-level contributions grounded entirely in open Indian public data:
1. **Empirical Anatomy of Phantom Spatial Arbitrage (`Exp 1`):** Quantifies how headline cross-mandi spreads erode across `178` core mandis in six states and four perishable crops (`Onion`, `Potato`, `Tomato`, `Apple`), separating highway freight/APMC charges, NABCONS-anchored climate transit spoilage, and arrival trap/reversion losses.
2. **Government-Verified Engineering Payoff Model (`Exp 6`):** Anchors market-level transit perishability to official MoFPI NABCONS (2022) crop loss rates \cite{nabcons2022phl}, statutory seller/user fees to GoI APMC reform notifications \cite{pib154554apmc}, hill freight premiums to official HP road statistics \cite{hpeconsurvey2026}, and smallholder welfare framing to NSO NSS 77th Round household benchmarks \cite{nss77report587}.
3. **Asymmetric Risk-Gated Dispatch Agent with Causal Conformal Bounds (`H1`–`H4`):** Wraps a single `2024`-trained return predictor in a causally updated `80%` conformal lower confidence bound (`LCB`) \cite{angelopoulos2023conformal} coupled with an explicit `REFUSE_PHANTOM_SPREAD` (`LOCAL`) option \cite{chow1970optimum}, verified via Leave-One-State-Out transfer (`Exp 9`) and `2026` grade-explicit Apple auctions (`Exp 3`).
4. **Sequential Verification Funnel Pareto Frontier (`Exp 5`):** Adapts budgeted feature acquisition \cite{kachuee2019opportunistic} and uncertainty-gated tool calling \cite{yao2023react, han2024uala} into a strict `T1 -> T2 -> T3 -> T4` pruning pipeline that matches full all-tools oracle utility (`₹452.79/qtl`) while slashing tool queries by `44.4%`.

---

## 2. Related Work & Positioning

Table 1 contrasts `MandiGuard` against three distinct threads of prior literature, separating established building blocks from our domain contributions.

| Research Thread | Representative Prior Studies | What Prior Work Establishes | Gap Addressed by `MandiGuard` |
|:---|:---|:---|:---|
| **Indian Mandi Integration & Market Access** | Jensen \cite{jensen2007digital}; Sekhar \cite{sekhar2012agricultural}; Chatterjee & Kapur \cite{chatterjee2016six}; Mitra et al. \cite{mitra2018asymmetric}; Negi et al. \cite{negi2018farmers}; Mahajan & Tomar \cite{mahajan2021covid} | Persistent spatial wedges, weak inter-state cointegration, and evidence that price boards alone without execution channels fail smallholders. | Operationalizes day-level, truck-level spatial arbitrage auditing under exact variety matching, yard trading presence, road geometry, and heat decay. |
| **AGMARKNET Forecasting & Applied Recommenders** | Madaan et al. \cite{madaan2019price}; Ma et al. \cite{ma2019price}; Guo et al. \cite{guo2020mandi}; Deka \cite{deka2026missing}; *AgriMarket AI* \cite{biradar2026agrimarket}; *Mandi Cast* \cite{manimegalai2026mandicast} | ML imputation/prediction on AGMARKNET; explicit notice of missing closed-yard days; point-net profit ranking using Haversine or weather covariates. | Replaces missing-quote statistical imputation and point-profit ranking with arrival-day execution hazard pruning, OSRM routing, ambient thermal spoilage, and conformal abstention. |
| **Selective Reject Rules, Conformal LCB & Tool Agents** | Chow \cite{chow1970optimum}; Franc et al. \cite{franc2023optimal}; Angelopoulos & Bates \cite{angelopoulos2023conformal}; ReAct \cite{yao2023react}; Kachuee et al. \cite{kachuee2019opportunistic}; UALA \cite{han2024uala} | Bayes-optimal reject option; distribution-free prediction intervals; budgeted test-time tool invocation. | Domain-specific 4-tool cascade minimizing external routing/climate/inference API cost on verified multi-modal Indian mandi corridors; audits empirical conformal stability under seasonal non-stationarity. |

Importantly, we make **no claim** of inventing new conformal theory, new thermodynamic spoilage equations, or general-purpose multi-agent theorems. Standard split conformal guarantees require exchangeability, which seasonal agricultural markets violate across monsoon and harvest swings; accordingly, we train strictly on `2024`, update conformal bounds causally as historical dispatches mature, and verify actual empirical coverage empirically on validation and holdout periods.

---

## 3. Data Infrastructure & Official Government Grounding

Every layer of our benchmark is built solely from authentic public Indian government archives, OpenStreetMap routing, and European Centre for Medium-Range Weather Forecasts (ECMWF) ERA5 / numerical weather prediction archives—with zero synthetic data generation and zero CAPTCHA circumvention.

### 3.1 Multi-State Daily AGMARKNET Decade Panel (`2017–2026`) & Live Snapshot
For our primary causal training, calibration, and pre-registered holdout pipeline (`2024–2026`), we streamed `14,443,770` raw official AGMARKNET records across India (`2024`, `2025`, and `January–April 13, 2026`), filtered to our six target states and four perishable crops (`681,258` raw rows), removed `284` corrupt/outlier price records (`0` invalid dates) and `7,003` exact duplicates, leaving `673,971` verified market-day records across `699` yards.

To prevent holdout **survivorship bias**, we never select markets using future trading counts. Instead, candidate markets had to report at least `20` active days during calendar `2024` and `80` cumulative days (`469` eligible yards), from which we selected the top `30` markets per state strictly by `2024` trading days (`28` active eligible yards in Himachal Pradesh). This yields a balanced **`178`-mandi causally selected `2024–2026` panel of `260,043` daily records** (`Gujarat: 45,298`; `Himachal Pradesh: 37,671`; `Maharashtra: 46,380`; `Uttar Pradesh: 80,981`; `Madhya Pradesh: 25,041`; `Karnataka: 24,672`; spanning `Onion: 89,161`, `Tomato: 73,241`, `Potato: 69,296`, and `Apple: 28,345`). Clerk variety labels (`Onion`, `Other`, `FAQ`) were harmonized cleanly (`Standard`; `Deshi` merged with `Desi`) while keeping distinct cultivars (`Red`, `Hybrid`, `Royal Delicious`, `Badshah`, etc.) separate. To test multi-regime structural generality back across GST, COVID-19 lockdowns, and agricultural export curbs (`2017–2023`), we further streamed `28,278,417` raw historical AGMARKNET records (`2017–2023`)—bringing the cumulative audited raw extract to **`42,722,187` transactions (`2017-01-01`..`2026-04-13`)** and expanding the fixed `178`-mandi panel to **`883,406` daily records** (`623,363` across `2017–2023` plus `260,043` across `2024–2026`).

For fine-grained quality validation, we additionally incorporate **`4,427` grade-explicit daily Himachal Pradesh Apple records** (`November 7, 2025–September 1, 2026` across `42` markets, explicitly distinguishing `Grade A`, `Grade B`, `Grade C`, `Medium`, `Grade Range-1`, and `Local`), alongside **`22` live unauthenticated API queries** retrieved on `November 17, 2026` from the official AGMARKNET portal showing `11/22` (`50.0%`) major state benchmark corridors non-reporting across the full prior 7-day window.

### 3.2 District-Validated Geocoding & OSRM Real Highway Network
Geocoding all `220` unique `(State, District, Market)` pairs using geographic name lookup can suffer severe homonym errors (e.g., identically named villages in neighboring states). We enforced strict district (`admin2`) matching plus a `<= 110 km` distance validation guard against verified District Headquarters coordinates (`150` exact market coordinates, `70` district-centroid fallbacks). Querying the public Open Source Routing Machine (OSRM) road engine \cite{luxen2011osrm} over all intra-state pairs between `15 km` and `500 km` yielded **`8,147` directed highway corridors** (`Gujarat: 817`, `Himachal Pradesh: 4,420`, `Karnataka: 682`, `Madhya Pradesh: 750`, `Maharashtra: 689`, `Uttar Pradesh: 789`).

Because Indian APMC wholesale auctions predominantly clear during morning yard sessions, an afternoon dispatch requires realistic travel-to-auction lead times: applying truck speeds (`1.35x` car routing, with additional mountain speed adjustment in Himachal Pradesh plus `4.0 h` loading/auction buffer) assigns arrival lag $\tau \in \{1, 2, 3\}$ days (`1 day: 3,810` corridors `<= 4.5 h`; `2 days: 3,942` corridors `4.5–8.5 h`; `3 days: 395` corridors `> 8.5 h`).

### 3.3 Realized Climate (`ERA5` & `NASA POWER`) vs. Decision-Day Weather Forecasts
To prevent look-ahead weather leakage cleanly, our pipeline strictly separates what the dispatch agent sees on decision morning $t$ from what physically hits the truck during highway transit `[t, t + \tau]`:
* **Physical Transit Truth (`145/145` Grid Cells `2024–2026` + `114` Grid Cells `2017–2023`):** Complete daily ECMWF ERA5 reanalysis \cite{hersbach2020era5} (`temperature_2m_max`, `precipitation_sum`, `relative_humidity_2m_mean`) across all `145` rounded `0.1°` mandi grid cells (`2024-01-01`..`2026-09-05`, `141,955` rows, `0.0%` missing), extended backwards across `2017–2023` using official United States Government NASA POWER `0.5°` agroclimatology daily records \cite{sparks2018nasapower} (`291,384` rows across `114` grid cells, `0.0%` missing).
* **Decision-Day Forecasts (`102/145` Native NWP + Causal Nowcasts):** Archived historical numerical weather prediction (NWP) daily forecasts cover `102/145` cells (`100%` of Gujarat, Karnataka, Madhya Pradesh, and Maharashtra plus `8` Uttar Pradesh locations). When free daily API request limits were reached on the remaining `43` northern cells (and for `2017–2023` historical regimes), we applied a strictly causal (`<= t` lagging and `2024`-only fitted) Ridge nowcaster over overlapping NWP grids (out-of-sample Jan–May 2025 MAE: `1.047°C` max temperature, `0.001 mm` rain, `0.284%` relative humidity). We report main holdout results both across all six states and explicitly inside the **`42,766`-episode four-state subset (`100%` native NWP forecasts)**.

### 3.4 Official Central & State Government Survey Grounding
Rather than relying on arbitrary constant fees or arbitrary spoilage guesses, Table 2 compiles the verified Government of India and State Government parameters embedded directly in our economic evaluator.

| State | Statutory APMC F&V Fee & Seller User-Charge Regime \cite{pib154554apmc} | Assumed Seller Yard Charge | Cold Storages (`Nov 2023`, Units / MT) \cite{pib2023coldstorage} | e-NAM Mandis (`Oct 2024`) \cite{pib2086484enam} |
|:---|:---|---:|---:|---:|
| **Gujarat** | Market fee exempted on F&V; user charges permitted | `0.5%` | `1,014` / `3,974,593 MT` | `144` |
| **Himachal Pradesh** | F&V exempted **except Apple** (`service charge` otherwise) \cite{pib154554apmc, hpeconsurvey2026} | `0.5%` Veg / `1.0%` Apple | `89` / `174,072 MT` | `38` |
| **Karnataka** | Zero market fee on flowers, F&V (Jan 2014 Act); yard user fee only | `0.5%` | `250` / `838,940 MT` | `5` *(state UMP)* |
| **Madhya Pradesh** | Exempted outside notified yards; regulated inside mandi yards | `1.5%` | `315` / `1,364,003 MT` | `139` |
| **Maharashtra** | Direct outside-yard deregulated (Jul 2016 Ord.); yard supervision inside APMC | `1.0%` | `656` / `1,176,499 MT` | `133` |
| **Uttar Pradesh** | Regulated under UP Krishi Utpadan Mandi Adhiniyam | `1.5%` | `2,472` / `15,045,874 MT` | `125` |

Additionally:
* **Crop Market-Level Spoilage Anchors (`PIB PRID 2151371`, MoFPI/NABCONS 2022 \cite{nabcons2022phl}):** Exact national post-harvest loss surveys measure market-level handling & transport loss fractions at **`3.25%` (`Tomato`)**, **`1.96%` (`Onion`)**, **`1.64%` (`Apple`)**, and **`0.86%` (`Potato`)** (with overall farm-plus-market losses summing to `11.62%` on tomato, `9.51%` on apple, `7.27%` on onion, and `5.96%` on potato, consistent with ICAR-CIPHET 2015 \cite{jha2015ciphet}).
* **Hill Terrain Evidence (`GoHP Economic Survey 2025–26` \cite{hpeconsurvey2026}):** Documents `88.86%` small and marginal growers (`0.95 ha` average), `65.01 lakh quintals` traded across HP APMCs up to December 2025, `2025–26` apple production volatility (`647.0` thousand MT vs `502.9` thousand MT in `2024–25`), and **`91.59%` single-lane motorable roads (`39,465 / 43,091 km`)**—grounding our `1.45x` per-km hill trucking factor.
* **Smallholder Income Anchor (`MoSPI NSO NSS Report No. 587` \cite{nss77report587}):** Uses **`30 quintals`** as the representative farmer truckload benchmark (`₹1/qtl = ₹30/truckload`) and **`₹3,798/month`** net crop receipt as household welfare scale.

---

## 4. Problem Formulation & Physical Economic Model

### 4.1 Realized Net Gain Over Local Sale (`ΔNet ₹/qtl`)
On decision morning $t$, a farmer at origin market $i$ holds a verified fresh lot of commodity $c$ and variety $v$ trading locally at $P_{i,t}^{\text{loc}}$. Any candidate destination yard $j$ reachable via OSRM road distance $d_{ij} \in [15, 500]\text{ km}$ (driving duration $h_{ij}$ hours, morning-auction arrival lag $\tau_{ij} \in \{1,2,3\}$ days) produces an intuitive realized net gain per quintal (`₹/qtl`) relative to selling locally (`SELL_LOCAL` $= ₹0$):

$$\Delta\text{Net}(i \to j, t) \;=\; P_{j}^{\text{sale}} \cdot \bigl(1 - s_{ij}\bigr) \;-\; F_{ij} \;-\; \text{Detention}_j \;-\; P_{i,t}^{\text{loc}}$$

Here:
* **Road Freight & Statutory Mandi Charges (`F_ij`):**
  $$F_{ij} = 35 + 0.45 \cdot m_{\text{HP}} \cdot d_{ij} + \mathbb{I}[\text{cross-district}]\cdot \gamma_{s,c} \cdot P_{i,t}^{\text{loc}}$$
  where $₹35\text{/qtl}$ covers loading/unloading, $₹0.45\text{/qtl/km}$ reflects Indian flatbed agricultural trucking ($m_{\text{HP}} = 1.45$ on single-lane Himachal hill highways, $1.0$ elsewhere), and $\gamma_{s,c} \in \{0.5\%, 1.0\%, 1.5\%\}$ applies the verified state-specific seller/user fee rate from Table 2.
* **Climate-Sensitive $Q_{10}$ Perishability (`s_ij`):** Anchored to each crop's official NABCONS (2022) market-level base fraction $s_{0,c}$ at $20^\circ\text{C}$ \cite{nabcons2022phl}, ambient biological decay doubles every $+10^\circ\text{C}$ above $20^\circ\text{C}$ (`Q10 = 2.0`), increases up to $+25\%$ under extreme relative humidity (`> 70%`), and adds `+2.0%` transit moisture damage if realized corridor rainfall exceeds `35 mm/day` (`capped at 55%`):
  $$s_{ij}(w) = \min\Bigl(0.55,\;\; s_{0,c} \cdot \frac{h_{ij} + 24w}{24} \cdot 2^{(T_{\max}-20)/10} \cdot \Bigl[1 + 0.25\max\Bigl(0, \frac{\text{RH}-70}{30}\Bigr)\Bigr] + 0.02\,\mathbb{I}[\text{Rain} \ge 35\text{ mm}]\Bigr)$$
  If heavy rain occurs (`>= 35 mm/day`), moisture grading pulls realized destination sale quality halfway from modal toward minimum yard price ($0.5\,P^{\text{modal}} + 0.5\,P^{\text{min}}$).
* **Realized Destination Auction Lookup (`P_sale` & Trap Penalty):**
  1. If the exact `(Commodity, Variety)` trades at destination $j$ on arrival day $t+\tau$ (`wait w = 0`) or within the next two mornings (`w = 1, 2`, adding $₹25\text{/qtl/day}$ detention and extra $24w$ hours of spoilage), the lot clears at that day's exact auction price. (`w > 0` flags a delay trap).
  2. If the exact variety never trades across `[t+tau, t+tau+2]`, a farmer physically already at the yard liquidates either at any other variety's `Min_Price` minus a `10%` distress discount, or—if the crop/yard is completely closed for three consecutive days—incurs `-1.5x` diversion freight back to the home area plus local ambient spoilage.

### 4.2 Temporal Firewall & Pre-Holdout Calibration Lock
To make zero-leakage guarantees airtight, time was strictly partitioned and frozen prior to touching holdout data:
* **`Train_2024` (`Jan 1–Dec 31, 2024`, `701,932` candidate pairs):** Used exclusively to fit our `CausalArrivalForecaster` (`HistGradientBoostingRegressor` predicting arrival return $(P_{\text{arr}} - P_{\text{ref}}) / P_{\text{ref}}$ from `17` purely causal lag/volatility/openness/calendar features; `Jan–Sep` fit, `Oct–Dec` seed conformal residuals).
* **`Val_2025H1` (`Jan 1–May 31, 2025`, `280,697` candidate pairs / `42,794` active episodes):** Used exclusively to check causal `80%` conformal LCB coverage (`78.85%` empirical coverage) and freeze one scalar decision margin **`safety_margin_inr = ₹50.0/qtl`** over `[50, 100, 150, 200, 250]` (maximizing validation mean $\Delta\text{Net}$ at `₹351.36/qtl` with `9.68%` phantom loss rate).
* **`Holdout_2025_2026` (`Jun 1, 2025–Apr 8, 2026`, `81,048` total episodes, `69,526` shortlisted active episodes / `468,816` candidates):** Never touched until after confirmatory hypotheses `H1`–`H4` were committed to version control. Note that causal conformal residuals update strictly online as historical arrival dates mature (`arrival_date <= decision_date t`).

---

## 5. `MandiGuard`: The 4-Step Sequential Verification Agent

On any morning $t$ where at least one corridor clears a coarse Step-0 screen spread (`screen_dest_price - local_price > ₹100/qtl` over the past 7-day board, capped at `K = 5` top-spread candidates), `MandiGuard` avoids blindly calling road, climate, and predictive services on every option. Instead, it processes candidates ranked by headline spread through an ascending-cost four-tool cascade:

1. **Tool `T1` — Market Vitality & Variety Verification (`1` call):** Checks whether the exact variety traded within the last `3` days (`dest_age_days <= 3`), whether recent 14-day yard reporting reliability meets `>= 50%`, and whether the historical arrival weekday openness rate (`t + tau`) clears `>= 35%`. **Hopeless or stale/closed destinations prune immediately in 1 call.**
2. **Tool `T2` — OSRM Highway Freight & Statutory APMC Gate (`+1` call):** Computes actual OSRM truck distance, mountain adjustment, and state-specific yard charges ($F_{ij}$); immediately prunes candidates where fresh spread fails to cover transport and mandi friction (`P_fresh - P_loc - F_ij <= 0`).
3. **Tool `T3` — Decision-Day Weather & Spoilage Risk Gate (`+1` call):** Queries day-$t$ causal temperature, humidity, and rainfall forecasts along the origin–destination corridor, evaluates biological $Q_{10}$ perishability $s_{ij}$ plus rain-downgrade risk, and prunes if post-weather net gain drops below zero.
4. **Tool `T4` — Arrival Return & Conformal `80%` LCB Scorer (`+1` call):** Scores the frozen `2024` arrival-return forecaster and subtracts the strictly causal commodity-level `80th`-percentile downside shortfall quantile $\hat{q}_{0.80}$ (`p_arr_lcb = p_fresh * (1 + lcb_ret)`), yielding conservative lower-bound net utility:
   $$\widehat{\text{LCB\_Net}}_{ij,t} = P^{\text{LCB}}_{\text{arr}} \cdot (1 - \hat{s}_{ij}) - \widehat{\text{RainPen}}_{ij} - \hat{F}_{ij} - P_{i,t}^{\text{loc}}$$

After scanning surviving candidates (or stopping once an optional tool-call budget expires), `MandiGuard` **dispatches** to $j^* = \arg\max_j \widehat{\text{LCB\_Net}}_{ij,t}$ only if $\widehat{\text{LCB\_Net}}_{ij^*,t} > ₹50\text{/qtl}$; otherwise it explicitly emits **`REFUSE_PHANTOM_SPREAD`** and sells locally (`ΔNet = ₹0`).

---

## 6. Experimental Protocol & Matched Comparators

We evaluate `MandiGuard` against seven clean, matched baselines around **four minimal, farmer-centric decision metrics**—(1) **`Mean Net Gain`** (`₹/qtl` and `30-qtl Truck Gain ₹`), (2) **`Loss-Trip Rate`** (`%` of dispatched trucks losing money), (3) **`Worst-10% Loss`** ($\text{CVaR}_{10\%}$ `₹/qtl`), and (4) **`Live API Calls / Query`**—alongside dispatch and physical Closed/Variety Trap rates (`%`):
* **`B0_SellLocal`:** Never dispatches (`ΔNet = ₹0`, `0` calls).
* **`B1_NaiveScreenGreedy`:** Models portal chasing—picks top `<= 7d` modal screen spread minus $1.2\times$ straight-line Euclidean freight `> ₹100/qtl` (`0` external verification calls).
* **`B2_FreshRoadGreedy`:** Strong simple heuristic requiring today's exact variety (`age = 0`) + real OSRM freight + statutory fees `> ₹100/qtl` (no weekday openness guard, no weather spoilage, no ML/conformal LCB).
* **`B3_MLPointDispatch`:** Uses `2024` ML point return $\hat{P}_{50}$ + OSRM road freight `> ₹50/qtl` margin, *omitting* `T1`, `T3`, and `T4` LCB—directly testing uncalibrated ML recommendations \cite{biradar2026agrimarket, manimegalai2026mandicast}.
* **`B4_UpfrontAllTools`:** Runs all four tools `T1`–`T4` upfront on every top-`5` candidate (`4 * n_cands` calls, zero sequential pruning); under tight budgets $B$, finishes only $\lfloor B/4 \rfloor$ candidates.
* **`B5_MultiAgentCoordinator`:** Three-role coordinator (`ScoutAgent -> LogisticsWeatherAgent -> RiskGateAgent`) passing quantized `₹150/qtl` tiered margin buckets over an inter-agent message bus.
* **`B6_HeuristicBucketRouter`:** Verbal rule router (`age <= 1`, `open_prob >= 0.60`, rough `50 + 0.55*km` road rule, flat `12%` haircut if `tmax >= 35°C` or `rain >= 25 mm`, `₹200/qtl` threshold).

All four confirmatory hypotheses (`H1`–`H4`) are scored on the `69,526` shortlisted holdout episodes via paired **Two-Way Origin-Mandi (`174`) $\times$ 2-Week-Block (`23`) Cluster Bootstrap** ($R = 5{,}000$) with Phipson–Smyth $p$-values \cite{phipson2010permutation} and Holm–Bonferroni correction at family-wise $\alpha = 0.05$ \cite{holm1979simple}.

---

## 7. Results & Deep Empirical Analysis

### 7.1 Model-Free Anatomy of Phantom Arbitrage (`Exp 1`)
Across `63,040` naive dispatches triggered by `B1` during June 2025–April 2026, headline screen spreads look deceptively large at **`₹1,330.49/qtl`**, yet average realized net gain shrinks by **71%** to `₹386.02/qtl`. Figure 1 decomposes where those rupee gains vanish:
* Highway freight and statutory mandi charges remove `₹160.81/qtl` and climate transit spoilage removes `₹68.76/qtl`.
* Far larger is the **`₹714.90/qtl` average erosion** from execution traps and price reversion: **`58.94%`** of naive dispatches encounter a closed yard or missing-variety delay (`46.69%` had zero exact-variety trade across three arrival days!), leaving **`40.46%` of dispatched trucks losing money**.
* Losses are acutely concentrated in perishable Onion (**`48.69%` phantom loss rate**, averaging just `+₹53.61/qtl` net) and Madhya Pradesh (**`51.57%` phantom losses**, `+₹95.82/qtl`) alongside Himachal Pradesh (`46.82%` phantom losses). Across longer `250–500 km` highway corridors, execution traps surge to **`62.99%`**.

![Anatomy of Phantom Arbitrage](../figures/fig1_phantom_arbitrage_anatomy.png)

### 7.2 Main Benchmark & Confirmatory Tests (`H1`–`H4`, `Exp 2`, `Exp 2b`)
Tables 3 and 4 report the pre-registered confirmatory tests and full policy comparison across `69,526` shortlisted holdout episodes (with empirical causal conformal `80%` LCB coverage holding steadily at **`79.07%`** across holdout arrivals).

| Hypothesis | Estimand (`N = 69,526`, `174` Mandis $\times$ `23` Blocks) | Estimate | 95% Bootstrap CI | $p_{\text{raw}}$ | $p_{\text{Holm}}$ | Outcome |
|:---|:---|---:|---:|---:|---:|:---|
| **`H1`** | `MandiGuard` minus `B1_NaiveScreen` Mean $\Delta\text{Net}$ (`₹/qtl`) | **`+102.78`** | `[+48.66, +153.45]` | `0.0006` | **`0.0012`** | **`SUPPORTED`** |
| **`H2`** | `MandiGuard` minus `B2_FreshRoad` Mean $\Delta\text{Net}$ (`₹/qtl`) | `+6.13` | `[-17.02, +25.02]` | `0.2699` | `0.2699` | **`NOT_SUPPORTED`** |
| **`H3`** | `MandiGuard` minus `B3_MLPoint` Episode Phantom Loss (`prob`) | **`-0.3729`** | `[-0.4019, -0.3424]` | `0.0002` | **`0.0008`** | **`SUPPORTED`** |
| **`H4`** | `MandiGuard` Calls minus `0.75 × B4_Upfront` Calls | **`-3.0548`** | `[-3.4408, -2.6906]` | `0.0002` | **`0.0008`** | **`SUPPORTED`** |

| Policy Comparator | Dispatch Rate (`%`) | Mean Net Gain (`₹/qtl`) | 30-qtl Truck Gain (`₹`) | Loss-Trip Rate (`%`) | Closed / Variety Trap (`%`) | Worst-10% Loss (`₹/qtl`) | Live API Calls / Query |
|:---|---:|---:|---:|---:|---:|---:|---:|
| **`B0_SellLocal`** | `0.00%` | `₹0.00` | `₹0.0` | `0.00%` | `0.00%` | `₹0.00` | `0.00` |
| **`B1_NaiveScreenGreedy`** | `90.67%` | `₹350.01` | `₹10,500.2` | `40.46%` | `58.94%` | `-₹1,062.66` | `0.00` |
| **`B2_FreshRoadGreedy`** | `62.11%` | `₹446.66` | `₹13,399.7` | `18.11%` | `24.32%` | `-₹436.67` | `7.87` |
| **`B3_MLPointDispatch`** | `93.05%` | `₹330.85` | `₹9,925.6` | `45.28%` | `65.65%` | `-₹1,097.80` | `7.87` |
| **`B6_HeuristicBucketRouter`** | `43.36%` | `₹431.94` | `₹12,958.3` | `11.88%` | `21.59%` | `-₹42.42` | `11.80` |
| **`B5_MultiAgentCoordinator`** | `41.59%` | `₹437.39` | `₹13,121.7` | `9.38%` | `16.57%` | `-₹31.77` | `8.76` |
| **`B4_UpfrontAllTools`** | `48.66%` | `₹452.79` | `₹13,583.6` | `9.97%` | `16.17%` | `-₹37.89` | `15.74` |
| **`MandiGuard` (Ours)** | **`48.66%`** | **`₹452.79`** | **`₹13,583.6`** | **`9.97%`** | **`16.17%`** | **`-₹37.89`** | **`8.75`** |

Figure 2 visualizes three pivotal scientific lessons from this main benchmark:
1. **Unconstrained ML Point Dispatch Fails Badly (`B3` vs `MandiGuard`):** Predicting future mandi prices with gradient boosting (`B3`) without market vitality gates or uncertainty intervals produces `45.28%` phantom loss dispatches and `-₹1,097.80/qtl` tail losses—worse than ignoring ML altogether (`B1`). Adding `MandiGuard`'s cascade lifts net gain by `+₹121.94/qtl` and eliminates `37.29 pp` of episode-level losses (`H3`).
2. **Honest Risk–Return Tradeoff Against `B2_FreshRoadGreedy` (`H2`):** While `MandiGuard` earns slightly higher mean net return overall (`+₹6.13/qtl`), the wide two-way cluster CI rejects universal mean superiority ($p_{\text{Holm}} = 0.2699$). Instead, `MandiGuard` protects farmers from ruin: it nearly **halves dispatched phantom losses** (`9.97%` vs `18.11%`), cuts execution traps (`16.17%` vs `24.32%`), and shrinks worst-10% tail risk **11.5x** (`-₹37.89` vs `-₹436.67/qtl`—protecting a 30-qtl truckload from `-₹13,100.1` vs `-₹1,136.7` worst-10% losses). Notably, within the **`42,766`-episode four-state subset carrying `100%` native NWP weather grids** (`Gujarat`, `Karnataka`, `Madhya Pradesh`, `Maharashtra`), `MandiGuard` widens its lead over `B2` to **`+₹31.82/qtl`** (`₹485.18` vs `₹453.37/qtl`). Across crops, `MandiGuard` raises `Onion` mean gain from `₹46.50/qtl` (`B1`) to `₹163.41/qtl` (`+₹116.91/qtl`) and `Potato` from `₹203.75` to `₹258.38/qtl`, while trimming extreme lottery exposure in volatile `Tomato` (`B1 ₹547.64` with `32.38%` loss episodes vs `MandiGuard ₹522.48` beating `B2 ₹484.64` with only `5.09%` loss episodes).
3. **Single Unified Agent Beats Coarse Multi-Agent Communication (`B5`) and Verbal Buckets (`B6`):** Quantizing continuous lower bounds into `₹150` inter-agent bus tiers (`B5`) drops mean profit by `-₹15.40/qtl` (`₹437.39` vs `₹452.79/qtl`), while coarse heuristic rules (`B6`) trail by `-₹20.85/qtl` while costing `34.9%` more tool queries (`11.80` vs `8.75`).

![Main Policy Comparison](../figures/fig2_main_policy_comparison.png)

### 7.3 Tool Ablations & Extreme Heat/Rain Regimes (`Exp 4` & `Exp 7`)
Table 5 and Figure 3 isolate each verification step's causal contribution overall and across the **`21,656` extreme heat (`>= 35°C`) or heavy monsoon (`>= 35 mm/day`) episodes**.

| Variant | Overall Mean $\Delta\text{Net}$ (`₹/qtl`) | Overall Phantom Loss (`%`) | Overall Trap Rate (`%`) | Heat/Rain Mean $\Delta\text{Net}$ (`₹/qtl`) | Heat/Rain Phantom Loss (`%`) | Heat/Rain $\text{CVaR}_{10\%}$ (`₹/qtl`) | Avg Tool Calls |
|:---|---:|---:|---:|---:|---:|---:|---:|
| **`Full MandiGuard`** | `₹452.79` | **`9.97%`** | **`16.17%`** | `₹470.07` | **`10.10%`** | **`-₹57.11`** | `8.75` |
| **`No_T1_Vitality`** | `₹318.74` | `42.80%` | `67.16%` | `₹367.77` | `38.74%` | `-₹1,003.01` | `11.03` |
| **`No_T2_OSRM_to_Euclid`** | `₹452.35` | `10.25%` | `16.22%` | `₹468.22` | `10.59%` | `-₹58.54` | `7.05` |
| **`No_T3_Weather`** | `₹455.25` | `10.61%` | `16.18%` | `₹474.31` | `11.39%` | `-₹67.49` | `7.23` |
| **`No_T4_ConformalLCB`** | `₹448.74` | `16.89%` | `16.13%` | `₹465.50` | `15.73%` | `-₹458.74` | `7.23` |

Two stark insights emerge honestly:
* **Market Vitality & Variety (`T1`) and Conformal Risk (`T4`) Do the Heavy Lifting:** Removing `T1` collapses mean net gain by `-₹134.05/qtl`, explodes execution traps four-fold (`67.16%`), and wastes `26%` more tool calls inspecting dead corridors (`11.03` vs `8.75`). In fact, `T1` alone eliminates `30.82%` of all holdout episodes (`25.48%` stale/missing-variety + `5.34%` low-openness/weekday risk, at `3.04–3.64` calls per episode). Meanwhile, dropping `T4` conformal bounds spikes dispatched phantom losses from `9.97% -> 16.89%` and magnifies tail ruin **10.5x** (`-₹37.89 -> -₹397.19/qtl`).
* **Transparent Reporting of `T2` and `T3` Subtle Effects:** Because corridors are already distance-bounded within `15–500 km`, OSRM highway lookup (`T2`) adds `+₹0.44/qtl` overall (`+₹1.85/qtl` under heat/rain). Similarly, pruning weather spoilage (`T3`) protects perishable quality under heatwaves and downpours—lowering heat/rain phantom losses by `-1.29 pp` (`11.39% -> 10.10%`) and worst-10% tail risk by `+₹10.38/qtl` (`-₹67.49 -> -₹57.11`)—while conservatively sacrificing `₹2.46/qtl` in average holdout profit (`₹455.25 -> ₹452.79`) when spot price jumps absorb spoilage costs.

![Tool Ablation and Heat/Rain Regimes](../figures/fig3_tool_ablation_and_monsoon_heat.png)

### 7.4 Budgeted Verification Pareto Frontier (`Exp 5`)
As Figure 4 demonstrates, ordering cheap gates before expensive checks creates decisive superiority whenever API or latency budgets are constrained. Under a strict budget of **`B = 6` tool calls per episode**, `MandiGuard` (`5.05` avg calls) achieves **`₹403.85/qtl`** (`+₹12,115.6` per truckload), beating `B4_UpfrontAllTools` (`₹299.31/qtl` at `5.75` calls) by **`+₹104.54/qtl` while making fewer queries**. Without any budget limit (`B = 20`), `MandiGuard` reaches exact oracle parity (`₹452.79/qtl`) using `44.4%` fewer total calls (`8.75` vs `15.74`, confirming `H4`).

![Tool Budget Pareto Frontier](../figures/fig4_tool_budget_pareto.png)

### 7.5 Grade-Explicit Himachal Apple Harvest (`Exp 3`), State Transfer (`Exp 9`), & Sensitivity (`Exp 6`)
* **Grade-Explicit HP Apple Validation (`2026-06-01`..`2026-08-27`, `1,537` Shortlisted Lots):** As shown in Figure 5, naive chasing (`B1`, `100%` dispatch) triggers **`94.14%` closed/grade-mismatch traps** and catastrophic tail losses (`CVaR_10% = -₹8,487.24/qtl`), turning `Grade B` dispatches negative on average (`-₹427.54/qtl`). `MandiGuard` cuts traps seven-fold to **`13.24%`**, eliminates `82x` tail risk (`-₹102.76/qtl`), cuts calls `41%` vs `B2` (`5.41` vs `9.17`), and turns `Grade B` into **`+₹833.70/qtl` profit**. **Crucial nuance reported candidly:** overall unconditional mean gain on HP Apple is lower under `MandiGuard` (`₹605.06/qtl` at `18.67%` dispatch) than aggressive `B2` (`₹1,150.83/qtl` at `33.64%` dispatch) and `B1` (`₹841.58/qtl`), because the `2024`-trained forecaster lacked `Grade A`/`Range-1` labels and applied wide `2024`-derived conformal penalties to `2026` high-value grade tiers (`5.39%` dispatch on `Grade A`).
* **Zero-Shot Leave-One-State-Out Transfer (`Exp 9`):** Training strictly on five states in `2024` and predicting unseen sixth-state holdout routes outperforms naive `B1` across **every single state** (`+₹424.19/qtl` in HP, `+₹122.79/qtl` in MP, `+₹69.51/qtl` in KA, `+₹61.54/qtl` in UP, `+₹55.39/qtl` in MH, `+₹11.50/qtl` in GJ) while holding actual arrival-price-drop rates to `3.34%–9.72%` (vs `45.29%–55.66%` under `B1`).
* **Physical Sensitivity & Statutory APMC Fee Impact (`Exp 6`, Figure 6):** Across the $3 \times 3$ freight (`0.75x, 1.0x, 1.25x`) $\times$ spoilage (`0.5x, 1.0x, 1.5x`) parameter grid, `MandiGuard` outperforms `B1` across all `9/9` regimes by **`+₹82.62` to `+₹121.42/qtl`**, and outperforms `B2` across all realistic and adverse spoilage regimes (`+₹5.27` to `+₹14.50/qtl`), trailing `B2` slightly (`-₹0.02` to `-₹1.52/qtl`) only when perishability is cut in half (`0.5x`). Swapping uniform `1.5%` mandi fees for verified GoI statutory APMC schedules unlocks `+₹7.12/qtl` in previously hidden net spatial margin (`₹452.79` vs `₹445.67/qtl`).

![HP Apple Grade Traps](../figures/fig5_hp_apple_grade_traps.png)

![Sensitivity Grid](../figures/fig6_sensitivity_and_govt_fees.png)

### 7.6 Nearly 10-Year Macro Regimes (`2017–2026`, `661,192` Episodes) & Modern AI / ACI Showdown (`Exp 10`, `10b`, `11`)
To test whether `MandiGuard`'s gains hold beyond recent `2024–2026` harvests, we constructed a causal nearly ten-year panel (`2017-01-01`..`2026-04-13`) merging historical AGMARKNET archives with NASA POWER agroclimatology \cite{sparks2018nasapower} and evaluated matched comparators across **`661,192` episodes spanning six macro-economic and weather regimes** (Table 6 and Figure 7A).

| Macro Regime (`Matched N`) | Naive `B1` Mean (`₹/qtl`) / Loss Rate | `B2` Fresh+Road Mean (`₹/qtl`) / Loss Rate | `MandiGuard` (`Expanding`) Mean (`₹/qtl`) | `MandiGuard` Loss Rate | `MandiGuard` Worst-10% (`vs B1`) |
|:---|---:|---:|---:|---:|---:|
| **`2017H2 GST Transition`** (`31,997`) | `₹393.39` / `39.18%` | `₹430.35` / `19.75%` | `₹425.04` (`₹12,751.2`) | **`11.67%`** | **`-₹31.62`** (`vs -₹910.99`) |
| **`2018–19 Pre-COVID`** (`145,972`) | `₹254.77` / `42.36%` | `₹329.53` / `17.69%` | **`₹345.17`** (`₹10,355.1`) | **`8.78%`** | **`-₹20.93`** (`vs -₹786.52`) |
| **`2020–21 COVID Shock`** (`139,032`) | `₹279.96` / `42.24%` | `₹355.24` / `18.63%` | `₹340.83` (`₹10,224.8`) | **`10.59%`** | **`-₹23.42`** (`vs -₹851.55`) |
| **`2022–23 Infl. & Export Curb`** (`178,197`) | `₹278.41` / `42.22%` | `₹376.00` / `18.79%` | **`₹394.37`** (`₹11,831.0`) | **`10.50%`** | **`-₹33.29`** (`vs -₹1,057.30`) |
| **`2024 El-Niño Heatwave`** (`96,468`) | `₹222.77` / `44.29%` | `₹381.99` / `18.94%` | **`₹387.91`** (`₹11,637.4`) | **`12.03%`** | **`-₹36.82`** (`vs -₹1,289.28`) |
| **`2025–26 Holdout Benchmark`** (`69,526`) | `₹350.01` / `40.46%` | `₹446.66` / `18.11%` | **`₹452.79`** (`₹13,583.6`) | **`9.97%`** | **`-₹37.89`** (`vs -₹1,062.66`) |

Across **all six regimes**, naive screen chasing destroys capital on `39.18%–44.29%` of trips with worst-10% shocks reaching `-₹1,289.28/qtl` during the **`2024 El-Niño Heatwave`**, whereas causally expanding `MandiGuard` holds `Loss-Trip Rate` stably within **`8.78%–12.03%`** and peaks at **`+₹165.14/qtl` above `B1`** during `2024`. Interestingly, scaling training data backwards on `Holdout_2025_2026` (`Exp 10b`) from **`1-Yr` (`2024`, `701,932` rows: `₹452.79/qtl`) -> `3-Yr` (`2022–2024`, `1,668,451` rows: `₹454.74/qtl`) -> `8-Yr` (`2017–2024`, `3,437,098` rows: `₹454.94/qtl`)** yields only `+₹2.15/qtl`, demonstrating that fresh prior-year calibration plus conformal bounds contributes far more than brute-force multi-year volume under evolving mandi regimes.

In our **Modern AI & Adaptive Conformal Showdown (`Exp 11`, Figure 7B)** plugging alternative predictors into the identical `T1 -> T2 -> T3 -> T4` funnel (`8.75` calls on holdout, `5.41` on HP Apple):
* **`Direct_Quantile_GBDT_Q20`** achieves top 6-state holdout gain (**`₹459.02/qtl`**, `9.40%` LTR, `-₹32.28/qtl` `CVaR_10%`), edging `ExtraTrees_Conformal` (`₹453.30/qtl`), `MandiGuard_Standard` (`₹452.79/qtl`), `Deep_MLP_Conformal` (`₹435.38/qtl`), and `Contextual_UCB_Bandit` (`₹406.47/qtl`).
* Under severe grade shift (`HP_Apple_Grade_2026`, `N = 1,537`), **`Deep_MLP_Conformal`** leads mean gain (`₹615.34/qtl`, `18.15%` LTR), closely followed by `Contextual_UCB_Bandit` (`₹615.04/qtl`), while **Adaptive Conformal Inference (`MandiGuard_ACI`) \cite{gibbs2021adaptive}** automatically tightens HP Apple's $\alpha$ from `0.200 -> 0.164` (`Tomato` on 6-state adapts to `0.038`)—cutting HP Apple worst-10% tail losses by **`27.6%`** (`-₹102.76 -> -₹74.42/qtl`).

![10-Year Regime Evolution and Modern AI Showdown](../figures/fig7_decade_2017_2026_evolution.png)

### 7.7 `MandiGuard-ZeroCloud` Edge-AI, FPO Truck Pooling, Split-Lot Portfolio & Biological Spoilage Clock (`Exp 12`, `13`, `13b`)
Because physical highways rarely change day-to-day (`T2`) and trained tabular trees evaluate in fractions of a millisecond on commodity hardware (`T4`), **offloading static routing tables and ML inference to local district servers or edge gateways (`MandiGuard-ZeroCloud`)** transforms operational economics (Table 7 and Figure 8):

| Agent / Logistics Variant (`N = 69,526`, API `₹0.05/call`) | Mean Net Gain (`₹/qtl`) | 30-qtl Truck Gain (`₹`) | Loss-Trip Rate (`%`) | Worst-10% Loss (`₹/qtl`) | Live API Calls / Query | API Spend / `10k` Queries |
|:---|---:|---:|---:|---:|---:|---:|
| **`B4_UpfrontAllTools`** | `₹452.79` | `₹13,583.6` | `9.97%` | `-₹37.89` | `15.74` | `₹7,868` |
| **`MandiGuard_Standard`** (`live T1..T4`) | `₹452.79` | `₹13,583.6` | `9.97%` | `-₹37.89` | `8.75` | `₹4,374` (`-44.4%`) |
| **`MandiGuard_ZeroCloud_Full`** (`cached T2 + CPU T4`) | **`₹455.33`** | **`₹13,659.8`** | **`9.89%`** | `-₹37.83` | **`5.53`** | **`₹2,764`** (`-64.9%`) |
| **`MandiGuard_ZeroCloud_Satisficing`** (`Val >= ₹250`) | `₹440.48` | `₹13,214.5` | `10.30%` | `-₹38.97` | **`3.84`** | **`₹1,922`** (`-75.6%`) |
| **`Cooperative FPO 90-qtl Shared Truck`** (`0.70x` freight) | **`₹477.28`** | **`₹14,318.5`** *(30-qtl share)* | `9.51%` | `-₹37.44` | `8.93` | — |
| **`Top-2 Split-Lot Portfolio`** (`50/50` LCB split) | `₹394.82` | `₹11,844.6` | **`8.09%`** (`9.85%` traps) | **`-₹26.40`** | `8.75` | — |

Three deployment findings stand out for real Indian agriculture:
1. **`ZeroCloud` + Val-Frozen Satisficing (`Exp 12`):** Offloading `T2 + T4` (`ZeroCloud_Full`) does not merely reduce API bills **`64.9%`** (`₹2,764` vs `₹7,868` per `10,000` queries)—because locally cached `T2` highway freight lets the edge agent pre-rank Step-0 candidates by freight-adjusted spread before keeping the top-5 shortlist (surfacing profitable nearby yards ahead of distant high-freight traps), mean net profit actually *rises* to **`₹455.33/qtl`** (`9.89%` LTR). Adding a validation-calibrated **satisficing early-exit** (`>= ₹250/qtl`, halting exploration once a surviving corridor beats `₹250/qtl`) slashes API demand further to **`3.84` live calls/query (`₹1,922` per `10k` queries = `-75.6%` API cost** at `0.075 ms/query` CPU), retaining `97.3%` of standard utility (`₹440.48/qtl`).
2. **Cooperative FPO Truck Pooling & Split-Lot Diversification (`Exp 13`):** While a marginal `10-qtl` smallholder facing `1.60x` per-qtl transport earns `₹409.53/qtl` under `MandiGuard` (still beating marginal `B1 ₹288.43`), **pooling three `30-qtl` lots via an FPO `90-qtl` shared truck (`0.70x` freight)** raises profit to **`₹477.28/qtl`** (`+₹24.49/qtl` over solo `30-qtl`, **`+₹67.75/qtl`** over marginal `10-qtl`). Conversely, risk-averse FPOs can split lots `50/50` across top-2 LCB-cleared markets, cutting closed-yard trap exposure **`39%` relative (`16.17% -> 9.85%`)** and loss trips to `8.09%`.
3. **Biological Spoilage Clock & `<= 160`-Char SMS Actionability (`Exp 13b`):** Translating $Q_{10}$ decay into maximum safe transit hours before reaching `15%` shrinkage highlights acute heat vulnerability—dropping **`Tomato`** safe haul windows from **`110.8 h` (`20°C` winter)** to **`48.2 h` (`32°C` spring/monsoon)** and just **`24.1 h` (`42°C` summer)** (versus `183.7 h / 79.9 h / 40.0 h` for `Onion` and `418.6 h / 182.2 h / 91.1 h` for `Potato`). Paired directly with actual holdout logs, `MandiGuard` emits concise SMS advisories under `160` characters—for example: *`[MandiGuard DISPATCH] MH Onion: Amrawati->Kamthi (170km/3.3h). LCB +Rs154, Real +Rs268/qtl!`* and *`[MandiGuard RAIN STOP] KA Tomato at Udupi: SKIP Chikkamagalo. Rain 123mm -> spoil risk. Sell local!`*

![ZeroCloud Edge-AI, FPO Pooling and Spoilage Clock](../figures/fig8_zerocloud_fpo_and_modern_ai.png)

---

## 8. Limitations & Practical Deployment Guidance

We highlight four clear boundary conditions for future researchers and state agricultural extension engineers:
1. **Structural Spoilage vs. Consignment Receipts:** Because AGMARKNET publishes market prices rather than truck-level weighment decay logs, transit perishability rests on $Q_{10}$ thermodynamics anchored to official MoFPI NABCONS (2022) benchmarks \cite{nabcons2022phl} rather than observed consignment receipts; sensitivity checks across `[0.5x, 1.5x]` decay confirm qualitative robustness.
2. **Institutional Unobservables:** Local *arhtiya* credit linkages, morning arrival congestion queues, highway tolls, and intra-day distress bargaining are absent from daily portals and remain unmodeled.
3. **Grade-Specific Training Under Shift:** As shown in `Exp 3`, transferring a `2024` generic-variety model directly onto scarce `2026` `Grade A` auctions leads conformal bounds to over-abstain. Deploying `MandiGuard` into grade-explicit portals requires periodic grade-stratified recalibration rather than pooling premium and medium lots.
4. **Conformal Non-Exchangeability:** While causal rolling conformal updates maintained `78.85%` validation and `79.07%` holdout empirical coverage close to `80%`, finite-sample guarantees remain empirical under monsoon and festival price shocks \cite{angelopoulos2023conformal}.

---

## 9. Conclusion

Chasing the highest headline price on digital wholesale dashboards frequently misleads Indian horticultural farmers into closed yards, unmatched variety auctions, mountain freight, and heat-driven perishability—losing money on `40.46%` of naive dispatches across `69,526` real holdout opportunities and on `39.18%–44.29%` across nearly ten years (`2017–2026`, `661,192` episodes). By replacing naive price-board chasing and unconstrained point-ML predictors with an explicit refusal action and a frugal `T1 -> T2 -> T3 -> T4` sequential verification cascade anchored to official Government of India APMC, NABCONS spoilage, highway, and climate records, `MandiGuard` boosts farmer net gains over naive portals by `+₹102.78/qtl` (`+₹3,083.5` per 30-quintal smallholder load, or `+₹165.14/qtl` during the `2024 El-Niño Heatwave`), cuts phantom losses four-fold (`9.97%` vs `40.46%` and `45.28%` under unconstrained ML), eliminates `11.5x` worst-case tail risk compared with fresh-price OSRM heuristics, cuts live external API costs up to `75.6%` (`3.84` calls/query) under edge-resident `ZeroCloud` deployment, and unlocks `₹477.28/qtl` through cooperative FPO `90-qtl` truck pooling.
