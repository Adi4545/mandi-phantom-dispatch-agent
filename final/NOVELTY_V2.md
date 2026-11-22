# Novelty & Literature Audit (`NOVELTY_V2` — Agents `A9`, `A10`, `A11`, `A12`, `A17`, `A18`)

## 1. Nearest Prior Work Overlap & Difference Table (`A9`)

| Work | Domain / Problem | Exact Method | Benchmark / Data | Closest Overlap with Revision v5 | Concrete Difference |
|---|---|---|---|---|---|
| **Baulch (1997)**, *AJAE* (`10.2307/1244145`) | Spatial market integration | Parity bounds vs transfer costs | Ex-post price pairs | Gaps below transfer cost yield no trade | Macroeconomic market integration, NOT ex-ante strictly-`<t` truck alert triage or `ES10`. |
| **Jensen (2007)**, *QJE* (`10.1162/qjec.122.3.879`) | Kerala fish markets & mobile quotes | Natural experiment of phone access | Fisher micro-survey | Phone calls eliminate arrival price surprise | Fishermen phoned live auctions; AGMARKNET spreads arrive lagged/incomplete by variety; `Safe-EV` filters noisy alerts prior to calling. |
| **Goyal (2010)**, *AEJ: Applied* (`10.1257/app.2.3.22`) | Soybeans (`e-Choupal` MP) | Diff-in-diff of kiosk rollout | Central India soy | Information hubs improve farm-gate realizations | Aggregate price levels, not route selection under daily non-reporting & variance. |
| **Fafchamps & Minten (2012)**, *WBER* (`10.1093/wber/lhr056`) | SMS price alerts in MH | RCT of market price SMS | 1,000+ Indian farms | Portal/SMS alerts alone rarely raise net farm receipts | Measures RCT average treatment effect; does not construct an actionable volatility/reporting filter. |
| **Mitra et al. (2018)**, *REStat* (`10.1162/rest_a_00699`) | Potato supply chain info asymmetry | Price info field experiment | WB potato growers | Middleman/transport frictions mute raw spreads | Models bargaining/credit rather than inter-mandi freight, fee incidence, and weekday non-reporting. |
| **Levi et al. (2020)**, *PNAS* (`10.1073/pnas.1906854117`) | Karnataka Unified Market Platform | Platform rollout diff-in-diff | KA APMC auctions | Unified digital auctions shape spatial dispersion | Evaluates platform design, not dispatch triage rules or tail losses. |
| **Mahajan & Tomar (2021)**, *AJAE* (`10.1111/ajae.12158`) | COVID-19 Indian food supply shocks | Disruption event study | Retail & AGMARKNET | Transport interruptions fracture spatial arbitrage | Descriptive disruption analysis, not an ex-ante routing filter. |
| **Madaan et al. (2019)**, *ACM COMPASS* (`10.1145/3314344.3332488`) | Mandi forecasting & anomaly flags | Time-series forecast + outlier detection | AGMARKNET multi-crop | Uses AGMARKNET series to flag anomalous patterns | Minimizes price RMSE without scoring sequential dispatch or missing-arrival risk. |
| **Ma et al. (2019)**, *ICTD* (`10.1145/3287098.3287100`) | Interpretable Indian price forecasting | Matrix completion + $k$NN | Daily AGMARKNET | Explicitly handles missing AGMARKNET daily rows | Imputes blank quotes to lower forecast MSE rather than down-weighting unreliable/volatile corridors. |
| **Guo et al. (2020)**, *AAAI* (`10.1609/aaai.v34i08.7039`) & **Deka (2026)** (`arXiv:2610.39949`) | Mandi price prediction & missing imputation | Deep sequence / NE regional factor model | State AGMARKNET | Highlights missing portal rows across regional yards | Optimizes statistical reconstruction rather than operational dispatch loss bounds (`ES10`). |
| **Chow (1970)** & **Franc et al. (2023)**, *JMLR* | Selective classification with reject | Bayes optimal reject tradeoff | Generic ML benchmarks | Mathematical foundation for abstaining under uncertainty | Assumes observed costs/labels without weekday reporting censoring or spatial transfer costs. |
| **Manski (1990)** & **Horowitz & Manski (2000)** | Nonparametric missing-outcome bounds | Worst-case / MAR identification bounds | Econometric trials | Direct theoretical anchor for our `open_yard_MAR`..`div=2.0` identification bounds | Provides general identification intervals rather than a deployed agricultural dispatch rule. |
| **Ban & Rudin (2019)**, *OR* (`10.1287/opre.2018.1757`) | Big Data Newsvendor | Asymmetric cost optimization from features | Operational inventory | Connects feature uncertainty directly to asymmetric loss | Assumes uncensored operational demand observations. |
| **Kallus & Zhou (2021)**, *Mgmt Sci* (`10.1287/mnsc.2020.3699`) | Minimax policy learning under confounding | Ambiguity-set regret bounds | Observational policies | Conservative bounding under unmeasured states | Complex ambiguity sets vs our zero-parameter weekday + 1-SD formula. |
| **Jin & Candès (2023)** & **Angelopoulos et al. (2024)**, *ICLR* | Conformal selection & Conformal Risk Control | Distribution-free calibration on exchangeable data | Drug/vision benchmarks | Legacy Stage I/II tried applying CRC to dispatch | Explicitly **rejected** here (`R7`): spatial-temporal panels violate exchangeability and dispatch-conditional risk breaks CRC. |

---

## 2. Progression From Tuned `A10` (`RR-Abstain`) to Zero-Parameter `A18` (`PREREG_A18.md`, `4cbb02d`)

1. **Why `RR-Abstain` Was Upgraded (`A17` + `A18`):** `RR-Abstain` (`87a0b62`) outperformed hard gates `MG_matched` (`+₹52.06 ES10`) yet collided with the validation ceiling `kappa* = 5.0`, blended `rep28` into `dow8` (over-predicting Sunday closings), omitted auction variance `cv28` (failing `div=0` on `ES10`, `p_2s=0.603`, and losing to `MG_matched` on HP Graded Apples), and suffered missing State prefixes (`336` buggy clusters).
2. **Locked Exploratory Zero-Parameter Rules (`4cbb02d` BEFORE `eval_a18.py`):**
   - **`Safe_EV_Sunk_m0`:** $S_{\text{Safe-EV}} = p_{\text{dow}}\cdot[P_{\text{dest,lag}}(1 - \text{cv}_{28})(1 - \tau_{\text{fee}}) - P_{\text{orig,lag}}] - F_{\text{road}} > 0$ (**0 free parameters!**).
   - **`RT_2F_Min_m0`:** $S_{\text{RT-2F-Min}} = \min(\text{rep}_{28}, p_{\text{dow}})\cdot[P_{\text{dest,lag}}(1 - \tau_{\text{fee}}) - P_{\text{orig,lag}}] - 2\,F_{\text{road}} > 0$ (**0 free parameters, NO `cv28`, Class-8 calculator!**).

| Hypothesis (`PREREG_A18.md`, `N = 58,676`) | Estimate | `origin_x_2week` (`173×23`) `p_holm_2s` | `b2dest_or_origin` (`172×23`) `p_holm_2s` | `policy_dest_or_origin` (`171–173×23`) `p_holm_2s` | Status (`exploratory: true`) |
|---|---:|---:|---:|---:|---|
| **`H_A18_1`:** `ES10(Safe_EV_Sunk_m0) - ES10(B2)` | **+₹181.17** | `0.0040` `[+124.77, +252.29]` | `0.0040` `[+109.76, +296.29]` | `0.0040` `[+122.97, +265.45]` | **SUPPORTED** |
| **`H_A18_2`:** `ES10(Safe_EV_matched) - ES10(RR)` | **+₹94.31** | `0.0040` `[+41.96, +158.72]` | `0.0040` `[+32.30, +201.07]` | `0.0040` `[+38.55, +172.92]` | **SUPPORTED** |
| **`H_A18_3`:** `EpLoss(Safe_EV_Sunk_m0) - EpLoss(B2)` | **−11.79 pp** | `0.0040` `[−13.47, −10.20]` | `0.0040` `[−14.78, −9.28]` | `0.0040` `[−14.38, −9.51]` | **SUPPORTED** |
| **`H_A18_4`:** `Mean(RT_2F_Min_m0) - Mean(B2)` | **+₹44.82** | `0.0040` `[+30.35, +60.62]` | `0.0040` `[+21.89, +72.88]` | `0.0040` `[+25.20, +67.97]` | **SUPPORTED** |

---

## 3. Single Defensible Novelty Sentence (Surviving `A12` + `A17` + `A18`)

> **"Claiming no new mathematical theorem or ML architecture, this study establishes—across 58,676 strictly causal (`<= t - 1`), sequentially settled wholesale dispatch episodes and an 88,014-episode unconditional origin audit across six states and four crops—that replacing black-box trees, hard activity gates, and tuned penalty grids with two zero-hyperparameter expected-value rules (`Safe_EV_Sunk_m0`: weekday reporting probability times 1-SD conservative spread exceeding sunk freight; `RT_2F_Min_m0`: conservative reporting probability times plain spread exceeding round-trip freight) cuts worst-10% shortfall by +₹181.17/qtl over equal-age road dispatch (`p_holm_2s = 0.0040` across all three cluster schemes) and +₹116.63/qtl over tuned `RR-Abstain`, surviving across all six states, all 36 tornado checks, exact-zero diversion (`+₹169.79`), and graded apples (`−₹1,454.86` vs `−₹2,392.12`) as a transparent upstream alert filter prior to trader confirmation—while openly disclosing its exploratory calendar boundary (`Gate J`) and Open-MAR mean reversal (`B2 +₹102.58`)."**
