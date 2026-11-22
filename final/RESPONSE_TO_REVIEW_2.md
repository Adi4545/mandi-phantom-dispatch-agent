> **Archival Note (Pre-Revision v5 Review-2 Response):** Preserved for git history completeness (`R8`). Every internal gap listed here (`N = 56,172`, lagged HP apples, `make reproduce`) was rebuilt and superseded by **Revision v5** (`Safe_EV_Sunk_m0`, `RT_2F_Min_m0`, `8.7/10`) — see `final/RESPONSE_TO_REVIEW_3.md`, `final/AUDIT_V4.md`, and `paper/manuscript.md`.

# Response to the external review (6.5/10, major revision)

The review described a paper that cited `revision/build_variant.py`, `build_run.py`, `eval_run.py`, and `revision/results/`, and a table with about 67,675 episodes and means MG ₹397.24, B2 ₹371.38, B2-matched ₹367.07, B1 ₹301.22, B3 ₹246.67. Those files and those rupee figures were not on `main` or on `finalization`. They are not treated as results. The files now in `revision/` are a new lagged replay. The paper cites that replay. The tables were produced in commit `eef9c98938969354136be7396e6854e3abedf034`.

## P0

1. **Reproducibility.** The cited revision was absent. It was rebuilt rather than invented to hit ₹397.24. The test set that survives a seven-day lagged exact-variety quote and a ₹100 gap has **56,172** episodes (1 June 2025–8 April 2026), not 67,675. Primary sequential, no-live-weather numbers: B1 mean ₹455.43, loss rate 41.47%, ES10 −₹530.85; B2 at cutoff ₹100 mean ₹432.41, loss rate 30.82%, ES10 −₹419.36, dispatch 73.95%; validation-tuned B2 at ₹250 mean ₹424.23, loss rate 30.51%, ES10 −₹398.18; cautious rule mean ₹490.52, loss rate 33.41%, ES10 −₹444.37, dispatch 73.73%. The 2024 forecaster pickle still does not load (scikit-learn 1.3.0, no Python 3.12 wheel). Old B3/B4 and Exp 15–17 were not resimulated. That is a remaining block, and the simplified paper does not depend on them.

2. **Decision-time information.** On 752,456 decision rows in 2025–26, the stored forecast rain equals realized ERA5 rain in 498,083 rows (66%), and humidity matches in 370,328 (49%). The review's 99,858/99,858 identity was not reproduced on this table; the leak is still real because ERA5 is not a morning forecast. The primary policy uses no live weather. A 2024 state-month climatology changes the cautious mean from ₹490.52 to ₹490.14. Prices used to choose the truck are exact-variety modals dated on or before the day before departure, age at most seven days.

3. **Settlement.** Sequential sell / wait / return uses only that day's record. Hindsight, which may use a price one or two days later, cuts the B1 loss rate from 41.47% to 26.57% and raises its mean from ₹455.43 to ₹624.11. The paper's main table is sequential.

4. **Missing prices.** The wording in the new paper is "no exact-variety price recorded." A grid over return multiples 0, 0.5, 1.0, and 1.5 and other-variety discounts 0, 5%, and 10%, by crop and by state, is in `revision/results/missing_sensitivity.csv`. Loss rates barely move. ES10 for the cautious rule moves from about −₹199 to −₹444. The mean order does not flip inside this grid. The older same-day design did flip when the penalty was removed; that negative result is kept as a statement about the older design, and it is not claimed again for this one.

5. **Baselines.** B2's cutoff was chosen on the validation months (lowest loss rate on a fixed grid). The frozen cutoff is ₹250. The cautious margin was frozen at ₹200 by the same kind of rule. Risk-coverage curves sweep both knobs from ₹0 to ₹800. At a matched dispatch near 74%, the cautious mean is higher and the loss rate and ES10 are worse than B2 at ₹100.

6. **ES10.** `revision/es10.py` uses exact 10% mass and a fractional boundary. Tests cover an integer tenth, a fractional boundary, and a case that differs from the old quantile mean. The manuscript, README, and the viva sheet use this definition. Older `cvar_10_inr` columns remain in historical CSVs as a deprecated estimator; a banner says they are not ES10.

## P1

- **T1+T4 versus road and weather.** Swapping the road table for 1.2× straight-line distance changes the cautious mean by ₹0.17. Adding 2024 climatology to the score changes ES10 by about ₹9. Live weather stays out. Road distance stays in the payoff because it is the stored route, not because it moves the mean.
- **Crop and state.** `revision/results/by_crop_state.csv`. The mean gap is positive in every slice. ES10 favors B2 in five of six states. These slices are descriptive.
- **HP apples.** Not resimulated under the lagged settlement. The stored grade-explicit result still has the heavier rule far below the road rule (about ₹605 versus ₹1,151). The new non-grade apple slice has a worse ES10 for the cautious rule (−₹1,078) than for B2 (−₹951).
- **Cleaning counts.** `revision/results/cleaning_counts.json`: 260,043 panel rows, 0 nonpositive modals, 759 modals outside min/max, 2,263 duplicate keys (1,489 conflicting), 257,747 retained key rows, 4,793 episodes touching a conflicting key.
- **Clustering.** Origin × fortnight and B2-destination × fortnight intervals for the mean gap versus tuned B2 both lie above zero (`revision/results/bootstrap.csv`). This is one contrast, not a new family of tests.
- **Post-hoc label.** The validation/test split is the only one available. The paper says there is no untouched holdout. The older Stage I H2 result (interval crossing zero) is unchanged.

## What the revision refuses to say

The cautious rule does not reduce simulated losses relative to the road rules. It raises the mean and worsens the tail. Hindsight is not the main result. The review's ₹397 table is not a result of this repository.
