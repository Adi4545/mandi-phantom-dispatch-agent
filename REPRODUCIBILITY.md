# Deterministic Reproducibility Guide (Revision v7 — Finalized Clean Audit)

All Revision v7 CSV tables, Phase 6 stress-audit CSVs (`v7_exp*.csv`), JSON summaries, publication figures, `7` compiled PDFs, `manuscript.tex`, and `MandiGuard_Research_Paper.docx` regenerate deterministically from tracked repository artifacts (`data/raw/*`, `data/processed/*`, `revision/*`, `scripts/*`).

## 1. Tracked Inputs (Zero External Downloads Needed; 100% Offline)
- `data/raw/agmarknet_6state_top_apple_2024_2026.parquet` (`260,043` raw rows superset; strict `2024`-active `171`-market primary slice = `257,576` raw rows; `172` Tier-1 markets minus `1` >500 km OSRM-excluded corridor yard)
- `data/raw/agmarknet_6state_decade_2017_2026.parquet` (`2017–2023` offline archive: `623,363` raw rows across `173` legacy yards; after excluding `7` post-2024 lookahead yards and enforcing exact `171 ∩ 173`, yields `166` clean non-lookahead markets / `N = 383,952` episodes, plus `115` clean `2017`-active markets / `N = 325,993` episodes; original `173` = `389,357` retained solely for provenance reconciliation)
- `data/raw/hp_apple_daily_2025_2026.csv` (`4,427` rows across `42` HP yards)
- `data/processed/osrm_corridor_matrix.parquet` (`8,147` road corridors within `2024`-active OSRM Top-30 frame, `15.19–499.43` km)
- `data/processed/state_apmc_and_loss_parameters.csv` (stylized APMC seller-fee tiers & NABCONS cumulative post-harvest loss parameters; see Table 2 provenance labels)
- `data/processed/mandi_weather_2024_2026.parquet` (settlement-only realized ERA5 `0.1°` reanalysis, `100.0%` coverage) and `data/processed/nasa_power_climate_2017_2023.parquet` (NASA POWER `0.5°` climate grid for `2018–2023` audit)

> **Offline Scope Note:** `make reproduce` runs strictly offline on the tracked datasets above and does not stream the live `2017–2023` raw HuggingFace universe (`647` markets) at runtime; the `166` clean-decade intersection remains inside the pre-built `2024` OSRM top-30 corridor frame.

## 2. Step-by-Step Build & Verification Targets
Run inside the repository root (`Python 3.11+`, dependencies in `environment/requirements.txt`):
```bash
# 1. Rebuild Revision v7 primary (171-mkt), clean decade (166-mkt), Phase 6 stress suite, & figures
python3 -m revision.build_run
make v7_stress

# 2. Rebuild all 7 PDFs, LaTeX, DOCX, and viva slides
make deliverables

# 3. Run leakage firewall, Revision v7 integrity tests, cleanroom independent audit & traceability gate
python3 -m pytest -v
python3 scripts/a16_independent_audit.py
python3 scripts/verify_traceability.py
```

## 3. Clean-Clone Parity Check
`Makefile` includes a standalone `reproduce` target that clones `HEAD` into a clean directory, runs the full `build`, `eval`, `sensitivity`, `a10`, `a18`, `v6`, `v7`, `v7_stress`, `figures`, `audit`, `verify`, and `test` sequence, and verifies `0.0` maximum absolute numeric difference across every generated CSV file under `revision/results/`. Note that `final/PREREG_A10.md` and `final/PREREG_A18.md` remain untouched (`git diff` empty), and any local `data/interim/omega_lab_*.parquet` caches remain untracked and excluded from the production pipeline.
