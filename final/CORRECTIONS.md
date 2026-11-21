# Correction record for the dispatch evaluation

Historical reference revision: `d20a0cb25827b73688e4ced19948ac5c01e49f6b`. The revision builds on the unmerged finalization branch at `b399358`. Use [the revised paper](../paper/manuscript.md) for the research claims. The former paper, built notebooks, PDFs and previous reviews document the historical analysis.

## 1. Which route had an arrival-day quote?

Sorting routes and applying pandas GroupBy.first could take the destination from the first row and a nonmissing diagnostic from a later row. The revised selectors retain one complete row per episode. The replay matches dispatched rows back to the candidate table on both episode ID and chosen destination. For the day-zero diagnostic, a local-sale episode contributes zero, a dispatch with a reported arrival-day quote contributes its modeled payoff, and a dispatch without one is excluded. This diagnostic has a policy-specific denominator. It cannot establish an unbiased comparison between policies.

Across six-state B1 dispatches, 22,940 missing diagnostics had been filled from another route. In graded HP apples, 661 B1 dispatches were affected and only 90 of 1,537 chosen routes had an observed arrival-day diagnostic. The changes affect the interpretation of the day-zero summaries. [Chosen-route audit and matched-cohort exceptions](SELECTED_ROUTE_AUDIT.md) · [Policy and grade-level denominators](../results/selected_route_integrity.csv)

## 2. How bad were the worst episodes?

Order all finite episode payoffs from smallest to largest. If there are 1,537 episodes, average the worst 153 plus 0.7 times the 154th, dividing by 153.7. Taking all episodes tied with the 10th percentile lets zero-payoff abstentions dilute the result. On the HP apple cohort, correcting this changes B2 from −₹272.50 to −₹2,069.03 per quintal and v1 from −₹102.76 to −₹876.47. These are episode-level lower-tail means, expressed as signed payoffs. The correction changes an evaluation statistic after the dispatch decision.

On the six-state holdout, v1 changes from −₹37.89 to −₹212.93. B2 is −₹436.69 and Stage II is −₹223.19. Thus Stage II scores higher on average than v1 but has a more negative lower tail. [All 42 comparisons](exact-decile-audit.csv) · [Metric and replay](TAIL_RISK.md)

## 3. Could the decision have used that day's weather?

The archive offers no cycle or issue timestamps to establish morning availability. A control assigns 20 °C, 70% relative humidity and zero rainfall to every decision, leaving the settlement weather and missing-price rules intact. The fitted policies and risk multiplier stay fixed within the comparison. On the six-state holdout, v1's modeled mean moves from ₹452.79 to ₹454.61 and its losing-trip share rises from 9.97% to 10.42%. Stage II's mean moves from ₹479.17 to ₹480.17 and its losing-trip share rises from 10.48% to 10.95%. B2 remains at ₹446.66. This sensitivity removes dependence on contemporaneous weather in the decision inputs. Real-time efficacy would require archived forecast vintages and timestamped market quotes. [Method and HP results](DECISION_WEATHER_CONTROL.md) · [Paired replay](decision-weather-control.csv)

## Reproduction

Use a full Git clone for the historical-row comparison. From its root, create a Python 3.11 environment and run the following with several GB of free memory and sufficient temporary disk space. The experiment runners write to the results directory, so use a disposable checkout to replay the historical protocol.

```sh
python -m pip install -r environment/requirements-replay.txt
export PYTHONPATH=. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python -m src.data.build_dispatch_episodes
python -m src.evaluation.run_all_experiments
python -m src.evaluation.run_official_parity_and_open_yard_sensitivity
python -m src.evaluation.run_mechanistic_autopsy_and_crc
python -m scripts.audit_selected_routes
python -m scripts.decision_weather_control
python -m pytest -q tests
```

The rebuilt six-state candidate parquet has SHA-256 `ea5ac38a90bb764aa659565935085c56aacab4302c2d67a8f053618fd0377aa2`. Git history distinguishes the original experiment outputs from this revision. The historical CVaR fields in unreplayed appendix tables, figures and older educational materials should be excluded from new quantitative claims. Comparisons on the previously inspected holdout remain retrospective.

[Independent review of these corrections](reviews/corrections-qa.md)

The final suite passed 30 tests on Python 3.11.5. The input, configuration and core output digests are recorded in [the replay manifest](replay-environment.json). The released pickle loaded with scikit-learn 1.3.0. The compatible environment was exercised locally; a new hosted Colab runtime was not used for this correction.
