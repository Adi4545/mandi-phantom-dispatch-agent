> **Archival Note (Pre-Revision v4 Log):** This snapshot records an earlier pre-v4 audit baseline prior to `final/AUDIT_V4.md` (`8.4/10`, clean-clone rebuild, `M9` statutory fee-base fix, and `RR-Abstain` `A10`). For canonical Revision v4 results, see `final/AUDIT_V4.md` and `paper/manuscript.md`.

# Audit report

## Environment and coverage

- HEAD at audit start: `d20a0cb25827b73688e4ced19948ac5c01e49f6b`.
- Branch: `finalization`.
- Python 3.12.3. First pytest run: 22 passed. After new tests: 23 passed (`results/pytest_execution.log`).
- Decade panel: 883,406 rows, 178 markets, 6 states, 4 commodities, 2017-01-01 to 2026-04-13. SHA matches the manifest. Manifest raw-row sum is 42,722,187.
- Episodes: 239,809 total, 209,450 shortlisted; holdout episode file has 81,048 rows and 69,526 shortlisted, 174 origins. SHA matches.
- OSRM matrix: 8,147 corridors, 15.19–499.43 km.
- Official XML SHA and HP-apple CSV SHA match `official_datagov_parity_manifest.json`.
- `candidates_6state.parquet` is gitignored. Rebuild: 1,457,515 rows, 209,450 shortlisted episodes, episode frame equal to the tracked file, byte SHA not equal to the manifest.

## What was recomputed

- Exp 14: rerun, CSV unchanged.
- B1 and B2 on all 69,526 holdout episodes: published means, dispatch rates, conditional loss rates, trap rate, three-day absence rate, and CVaR match within ₹0.02. See `results/finalization_recompute.json`.
- B1 outcome types: `results/exp1b_b1_outcome_types.csv`.
- Exp 18, B1/B2 only, split at 2026-02-12: `results/exp18_used_holdout_temporal_slice.csv`. Early (`N = 59,640`): B2 − B1 = +₹131.42. Late (`N = 9,886`): B2 − B1 = −₹113.06. Full: +₹96.66, percentile cluster p ≈ 0.0012, basic p ≈ 0.0022. This contrast was not pre-registered.
- Not recomputed: MandiGuard, B3, B4, conformal coverage, Exp 10–13, Exp 15–17. Blocker: pickle requires scikit-learn 1.3.0.

## Data and economics

Observed: portal min/max/modal and whether a row exists; stored OSRM kilometres and hours; ERA5 and NASA POWER grids; published fee schedules and the NABCONS loss rates as documents.

Derived: 7-day forward-filled screen board, median when duplicate keys conflict, episode shortlist, model scores.

Assumed counterfactuals: ₹35 + ₹0.45/km (×1.45 on HP km), Q10 spoilage from the 24h base rates, ₹25/qtl per wait day, 10% other-variety discount, 1.5× freight when the chosen non-quote branch fires, fee rate times the **local** modal.

A missing price is not a closed market. The portal modal is not a farmer’s net realization. The exercise is a model-based retrospective comparison of decision rules on identical episodes. It is not an estimate of income gained in the field.

Weather in the decision uses `route_fc_*`. Weather in the payoff uses realized ERA5 over the trip. That is a timing split inside a model, not an identified causal effect of weather.

## Statistics

- CVaR_10% is the mean of episode outcomes at or below the sample 10% quantile. Abstention is 0, so the tail of a selective rule is not the tail of dispatched trips only.
- Stage I p-values count bootstrap replicates on the wrong side of 0 (percentile interval inversion) and apply Holm to four tests. They are not null-recentered. Stage II p-values are outside that family.
- Baselines that were rerun (B1, B2) use the same episodes and the same payoff function. B1’s freight is the Euclidean proxy inside its own rule; B2 uses the stored road kilometres. That difference is the definition of the baselines, and it is the right comparison for H2 only if it is described that way.
- H2 remains the stored result NOT_SUPPORTED. Nothing in this audit rescues it.
- The late-window reversal of B2 versus B1 shows the full-period road-heuristic advantage is not uniform. It does not create a new confirmed hypothesis.

## CRC

Angelopoulos et al. (ICLR 2024) Theorem 1 does not apply: the panel is not exchangeable, and the loss rate is conditional on a λ-dependent dispatch set. The implemented rule is an empirically calibrated risk gate. A code path that scored “never dispatch” as risk 0 was corrected; the stored validation row for λ = 0.15 still shows dispatch, so that bug is not why λ = 0.15 was chosen.
