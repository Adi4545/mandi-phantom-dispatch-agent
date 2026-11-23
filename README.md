# MandiGuard (Revision v6): Leak-Free Wholesale Dispatch Replay & Zero-Parameter Risk-Aware Rules

[![Python 3.11.5](https://img.shields.io/badge/Python-3.11.5-blue.svg)](environment/requirements.txt)
[![Tests](https://img.shields.io/badge/pytest-36%20passed-brightgreen.svg)](Makefile)

**`MandiGuard` Revision v6** (Aditya Sharma, Shoolini University, Solan, HP; branch `finalization`, PR #1) audits when online AGMARKNET price spreads between Indian wholesale *mandis* survive realistic transport costs, destination-base statutory APMC fees, biological decay, daily auction volatility, realized ERA5 arrival weather, and strictly sequential arrival settlement across six states and four crops (`Onion`, `Potato`, `Tomato`, `Apple`).

## Verified Results (`make reproduce` — Zero Free Parameters, Strictly `<= t - 1`)

Every table and figure in [`paper/manuscript.md`](paper/manuscript.md) and [`revision/results/`](revision/results/) builds deterministically from **tracked primary files only** (zero gitignored caches, zero weather in decisions, zero pickled trees, zero tuned magic cutoffs). Calendar test split `2025-06-01..2026-04-08` was previously exposed (`exploratory: true`), and both follow-up specifications ([`PREREG_A10.md`](final/PREREG_A10.md) at `87a0b62` and [`PREREG_A18.md`](final/PREREG_A18.md) at `4cbb02d`) were committed before their execution scripts (`R5`).

| Policy (`N = 58,676` Lagged Test, Equal `lag 1..3` Except `B1`) | Free Params | Dispatch (%) | Mean Net (₹/qtl) | Episode Loss (%) | Exact `ES10` (₹/qtl) | Loss Given Loss |
|---|---:|---:|---:|---:|---:|---:|
| **`B1_lagged_screen`** (`lag_spread > ₹100`, `1..7`d) | 1 | `100.00%` | `₹397.87` | `45.21%` | `−₹641.26` | `−₹271.24` |
| **`B2_age_matched`** (`lag 1..3`, road + dest fee `> ₹200`) | 1 | `72.03%` | `₹433.56` | `26.72%` | `−₹525.25` | `−₹293.73` |
| **`MG_matched`** (hard gates `T1..T4`, val-match) | 4 | `69.51%` | `₹467.90` | `18.57%` | `−₹512.78` | `−₹331.27` |
| **`RR_Abstain_matched`** (`kappa*=5.0`, val-match `₹3.73`) | 2 | `69.02%` | `₹475.36` | `17.23%` | `−₹460.72` | `−₹308.18` |
| **`Safe_EV_Sunk_m0`** (`p_dow * G_1SD - F > 0`) | **0** | **`63.27%`** | **`₹465.59`** | **`14.93%`** | **`−₹344.09`** | **`−₹260.05`** |
| **`Safe_EV_Phys_m0`** (`1.5F` settlement-matched, `0` tuned) | **0** | `60.85%` | `₹462.16` | **`13.73%`** | **`−₹333.57`** | `−₹264.64` |
| **`RT_2F_Min_m0`** (Class-8 `p_min * G - 2F > 0`, NO `cv28`) | **0** | `64.92%` | **`₹478.38`** | `16.26%` | `−₹468.32` | `−₹325.70` |

- **Statistical Inference (`R = 5,000`, [`v6_bootstrap_5000.csv`](revision/results/v6_bootstrap_5000.csv)):** Across ALL THREE two-way clustering schemes (`173` origins, `172` State-prefixed B2 destinations, `171–173` policy destinations) and `1`-week (`45`), `2`-week (`23`), and `4`-week (`12`) blocks with **two-sided Holm-Bonferroni (`p_holm_2s`)**, zero-parameter `Safe_EV_Sunk_m0` improves `ES10` by **`+₹181.17/qtl`** vs `B2_age_matched` (`Safe_EV_Phys_m0` `+₹191.69/qtl`), lowers EpLoss by **`−11.79 pp`**, raises Mean by `+₹32.03/qtl` (`p_holm_2s = 0.0028–0.0436`), and Class-8 `RT_2F_Min_m0` raises Mean by **`+₹44.82/qtl`** (all tail/loss/`RT`-mean **`p_holm_2s = 0.0024`**).
- **`Revision v6` Upgrades ([`v6_upgrades.csv`](revision/results/v6_upgrades.csv), [`v6_breakeven.csv`](revision/results/v6_breakeven.csv)):** Fresh end-to-end rebuilt strict `2024`-only `171`-market panel (`N = 57,634`, zero market-selection lookahead), `100.0%`-covered realized ERA5 destination arrival-day weather settlement (zero weather in decisions: `Safe_EV_Sunk_m0` `+₹190.43` `ES10` on `178` mkts, `+₹187.80` on `171` mkts; `Safe_EV_Phys_m0` `+₹201.55` / `+₹199.07`), and exact silent-market break-even (`+₹328.37/qtl` uniform shift above turn-back, `+₹95.97/qtl` under a separate flat constant-payoff counterfactual, or `23.79%` homogeneous Open-MAR share; `+₹363.74` / `+₹119.16` / `26.65%` on `171`-mkt ERA5; `verification_resid = 0.0`).
- **Global Robustness & Honest Boundaries (`R5`–`R7`):** `Safe_EV_Sunk_m0` holds strictly positive `ES10` CIs vs `B2_age_matched` in all 6 states and all 5 crop slices (while trailing `RR_Abstain_matched` on Potato `ES10` by `−₹16.60/qtl`), all 36 frozen+rescored tornado cells, centroid-free corridors (`N = 40,690`; `18,189` all-5 exact), `N = 88,014` unconditional origin episodes (`ES10 −₹335.04` vs `−₹515.93`), `exact_zero_divert_payoff_0` (`+₹169.79 ES10`), and HP Apples (`−₹1,454.86` vs `−₹2,392.12`). Open disclosures: acts strictly as a 6 a.m. alert filter ahead of a live *arhtiya* phone call; Open-MAR reverses Mean to `B2` (`+₹102.58` `20°C` / `+₹100.57` ERA5) while `Safe_EV` retains `+₹190.00` (`+₹196.38` ERA5) `ES10`; HP Apple conditional loss remains `41.38%`; legacy Stage I `H2` stays `+₹6.13` (`p = 0.2699`); `Gate J = BLOCKED`.

## One-Command Reproduction (`make reproduce`)

```bash
pip install -r environment/requirements.txt
make reproduce
```

Runs `build_variant`, `build_hp_apple_lagged`, `eval_run`, `sensitivity_a8`, `eval_a10`, `eval_a18`, `eval_v6`, `make_figures`, cleanroom [`scripts/a16_independent_audit.py`](scripts/a16_independent_audit.py) (`₹0.00` parity across 8 policies + cluster invariants), [`scripts/verify_traceability.py`](scripts/verify_traceability.py) (`0` untraceable numbers across all `23/23` active docs), and `pytest -v` (`36/36` passing).

## Compiled Revision v6 Deliverables Index (`make deliverables`)

| Deliverable | Format | Source & Scope |
|---|---|---|
| [`paper/MandiGuard_Research_Paper.pdf`](paper/MandiGuard_Research_Paper.pdf) | PDF / [`.html`](paper/MandiGuard_Research_Paper.html) | Full Revision v6 research manuscript (`paper/manuscript.md`, `49` verified citations) with equations, tables & `rev_fig1..4` |
| [`paper/manuscript.tex`](paper/manuscript.tex) & [`paper/MandiGuard_Research_Paper.docx`](paper/MandiGuard_Research_Paper.docx) | LaTeX & Word | Compile-ready LaTeX (`49/49` cited keys from `61` in [`paper/references.bib`](paper/references.bib)) & Word bundle |
| [`paper/MandiGuard_Easy_Reading_Edition.pdf`](paper/MandiGuard_Easy_Reading_Edition.pdf) | PDF / [`.html`](paper/MandiGuard_Easy_Reading_Edition.html) | Class-12 pocket-calculator companion guide |
| [`viva/MandiGuard_Viva_Defense_Slides.pdf`](viva/MandiGuard_Viva_Defense_Slides.pdf) | 12-Slide PDF / [`.html`](viva/MandiGuard_Viva_Defense_Slides.html) | 16:9 widescreen M.Tech viva presentation (`final/SLIDE_OUTLINE.md`) |
| [`docs/MandiGuard_First_Principles_and_Thesis_Defense_Handbook.pdf`](docs/MandiGuard_First_Principles_and_Thesis_Defense_Handbook.pdf) | PDF / [`.html`](docs/MandiGuard_First_Principles_and_Thesis_Defense_Handbook.html) | Complete first-principles & viva compendium |
| [`docs/MandiGuard_Master_Study_Guide.pdf`](docs/MandiGuard_Master_Study_Guide.pdf) | PDF / [`.html`](docs/MandiGuard_Master_Study_Guide.html) | Structured 3-part master study guide (`docs/study_guide_v2_parts/`) |
| [`docs/MandiGuard_Student_Study_Guide.pdf`](docs/MandiGuard_Student_Study_Guide.pdf) | PDF / [`.html`](docs/MandiGuard_Student_Study_Guide.html) | Plain-English beginner & Class 10–12 study guide |
| [`notebooks/10_finalization_reproduction.ipynb`](notebooks/10_finalization_reproduction.ipynb) & [`colab_standalone_reproduction.ipynb`](notebooks/colab_standalone_reproduction.ipynb) | Executed / Colab `.ipynb` | End-to-end reproduction notebooks from tracked files only (`00..09` archived) |
