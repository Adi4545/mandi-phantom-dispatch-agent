# MandiGuard: Climate-, Road-, and Freshness-Aware Dispatch Agent for Indian Mandis

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](environment/requirements.txt)
[![Tests](https://img.shields.io/badge/pytest-18%20passed-brightgreen.svg)](results/pytest_execution.log)

**`MandiGuard`** investigates and mitigates **Phantom Spatial Arbitrage** across `6` major Indian agricultural states (`Maharashtra`, `Uttar Pradesh`, `Karnataka`, `Madhya Pradesh`, `Gujarat`, `Himachal Pradesh`) and `4` perishable commodities (`Onion`, `Potato`, `Tomato`, `Apple`), evaluated across **`2024–2026`** and stress-tested across **nearly 10 years (`2017–2026`, `42,722,187` raw AGMARKNET records -> `883,406` balanced panel rows across `178` core mandis)**. Rather than chasing naive price-board spreads or unconstrained ML point predictions, `MandiGuard` executes a frugal `T1 -> T2 -> T3 -> T4` sequential verification cascade anchored to **100% authentic AGMARKNET prices, OSRM highway routes, ECMWF ERA5 & NASA POWER climate grids, and verified Government of India surveys**—emitting either a calibrated `DISPATCH` or an explicit `REFUSE_PHANTOM_SPREAD` (`SELL_LOCAL`).

---

## Key Results Around 4 Minimal Metrics (`Mean Net Gain`, `Loss-Trip Rate`, `Worst-10% Loss`, `Live API Calls/Query`)

* **H1 (`SUPPORTED`, $p_{\text{Holm}} = 0.0012$):** **`+₹102.78/qtl`** higher net profit than naive price-board chasing (`B1`) on `69,526` shortlisted holdout episodes, equal to **`+₹3,083.5` extra profit per 30-quintal smallholder load** (`81.2%` of average monthly household net crop income of `₹3,798` per MoSPI NSS 77th Round).
* **H3 (`SUPPORTED`, $p_{\text{Holm}} = 0.0008$):** Cuts episode phantom losses by **`37.29 pp`** compared with unconstrained ML point forecasts (`B3`: `45.28%` conditional loss-trip rate -> `MandiGuard`: **`9.97%`**).
* **H4 (`SUPPORTED`, $p_{\text{Holm}} = 0.0008$):** Matches upfront all-tool oracle profit (`₹452.79/qtl`) using **`44.4%` fewer tool calls** (`8.75` vs `15.74` calls/episode).
* **H2 (`NOT_SUPPORTED` on mean gain, $p_{\text{Holm}} = 0.2699$; Major Tail-Risk Advantage):** `MandiGuard` beats fresh same-day OSRM heuristics (`B2`) by `+₹6.13/qtl` overall (and **`+₹31.82/qtl`** in the 4 states with `100%` native NWP forecasts) while **nearly halving phantom loss risk (`9.97%` vs `18.11%`) and shrinking worst-10% $\text{CVaR}_{10\%}$ 11.5-fold (`-₹37.89` vs `-₹436.67/qtl`)**.
* **10-Year Regimes, Edge-AI `ZeroCloud` & Cooperative FPO Pooling (`Exp 10`–`Exp 13b`):**
  * Across **`661,192` matched episodes (`2017H2–2026`)**, `MandiGuard` locks `Loss-Trip Rate` to `8.78%–12.03%` vs `39.18%–44.29%` naive (`+₹165.14/qtl` gain over `B1` during the `2024 El-Niño Heatwave`).
  * **`MandiGuard-ZeroCloud`** (cached OSRM table + on-device CPU scorer) achieves **`₹455.33/qtl`** at **`5.53` live API calls**, while Val-calibrated **satisficing early-exit** cuts live calls to **`3.84` calls/query (`₹1,922` vs `₹7,868` per `10k` queries = `-75.6%` API spend)**.
  * **FPO `90-qtl` Shared Truck Pooling (`0.70x` freight)** elevates realized gain to **`₹477.28/qtl`** (`+₹24.49/qtl` above solo `30-qtl` and `+₹67.75/qtl` above marginal `10-qtl` growers).

---

## Repository Map

* **`configs/`**: Master pipeline settings ([config.json](file:///Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent/configs/config.json)) and `Val_2025H1`-frozen safety margin ([frozen_calibration.json](file:///Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent/configs/frozen_calibration.json)).
* **`data/manifests/`**: SHA-256 provenance records for 2024–2026 & 2017–2026 AGMARKNET (`42.72M` streamed rows), OSRM roads, ERA5/NWP & NASA POWER (`291,384` rows) climate, GoI surveys, and compiled episode panels.
* **`data/processed/state_apmc_and_loss_parameters.csv`**: Audited 6-state $\times$ 4-crop table combining NABCONS (2022) market losses, GoI APMC F&V fee rules (`PIB relid=154554`), Nov-2023 MoFPI cold-storage capacity, Oct-2024 e-NAM integration, and NSO NSS Report No. 587 metrics.
* **`src/`**: Modular extraction (`src/data/`), sequential & ZeroCloud agent (`src/agents/`), baselines `B1`–`B6` (`src/baselines/`), causal/ACI conformal & modern forecasters (`src/models/`), two-way bootstrap, decade, ZeroCloud & FPO runners (`src/evaluation/`), and publication plotting (`src/visualization/`).
* **`results/` & `figures/`**: Complete confirmatory and exploratory CSV/JSON tables (`exp1`–`exp13b`), `<=160`-char real farmer SMS advisory cards, `250` JSONL execution traces, and eight 300-DPI PNG figures.
* **`notebooks/`**: Ten executed sequential notebooks (`00`–`09`) plus clean-room verified `<3 min` **`colab_standalone_reproduction.ipynb`** paired with `<5 MB` (`4.82 MB`) `data/processed/colab_data_pack.tar.gz`.
* **`paper/` & `viva/`**: Plain-English M.Tech manuscript ([manuscript.md](file:///Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent/paper/manuscript.md)), verified bibliography ([references.bib](file:///Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent/paper/references.bib)), plain-English viva guide, 35 examiner Q&As, and `1m/5m/15m` defense scripts.

## Quick Verification

```bash
PYTHONPATH=. python3 -m pytest -v tests
```
See [REPRODUCIBILITY.md](file:///Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent/REPRODUCIBILITY.md) for step-by-step full pipeline execution and Google Colab setup.
