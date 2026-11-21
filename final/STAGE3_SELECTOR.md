# Could a trained policy decide when to override B2?

A depth-three regression tree learned when to accept the B2 fresh-price-and-road proposal or sell locally. Its eight estimated dispatch values were all positive. The learned selector therefore retained every B2 decision in the six-state and graded-apple evaluations. For these modeled returns the selector added complexity without changing the action.

## Decision and training

B2 ranks screened destinations by headline spread, considers five, and proposes the fresh exact-key destination with the highest net margin if that margin exceeds ₹100/qtl. The selector estimates the incremental return on the proposed trip. It accepts a positive estimate and otherwise sells locally for zero incremental return. It reads the board and cached road attributes. There is no new weather lookup, call to a buyer, or arrival-price inquiry. Availability of the historical final daily quotes by a particular dispatch time remains unverified.

Only the predetermined board, freight and reporting-history variables are eligible for inference. The seven features are the fresh net margin, origin modal price, road distance, trailing reporting frequency, historical reporting frequency on the arrival weekday, trailing price volatility and trailing within-day price spread. The two frequency fields refer to price reports. An explicit inference command reads only the board columns from Parquet.

We fixed maximum depth at three, the minimum training leaf at 250 and squared-error loss before inspecting either set of results. The target was the modeled per-quintal payoff for the B2-selected route less the local alternative's zero incremental score. Of 96,821 shortlisted 2024 training episodes, 60,210 had a B2 dispatch with its entire three-day scoring window complete by 31 December 2024. Each has both simulator action values, including the published fallback for an unreported destination quote. Training and feature-median estimation used these dispatches only. Selection used no 2025 or 2026 labels. No validation search or test-time adaptation was used.

The fitted leaf means range from ₹102.56 to ₹6,022.50/qtl. Six of the seven splits use the net margin, and the seventh uses trailing reporting frequency. Positive means in each leaf explain why a zero-threshold expected-return rule accepts every proposed trip, including trips whose individual simulated payoff later turns out negative.

## Paired evaluation

| Cohort | Shortlisted episodes | B2 and selector dispatches | Negative modeled dispatches | Mean for either policy, ₹/qtl per episode | Selector minus B2 | 95% paired cluster interval |
|---|---:|---:|---:|---:|---:|---:|
| Six states | 69,526 | 43,183 | 7,820 | 446.66 | 0.00 | [0.00, 0.00] |
| HP grade-explicit apple | 1,537 | 517 | 147 | 1,150.83 | 0.00 | [0.00, 0.00] |

Within each of 5,000 replicates, we resampled origin markets and Monday–Sunday origin-date weeks independently with replacement. We weighted each paired episode difference by the product of its market and week multiplicities. The six-state panel has 174 origin markets and 46 weeks. The HP panel has 39 origin markets and 13 weeks. Every paired difference is identically zero. The resulting point intervals follow algebraically from identical actions. They provide no evidence of certainty about either policy's return in new markets, under different market conditions or in the field.

The B2 route and payoff were independently checked against the implementation for every sampled episode. Scoring the saved tree from the board alone also matched B2 on all 3,923 shortlisted HP apple episodes, including the pre-evaluation portion. The test sets were previously inspected. This post-diagnostic experiment supports a limited decision about model complexity and supplies no independent confirmation of a generalization or welfare claim.

## Reproduction

From the repository root, after rebuilding the six-state candidates, run the experiment and, optionally, score a board without outcome labels. The second command writes its output to the current directory.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/stage3_policy_selector.py
python scripts/stage3_policy_selector.py --score-board data/processed/candidates_hp_apple_grade.parquet --decisions-out stage3-choices.csv
```

[Unrounded results](stage3-selector.csv) · [Frozen tree, split thresholds, training statistics and data hashes](stage3-selector-model.json) · [Training, crossed bootstrap and outcome-free inference](../scripts/stage3_policy_selector.py)
