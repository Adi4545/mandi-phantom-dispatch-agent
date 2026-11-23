> **Archival Note (Historical Stage-I Confirmatory Protocol):** Preserved verbatim for provenance (`R8`). For subsequent exploratory Revisions (`A10` & Revision v5 zero-parameter `Safe_EV_Sunk_m0` / `RT_2F_Min_m0`), see `final/PREREG_A10.md`, `final/PREREG_A18.md`, `final/AUDIT_V4.md`, and `paper/manuscript.md`.

# Pre-Registered Confirmatory Hypotheses & Statistical Protocol — `MandiGuard`

**Pre-Registration Timestamp Status:** Locked in Git **before** any evaluation script reads holdout test dates (`2025-06-01`..`2026-04-08` for the 6-state TOP+Apple benchmark; `2026-06-01`..`2026-08-27` for the grade-explicit HP Apple benchmark).  
**Primary Analysis Set:** All shortlisted origin-day-variety dispatch episodes (`has_screen_shortlist = True`) in `Holdout_2025_2026` (`2025-06-01`..`2026-04-08`, with realized arrival lookups up to `2026-04-13`), restricted to intra-state OSRM highway corridors (`15–500 km`).  
**Inferential Engine:** Paired **Two-Way Origin-Mandi $\times$ 2-Week-Block Cluster Bootstrap** ($R = 5{,}000$ draws, `seed = 20261117`) with Phipson & Smyth (2010) finite-sample $p$-values and **Holm–Bonferroni step-down FWER adjustment** across $m = 4$ confirmatory hypotheses at family-wise $\alpha = 0.05$.

---

## Confirmatory Family ($m = 4$, Holm–Bonferroni Controlled)

| ID | Directional Hypothesis | Estimand & Metric | Matched Comparator | Null Hypothesis ($H_0$) | Acceptance Rule |
|:---|:---|:---|:---|:---|:---|
| **`H1`** | **Net Welfare Over Naive Screen Dispatch:** `MandiGuard` achieves strictly higher mean realized net gain over selling locally ($\Delta\text{Net}\text{ \₹/qtl}$) than naive farmer/portal screen chasing. | $\mu_{\text{MG}}(\Delta\text{Net}) - \mu_{\text{B1}}(\Delta\text{Net}) > 0$ | `B1_NaiveScreenGreedy` (highest $\le 7\text{d}$ headline modal price minus $1.2\times$ Euclidean freight) | $\Delta \le 0$ | Holm-adjusted $p_{\text{adj}} < 0.05$ and point diff $> 0$ |
| **`H2`** | **Value Beyond Fresh Prices & OSRM Roads:** Adding yard-vitality/DOW guards (`T1`), weather spoilage (`T3`), and arrival conformal bounds (`T4`) beats fresh same-day price + OSRM road greedy dispatch. | $\mu_{\text{MG}}(\Delta\text{Net}) - \mu_{\text{B2}}(\Delta\text{Net}) > 0$ | `B2_FreshRoadGreedy` (same-day `age=0` price + exact OSRM road freight + state APMC fees $> \text{₹100/qtl}$) | $\Delta \le 0$ | Holm-adjusted $p_{\text{adj}} < 0.05$ and point diff $> 0$ |
| **`H3`** | **Phantom-Loss Protection Over Point-Forecast ML:** `MandiGuard` significantly reduces episode-level phantom arbitrage losses (dispatches yielding realized $\Delta\text{Net} < 0$) compared with unconstrained point-forecast ML dispatch. | $\text{Incidence}_{\text{MG}}(\text{Phantom}) - \text{Incidence}_{\text{B3}}(\text{Phantom}) < 0$ *(with secondary report of conditional Phantom Loss Rate among dispatched trucks and $\Delta\text{Net}$)* | `B3_MLPointDispatch` (uses OSRM road freight + 2024 ML point forecast $\hat{P}_{50}$, omitting `T1`, `T3`, and `T4` LCB) | $\Delta \ge 0$ | Holm-adjusted $p_{\text{adj}} < 0.05$ and point diff $< 0$ |
| **`H4`** | **Sequential Verification Savings Over Upfront Oracle Polling:** `MandiGuard`'s ordered 4-tool cascade reduces mean tool calls per shortlisted episode by at least **25%** relative to upfront all-tool verification (`B4`) while preserving identical unrestricted dispatch outcomes. | $\mathbb{E}[\text{Calls}_{\text{MG}} - 0.75 \cdot \text{Calls}_{\text{B4}}] < 0$ *(equiv. $>25\%$ call reduction; matched decision $\Delta\text{Net}_{\text{MG}} \equiv \Delta\text{Net}_{\text{B4}}$)* | `B4_UpfrontAllTools` (runs all 4 tools `T1`–`T4` upfront on every top-$K$ candidate) | $\Delta \ge 0$ | Holm-adjusted $p_{\text{adj}} < 0.05$ and call reduction $> 25\%$ |

---

## Pre-Registered Secondary / Diagnostic Analyses (Reported Unadjusted with Honest Disaggregation)

1. **Multi-Agent vs. Unified Cascade Comparison (`B5`, `B6`):** Compare `MandiGuard` against a 3-role discretized coordinator (`B5_MultiAgentCoordinator`) and coarse verbal rule router (`B6_HeuristicBucketRouter`) to test whether multi-agent quantization losses hurt utility compared with unified single-agent tool orchestration.
2. **State & Commodity Disaggregation + Clean NWP Subgroup:** Break down phantom arbitrage anatomy (`Exp 1`) and policy gains (`Exp 2b`) across all 6 states and 4 crops, explicitly reporting the 4 states with 100% native Open-Meteo NWP forecast grids (`Gujarat`, `Karnataka`, `Madhya Pradesh`, `Maharashtra`) alongside the 2 northern states supplemented by causal $\le t$ ERA5 nowcasting (`Uttar Pradesh`, `Himachal Pradesh`).
3. **Grade-Explicit HP Apple Validation (`Exp 3`):** Evaluate on 2026 Himachal Pradesh grade-explicit harvest records (`Grade A`, `Grade B`, `Medium`, etc.; `2026-06-01`..`2026-08-27`).
4. **Leave-One-Tool-Out Ablations & Extreme-Weather Regimes (`Exp 4`):** Evaluate `No-T1`, `No-T2 (OSRM->Euclid)`, `No-T3 (No Weather)`, and `No-T4 (No Conformal LCB)` both overall and inside extreme heat/rain (`era5_tmax >= 35°C` or `era5_rain >= 35 mm`).
5. **Budget Pareto Frontier (`Exp 5`), Sensitivity Grid & Government Fee Ablation (`Exp 6`), Rejection Taxonomy (`Exp 7`), Live Nov-2026 Yard Audit (`Exp 8`).**
