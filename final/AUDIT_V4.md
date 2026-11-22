# Independent Final Audit (`AUDIT_V4.md` — Agent `A16`)

**Auditor Role:** Independent Adversarial Final Auditor (`A16`), using `scripts/a16_independent_audit.py` (ZERO imports from `revision/build_variant.py`, `revision/eval_run.py`, or `revision/eval_a10.py`, reading ONLY tracked raw files).  
**Branch & Base Audit Point:** `finalization` (remediated from Review-3 base SHA `b3bb46f8fee131218d6154898f4d0659b3018fa4`, PR #1).  
**Headline Score & Verdict:** **8.4 / 10 — CONDITIONAL PASS (M.Tech Defense & Exploratory Retrospective Benchmark Ready; Blocked on Prospective Gate J & Live Field Trial).**

---

## 1. Independent Cleanroom Re-Derivation (`scripts/a16_independent_audit.py`)

`scripts/a16_independent_audit.py` independently loaded `data/raw/agmarknet_6state_top_apple_2024_2026.parquet`, `data/processed/osrm_corridor_matrix.parquet`, and `data/processed/state_apmc_and_loss_parameters.csv`, re-implemented invalid-row filtering, canonical variety consolidation, strictly-`< t` `merge_asof` lookup, shifted cumulative reporting probabilities, sequential no-lookahead settlement, destination post-spoilage statutory fees, and exact fractional `ES10`, yielding **exact `₹0.00` discrepancy** against committed `revision/results/a10_results.csv`:

| Audit Check (`N = 58,676` Test Episodes) | Committed Output (`revision/results/`) | Independent `A16` Re-Derivation | Absolute Diff | Status |
|---|---:|---:|---:|---|
| Raw panel rows | `260,043` | `260,043` | `0` | **EXACT MATCH** |
| Valid rows after dropping `modal_outside_minmax` (`759`) | `259,284` | `259,284` | `0` | **EXACT MATCH** |
| Canonical `(State, Market, Comm, Var, Date)` rows | `248,302` | `248,302` | `0` | **EXACT MATCH** |
| Origin days in window with `1..7`d lag | `129,023` | `129,023` | `0` | **EXACT MATCH** |
| `B1_lagged_screen` (Dispatch / Mean / `ES10`) | `1.0000` / `₹397.87` / `−₹641.26` | `1.0000` / `₹397.87` / `−₹641.26` | `₹0.00` | **EXACT MATCH** |
| `B2_age_matched` (Dispatch / Mean / `ES10`) | `0.7203` / `₹433.56` / `−₹525.25` | `0.7203` / `₹433.56` / `−₹525.25` | `₹0.00` | **EXACT MATCH** |
| `RR_Abstain_matched` (Dispatch / Mean / `ES10`) | `0.6902` / `₹475.36` / `−₹460.72` | `0.6902` / `₹475.36` / `−₹460.72` | `₹0.00` | **EXACT MATCH** |
| `RR_Abstain_m0` (Dispatch / Mean / `ES10`) | `0.6952` / `₹475.76` / `−₹461.74` | `0.6952` / `₹475.76` / `−₹461.74` | `₹0.00` | **EXACT MATCH** |

*(Note: On its initial run, `A16` flagged a `₹0.11/qtl` discrepancy on `B1_lagged_screen`, tracing immediately to `Min_Price` aggregation (`median` vs canonical market-minimum `min` across multi-grade duplicates before commodity fallback). Reconciling to canonical market-minimum `min` reduced the discrepancy to `₹0.00`.)*

---

## 2. Dimension-by-Dimension Score Breakdown (`/10`)

| Dimension | Review-3 Baseline (`b3bb46f`) | Revision v4 (`AUDIT_V4`) | Evidence Summary |
|---|---:|---:|---|
| Data Provenance & Cleaning Funnel | 6/10 | **9/10** | Full integer reconciliation (`260,043 -> 259,284 -> 256,997 -> 248,302 -> 58,676`), 100% OSRM join (`178/178`, `42/42`), zero gitignored files. |
| Temporal Causality (`R3`) | 3/10 | **9.5/10** | Fixed `C1` day-$t$ shortlist leak, `M9` same-day origin price leak, and stripped `98.64%` ERA5-identical weather; proven by counterfactual future perturbation tests. |
| Fairness & Economic Fidelity (`R4`, `M4`, `M9`) | 5/10 | **8.5/10** | Age-matched `B2` (`1..3`d), destination-gross-sale statutory fees (`0` intra-district/divert), sequential arrival settlement, NITI Aayog / RBI / NABCONS / GoHP tornado bounds. |
| Statistical Inference & Stability (`A7`) | 6/10 | **9/10** | Two clustering schemes (`origin_x_2week` & `b2dest_or_origin_x_2week`), exact `ES10` & `ep_loss_rate` CIs, Holm-Bonferroni FWER, crop/state splits showing Non-Apple (`N = 52,207`) strength. |
| Simplicity & Pre-Registered Novelty (`A10`, `A15`) | 6/10 | **8.5/10** | Pre-registered `RR-Abstain` (`87a0b62`) before coding `eval_a10.py`; cut difficulty `4.3 -> 1.6 / 5` while improving `ES10` (`+₹64.54` vs `B2_age`, `+₹52.06` vs `MG_matched`, `p_holm = 0.0020`). |
| Prospective Holdout & Field Validation (Gate J) | 2/10 | **3/10** *(capped cleanly)* | No untouched post-April-2026 multi-state panel exists (`exploratory: true` disclosed); zero field truck receipts (`R7`). |
| Reproducibility & Traceability (`A13`, `R2`) | 5/10 | **9.5/10** | Fresh-clone `make reproduce` diff `0.0000`; `32/32` pytest green; `0` untraceable numbers across `paper/` and `viva/`. |
| **Overall Honest Score** | **6.0 / 10** | **8.4 / 10** | **All internal code, timing, statistical, and traceability defects resolved; remaining ceiling is external Gate J prospective data & live field receipts.** |
