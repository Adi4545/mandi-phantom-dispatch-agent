# How much can a simple mandi decision rule establish?

Four exploratory experiments reused the six-state evaluation set (69,526 shortlisted episodes) and the Himachal graded apple set (1,537). No experiment trained a model, changed the deployed architecture, or contacted buyers. B1 is the stale screen-price rule and B2 uses fresh variety quotes and road costs. Monetary quantities below are simulated incremental payoffs in rupees per quintal. The same episode set is used within each comparison.

## A break-even value for missing prices

Let a be an additive change to the modeled payoff of each dispatched route that lacks an exact-variety quote on arrival and both following days. Hold the decisions and all other payoffs fixed. In six states the difference in B1 and B2 means is −96.652 + 0.386201a. The slope is (29,433 − 2,582) / 69,526 because B1 selects many more unquoted trips. The mean ranking reverses at **+₹250.26/qtl**. In apples the corresponding threshold is **+₹351.57/qtl**. These offsets measure how sensitive the ranking is to the assumed settlement. Their plausibility needs buyer or receipt data. They do not estimate missing sale prices. The CSV also gives bounds for route-specific perturbations. [Results](payoff-crossover.csv)

## One extra rule: refuse older headline prices

Keep B1's chosen destination and sell locally if the commodity headline quote is more than one calendar day old. In six states this vetoed 7,605 dispatches, of which 4,798 would have lost and 2,807 would have gained under the simulator. Loss among dispatched trips fell from 40.46% to 37.36%, while gain per shortlisted episode fell from ₹350.01 to ₹340.84. The paired difference versus B1 was −₹9.16 (exploratory 95% cluster-bootstrap interval −₹19.20 to +₹0.03). B2 averaged ₹446.66. In apples the veto reduced the mean from ₹841.58 to ₹783.52. These observations support reporting the trade-off and retaining the original policies. [Results and denominators](freshness-rule.csv)

## A known one-day reporting gap

For each fixed selected route with exact quotes on consecutive arrival days, hide the first quote at settlement and rescore against the second. The day-one quote remains available in each focal perturbation. The policy still chooses from the original decision information. On affected six-state dispatches the modeled mean fell ₹243.09 for B1 and ₹237.32 for B2. Across the full episode set, B2's lead over B1 narrowed from ₹96.65 to ₹79.38. In apples it narrowed from ₹309.25 to ₹172.60; only 54 B1 apple dispatches were eligible for the perturbation. These shifts include the simulator's waiting and spoilage charges. The exercise identifies what the scoring rule does to a known gap. Genuinely unreported sales can differ. [Payoff components and sign changes](one-day-gap.csv)

## Is there a case for a buyer-verification step?

Start with B1 dispatch proposals. Each day's batch gets one hypothetical check per ten proposed trips, rounded down. Compare allocating those checks at random, to the oldest exact-variety quotes, or to the smallest estimated B1 margins. Average across ties at the daily cutoff. To establish an upper bound for each allocation, give each check perfect knowledge of the modeled trip payoff and let it veto every losing trip at zero cost. The oracle used to score the check would be unavailable in practice. It only allows canceling the original trip, with no rerouting. A fourth, hindsight-only priority selects the greatest losses as a ceiling.

| Call allocation | Six states: ceiling gain per episode | HP apples: ceiling gain per episode |
|---|---:|---:|
| Uniform random | 15.74 | 118.15 |
| Oldest exact-variety quote first | 25.98 | 120.06 |
| Smallest predicted screen margin first | 16.43 | 301.06 |
| Greatest realized modeled loss first (hindsight) | 98.40 | 432.38 |

There were 6,163 and 112 hypothetical slots respectively. The historical cohorts favor different priorities. No call was placed. The batch design assumes the day's proposals can be compared together. These figures cannot establish the return to phoning a buyer, since their information could be incomplete and time and calls have costs. [Full results](verification-budget.csv)

## Research decision

Retain the existing decision architecture. Add the missing-price crossover as a diagnostic beside each baseline comparison. It answers a question a supervisor or examiner can audit directly: how large a change in the settlement assumption would reverse the ranking? The increment is empirical; the affine sensitivity calculation is elementary. A prospective buyer check would test whether real missing-quote outcomes fall on either side of these thresholds. All four experiments used previously inspected cohorts.

## Replay

From the corrected repository root, use the Python 3.11 replay environment and the rebuilt six-state candidate table documented in CORRECTIONS.md. Run:

```sh
export PYTHONPATH=. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python -m scripts.audit_payoff_crossover
python -m scripts.audit_freshness_rule
python -m scripts.audit_one_day_gap
python -m scripts.audit_verification_budget
```
