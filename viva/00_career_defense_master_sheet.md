# MandiGuard Revision v4 — Career Defense Master Sheet (`C2` Fixed: Verified Claims Only)

> **Audit Guarantee (`R2` & `C2`):** All Stage I unlagged `cvar_10` / quantile-mean and Stage II pseudo-conformal numbers have been superseded. Every number below traces verbatim to `revision/results/` (reproduced in clean clone `make reproduce` with `0.00` discrepancy) or verified Stage I historical files (`results/confirmatory_holm_summary.csv`, `results/exp3_hp_apple_grade_holdout.csv`).

---

## 1. Your 45-Second Core Thesis Pitch

> *"Sir/Ma'am, online mandi portals like AGMARKNET show tempting price gaps between mandis, but a displayed spread is not realized cash. Across `58,676` strictly causal (`<= t - 1`) test episodes spanning 6 states and 4 crops with sequential arrival settlement and destination-base APMC fees, chasing the top lagged spread loses money **`45.21%`** of the time with worst-10% expected shortfall **`ES10 = −₹641.26/qtl`**. Early versions leaked future day-$t$ shortlists and ERA5 weather and relied on brittle ML trees (`H2` stayed inconclusive at `+₹6.13`, `p = 0.2699`). We stripped that complexity down to **one calculator-verifiable expected-value formula (`RR-Abstain`)**: weighting open-market gain by past variety-reporting reliability against a bounded return-freight loss. At matched ~69–72% dispatch (`2025-01..2025-05` validation frozen `kappa* = 5.0`), `RR-Abstain` achieves **`₹475.36/qtl` mean gain** (`+₹41.80` vs age-matched road baseline, Holm `p = 0.0020`), cuts episode losses to **`17.23%`** (`−9.49 pp`, Holm `p = 0.0020`), and strengthens **`ES10` to `−₹460.72/qtl`** (`+₹64.54` over road dispatch and `+₹52.06` over hard activity gates, Holm `p = 0.0020`), holding across Onion, Potato, and Tomato and down to `0` missing-quote penalty, while leaving graded HP apples openly fragile (`44.63%` conditional loss rate)."*

---

## 2. The Verified Benchmark Numbers (`N = 58,676` Lagged Test Episodes, `exploratory` wrt Calendar Exposure)

| Policy | Calibration / Rule | Dispatch Rate | Mean Net (₹/qtl) | Episode Loss Rate | Cond. Loss Rate | Exact `ES10` (₹/qtl) |
|---|---|---:|---:|---:|---:|---:|
| **`B1_lagged_screen`** | Highest lagged spread `> ₹100`, age `1..7`d | `100.00%` | `₹397.87` | `45.21%` | `45.21%` | `−₹641.26` |
| **`B2_fresh_val`** | `lag_age == 1`, road+dest fee `> ₹300` | `54.65%` | `₹374.90` | `18.49%` | `33.83%` | `−₹447.55` |
| **`B2_age_matched`** | `lag_age 1..3`, road+dest fee `> ₹200` | `72.03%` | `₹433.56` | `26.72%` | `37.10%` | `−₹525.25` |
| **`B_simple_activity_matched`** | `lag_age 1..3`, `rep14>=0.50`, `> ₹168.04` | `70.73%` | `₹440.97` | `23.48%` | `33.20%` | `−₹506.28` |
| **`MG_matched`** *(hard gates `T1..T4`)* | `rep14>=0.50 & dow8>=0.35`, `> ₹131.26` | `69.51%` | `₹467.90` | `18.57%` | `26.71%` | `−₹512.78` |
| **`RR_Abstain_matched`** *(Pre-Reg `A10`)* | `kappa*=5.0`, val-matched (`> ₹3.73`) | **`69.02%`** | **`₹475.36`** | **`17.23%`** | **`24.96%`** | **`−₹460.72`** |
| **`RR_Abstain_m0`** *(zero cutoff)* | `kappa*=5.0`, fixed `S_RR > 0` | `69.52%` | `₹475.76` | `17.43%` | `25.07%` | `−₹461.74` |

### Non-Apple Crops vs Apples (`a10_crop_splits.csv`) & HP Graded Apples (`a10_hp_apple.csv`)
- **Non-Apple Vegetables (`N = 52,207`):** Mean `₹288.55` vs `₹253.73` (`+₹34.82`, CI `[+₹23.89, +₹46.25]`), EpLoss `16.59%` vs `26.48%`, **`ES10` `−₹319.49` vs `−₹397.59`** (`+₹78.10`, CI `[+₹58.38, +₹99.51]`).
  - **Onion (`N = 19,820`):** Mean `+₹31.41`, `ES10 +₹101.93` CI `[+₹67.58, +₹139.80]`.
  - **Potato (`N = 14,923`):** Mean `+₹32.28`, `ES10 +₹88.91` CI `[+₹62.96, +₹113.95]`.
  - **Tomato (`N = 17,464`):** Mean `+₹40.87`, `ES10 +₹49.31` CI `[+₹17.25, +₹82.73]`.
- **Generic Apple (`N = 6,469`):** Mean `+₹98.14`, `ES10` statistically tied (`−₹1,537.30` vs `−₹1,533.29`, CI `[−₹209.47, +₹160.84]`).
- **HP Graded Apples (`N = 2,802` lagged):** `RR_Abstain_matched` (`78.69%` disp) reaches Mean `₹1,318.60` vs `B2_age_matched` `₹1,199.31` and `ES10` `−₹2,165.73` vs `−₹2,392.12`, **yet `44.63%` conditional loss rate remains too risky for field recommendation**.

---

## 3. Whiteboard Math in 4 Lines (Class-12 Arithmetic)

<!-- WORKED_EXAMPLE_START -->
**MP Tomato Route:** `road_km = 200`, `truck_hours = 6`, `fee_rate = 1.5%`, $P_{\text{orig,lag}} = ₹1,500$, $P_{\text{dest,lag}} = ₹2,000$:
1. **Road Freight:** $F = 35 + 0.45 \times 200 = ₹125.00/\text{qtl}$.
2. **NABCONS 20°C Shrinkage (`0.0325/24h`):** $s = 0.0325 \times (6 / 24) = 0.008125$.
3. **Open-Market Net after Destination Fee (`1.5%` on surviving sale):**
   $\widehat{\Delta}_{\text{open}} = 2,000(1 - 0.008125)(0.985) - 1,500 - 125 = +₹328.99/\text{qtl}$.
4. **RR-Abstain Score ($\kappa^* = 5.0$, missing bound $\widehat{\Delta}_{\text{miss}} = -5(125) - 1,500(0.008125) = -₹637.19$):**
   - Reliable yard (`p_rep = 0.85`): $0.85(328.99) + 0.15(-637.19) = +₹184.06 \implies$ **Dispatch**.
   - Thin sporadic yard (`p_rep = 0.35`): $0.35(328.99) + 0.65(-637.19) = -₹299.02 \implies$ **Abstain**.
<!-- WORKED_EXAMPLE_END -->

---

## 4. Red-Line Defensibility Rules (What You MUST & MUST NOT Claim)

- **DEFEND:** Reproducibility from tracked raw files (`make reproduce`), `R3` property proof (`dest_quote_date < date` and counterfactual `>= t*` invariance), equal-age/equal-menu fairness, destination gross-sale fee incidence (`M9`), pre-registered `A10` (`87a0b62`) surviving two-way cluster Holm (`p = 0.0020`) on both origin & destination schemes, non-apple vegetable consistency, and zero-penalty resilience (`div = 0.0`).
- **DO NOT CLAIM:** A conformal theorem (`R7`), observed farmer household cash income (`R7`), physical mandi closures (`R7`), ML tree necessity (removed!), live ERA5 weather effects (`98.64%` leaked -> stripped), Stage I `H2` success (`+₹6.13`, `p = 0.2699`), solved HP graded apples (`44.63%` cond loss rate), or an untouched post-April-2026 multi-state holdout (Gate J = `BLOCKED`, disclosed).
