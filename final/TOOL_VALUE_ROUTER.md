# Learning when a forecast is worth running

A forecast can veto a profitable dispatch as well as a loss. We trained a shallow tree to predict the signed change in modeled return caused by consulting the fixed 2024 price forecaster on a B2-proposed trip. If the forecast lowers the projected road-adjusted margin to ₹100/qtl or less, the policy sells locally. In that case the training label is the negative of B2's trip payoff. Otherwise the label is zero. This target distinguishes the value of consulting this particular tool from the loss an all-knowing verifier could avoid.

Training used 26,566 B2-proposed dispatches from January–May 2025 whose full three-day settlement window ended by 31 May. The fixed forecaster would have vetoed 1,921 trips. Of these vetoes, 981 would have prevented a modeled loss and 940 would have given up a positive modeled payoff. Each action's value uses the same missing-price scenarios as the main study. The forecaster reads historical price features and returns an estimated arrival-price change. The router can see relative hurdle margin, net margin, local price, road distance, trailing reporting frequencies, volatility and within-day spread before allocating a call. Median imputation uses training values only. The regression tree was fitted once with maximum depth three and minimum leaf size 250. No candidate architectures, budgets or thresholds were searched.

Within each date, the learned router selects the highest predicted signed values up to exactly one tenth of B2 proposals, rounded down. Ties are settled by episode ID. The margin policy spends the same budget on the smallest normalized margins. Only selected proposals receive a price forecast in either policy. The uniform random benchmark draws the same number from that day's proposals. Its expected payoff integrates exactly over equal inclusion probabilities. The separate evaluator obtains the required deterministic forecasts through budget-respecting cyclic batches, memoizing answers from selected rows. It queried 43,183 distinct six-state proposals and 275 HP proposals across all counterfactual random allocations. The learned and margin policies each executed only 4,175 and 22 forecast-row evaluations on the respective panels.

| Panel and comparator | Learned minus comparator, ₹/qtl per shortlisted episode | Paired 95% cluster interval |
|---|---:|---:|
| Six states, B2 | +2.33 | [0.32, 4.71] |
| Six states, low margin | −0.44 | [−2.39, 1.50] |
| Six states, expected uniform random | +1.67 | [−0.13, 3.77] |
| HP apples, B2 | −0.98 | [−4.89, 0.00] |
| HP apples, low margin | −0.02 | [−2.55, 2.21] |
| HP apples, expected uniform random | −1.47 | [−5.85, 0.13] |

On 69,526 six-state episodes the router vetoed 504 proposals, versus 1,893 for low-margin ranking. The mean modeled returns were ₹448.99 and ₹449.42/qtl respectively. On 1,537 HP apple episodes the router vetoed one trip, with a mean of ₹1,149.85/qtl. The margin policy vetoed six and averaged ₹1,149.88/qtl. The exploratory intervals resample origin markets and 14-day date blocks independently 5,000 times. The intervals with the random comparator describe differences against its exact conditional mean over allocations. The analysis assumes a common daily batch and no marginal monetary cost for running the offline price model. Portal revisions, selective reporting, score-model assumptions and prior inspection of these cohorts continue to limit interpretation.

**Conclusion.** The signed routing target is implementable without observing the trip outcome at decision time. This evaluation provides no evidence of a mean advantage over same-budget margin ranking on either panel. The small main-panel advantage over B2 alone does not justify replacing the simpler budgeted policy. No additional model was selected after observing this result.

Run `python -m scripts.tool_value_router` from repository root after rebuilding the candidates. Run `python -m pytest -q tests/test_tool_value_router.py` to check budgeted selection and exact random expectations.

[Policy results](tool-value-router.csv) · [Paired comparisons](tool-value-router-contrasts.csv) · [Training statistics, fitted rules, input hashes](tool-value-router-metadata.json) · [Reproduction script](../scripts/tool_value_router.py)
