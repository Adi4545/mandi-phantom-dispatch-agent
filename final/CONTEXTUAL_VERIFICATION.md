# Selecting B2 proposals for verification

A daily batch contains next-market dispatches proposed by the fresh-road heuristic B2. The router can request one additional check per ten proposals, rounding down separately for each day. A shallow tree ensemble estimates the number of rupees per quintal that perfect verification could save on each proposal. The final choices are the largest predicted values within each daily budget, with episode ID breaking ties. It uses the B2 margin, local and reference prices, route distance and duration in days, trailing quote frequency and variation, season, state and crop. Same-date quotes are assumed available before the batch is ranked.

The training target is the positive part of the negative modeled dispatch payoff. A profitable route has zero avoidable loss under a veto. The fit used 60,093 B2 proposals from 2024, including 11,335 modeled losses. Every candidate in each retained training episode had observed or scenario-assigned settlement by December 31 under a conservative arrival-plus-two-days rule. The ensemble used 60 boosting iterations at maximum tree depth three. Its hyperparameters and budget were fixed for these runs. Both evaluation cohorts had already been examined in earlier research.

The scorer assumes a selected check identifies every otherwise losing trip before departure, permits a costless local sale instead, and leaves every selected profitable trip alone. The results therefore bound the value of **perfect verification at the selected routes**. A live checker would need a signal with timely information, false positives and misses could change its value, and staff time would incur costs. The additional ranking ceiling assumes perfect advance knowledge of which proposed losses are largest.

| Routing priority | Six-state gain per eligible episode, ₹/qtl | HP apple gain per eligible episode, ₹/qtl |
|---|---:|---:|
| Learned expected avoidable loss | 18.05 | 7.77 |
| Uniform random, exact expected allocation | 4.25 | 9.37 |
| Smallest B2 margin | 4.28 | 8.48 |
| Lowest recent reporting frequency | 7.77 | 10.90 |
| Largest realized modeled losses, prescient ceiling | 35.66 | 40.56 |

The six-state calculation spent 4,175 checks among 43,183 B2 proposals and reported gains over all 69,526 eligible episodes. The learned ranking selected 1,470 losing trips. The reporting-frequency rule captured more (1,527), but the learned rule selected more severe losses on average. Its gain above uniform selection was ₹13.80/qtl per episode, with a paired 95% calendar-block bootstrap interval of ₹10.97 to ₹16.86. Against reporting frequency the difference was ₹10.28 [₹6.75, ₹14.00].

Only 22 of 76 HP proposal-days had at least ten B2 proposals. This gave 22 checks across 517 proposals and 1,537 eligible episodes. The learned rule's gain fell below uniform selection by ₹1.60/qtl per episode. Its paired interval ranged from −₹7.76 to ₹5.93. Seven nonoverlapping calendar blocks support that estimate, compared with 23 for the six-state cohort. Each of 5,000 bootstrap replicates resamples entire 14-day blocks and divides the paired incremental rupee sum by the resampled number of eligible episodes. The intervals condition on the fitted model and structural scoring assumptions.

Run `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m scripts.audit_contextual_verification` from a checkout with the rebuilt candidate tables. The [executable fit, routing and replay](../scripts/audit_contextual_verification.py), [full results](contextual-verification.csv) and [input hashes and model settings](contextual-verification-metadata.json) specify the experiment.

## Replacing the perfect signal with the released price forecast

The executable agent uses the same learned priority at the same daily budget. At a selected B2 proposal it evaluates the released 2024 point-return regressor. It vetoes a trip if the B2 margin plus the reference price times the predicted return falls to ₹100/qtl or below. The simple comparator gives those same daily slots to the smallest normalized surplus above the B2 hurdle. Both can cancel profitable modeled trips. They cannot redirect a truck to another market.

| Cohort and routing rule | Routing-model rows | Forecast-tool rows | Modeled losses vetoed | Profitable trips vetoed | Mean of modeled payoffs, ₹/qtl per eligible episode |
|---|---:|---:|---:|---:|---:|
| Six states, B2 | 0 | 0 | 0 | 0 | 446.66 |
| Six states, normalized margin | 0 | 4,175 | 950 | 943 | 449.42 |
| Six states, learned | 43,183 | 4,175 | 506 | 276 | 450.84 |
| HP apples, B2 | 0 | 0 | 0 | 0 | 1,150.83 |
| HP apples, normalized margin | 0 | 22 | 2 | 4 | 1,149.88 |
| HP apples, learned | 517 | 22 | 3 | 3 | 1,150.47 |

On the six-state test period, the actual forecast recovered ₹4.18/qtl per eligible episode relative to B2. The corresponding ceiling of ₹18.05/qtl assumes all losses on the chosen routes are known perfectly in advance. The learned and margin rules shared just 584 of their 4,175 checked proposals. Learned routing increased mean payoff relative to the margin ranking by ₹1.41/qtl. Its conditional loss-trip rate, 17.25%, exceeded the margin ranking's 16.64%. The HP estimate relative to B2 was −₹0.36/qtl; only 22 proposals received checks. No claim about better overall CPU cost follows from reduced point-model rows since the router must score every B2 proposal.

The paired 95% percentile interval for learned minus B2, crossing 174 origin markets with 23 fortnight blocks, is ₹1.92 to ₹6.94/qtl on the six-state cohort. For learned minus normalized margin, the same design gives −₹0.39 to ₹3.56/qtl. Resampling only time blocks narrows this latter interval to ₹0.17 to ₹2.79/qtl. Evidence of an incremental advantage over the simpler budgeted rule therefore depends on the dependence assumptions. On HP apples the crossed interval for learned minus B2 is −₹4.35 to ₹3.82/qtl.

The replay checked the model's input column allow-list, complete settlement of the router's training targets, equality of daily budgets and agreement between logged calls and actual predictor input rows. In both test panels, permuting episode order and replacing held-out outcome columns left the learned router's calls and vetoes unchanged. These checks establish separation of replay labels from decision inputs. They cannot establish the original portal publication time.

Run `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m scripts.audit_learned_forecast`. [Real-tool results and paired intervals](learned-forecast.csv) · [Forecast hash and leakage checks](learned-forecast-metadata.json) · [Executable policy](../src/agents/budgeted_forecast.py)
