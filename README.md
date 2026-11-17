# MandiGuard: Climate-, Road-, and Freshness-Aware Dispatch Agent for Indian Mandis

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](environment/requirements.txt)
[![Tests](https://img.shields.io/badge/pytest-19%20passed-brightgreen.svg)](results/pytest_execution.log)

**`MandiGuard`** investigates and mitigates **Phantom Spatial Arbitrage** across `6` major Indian agricultural states (`Maharashtra`, `Uttar Pradesh`, `Karnataka`, `Madhya Pradesh`, `Gujarat`, `Himachal Pradesh`) and `4` perishable commodities (`Onion`, `Potato`, `Tomato`, `Apple`), evaluated across **`2024–2026`** and stress-tested across **nearly 10 years (`2017–2026`, `42,722,187` raw AGMARKNET records -> `883,406` balanced panel rows across `178` core mandis, cross-verified at `100%` `Min`/`Max` and `99.42%` `Modal` parity against official `data.gov.in` Resource `9ef84268-d588-465a-a308-a864a43d0070`)**. Rather than chasing naive price-board spreads or unconstrained ML point predictions, `MandiGuard` executes a frugal `T1 -> T2 -> T3 -> T4` sequential verification cascade anchored to **verified AGMARKNET mirror & `.gov.in` records, OSRM highway routes, ECMWF ERA5 & NASA POWER climate grids, and verified Government of India surveys**—emitting either a calibrated `DISPATCH` or an explicit `REFUSE_PHANTOM_SPREAD` (`SELL_LOCAL`).

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
* **Open-Yard / Clerk-Upload-Lag Sensitivity (`Exp 15`) & Direct `.gov.in` Parity (`Exp 14`):** Holds `+₹77.34` to `+₹102.78/qtl` over `B1` across all missing-entry clerk-lag assumptions, and earns **`₹1,035.32/qtl` (`4.98%` LTR)** on 100%-observed arrival-day dispatches (zero missing data: **`+₹178.46/qtl` vs `B1`** and **`+₹201.59/qtl` vs `B2`**).

---

## Repository Map

* **`configs/`**: Master pipeline settings ([config.json](configs/config.json)) and `Val_2025H1`-frozen safety margin ([frozen_calibration.json](configs/frozen_calibration.json)).
* **`data/`**: Self-contained verified public datasets (`<= 4.82 MB` per file) including AGMARKNET 2017–2026 (`agmarknet_6state_decade_2017_2026.parquet`), HP graded apples, `8,147` OSRM highway corridors, ERA5/NWP & NASA POWER climate grids, 8 official GoI PIB survey files, SHA-256 manifests (`data/manifests/`), and [state_apmc_and_loss_parameters.csv](data/processed/state_apmc_and_loss_parameters.csv).
* **`src/`**: Modular extraction (`src/data/`), sequential & ZeroCloud agent (`src/agents/`), baselines `B1`–`B6` (`src/baselines/`), causal/ACI conformal & modern forecasters (`src/models/`), two-way bootstrap, decade, ZeroCloud & FPO runners (`src/evaluation/`), and publication plotting (`src/visualization/`).
* **`results/` & `figures/`**: Complete confirmatory and exploratory CSV/JSON tables (`exp1`–`exp15`), `<=160`-char real farmer SMS advisory cards, `250` JSONL execution traces, and eight 300-DPI PNG figures (`fig1`–`fig8`).
* **`notebooks/`**: Ten executed sequential notebooks (`00`–`09`) plus clean-room verified `<3 min` **`colab_standalone_reproduction.ipynb`** paired with `<5 MB` (`4.82 MB`) `data/processed/colab_data_pack.tar.gz`.
* **`paper/` & `viva/`**:
  * **Thesis Paper (Class-12 Clear + Full Rigor):** [manuscript.md](paper/manuscript.md) & verified BibTeX [references.bib](paper/references.bib) (`31/31` cited).
  * **12th-Class Easy Reading Companion Edition:** [12th_class_easy_reading_edition.md](paper/12th_class_easy_reading_edition.md) (everyday analogies, worked truck math, visual guide to all 8 figures, mini-dictionary).
  * **Career & M.Tech Viva Defense Suite:** [00_career_defense_master_sheet.md](viva/00_career_defense_master_sheet.md) *(2-page exam-room master sheet + 15 toughest examiner questions)*, [01_plain_english_complete_guide.md](viva/01_plain_english_complete_guide.md), [02_35_viva_questions_and_answers.md](viva/02_35_viva_questions_and_answers.md) (`40` Q&As), and [03_spoken_pitches_1m_5m_15m.md](viva/03_spoken_pitches_1m_5m_15m.md).

## Quick Clone-and-Run Verification

```bash
PYTHONPATH=. python3 -m pytest -v tests
```
All compact datasets (`<= 4.82 MB` each), `forecaster_2024.pkl`, `colab_data_pack.tar.gz`, official `data.gov.in` parity XML, and manifests are included directly in this repository for zero-friction offline testing (`19 passed`). See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for rebuilding the large raw candidate caches (`77 MB` / `126 MB`) from included parquets or running on Google Colab.
