# MandiGuard defense slides

1. **Research question.** A portal lists two prices. Can a rule choose whether to dispatch when the quote that will matter is the one available on arrival?
2. **Evidence.** Six states, four crops, 178 retained markets. Explain what a market reported, what the simulator derived, and which settlement assumptions enter an unquoted arrival.
3. **Policy.** Start with the local-sale option. Check variety and reporting frequency, subtract road costs, account for weather-related quality loss, then apply the forecast cushion. Each check can end a candidate's evaluation.
4. **Matched decisions.** Compare each policy on the same 69,526 shortlisted episodes. Report mean payoff per episode and the share losing money among dispatched trips. The denominators differ.
5. **Primary result.** MandiGuard v1 gained ₹102.78/qtl over stale screen chasing. Against B2 the difference was ₹6.13/qtl, with a 95% interval of −₹17.02 to +₹25.02. H2 remains unsupported.
6. **Downside and trade-offs.** Show [the corrected figure](../figures/corrected_benchmark.png). In graded apples B2 had the higher mean and the deeper downside.
7. **Arrival-day diagnostic.** Sorting candidates previously allowed a quote from a lower-ranked destination to enter the selected row. Only 90 of 1,537 naive apple dispatches had their own usable arrival-day observation.
8. **Weather.** Substituting fixed decision weather changed 1,058 six-state v1 decisions or destinations. Its conditional loss rate increased from 9.97% to 10.42%. The archive cannot establish forecast issue time.
9. **Stage II.** A validation-calibrated score was developed after holdout inspection. The redesigned rule reached 10.48% losing trips on the same holdout against a 9.5% target. Independent prospective validation remains open.
10. **Field study.** Freeze the policies, record decision-time quotes and forecasts, verify arrivals and collect actual receipts and costs. A comparison group is required to estimate farmer benefit.
