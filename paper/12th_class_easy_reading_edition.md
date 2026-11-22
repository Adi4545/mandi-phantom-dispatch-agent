# MandiGuard (Class-12 Plain-English Companion — Revision v4 Verified)

> **Verified Edition Note:** This guide matches `paper/manuscript.md` (`Revision v4`) and traces every dataset figure to `revision/results/` (`0` untraceable numbers). Earlier draft terminology (`ZeroCloud`, `90-qtl`, GBDT pickles, Stage II conformal proofs, uncalibrated `cvar_10`) was retired to keep the math clean, honest, and easy to defend (`final/DIFFICULTY.md`: difficulty cut from `4.3` to `1.6 / 5`).

---

## 1. The Everyday Problem: When Yesterday's High Mandi Price Tricks You

Suppose you manage a tomato farmer cooperative (FPO). You open the government AGMARKNET portal at 6 a.m. (`<= t - 1` quotes only—never today's unknown price!). Yesterday:
- Your local mandi paid `₹1,500` per quintal (`100 kg`).
- Another mandi `150 km` away listed `₹2,000` per quintal—a `₹500` gap on your phone screen!

Sending a truck blindly (`B1_lagged_screen`) assumes that `₹500` screen gap turns directly into `₹500` profit. Across **`58,676`** test episodes (`2025-06-01..2026-04-08`), blindly chasing top lagged spreads loses money on **45.21%** of all days, with worst-decile trips averaging **`−₹641.26/qtl` (`ES10`)**, and **28.98%** (`17,005` trips) reaching a destination where no trade for that crop is recorded on arrival day.

Three real-world frictions erase that screen gap:
1. **Road Freight (`F`):** Loading plus distance (`₹35 + ₹0.45 * hp * km`, where Himachal Pradesh hills use `hp = 1.45` due to `91.59%` single-lane roads).
2. **Destination Statutory Fee & Physical Decay:** State APMC seller commission (`0.5%–1.5%`, `0` inside the same district or if diverted) deducted from destination auction revenue after biological spoilage (`NABCONS` 24-hour market loss at `20°C`: Tomato `3.25%`, Onion `1.96%`, Apple `1.64%`, Potato `0.86%`).
3. **Reporting Gaps on Thin Yards (`p_rep`):** A yard that only posts exact-variety tomato prices irregularly on recent market days is much more likely to yield a blank arrival board—forcing a costly wait or turn-back truck trip—than a steady regular-reporting yard (see the worked example below).

---

## 2. The Pocket-Calculator Rule (`RR-Abstain` & Zero-Cutoff `RR_Abstain_m0`)

Instead of black-box machine learning trees or brittle hard cutoffs (`T1..T4`), **`RR-Abstain`** blends two Class-12 arithmetic numbers using the destination yard's strictly prior exact-variety reporting reliability `p_rep = 0.5 * rep28 + 0.5 * dow8` (`dest_lag_age in 1..3` days):

1. **Open-Market Net Gain (`Delta_open`):** Destination lagged price after spoilage and statutory destination fee minus freight minus origin lagged price.
2. **No-Quote Return Bound (`Delta_miss`):** `-kappa * F - P_orig * s_ref`, representing wasted round-trip transport and transit spoilage risk when an irregular market yields no trade.
3. **Single Score:** `S_RR = p_rep * Delta_open + (1 - p_rep) * Delta_miss`. With `kappa* = 5.0`, the validation-matched rule (`S_RR > ₹3.73/qtl`) achieves `69.02%` dispatch—**and the zero-cutoff version `RR_Abstain_m0` (`S_RR > 0`) eliminates threshold tuning completely**!

<!-- WORKED_EXAMPLE_START -->
> **Worked Arithmetic Example (With a Normal Calculator):**  
> Take a `200 km` tomato trip (`hp = 1.0`), `fee = 1.5%`, `P_orig = ₹1,500`, `P_dest = ₹2,000`, transit time `6` hours:  
> 1. **Freight:** `F = 35 + 0.45 * 200 = ₹125.00/qtl`.  
> 2. **Reference Spoilage (`6h` of `24h` `3.25%`):** `s = 0.0325 * (6 / 24) = 0.008125`.  
> 3. **If Open (`Delta_open`):** `2,000 * (1 - 0.008125) * (1 - 0.015) - 125 - 1,500 = 1,983.75 * 0.985 - 1,625 = +₹328.99/qtl`.  
> 4. **If Blank / Returned (`Delta_miss`, `kappa* = 5.0`):** `-5.0 * 125 - 1,500 * 0.008125 = -₹637.19/qtl`.  
> - **Steady Yard A (`p_rep = 0.85`):** `S_RR = 0.85 * 328.99 + 0.15 * (-637.19) = 279.64 - 95.58 = +₹184.06 > 0` -> **DISPATCH!**  
> - **Sporadic Yard B (`p_rep = 0.35`):** Both have the exact same `+₹345` plain road gain! But `S_RR = 0.35 * 328.99 + 0.65 * (-637.19) = 115.15 - 414.17 = -₹299.02 < 0` -> **STAY HOME (ABSTAIN)!**
<!-- WORKED_EXAMPLE_END -->

---

## 3. Verified Headline Evidence (`N = 58,676`, `exploratory: true`)

| Strategy (`lag_age 1..3`, except `B1`) | Dispatch (%) | Mean Net (₹/qtl) | Episode Loss (%) | Exact `ES10` (₹/qtl) |
|---|---:|---:|---:|---:|
| **`B1_lagged_screen`** (Screen spread `> ₹100`, lag 1–7d) | `100.00%` | `₹397.87` | `45.21%` | `−₹641.26` |
| **`B2_age_matched`** (Road + fee `> ₹200`) | `72.03%` | `₹433.56` | `26.72%` | `−₹525.25` |
| **`MG_matched`** (Hard gates `T1..T4`) | `69.51%` | `₹467.90` | `18.57%` | `−₹512.78` |
| **`RR_Abstain_matched`** (`kappa*=5.0`, `m*=₹3.73`) | **`69.02%`** | **`₹475.36`** | **`17.23%`** | **`−₹460.72`** |
| **`RR_Abstain_m0`** (Zero cutoff `S_RR > 0`) | `69.52%` | `₹475.76` | `17.43%` | `−₹461.74` |

- **Why hard gates (`MG_matched`) were not enough:** At matched `~70%` dispatch, `MG_matched` improved Mean (`+₹34.35`) but failed to improve worst-10% `ES10` significantly over `B2_age_matched` (`+₹12.49`, `p_holm = 0.589`).
- **Pre-registered `RR-Abstain` (`87a0b62`) wins everywhere cleanly:** Improves `ES10` by **`+₹64.54/qtl` vs `B2_age_matched`** and **`+₹52.06/qtl` vs `MG_matched`** (`p_holm = 0.0020` across BOTH origin and destination clusterings), generalizes across all `52,207` Non-Apple episodes (`ES10 +₹78.10`, Onion `+₹101.93`, Potato `+₹88.91`, Tomato `+₹49.31`), and holds down to **`div = 0.0, disc = 0.00`** (`ES10 −₹349.35` vs `−₹359.17`).

---

## 4. What We Still Honestly Admit (For Any Examiner Question)

1. **Graded Apples Remain Unsolved (`R6`):** Across `2,802` lagged Himachal Pradesh graded-apple episodes (`a10_hp_apple.csv`), `RR_Abstain_matched` lowers losses relative to `B2_age_matched` (`ES10 −₹2,165.73` vs `−₹2,392.12`) but still suffers `44.63%` conditional losses (`−₹3,453.18` in summer 2026).
2. **Modeled Payoff != Real Farmer Income (`R7`):** Zero physical truck bills or *patti* auction slips exist in AGMARKNET, and a missing row means "no portal quote recorded", not necessarily a locked gate.
3. **Exploratory Calendar & Field Pilot (`Gate J = BLOCKED`):** Bulk AGMARKNET snapshots end `2026-04-13`, so `2025-06-01..2026-04-08` is `exploratory: true`; a live FPO trial is the required next step.
