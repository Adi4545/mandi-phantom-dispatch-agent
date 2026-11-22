# When Online Mandi Prices Mislead: A Retrospective Audit of Phantom Price Gaps and a Cautious Dispatch Rule for Indian Wholesale Markets

## Abstract

Farmers can see another mandi's price on a government portal before they hire a truck. That gap is not cash. This paper asks three questions about onion, potato, tomato, and apple in six Indian states. How often does a gap that looks attractive on yesterday's exact-variety quote lose money once freight, a statutory fee, reference spoilage, and a stated penalty for a missing arrival price are applied? Does a simple rule that refuses thin gaps reduce simulated losses relative to strong baselines? How much do the answers move when the missing-price penalty, the settlement rule, or the crop changes?

The test window is 1 June 2025 to 8 April 2026. There are 56,172 origin-days with a lagged exact-variety quote no more than seven days old and a gap above ₹100 per quintal. Chasing the largest such gap loses money on 41.47% of those trips. The mean is still positive (₹455.43 per quintal) because the wins are large. The worst 10% of episode outcomes average −₹530.85 per quintal (ES10).

A cautious rule keeps quotes that are one to three days old and dispatches only if the lagged gap minus road freight and the fee exceeds ₹200. The ₹200 cutoff was frozen on January–May 2025. On the test window it dispatches 73.73% of episodes, with mean ₹490.52, a 33.41% loss rate on the trips it takes, and ES10 −₹444.37. A fresh-quote road rule with a ₹100 cutoff dispatches a similar share (73.95%) but has a lower mean (₹432.41), a lower loss rate (30.82%), and a milder ES10 (−₹419.36). A more conservative road rule, with the cutoff frozen at ₹250, has the mildest ES10 in the table (−₹398.18) and a lower mean (₹424.23). The cautious rule raises average simulated net versus the road rules. It does not reduce the loss rate or ES10 versus those road rules.

Two further results bound the claim. Scoring the same chosen trips with hindsight — using a later exact price that the traveler could not have known when deciding to wait — lifts the screen-chasing loss rate from 41.47% to 26.57%. And ES10 moves by about ₹245 per quintal for the cautious rule when the missing-price return penalty goes from zero to 1.5 times freight. The loss rate barely moves. There is no untouched holdout beyond this split. An older same-day comparison of a heavier rule with the road heuristic was inconclusive (about +₹6 per quintal, interval crossing zero). Grade-explicit Himachal apples, in that older run, were a failure for the heavier rule. Live weather is not used: stored "forecast" rain matches realized ERA5 on 66% of the 2025–26 decision rows, and ERA5 is not a same-day public forecast.

Code and tables: `revision/build_run.py`, in commit `eef9c98938969354136be7396e6854e3abedf034`.

## 1. Three questions

Online portals such as AGMARKNET publish a modal price, a minimum, a maximum, and a variety name. A modal is not the price a named farmer is paid. A missing row is not a record that the market was closed. It is only the absence of an exact-variety price.

Research on market integration already treats a price gap as untradable when transfer costs are large \cite{baulch1997transfer}. Information alone does not move farmer revenue when the sale still depends on a trader or a truck \cite{fafchamps2012sms, mitra2018asymmetric}. Mandi forecasting papers predict the next price \cite{madaan2019price, ma2019price}. They do not score a dispatch under a missing quote. The narrow contribution here is a reproducible retrospective score of dispatch policies when variety-specific reports are incomplete, the settlement rule is explicit, and the downside is reported as well as the mean.

The questions are:

1. How often do attractive lagged gaps become unprofitable under the stated assumptions?
2. Does a simple risk-aware rule reduce simulated losses relative to strong baselines?
3. How do missing prices, information delay, and crop change that answer?

Everything after the pre-registered Stage I comparison in the previous draft is exploratory relative to that older protocol. This revision's thresholds were chosen on the 2025 validation months and then frozen. They were not part of the original four-hypothesis plan. No later period was held out.

## 2. Data, in one page

The price panel is the 178-market, four-crop extract for 2024 through 13 April 2026 (260,043 rows). Of these, 759 rows have a modal outside the published minimum and maximum. None have a nonpositive modal. There are 2,263 duplicate market-variety-grade-day keys, 1,489 of them with conflicting modals. Collapsing each key to a median modal leaves 257,747 rows. 4,793 episodes in the 2025–26 decision table touch one of those conflicting keys. The panel is a public archive mirror. A one-day official file and a 149-day Himachal apple export match the mirror on the keys checked earlier; they do not certify every row.

A decision on the morning of day \(t\) may use the farmer's own market that morning and any portal row dated \(t-1\) or earlier. It may not use the destination's price on day \(t\). The quote used here is the latest exact-variety modal on or before \(t-1\), and it is discarded if it is more than seven days old. Road kilometres come from a stored OSRM table. They are not the truck's actual route. Weather enters the primary score only as the 20°C reference behind the published 24-hour loss rates. A sensitivity uses each state's average 2024 weather by calendar month, which was known before 2025. Same-day ERA5, and the column stored as a forecast, are not treated as known: on the 752,456 decision rows in 2025–26, forecast rain equals realized ERA5 rain in 498,083 rows (66%).

## 3. The arithmetic, with one example

**Payoff.** Let the local modal be \(L\) and the sale price be \(S\). Freight including the state fee is \(F\). The spoilage fraction at the reference temperature is \(q\). Detention is ₹25 per quintal per extra day. If an exact-variety price is recorded and the lot is sold,

\[
\text{net} = S(1-q) - F - 25 \times \text{wait} - L.
\]

If no exact-variety price is recorded and another variety of the same crop is recorded, the model sells that other variety's minimum at a 10% discount. If nothing is recorded, the model charges a return:

\[
\text{net} = -1.5 F - L q - 25 \times \text{wait}.
\]

The 1.5 and the 10% are assumptions. Section 5 varies them.

**Example.** Maharashtra onion, \(L = 1500\), lagged destination modal \(2000\), road 100 km. The distance charge is \(35 + 0.45 \times 100 = 80\). The fee is 1% of 1500, which is 15, so \(F = 95\). Four hours on the road at the onion base rate 1.96% per day gives \(q = 0.0196 \times 4/24 = 0.00327\). Selling at 2000 gives

\[
2000 \times (1-0.00327) - 95 - 1500 = 398.5
\]

rupees per quintal. If instead no price is recorded at all, the 1.5-times return gives \(-1.5 \times 95 - 1500 \times 0.00327 = -147.4\). With the return multiple set to zero, the same trip scores \(-4.9\). The multiple does not create the loss. It changes how deep the loss is.

**Sequential settlement.** On the arrival day, sell if an exact-variety price is recorded. Otherwise, if any variety of that crop is recorded, wait one day and look again. Otherwise return. Do the same the next day, and once more on the second extra day. The rule never uses a price from a future day to justify today's wait. The hindsight convention does: it takes the first exact price within three days, including days the sequential rule would already have left. Hindsight is reported only as a comparison.

**Dispatch.** The cautious rule looks at candidates whose lagged quote is one, two, or three days old. The score is lagged modal minus local modal minus road freight and fee. It dispatches the best candidate if that score exceeds a margin. The margin was chosen on 1 January–31 May 2025 from the grid {0, 50, …, 400} as the value with the lowest loss rate among rules that still dispatch at least 25% of validation episodes. The frozen margin is ₹200. Ties would have gone to the higher mean. The test window was not used for that choice.

**Rates.** The dispatch rate is the share of episodes that send a truck. The loss rate is the share of those trucks with negative net. The mean is the average net over all episodes, with a refusal scored as zero (sell locally). Loss given loss is the average net on the losing trucks only.

**ES10.** Sort the episode nets from worst to best. Let there be \(n\) episodes. The worst 10% has mass \(m = 0.1 n\). Let \(k\) be the integer part of \(m\) and \(f\) the fraction left over. ES10 is the average of the \(k\) worst nets plus a weight \(f\) on the next one, divided by \(m\). For the eleven numbers 1 through 11, \(m = 1.1\), so ES10 \(= (1 + 0.1 \times 2) / 1.1 = 1.09\). The older "average of every point below the 10% quantile" can include a different share of the sample. Those older figures are withdrawn. They are not ES10.

**Interval.** The paired difference of means is resampled by origin mandi and by two-week block, 2,000 times, seed 20261117. The interval is the 2.5 and 97.5 percentiles of those draws. A second clustering, by the road rule's destination when it dispatched and by the origin otherwise, is a sensitivity. It is not a second confirmation.

## 4. Baselines

All rules see the same lagged shortlist: gap above ₹100, at most five destinations, exact variety, quote age at most seven days.

- **B1** sends the truck to the largest lagged gap. Inside this shortlist it always dispatches.
- **B2** uses only a quote from the previous day, subtracts road freight and the fee, and dispatches if the net exceeds a cutoff. The cutoff ₹100 is the simple version. The cutoff ₹250 was the validation choice that minimized the loss rate on the same grid idea as the margin (grid {100, 150, …, 500}, lowest loss rate, tie broken by the higher mean).
- **Cautious rule** is the age-1-to-3 rule with margin ₹200, described above.
- Replacing road kilometres with 1.2 times straight-line kilometres, or subtracting a 2024 climatological spoilage cost from the score, is an ablation. Neither is a new claim.

The older machine-learning and conformal rules are not the proposal. Their same-day comparison with B2 was inconclusive, and the pickled 2024 model does not load under a current scikit-learn (it was saved with version 1.3.0). This paper does not resimulate them.

## 5. Results

### RQ1. Attractive gaps

On the 56,172 test episodes, B1 loses money on 41.47% of trips. Mean net is ₹455.43 per quintal. ES10 is −₹530.85. Loss given loss is −₹261.59. So a gap above ₹100 on a lagged exact-variety quote is often still a loss under these assumptions, even though the average trip makes money. That 41.47% is not a count of closed markets. It is the share of simulated nets below zero.

### RQ2. Does the cautious rule reduce losses?

| Rule | Dispatch | Mean (₹/qtl) | Loss rate | ES10 | Loss given loss | Trucks |
|---|---:|---:|---:|---:|---:|---:|
| B1, largest lagged gap | 100% | 455.43 | 41.47% | −530.85 | −261.59 | 56,172 |
| B2, yesterday's quote, cutoff ₹100 | 73.95% | 432.41 | 30.82% | −419.36 | −271.18 | 41,541 |
| B2, cutoff ₹250 frozen on validation | 60.13% | 424.23 | 30.51% | −398.18 | −284.80 | 33,779 |
| Cautious, margin ₹200 | 73.73% | 490.52 | 33.41% | −444.37 | −279.24 | 41,417 |

The cautious rule and B2 at ₹100 dispatch almost the same share of episodes. The cautious mean is higher by about ₹58 per quintal on that point comparison. Against the validation-tuned B2, the paired mean gap is +₹66.29, with a 95% interval [+₹42.70, +₹94.14] under origin-by-fortnight resampling (2,000 draws). Clustering on the B2 destination instead gives [+₹39.31, +₹100.08]. Both intervals sit above zero.

The loss rate and ES10 point the other way. B2 at either cutoff has a lower loss rate and a milder ES10 than the cautious rule. The cautious rule therefore does **not** reduce simulated downside relative to the road rules. It buys a higher mean by accepting a worse tail. Against B1, the mean gap is +₹35.09 [+₹23.35, +₹48.11] and ES10 is milder (−₹444 versus −₹531), while B1's loss rate is worse.

Using straight-line distance instead of the road table changes the cautious mean from ₹490.52 to ₹490.35. Adding the 2024 climatology to the score changes it to ₹490.14 and moves ES10 from −₹444.37 to −₹435.84. Road-versus-straight-line and reference weather are not what the result hinges on. Live weather is omitted.

### RQ3. Missing prices, delay, and crop

**Settlement delay.** On the same chosen trucks, hindsight settlement — peeking at a later exact price — raises B1's mean from ₹455.43 to ₹624.11 and cuts its loss rate from 41.47% to 26.57%. The cautious loss rate falls from 33.41% to 16.08%. A paper that uses the hindsight convention will understate how often the traveler is stuck without a recorded price. The primary numbers in the table above are the sequential ones.

**Missing-price penalty.** The return multiple is applied only when no variety of the crop is recorded. Moving it from 0 to 1.5, with the other-variety discount held at 10%, leaves loss rates essentially unchanged (cautious loss rate stays 33.3–33.4%; B1 stays 41.3–41.5%). Means fall for every rule, and the order cautious > B1 > tuned B2 on the mean does not flip inside this grid. ES10 does move. For the cautious rule it goes from −₹198.93 at a zero return multiple to −₹444.37 at 1.5. For tuned B2 the same step is −₹152.00 to −₹398.18. The depth of the bad tail is an assumption. The loss rate, in this range, is not. The older same-day study did find a mean ranking that flipped when the penalty was removed entirely. That flip is not repeated in this lagged, sequential design. Both facts should be stated. Neither is a field measurement.

**Crop and state.** The cautious mean exceeds the tuned B2 mean in every crop and every state in the test window. The gap is ₹11 on onion and ₹367 on apple, and ₹1.70 in Madhya Pradesh versus ₹207 in Himachal Pradesh. ES10 is worse for the cautious rule than for B2 in five of six states. Maharashtra is the exception, and only barely (−₹396 versus −₹398). These slices were not a pre-registered family. They are descriptions.

**Same tail, fewer trucks.** The risk-coverage sweep raises the cautious margin from ₹0 to ₹800. ES10 moves from −₹473 to −₹345, and the mean falls from ₹489 to ₹411. The tuned B2 ES10 of −₹398 is matched by the cautious rule only at a margin near ₹500, where dispatch is about 50% and the mean is ₹459. Matching the road rule's tail means giving up the dispatch rate at which the mean advantage showed up. That is the tradeoff in one curve (`revision/results/risk_coverage.csv`).

**Grade-explicit apples.** The new table does not split Himachal apple grades. The older grade-explicit holdout, which this revision did not resimulate, had the heavier rule at about ₹605 per quintal and 19% dispatch against a road rule at about ₹1,151 and 34% dispatch. That failure stands. It is not repaired here.

## 6. What this does not show

The nets are not farmer receipts. Freight, spoilage, the other-variety discount, and the return multiple are a model. Refusing a trip scores zero, which is "sell at the local modal," not a measured local sale. ES10 includes those zeros, so a rule that stays home looks safer than its dispatched trucks alone. The validation months and the test months are the only 2025–26 split available; Stage II of the older draft already used the test months, and this revision uses them again for a simpler rule. There is no untouched holdout. Duplicate conflicting quotes were median-collapsed, and 4,793 episodes touch those keys. The interval is a cluster bootstrap, not a guarantee under dependence we did not model.

The defendable sentence is this. Under an explicit sequential settlement and a lagged exact-variety quote, a large share of attractive portal gaps lose money in the model; a margin rule raises the average simulated net relative to a yesterday's-quote road rule at a similar dispatch rate; and that same road rule still has the better loss rate and the better ES10. Changing the missing-price penalty changes the tail by hundreds of rupees per quintal and does not, in the grid above, overturn the mean ordering.

## References

The bibliography is `paper/references.bib`. The load-bearing citations for this revision are Baulch (1997), Fafchamps and Minten (2012), Madaan et al. (2019), Ma et al. (2019), and Mitra et al. (2018).
