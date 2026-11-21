# Weather availability and the dispatch decision

Existing results used day-of-decision weather columns with uncertain issue times. The national grid audit found 99,858 of 99,858 historical NWP records with rainfall and humidity equal to the corresponding realized values. In 43 additional cells a proxy consumed same-day realized ERA5. The source comparison is in `final/weather-and-apple-checks.json`. ERA5 is generally published about five days later, and its final version can change after the initial release. The historical forecast endpoint stitches near-term hours from successive runs. A daily summary therefore needs an issuance-time audit before operational use. [Copernicus ERA5](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries) · [Open-Meteo historical forecasts](https://open-meteo.com/en/docs/historical-forecast-api)

For this exploratory control we set every decision-time maximum temperature to 20 °C, humidity to 70%, and rainfall to 0 mm. These are the reference temperature, onset of excess humidity, and absence of rain in the original payoff formula. The resulting spoilage estimate still varies by commodity and travel time. These constants require no measurements. They represent a reference-weather decision rule and do not estimate the weather at a market.

The comparison uses the same shortlists, episode IDs, road and price inputs, learned policies, safety margin and scenario payoffs across the two arms. B2 uses no weather. Stage I reads the committed fitted arrival-price model, and makes point and lower-bound predictions before substituting decision weather. Its feature list excludes the weather inputs. The model updates its rolling residuals by the original date-based rule in both arms. Stage II has no fitted artifact in the original repository. We refit its historical 2024 training recipe once using the original weather, retain those fitted trees for both arms, and hold the published multiplier at 0.15. Substituting decision weather alters the Stage II static margin, derived risk score and pruning decisions. The weather-dependent historical training labels and selection rule remain part of the comparison. The per-quintal outcomes use the historical ex-post weather, missing-quote scenarios and opportunity cost of selling locally. This isolates sensitivity to weather **at evaluation time**.

Run the following in the repository after generating the six-state candidate table. The checked-in HP candidate table is the other input. Python 3.11, NumPy, pandas, scikit-learn, pyarrow and threadpoolctl are required.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/decision_weather_control.py
```

The optional `--main-candidates` argument accepts a rebuilt table at another path. All means include the zero incremental score for local decisions. Both denominators are in the output CSV. `changed_action_or_destination` counts changes in the selected destination including switching to or from selling locally. See `final/decision-weather-control-metadata.json` for input checksums, fitted-model provenance, constants and environment, and `final/decision-weather-control.csv` for the complete numeric comparison.

The comparison reuses the inspected six-state and HP holdouts. It does not identify the incremental value of a genuine weather forecast, establish as-of availability of the daily price inputs, or validate the assumed economic consequences of missing prices. Distinguish it from the HP-only seven-day-lag sensitivity in `scripts/audit_weather_and_apple.py`, which uses historical reanalysis values at a different lag.

## Results

Mean incremental simulator score in ₹/qtl per shortlisted episode. Losses are the percentage of dispatched episodes with a negative simulator score.

| Panel and policy | Archived mean | Fixed mean | Archived loss % | Fixed loss % | Changed decisions |
|---|---:|---:|---:|---:|---:|
| Six states, B2 | 446.66 | 446.66 | 18.11 | 18.11 | 0 |
| Six states, Stage I | 452.79 | 454.61 | 9.97 | 10.42 | 1,058 |
| Six states, Stage II | 479.17 | 480.17 | 10.48 | 10.95 | 1,239 |
| HP apple, B2 | 1,150.83 | 1,150.83 | 28.43 | 28.43 | 0 |
| HP apple, Stage I | 605.06 | 588.19 | 21.25 | 22.37 | 14 |
| HP apple, Stage II | 812.08 | 814.94 | 21.08 | 21.79 | 11 |

The six-state comparison contains 69,526 shortlisted episodes. With constant decision weather, Stage II exceeds B2 by ₹33.51/qtl there. On 1,537 HP apple episodes Stage II falls ₹335.90/qtl below B2. In both panels the mean ranking persists, while the two learned policies dispatch more frequently and incur a higher conditional modeled loss rate. These are descriptive paired contrasts on the same inspected cohorts.
