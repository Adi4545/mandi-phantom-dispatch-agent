# Which destination supplied the arrival quote?

Four historical baselines selected the highest-scoring destination with pandas GroupBy.first. This takes each column's first *nonmissing* value separately. A dispatch to market A could therefore receive market B's arrival-day payoff whenever A's day-zero quote was missing. The repair retains the entire winning row after sorting by the same score and market-name tie-break. Every dispatched record in the replay was joined back to its unique episode and destination, and checked against both modeled payoffs.

| Cohort | Rule | Dispatches | Day-zero payoff on selected route | Historical cross-route fills | Historical → corrected day-zero mean (₹/qtl) |
|---|---|---:|---:|---:|---:|
| Six states | B1 | 63,040 | 25,882 | 22,940 | 606.71 → 685.16 |
| Six states | B2 | 43,183 | 32,679 | 6,618 | 467.48 → 461.62 |
| Six states | B3 | 64,695 | 22,224 | 23,995 | 676.67 → 828.97 |
| Six states | B6 | 30,145 | 23,637 | 4,553 | 430.65 → 416.42 |
| Himachal Pradesh apples | B1 | 1,537 | 90 | 661 | 3,471.46 → 8,350.03 |
| Himachal Pradesh apples | B2 | 517 | 341 | 21 | 1,156.79 → 1,109.92 |
| Himachal Pradesh apples | B3 | 1,537 | 42 | 443 | 4,351.62 → 16,997.66 |

The day-zero mean includes abstentions at zero and dispatches with a report for the chosen variety on arrival. Its denominator differs by policy. B3's apple figure, for example, uses 42 of 1,537 episodes. Comparing these means across policies can conflate coverage and realized scenario payoff. Five apple policy–grade cells lack any eligible episode. Their means are now blank in the CSV. All remaining published Exp 2/3 summary fields for the affected baselines reproduce under the historical tail convention. The separate expected-shortfall correction also changes the reported tail column.

The main matched sensitivity selects episodes whose five highest screen spreads have reported arrival prices. A policy that reorders a larger candidate pool can choose outside those five. In the day-zero cohort, B1 sent 14 of its 7,599 dispatches outside that set and eight had no day-zero quote. In the three-day cohort, B1 sent 26 of 13,723 outside and nine lacked a quote across all three dates. The final Stage-II policy chose 39 of 5,631 destinations outside the qualifying five and lacked one selected day-zero quote. B2, B3, and Stage-I MandiGuard stayed within the five and had a day-zero report for each selected destination. The two independent Stage-II replays produced byte-identical validation and bootstrap tables. These counts qualify the original interpretation of a completely observed cohort. The historic selection rules are preserved.

## Reproduction

Use a checkout that includes commit d20a0cb25827b73688e4ced19948ac5c01e49f6b, the rebuilt six-state candidates, the supplied apple panel, and a compatible frozen point forecaster. Run these commands from its root.

```sh
python -m pytest -q tests/test_route_selection.py
python -m scripts.audit_selected_routes
python -m src.evaluation.run_mechanistic_autopsy_and_crc
```

The first audit writes all policy–grade denominators to results/selected_route_integrity.csv and the B1 matched-scope counts to results/exp15_matched_b1_route_audit.csv. The Stage-II command writes the matched top-five selection and quote counts for all seven policies to results/exp17_matched_route_audit.csv. Full production Exp 2/3 outputs are in results/exp2_main_benchmark_6state.csv and results/exp3_hp_apple_grade_holdout.csv.
