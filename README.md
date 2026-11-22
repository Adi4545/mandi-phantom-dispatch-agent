# MandiGuard (Revision v5): Leak-Free Wholesale Arbitrage Audit & Zero-Parameter Dispatch Rules

[![Python 3.11.5](https://img.shields.io/badge/Python-3.11.5-blue.svg)](environment/requirements.txt)
[![Tests](https://img.shields.io/badge/pytest-34%20passed-brightgreen.svg)](Makefile)

**`MandiGuard` Revision v5** (branch `finalization`, PR #1) audits when online AGMARKNET price spreads between Indian wholesale *mandis* fail under realistic transport costs, destination-base statutory APMC fees, biological decay, daily auction volatility, and strictly sequential arrival settlement across six states and four crops (`Onion`, `Potato`, `Tomato`, `Apple`).

## Verified Results (`make reproduce` — Zero Free Parameters, Strictly `<= t - 1`)

Every table and figure in [`paper/manuscript.md`](paper/manuscript.md) and [`revision/results/`](revision/results/) builds deterministically from **tracked primary files only** (zero gitignored caches, zero live/ERA5 weather leaks, zero pickled trees, zero tuned magic cutoffs). Calendar test split `2025-06-01..2026-04-08` was previously exposed (`exploratory: true`), and both follow-up specifications ([`PREREG_A10.md`](final/PREREG_A10.md) at `87a0b62` and [`PREREG_A18.md`](final/PREREG_A18.md) at `4cbb02d`) were committed before their execution scripts (`R5`).

| Policy (`N = 58,676` Lagged Test, Equal `lag 1..3` Except `B1`) | Free Params | Dispatch (%) | Mean Net (₹/qtl) | Episode Loss (%) | Exact `ES10` (₹/qtl) | Loss Given Loss |
|---|---:|---:|---:|---:|---:|---:|
| **`B1_lagged_screen`** (`lag_spread > ₹100`, `1..7`d) | 1 | `100.00%` | `₹397.87` | `45.21%` | `−₹641.26` | `−₹271.24` |
| **`B2_age_matched`** (`lag 1..3`, road + dest fee `> ₹200`) | 1 | `72.03%` | `₹433.56` | `26.72%` | `−₹525.25` | `−₹293.73` |
| **`MG_matched`** (hard gates `T1..T4`, val-match) | 4 | `69.51%` | `₹467.90` | `18.57%` | `−₹512.78` | `−₹331.27` |
| **`RR_Abstain_matched`** (`kappa*=5.0`, val-match `₹3.73`) | 2 | `69.02%` | `₹475.36` | `17.23%` | `−₹460.72` | `−₹308.18` |
| **`Safe_EV_Sunk_m0`** (`p_dow * G_1SD - F > 0`) | **0** | **`63.27%`** | **`₹465.59`** | **`14.93%`** | **`−₹344.09`** | **`−₹260.05`** |
| **`Safe_EV_Sunk_matched`** (val-match `70.71%`) | 1 | `70.90%` | `₹469.94` | `18.51%` | `−₹366.41` | `−₹243.04` |
| **`RT_2F_Min_m0`** (Class-8 `p_min * G - 2F > 0`, NO `cv28`) | **0** | `64.92%` | **`₹478.38`** | `16.26%` | `−₹468.32` | `−₹325.70` |

- **Statistical Inference ([`a18_bootstrap.csv`](revision/results/a18_bootstrap.csv)):** Across ALL THREE two-way clustering schemes (`173` origins, `172` State-prefixed B2 destinations, `171–173` policy destinations $\times$ 23 fortnights) with **two-sided Holm-Bonferroni (`p_holm_2s`)**, zero-parameter `Safe_EV_Sunk_m0` cuts `ES10` by **`+₹181.17/qtl`** vs `B2_age_matched` (`p_holm_2s = 0.0040`), cuts EpLoss by **`−11.79 pp`** (`p_holm_2s = 0.0040`), and matched `Safe_EV_Sunk_matched` beats tuned `RR_Abstain_matched` by **`+₹94.31/qtl` `ES10`** (`p_holm_2s = 0.0040`), while Class-8 `RT_2F_Min_m0` lifts Mean by **`+₹44.82/qtl`** (`p_holm_2s = 0.0040`).
- **Global Robustness & Honest Boundaries (`R5`–`R7`):** `Safe_EV_Sunk_m0` holds strictly positive `ES10` CIs in all 6 states, all 36 frozen+rescored tornado cells, centroid-free corridors (`N = 40,690` episodes retaining exact-geocoded candidates; `N = 18,189` all-5 exact), `N = 88,014` unconditional origin episodes (`ES10 −₹335.04` vs `−₹515.93`), `exact_zero_divert_payoff_0` (`+₹169.79 ES10`), and HP Apples (`−₹1,454.86` vs `−₹2,392.12`). Open disclosures: acts as 6 a.m. alert filter prior to live *arhtiya* phone calls; Open-MAR upload omission flips Mean to `B2` (`+₹102.58`) while `Safe_EV` retains `+₹190.00` `ES10`; Mean CIs cross zero in Gujarat/MH/UP/Tomato/Apple (`RT_2F_Min_m0` leads point Mean everywhere); HP Apple conditional loss remains `41.38%`; legacy Stage I `H2` stays `+₹6.13` (`p = 0.2699`); `Gate J = BLOCKED`.

## One-Command Reproduction (`make reproduce`)

```bash
pip install -r environment/requirements.txt
make reproduce
```

Runs `build_variant`, `build_hp_apple_lagged`, `eval_run`, `sensitivity_a8`, `eval_a10`, `eval_a18`, `make_figures`, cleanroom [`scripts/a16_independent_audit.py`](scripts/a16_independent_audit.py) (`₹0.00` discrepancy across 8 policies + cluster invariants), [`scripts/verify_traceability.py`](scripts/verify_traceability.py) (`0` untraceable numbers across all `9/9` docs), and `pytest -v` (`34/34` passing).
