> **Archival Note (Historical Stage-I/II Literature Matrix):** Preserved for provenance (`R8`). For the active verified 15-work overlap table and Revision v5 bibliography, see `final/NOVELTY_V2.md`, `paper/references.bib`, and `paper/manuscript.md`.

# Verified Literature Matrix — `MandiGuard`

**Project:** *Phantom Spatial Arbitrage in Indian Mandis — Stage I (`MandiGuard`) & Stage II (`MandiGuard-CRC`)*  
**Scope of Literature Audit:** 20 verified primary-source citations (14 Stage-I pillars + 6 Stage-II mechanistic/uncertainty/selective-label/market-integration pillars) across five foundational streams, plus an explicit comparison against 8 closest prior academic and applied Indian mandi forecasting, imputation, routing, and market-selection works.  
**Verification Standard:** Every author list, title, publication year, venue, volume/issue/pages, and DOI/URL below was verified directly against primary bibliographic records via web search on November 17–18, 2026.

---

## 1. Quick-Scan Matrix of the 20 Core Primary Citations

| # | Pillar | Citation | Venue & Year | Core Contribution | Remaining Gap Addressed by `MandiGuard` (Stage I & Stage II) |
|:-:|:---|:---|:---|:---|:---|
| 1 | Spatial Arbitrage & Market Integration | **Jensen (2007)** | *QJE*, 122(3):879–924 | Mobile phones cut spatial price dispersion & waste in Kerala fisheries via real-time arbitrage | Assumes low-friction coastal routing & uniform fish quality; does not model inland road topology, yard closures, variety mismatch, or heat decay |
| 2 | Spatial Arbitrage & Market Integration | **Sekhar (2012)** | *Food Policy*, 37(3):309–322 | Econometric cointegration tests across Indian crops show structural/inter-state market friction | Aggregate long-run cointegration tests cannot guide daily dispatch or quantify decision-time execution failures |
| 3 | Spatial Arbitrage & Market Integration | **Chatterjee & Kapur (2016/2017)** | *India Policy Forum*, 13(1):185–229 | Documents substantial persistent inter-mandi spatial price dispersion across India despite rising connectivity | Identifies the spatial price puzzle macro-empirically without operationalizing dispatch feasibility or physical shrinkage |
| 4 | Spatial Arbitrage & Market Integration | **Negi et al. (2018)** | *Food Policy*, 81:106–121 | Links transport & communication networks to farmer channel choice and producer price realization | Evaluates survey-level channel access rather than daily corridor-specific road travel time, climate decay, and yard activity |
| 5 | Mandi Data & Anomaly Modeling | **Madaan et al. (2019)** | *ACM COMPASS '19*, pp. 52–64 | Forecasts AGMARKNET onion/potato prices & flags anomalies across mandis | Optimizes point price forecasting/anomaly alerts; does not evaluate executable cross-mandi dispatch under spoilage & road cost |
| 6 | Indian Post-Harvest Loss & Climate | **Jha et al. (2015)** | ICAR-CIPHET / MoFPI (173 pp.) | Landmark national benchmark of harvest & post-harvest losses across 45+ crops including transport | Static national averages; does not map losses to daily corridor temperature or transit duration in dispatch decisions |
| 7 | Indian Post-Harvest Loss & Climate | **NABCONS / MoFPI (2022)** | MoFPI Final Report (2020–22 ref.) | Updated 54-crop national loss audit showing fruits (6.02–15.05%) & veg (4.87–11.61%) remain severe | Macro policy baseline rather than an operational day-level transit-spoilage penalty for inter-mandi routing |
| 8 | Indian Post-Harvest Loss & Climate | **Hersbach et al. (2020)** | *QJRMS*, 146(730):1999–2049 | ERA5 global atmospheric reanalysis providing hourly gridded temperature/meteorology since 1940s | Widely used in meteorology, rarely coupled with road-network routing & mandi prices to measure thermal spoilage risk |
| 9 | Selective Prediction & Conformal Risk | **Chow (1970)** | *IEEE TIT*, 16(1):41–46 | Derives Bayes-optimal error–reject tradeoff when mistakes carry explicit asymmetric costs | Classical classification theory; requires domain loss mapping and finite-sample calibration for perishable spatial dispatch |
| 10 | Selective Prediction & Conformal Risk | **Franc, Průša, & Voráček (2023)** | *JMLR*, 24(11):1–49 | Unifies cost-based, bounded-improvement, & bounded-abstention reject classifiers via proper scores | Assumes general i.i.d. classification; does not instantiate financial asymmetry of false dispatch vs. local hold |
| 11 | Selective Prediction & Conformal Risk | **Angelopoulos & Bates (2023)** | *FnTML*, 16(4):494–591 | Distribution-free split conformal prediction intervals & risk control for black-box predictors | Provides uncertainty quantification toolkit, not an end-to-end sequential verification or agricultural arbitrage pipeline |
| 12 | Tool-Using & Budgeted Agents | **Yao et al. (2023)** | *ICLR 2023* | ReAct interleaves reasoning traces with external API/tool calls to reduce hallucination | Unconstrained polling loop lacks explicit per-call cost budgeting or asymmetric risk-based early stopping |
| 13 | Tool-Using & Budgeted Agents | **Kachuee et al. (2019)** | *ICLR 2019* | Opportunistic Learning acquires costly features sequentially at prediction time under budget | Formulated as RL over feature streams; not coupled with conformal risk bounds or geospatial/weather dispatch funnels |
| 14 | Tool-Using & Budgeted Agents | **Han, Buntine, & Shareghi (2024)** | *Findings of ACL 2024*, pp. 6662–6685 | UALA gates external tool calls via calibrated uncertainty instead of uncalibrated verbalized scores | Evaluated on text QA benchmarks (HotpotQA/StrategyQA/MMLU), not multi-modal geospatial/climate/price dispatch |
| 15 | Conformal Risk & Conditional Coverage | **Lei et al. (2018)** | *JASA*, 113(523):1094–1111 | Establishes distribution-free split conformal prediction and locally weighted residuals for regression | General statistical framework; Stage II measures how pooled residuals create a 21–23 pp volatility-quartile illusion in mandis |
| 16 | Conformal Risk & Conditional Coverage | **Romano, Patterson, & Candès (2019)** | *NeurIPS 32*, pp. 3538–3548 | Conformalized Quantile Regression (CQR) adapts prediction intervals dynamically to local heteroscedasticity | Does not model uncensored arrival-closure payoffs or selective `HOLD_LOCAL` dispatch risk |
| 17 | Conformal Risk & Conditional Coverage | **Angelopoulos et al. (2024)** | *ICLR 2024* (Spotlight) | Conformal Risk Control (CRC) extends split conformal to monotone loss functions via finite-sample threshold tuning | Exchangeability Theorem 1 fails under agricultural season shifts & post-selection denominators; Stage II adapts its validation ratio empirically |
| 18 | Selective Labels & Censored Outcomes | **Lakkaraju et al. (2017)** | *ACM KDD '17*, pp. 275–284 | Formalizes selective-labels missingness when downstream outcomes are only observed under historical decisions | Focuses on observational decision confounding; Stage II uncovers arrival-censored (`dropna`) downside understatement (up to 2.54x) |
| 19 | Thin/Fragmented Indian Markets | **Goyal (2010)** | *AEJ: Applied Economics*, 2(3):22–45 | Shows ITC e-Choupal internet kiosks raised soy prices in MP by cutting market isolation & intermediary margins | Focuses on static spot competition for oilseeds rather than grade-fragmented mountain horticultural `T1` sparsity |
| 20 | Thin/Fragmented Indian Markets | **Levi et al. (2020)** | *PNAS*, 117(5):2366–2371 | Demonstrates unified wholesale bidding platforms (`ReMS` Karnataka) improve modal farm prices across commodities | Examines platform auction design rather than cross-mandi sub-grade reporting sparsity (`HP Apple`) causing false `T1` refusals |

---

## 2. Detailed Summaries of the 20 Verified Primary Citations

### Pillar I: Agricultural Spatial Arbitrage, Price Dispersion & Indian Mandi Cointegration

#### 1. Jensen (2007) — *The Digital Provide*
* **Exact Citation:** Jensen, Robert. (2007). "The Digital Provide: Information (Technology), Market Performance, and Welfare in the South Indian Fisheries Sector." *The Quarterly Journal of Economics*, Vol. 122, Issue 3, pp. 879–924.
* **DOI / URL:** `10.1162/qjec.122.3.879` — <https://doi.org/10.1162/qjec.122.3.879>
* **Plain-English Summary:** Jensen studied Kerala sardine fishermen before and after mobile phone coverage rolled out along the coast (1997–2001). Once fishermen could phone ahead to coastal landing markets while still at sea, cross-market price dispersion dropped sharply, almost all zero-sale fish dumping ("waste") disappeared, fishermen's profits rose by ~8%, and consumer prices fell by ~4%.
* **Relevance & Remaining Gap:** This is the canonical empirical proof that spatial arbitrage can unlock substantial producer welfare when perishables are matched to the right market in time. However, Kerala coastal boats moved homogeneous fish over short sea distances; inland horticultural mandis in India face **variety/grade heterogeneity**, **intermittent yard reporting/closures**, **mountain/highway road bottlenecks**, and **ambient heat spoilage during multi-hour truck transit**—making naive price chasing deceptive ("phantom arbitrage").

#### 2. Sekhar (2012) — *Agricultural Market Integration in India*
* **Exact Citation:** Sekhar, C. S. C. (2012). "Agricultural market integration in India: An analysis of select commodities." *Food Policy*, Vol. 37, Issue 3, pp. 309–322.
* **DOI / URL:** `10.1016/j.foodpol.2012.03.002` — <https://doi.org/10.1016/j.foodpol.2012.03.002>
* **Plain-English Summary:** Sekhar tested econometric spatial cointegration across major Indian agricultural wholesale markets for commodities including gram, edible oil/mustard, rice, and wheat. He showed that while regional markets within states or less-regulated commodities often exhibit long-run price integration, inter-state market fragmentation and regulatory/logistical barriers prevent uniform national price convergence.
* **Relevance & Remaining Gap:** Establishes that Indian agricultural markets are structurally segmented rather than frictionlessly integrated. However, monthly/weekly econometric cointegration tests measure equilibrium over months; they do not dissect **day-level operational dispatch failures** for short-shelf-life perishables (Onion, Potato, Tomato, Apple) or build a decision agent.

#### 3. Chatterjee & Kapur (2016/2017) — *Price Variation & Six Puzzles in Indian Agriculture*
* **Exact Citation:** Chatterjee, Shoumitro, and Devesh Kapur. (2016). "Understanding Price Variation in Agricultural Commodities in India: MSP, Government Procurement, and Agriculture Markets." NCAER *India Policy Forum* Conference Paper (July 12–13, 2016); published as "Six Puzzles in Indian Agriculture," *India Policy Forum* (NCAER / SAGE), Vol. 13(1), 2016–17, pp. 185–229.
* **Verified URLs:** Conference Paper PDF: <http://www.ncaer.org/events/ipf-2016/IPF-2016-Paper-Chatterjee-Kapur.pdf> | Published Journal Entry: <https://ideas.repec.org/a/nca/ncaerj/v13y2017i2017-1p185-229.html>
* **Plain-English Summary:** Using granular mandi-level data, Chatterjee and Kapur documented that spatial price dispersion across Indian mandis remains strikingly large—even across relatively close markets and even after accounting for transport costs—highlighting deep frictions from APMC rules, local market power, asymmetric information, and quality differences.
* **Relevance & Remaining Gap:** Directly motivates why naive cross-mandi spreads in AGMARKNET look enormous on paper. Yet Chatterjee and Kapur treat the residual price gap largely as institutional/structural wedge without decomposing how much apparent arbitrage vanishes due to **variety mismatch, closed/non-reporting yards, OSRM road travel cost, and ERA5 thermal spoilage**.

#### 4. Negi, Birthal, Roy, & Khan (2018) — *Market Channels, Transport & Communication Networks*
* **Exact Citation:** Negi, Digvijay S., Pratap S. Birthal, Devesh Roy, and Md. Tajuddin Khan. (2018). "Farmers' choice of market channels and producer prices in India: Role of transportation and communication networks." *Food Policy*, Vol. 81, pp. 106–121.
* **DOI / URL:** `10.1016/j.foodpol.2018.10.008` — <https://doi.org/10.1016/j.foodpol.2018.10.008>
* **Plain-English Summary:** Analyzing nationally representative Indian farm household survey data, the authors show that smallholders with poor access to transport and communication networks disproportionately sell locally to village traders/middlemen at lower realized prices, whereas better road connectivity and information access enable higher-margin wholesale channel participation.
* **Relevance & Remaining Gap:** Confirms empirically that transport friction and information access jointly constrain producer price realization in India. Because it relies on cross-sectional household surveys, it cannot evaluate daily dynamic routing, perishable thermal degradation, or uncertainty-calibrated abstention when remote market spreads are risky.

#### 5. Madaan, Sharma, Khandelwal, Goel, Singla, & Seth (2019) — *AGMARKNET Forecasting & Anomaly Detection*
* **Exact Citation:** Madaan, Lovish, Ankur Sharma, Praneet Khandelwal, Shivank Goel, Parag Singla, and Aaditeshwar Seth. (2019). "Price Forecasting & Anomaly Detection for Agricultural Commodities in India." In *Proceedings of the 2nd ACM SIGCAS Conference on Computing and Sustainable Societies (COMPASS '19)*, pp. 52–64.
* **DOI / URL:** `10.1145/3314344.3332488` — <https://doi.org/10.1145/3314344.3332488>
* **Plain-English Summary:** Using multi-year AGMARKNET daily series for onions and potatoes, the authors build forecasting and anomaly-detection models to flag abnormal mandi price spikes and hoarding/supply shocks, including handling missing entries and market irregularities.
* **Relevance & Remaining Gap:** One of the strongest CS/ICTD-for-development papers directly using AGMARKNET data. However, its target is **price forecasting and price-anomaly detection**, not **spatial dispatch optimization**. It does not route across OSRM road networks, price thermal spoilage, separate variety/grade mismatches in arbitrage spreads, or introduce a cost-sensitive `HOLD_LOCAL` reject rule.

---

### Pillar II: Official Indian Post-Harvest Losses & Climate Reanalysis

#### 6. Jha, Vishwakarma, Ahmad, Rai, & Dixit (2015) — *ICAR-CIPHET National Post-Harvest Loss Study*
* **Exact Citation:** Jha, S. N., R. K. Vishwakarma, Tauqueer Ahmad, Anil Rai, and Anil K. Dixit. (2015). *Report on Assessment of Quantitative Harvest and Post-Harvest Losses of Major Crops and Commodities in India*. ICAR-All India Coordinated Research Project on Post-Harvest Technology, ICAR-Central Institute of Post-Harvest Engineering and Technology (ICAR-CIPHET), Ludhiana; sponsored by Ministry of Food Processing Industries (MoFPI), Government of India, 173 pp.
* **Verified URL:** <https://www.researchgate.net/publication/289637983_Assessment_of_Quantitative_Harvest_and_Post-Harvest_Losses_of_Major_CropsCommodities_in_India>
* **Plain-English Summary:** India's benchmark multi-agro-climatic-zone field survey measuring quantitative harvest and post-harvest physical losses across 45+ crops via direct observation and interviews across farm, storage, transport, and market stages. Estimated losses reached **6.70%–15.88% for fruits** (with apple among key horticultural crops) and **4.58%–12.44% for vegetables** (including potato, onion, tomato).
* **Relevance & Remaining Gap:** Provides official empirical loss ranges that anchor physical realism in perishable supply chains. However, CIPHET reports aggregate multi-stage annual percentages, not operational **per-hour/per-degree-Celsius transit decay functions** usable in daily dispatch scoring.

#### 7. NABCONS / MoFPI (2022) — *Updated 54-Crop Post-Harvest Loss Study*
* **Exact Citation:** NABARD Consultancy Services Pvt. Ltd. (NABCONS). (2022). *Study to Determine Post-Harvest Losses of Agri Produces in India* (Reference Period: 2020–22; Final Report dated December 7, 2022). Commissioned by Ministry of Food Processing Industries (MoFPI), Government of India.
* **Verified URL:** <https://www.mofpi.gov.in/sites/default/files/phl_study_final_report_07.12.2022_2.pdf>
* **Plain-English Summary:** Updates CIPHET (2015) across **54 crops/commodities and 292 districts** spanning 15 agro-climatic zones, decomposing losses across harvesting, grading, packaging, transport, storage, wholesale, and retail. Persistent perishable losses remained high (**6.02%–15.05% for fruits**, **4.87%–11.61% for vegetables**), translating to ~11.97 million MT of vegetables and ~7.36 million MT of fruits lost annually.
* **Relevance & Remaining Gap:** Confirms that despite infrastructure expansion since 2015, transport and wholesale handling remain major leakage stages for Indian perishables. Like CIPHET, it is a static macro-audit and offers no route-level, day-level dispatch decision tool.

#### 8. Hersbach et al. (2020) — *The ERA5 Global Reanalysis*
* **Exact Citation:** Hersbach, Hans, Bill Bell, Paul Berrisford, Shoji Hirahara, András Horányi, Joaquín Muñoz-Sabater, Julien Nicolas, Carole Peubey, Raluca Radu, Dinand Schepers, Adrian Simmons, Cornel Soci, Saleh Abdalla, Xavier Abellan, Gianpaolo Balsamo, Peter Bechtold, Gionata Biavati, Jean-Raymond Bidlot, Massimo Bonavita, Giovanna De Chiara, Per Dahlgren, Dick Dee, Michail Diamantakis, Rossana Dragani, Johannes Flemming, Richard G. Forbes, Manuel Fuentes, Alan J. Geer, Leopold Haimberger, Sean B. Healy, Robin James Hogan, Elías Valur Hólm, Marta Janisková, Sarah P. E. Keeley, Patrick Laloyaux, Philippe Lopez, Cristina Lupu, Gabor Radnoti, Patricia de Rosnay, Iryna Rozum, Freja Vamborg, Sébastien Villaume, and Jean-Noël Thépaut. (2020). "The ERA5 global reanalysis." *Quarterly Journal of the Royal Meteorological Society*, Vol. 146, Issue 730, pp. 1999–2049.
* **DOI / URL:** `10.1002/qj.3803` — <https://doi.org/10.1002/qj.3803>
* **Plain-English Summary:** Describes ECMWF's fifth-generation global atmospheric reanalysis (ERA5), providing physically consistent hourly gridded estimates of 2 m air temperature, precipitation, humidity, and atmospheric variables at ~31 km (0.25°) spatial resolution globally.
* **Relevance & Remaining Gap:** Enables spatially complete, gap-free historical ambient temperature estimation across all Indian agricultural corridors—avoiding missing weather-station coverage in rural APMC districts. Yet ERA5 has rarely been integrated with AGMARKNET and OSRM road travel times to price thermal spoilage in Indian mandi dispatch.

---

### Pillar III: Selective Prediction, Asymmetric Reject Rules & Conformal Prediction

#### 9. Chow (1970) — *Optimum Recognition Error and Reject Tradeoff*
* **Exact Citation:** Chow, C. K. (1970). "On optimum recognition error and reject tradeoff." *IEEE Transactions on Information Theory*, Vol. 16 (IT-16), Issue 1, pp. 41–46.
* **DOI / URL:** `10.1109/TIT.1970.1054406` — <https://doi.org/10.1109/TIT.1970.1054406>
* **Plain-English Summary:** Proves the foundational Bayes-optimal decision rule when a predictor can either classify or **abstain ("reject")**: abstaining is optimal whenever the posterior confidence falls below a threshold governed by the ratio of rejection cost to misclassification cost.
* **Relevance & Remaining Gap:** Supplies the exact decision-theoretic justification for `MandiGuard`'s **`HOLD_LOCAL` abstention option**: dispatching a truck on a false-positive spread loses sunk road freight + thermal spoilage + yard risk, making abstention strictly rational when uncertainty is high. However, Chow's rule assumes true calibrated posterior probabilities, which real forecasting models lack without distribution-free calibration.

#### 10. Franc, Průša, & Voráček (2023) — *Optimal Strategies for Reject Option Classifiers*
* **Exact Citation:** Franc, Vojtěch, Daniel Průša, and Václav Voráček. (2023). "Optimal Strategies for Reject Option Classifiers." *Journal of Machine Learning Research (JMLR)*, Vol. 24, No. 11, pp. 1–49.
* **Verified URLs:** <https://jmlr.org/papers/v24/21-0048.html> | Preprint: <https://arxiv.org/abs/2101.12523>
* **Plain-English Summary:** Unifies three classic abstention formulations—explicit cost-based rejection, bounded-improvement (max coverage at capped risk), and bounded-abstention (min risk at target coverage)—showing all three reduce to a Bayes classifier paired with a randomized selection function over a *proper uncertainty score*, and gives Fisher-consistent algorithms to learn that score from black-box models.
* **Relevance & Remaining Gap:** Bridges theoretical reject rules with practical black-box predictors via **risk–coverage curves** and proper uncertainty scores. Still, agricultural arbitrage requires **continuous asymmetric net-profit payoff calibration** (where mistake magnitude scales with freight distance and heat decay) rather than symmetric 0–1 classification risk.

#### 11. Angelopoulos & Bates (2023) — *Conformal Prediction: A Gentle Introduction*
* **Exact Citation:** Angelopoulos, Anastasios N., and Stephen Bates. (2023). "Conformal Prediction: A Gentle Introduction." *Foundations and Trends in Machine Learning*, Vol. 16, Issue 4, pp. 494–591.
* **DOI / URL:** `10.1561/2200000101` — <https://doi.org/10.1561/2200000101>
* **Plain-English Summary:** Comprehensive monograph on distribution-free uncertainty quantification. Shows how split conformal prediction uses a held-out calibration set to wrap *any* heuristic black-box predictor into prediction intervals or sets with finite-sample coverage guarantees under exchangeability, and extends the framework to conformal risk control for general loss functions.
* **Relevance & Remaining Gap:** Enables `MandiGuard` to compute calibrated lower confidence bounds on net post-freight, post-spoilage spatial profit (`LCB(NetProfit)`) before committing a dispatch. Key limitation to handle honestly in temporal market panels: strict finite-sample coverage assumes exchangeability, which weakens under seasonal shifts—necessitating rolling/recent calibration windows and empirical holdout coverage auditing.

---

### Pillar IV: Tool-Using & Budgeted Verification AI Agents

#### 12. Yao et al. (2023) — *ReAct: Synergizing Reasoning and Acting*
* **Exact Citation:** Yao, Shunyu, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, and Yuan Cao. (2023). "ReAct: Synergizing Reasoning and Acting in Language Models." *International Conference on Learning Representations (ICLR 2023)* (Notable-Top-5%).
* **Verified URLs:** <https://openreview.net/forum?id=WE_vluYUL-X> | Preprint: <https://arxiv.org/abs/2210.03629>
* **Plain-English Summary:** Introduces the ReAct loop—interleaving chain-of-thought reasoning with external tool/API queries so an agent grounds decisions in retrieved observations rather than hallucinating facts.
* **Relevance & Remaining Gap:** Establishes the standard tool-calling agent baseline. However, naive ReAct loops neither optimize **external API/verification cost** across dozens of candidate destinations nor embed **conformal asymmetric-cost abstention**; polling every external route/climate tool blindly scales poorly in latency and cost.

#### 13. Kachuee et al. (2019) — *Opportunistic Learning: Budgeted Cost-Sensitive Feature Acquisition*
* **Exact Citation:** Kachuee, Mohammad, Orpaz Goldstein, Kimmo Kärkkäinen, Sajad Darabi, and Majid Sarrafzadeh. (2019). "Opportunistic Learning: Budgeted Cost-Sensitive Learning from Data Streams." *International Conference on Learning Representations (ICLR 2019)*.
* **Verified URLs:** <https://openreview.net/forum?id=S1eOHo09KX> | Preprint: <https://arxiv.org/abs/1901.00243>
* **Plain-English Summary:** Formulates test-time feature acquisition under explicit acquisition cost budgets: instead of observing all expensive features upfront, the model sequentially estimates the uncertainty reduction / value of acquiring each feature and stops once expected gain no longer justifies cost.
* **Relevance & Remaining Gap:** Provides the exact conceptual principle behind `MandiGuard`'s **staged verification funnel**: cheap metadata and historical/variety filters prune hopeless destinations first, reserving expensive OSRM routing, ERA5 corridor temperature lookups, and calibrated risk inference for surviving candidates.

#### 14. Han, Buntine, & Shareghi (2024) — *Towards Uncertainty-Aware Language Agent (UALA)*
* **Exact Citation:** Han, Jiuzhou, Wray Buntine, and Ehsan Shareghi. (2024). "Towards Uncertainty-Aware Language Agent." *Findings of the Association for Computational Linguistics: ACL 2024*, pp. 6662–6685.
* **DOI / URL:** `10.18653/v1/2024.findings-acl.398` — <https://aclanthology.org/2024.findings-acl.398/>
* **Plain-English Summary:** Shows that uncalibrated verbalized agent confidence is unreliable, and introduces UALA, which uses calibrated uncertainty quantification over small calibration sets to decide *when* an agent can decide directly vs. *when* it must invoke external verification tools—improving accuracy while sharply cutting tool calls over ReAct.
* **Relevance & Remaining Gap:** Directly motivates replacing naive all-pairs external verification or uncalibrated heuristic confidence with **calibrated uncertainty-gated verification** in `MandiGuard`, bridging uncertainty quantification and tool budgeting—applied here for the first time to multi-state geospatial/climate/price agricultural dispatch.

---

### Pillar V: Conditional Heteroscedasticity, Conformal Risk Control, Selective Labels & Grade Fragmentation (Stage-II Extensions)

#### 15. Lei, G'Sell, Rinaldo, Tibshirani, & Wasserman (2018) — *Distribution-Free Predictive Inference for Regression*
* **Exact Citation:** Lei, Jing, Max G'Sell, Alessandro Rinaldo, Ryan J. Tibshirani, and Larry Wasserman. (2018). "Distribution-Free Predictive Inference for Regression." *Journal of the American Statistical Association*, Vol. 113, No. 523, pp. 1094–1111.
* **DOI / URL:** `10.1080/01621459.2017.1307116` — <https://doi.org/10.1080/01621459.2017.1307116>
* **Plain-English Summary:** Formalizes split conformal regression intervals and proves why unscaled constant-width conformal residuals only guarantee *marginal* coverage while failing *conditional* coverage when error variance varies across feature regimes, proposing locally weighted conformity scores.
* **Relevance & Remaining Gap:** Stage-II `Exp 16` quantifies this exact mechanism inside Indian mandis (`Q1_Calm` 90.46% vs `Q4_Volatile` 67.80% empirical coverage—a 22.66 pp spread), motivating `MandiGuard-CRC`'s move away from commodity-pooled additive intervals.

#### 16. Romano, Patterson, & Candès (2019) — *Conformalized Quantile Regression (CQR)*
* **Exact Citation:** Romano, Yaniv, Evan Patterson, and Emmanuel J. Candès. (2019). "Conformalized Quantile Regression." *Advances in Neural Information Processing Systems (NeurIPS)*, Vol. 32, pp. 3538–3548.
* **Verified URL:** <https://proceedings.neurips.cc/paper/2019/hash/5103c3584b063c431bd1268e9b5e76fb-Abstract.html>
* **Plain-English Summary:** Wraps pinball-loss quantile regressors with split conformal residual adjustment so interval widths adapt automatically to local input heteroscedasticity without sacrificing marginal finite-sample validity.
* **Relevance & Remaining Gap:** Explains why Stage-I pooled residual quantiles fail under heteroscedastic market volatility (`Exp 16`) and connects naturally to asymmetric downside control—though CQR targets observed continuous outcomes rather than censored closed-yard arrival payoffs (`Exp 17`).

#### 17. Angelopoulos, Bates, Fisch, Lei, & Schuster (2024) — *Conformal Risk Control (CRC)*
* **Exact Citation:** Angelopoulos, Anastasios N., Stephen Bates, Adam Fisch, Lihua Lei, and Tal Schuster. (2024). "Conformal Risk Control." *International Conference on Learning Representations (ICLR 2024 Spotlight)*.
* **Verified URL:** <https://openreview.net/forum?id=uPD0kqYEfS> (Preprint: `arXiv:2208.02814`)
* **Plain-English Summary:** Extends split conformal prediction beyond 0–1 miscoverage to any bounded, monotone non-increasing loss function of a scalar threshold $\lambda$, choosing $\hat{\lambda}$ via finite-sample calibration ratio adjustment.
* **Relevance & Remaining Gap:** Stage-II `MandiGuard-CRC` adapts this validation calibration heuristic—selecting $\lambda^* = 0.15$ on `Val_2025H1` via $(n_{\text{loss}}+1)/(n_{\text{disp}}+1) \le 0.095$ (`lambda_grid = [0.00..1.20]`) for expected-value-minus-tail score $\hat{\mu} - \lambda^* P_{\text{loc}} \hat{p}_{\text{loss}}$. Critically, because agricultural prices violate exchangeability and dispatch rate varies with $\lambda$, we **explicitly do not claim Angelopoulos et al. Theorem 1 theoretical guarantees**; Stage II reports empirical out-of-sample performance transparently.

#### 18. Lakkaraju, Kleinberg, Leskovec, Ludwig, & Mullainathan (2017) — *The Selective Labels Problem*
* **Exact Citation:** Lakkaraju, Himabindu, Jon Kleinberg, Jure Leskovec, Jens Ludwig, and Sendhil Mullainathan. (2017). "The Selective Labels Problem: Evaluating Algorithmic Predictions in the Presence of Unobservables." *Proceedings of the 23rd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (KDD '17)*, pp. 275–284.
* **DOI / URL:** `10.1145/3097983.3098066` — <https://doi.org/10.1145/3097983.3098066>
* **Plain-English Summary:** Demonstrates that evaluating or training predictive models solely on rows where outcomes were historically observed induces severe selection bias when unobservables affect both observation/selection and downstream outcomes.
* **Relevance & Remaining Gap:** Directly illuminates **Stage-II Finding A (Censored-Arrival Survivorship Bias)**: standard `dropna(target_ret)` training drops 55.83% of raw corridors (and 12.64% post-`T1`), understating 20th-percentile downside drops by 1.82–2.54x (`age_0d..age_3d`) and creating blind spots that `MandiGuard-CRC` repairs by training directly on uncensored `Y_full` plus counterfactual open-yard validation (`N=10,162`).

#### 19. Goyal (2010) — *Information, Direct Access, and Rural Market Performance in Central India*
* **Exact Citation:** Goyal, Aparajita. (2010). "Information, Direct Access to Farmers, and Rural Market Performance in Central India." *American Economic Journal: Applied Economics*, Vol. 2, No. 3, pp. 22–45.
* **DOI / URL:** `10.1257/app.2.3.22` — <https://doi.org/10.1257/app.2.3.22>
* **Plain-English Summary:** Shows in Madhya Pradesh soybean districts that rural internet price kiosks and direct procurement competition increased mandi prices by ~1.7% and shifted crop area toward higher-value cash production.
* **Relevance & Remaining Gap:** Highlights that rural market participation depends jointly on physical access and clearing liquidity; where grade differentiation fractures volume across days (as in Himachal apples), rolling average presence metrics misfire.

#### 20. Levi, Rajan, Singhvi, & Zheng (2020) — *The Impact of Unifying Agricultural Wholesale Markets*
* **Exact Citation:** Levi, Retsef, Manoj Rajan, Somya Singhvi, and Yanchong Zheng. (2020). "The impact of unifying agricultural wholesale markets on prices and farmers' profitability." *Proceedings of the National Academy of Sciences (PNAS)*, Vol. 117, No. 5, pp. 2366–2371.
* **DOI / URL:** `10.1073/pnas.1906854117` — <https://doi.org/10.1073/pnas.1906854117>
* **Plain-English Summary:** Uses natural experiment differences across Karnataka's Unified Market Platform (`ReMS`) to prove that centralized electronic auctioning across fragmented wholesale yards raises modal farmer prices (+5.1% average), while revealing acute sensitivity to quality grading and yard liquidity.
* **Relevance & Remaining Gap:** Provides structural economic context for **Stage-II Finding C**: when AGMARKNET splits fresh apple harvests into sparse sub-grades (`Grade A`, `Grade B`, `Range-1`), yard-level `open_prob_14d` appears fragmented even though the destination apple auction is actively operating—accounting for 77.82%–82.75% of Stage-I `MandiGuard` refusals vs `B2` (`Exp 16`).

---

## 3. Closest Prior Work on Indian Mandi Selection, Price Imputation & Agri-Logistics (Honesty Audit)

To avoid claiming novelty where prior systems already exist, the table below records verified closest works touching Indian mandis, AGMARKNET data, weather, road routing, and spatial market selection:

| Citation | Venue & Year | Verified DOI / URL | What It Already Does | Exact Gap Left Open for `MandiGuard` |
|:---|:---|:---|:---|:---|
| **Mitra, Mookherjee, Torero, & Visaria (2018)** | *Review of Economics and Statistics*, 100(1):1–13 | `10.1162/rest_a_00699` | Field experiment with West Bengal potato farmers proving that providing daily wholesale mandi prices alone failed to raise average farmgate realization without outside dispatch options | Demonstrates *why* price transparency alone fails; does not build a road-, climate-, and risk-calibrated dispatch agent |
| **Ma, Nowocin, Marathe, & Chen (2019)** | *ACM ICTD '19*, Art. 6, pp. 1–11 | `10.1145/3287098.3287100` | *An Interpretable Produce Price Forecasting System for Small and Marginal Farmers in India Using Collaborative Filtering and Adaptive Nearest Neighbors* across 1,000+ AGMARKNET mandis | Focuses purely on interpretable price imputation/prediction; no spatial arbitrage decomposition, OSRM routing, spoilage, or abstention |
| **Guo, Woodruff, & Yadav (2020)** | *AAAI-20*, 34(08):13294–13299 | `10.1609/aaai.v34i08.7039` | *Improving Lives of Indebted Farmers Using Deep Learning: Predicting Agricultural Produce Prices Using Convolutional Neural Networks*; explicitly observes missing quotes arise from yard closures/zero-sales days | Treats yard closures as a preprocessing filter for price MSE rather than an execution-time *closed-yard hazard* in spatial arbitrage |
| **Mahajan & Tomar (2021)** | *AJAE*, 103(1):35–52 | `10.1111/ajae.12158` | Quantifies sharp distance gradients in Indian food supply chain disruptions during COVID-19 | Macro disruption event study; does not model routine spatial arbitrage, variety mismatch, or thermal decay |
| **Luxen & Vetter (2011)** | *ACM SIGSPATIAL GIS '11*, pp. 513–516 | `10.1145/2093973.2094062` | Introduces Open Source Routing Machine (OSRM) using contraction hierarchies on OpenStreetMap road networks | Routing engine only; highlights why straight-line Haversine underestimates actual road distances & transit durations in India |
| **Divyashree & Biradar (2026)** | *IJEDR*, 14(3):538–547 | [PDF](https://rjwave.org/IJEDR/papers/IJEDR2603265.pdf) | *AgriMarket AI: Intelligent Market Selection and Profit Prediction System for Farmers Using Machine Learning* (XGBoost/RF with Haversine distance & AGMARKNET prices) | **Closest naive baseline:** uses Haversine (not OSRM), ignores variety/grade mismatch, closed-yard risk, ERA5 thermal spoilage, conformal abstention, and tool budgeting |
| **Manimegalai, Sanjay, Siddarth, & Udayabhaarathi (2026)** | *IJRPR*, 7(11):1–5 | *(Verified via IJRPR Vol. 7, Issue 11, Nov 2026)* | *Mandi Cast: AI-Based Crop Price Forecasting and Sell Advisory System* (SARIMA/XGBoost + OpenWeatherMap covariates) | Weather is used only as a price-forecast covariate—not for transit freshness decay, road-network arbitrage, or selective abstention |
| **Pritam Deka (2026)** | *arXiv:2610.39949* | `10.48550/arXiv.2610.39949` | *Reconstructing Missing Mandi Prices in North-East India with Regional Factors* (dynamic factor models & adaptive ensembles) | Imputes missing price series statistically rather than treating non-reporting yards as a dispatch-time operational risk |

---

## 4. Cross-Cutting Synthesis: Four Concrete Gaps Motivating `MandiGuard`

1. **No Quantitative Decomposition of Phantom Spatial Arbitrage:** Economists documented persistent cross-mandi dispersion (Sekhar 2012; Chatterjee & Kapur 2016/2017) and ML researchers improved AGMARKNET price MSE/imputation (Madaan et al. 2019; Ma et al. 2019; Guo et al. 2020; Deka 2026), yet no multi-state study decomposes nominal apparent spreads into **(i) variety/grade mismatch**, **(ii) closed-yard/stale-quote execution hazard**, **(iii) Haversine-vs-OSRM road friction**, and **(iv) ERA5 ambient thermal spoilage**.
2. **Naive Applied Recommenders Optimize Symmetric Accuracy or Point Net-Profit:** Recent applied systems (*AgriMarket AI* 2026; *Mandi Cast* 2026) compute point-estimate net gains using Haversine distances or weather-augmented price regressions, exposing farmers to asymmetric downside losses when a distant spread fails in transit or on arrival.
3. **Missing Bridge Between Conformal Abstention, Uncensored Risk Control, and Agricultural Logistics:** Selective reject theory (Chow 1970; Franc et al. 2023), heteroscedastic conformal intervals (Lei et al. 2018; Romano et al. 2019), conformal risk control (Angelopoulos et al. 2024), and selective-labels audits (Lakkaraju et al. 2017) provide exact diagnostic and calibration tools, yet remain unapplied to arrival-censored perishable mandi dispatch and thin-grade market aggregation (Goyal 2010; Levi et al. 2020).
4. **Absence of Budgeted Verification in Multi-Modal Agri-Agents:** Checking OSRM routes, ERA5 corridor temperatures, and calibrated risk scores for every destination on every day wastes compute/API budget (contrary to Kachuee et al. 2019 and Han et al. 2024), motivating `MandiGuard`'s **sequential verification funnel**.
