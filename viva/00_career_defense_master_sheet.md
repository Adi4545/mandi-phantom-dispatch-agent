# MandiGuard Revision v6 — Career Defense Master Sheet (`C2` & `A17`/`A18`/`v6` Verified)

> **Audit Guarantee (`R2` & `C2`):** All Stage I unlagged quantile-mean proxies, Stage II pseudo-conformal bounds, `336` buggy cluster keys, and even tuned `kappa* = 5.0` workarounds have been superseded cleanly. Every number below traces verbatim to `revision/results/` (`0` untraceable numbers) or verified legacy Stage I files (`results/confirmatory_holm_summary.csv`).

---

## 1. Your 45-Second Core Thesis Pitch

> *"Sir/Ma'am, online mandi portals like AGMARKNET show tempting spreads between home and distant wholesale markets, but a portal screen spread is not cash. Across `58,676` strictly lagged (`<= t - 1`) test episodes in 6 states and 4 crops with sequential settlement and destination APMC fees, chasing the top spread loses money **`45.21%`** of the time (`ES10 = −₹641.26/qtl`, with `28.98%` turning back sequentially). Early prototypes leaked ERA5 weather into decisions, hit grid ceilings at `kappa* = 5.0`, and broke on `H2`. We stripped all tuning and ML trees down to **zero-parameter Class-10 arithmetic (`Safe_EV_Sunk_m0`: $p_{\text{dow}} G_{\text{1SD}} > F$)**, settlement-matched **`Safe_EV_Phys_m0` (`1.5F`)**, and a 4-function phone rule (**`RT_2F_Min_m0`: $p_{\min} G > 2F$**). With zero tuned thresholds across `R = 5,000` cluster bootstraps, **`Safe_EV_Sunk_m0`** achieves `₹465.59/qtl` mean (`+₹32.03` vs `B2`, `p_holm_2s = 0.0028–0.0436`), cuts losses to **`14.93%`** (`−11.79 pp`, `p_holm_2s = 0.0024`), and strengthens **`ES10` to `−₹344.09/qtl`**—beating age-matched road dispatch by **`+₹181.17/qtl`** (`p_holm_2s = 0.0024` across all three spatiotemporal clusterings `171–173` and 1-, 2-, 4-week blocks; `Safe_EV_Phys_m0` `+₹191.69`; descriptive unmatched gains `+₹168.69` over hard gates and `+₹116.63` over tuned `RR-Abstain`). Gains hold on a freshly rebuilt `2024`-only `171`-market panel (`N = 57,634`), `100.0%`-covered realized ERA5 arrival-weather settlement (`+₹190.43` / `+₹187.80` `ES10`), **every individual state (`6/6`) vs `B2`**, all `36/36` tornado cells, `N = 88,014` unconditional origin episodes, and HP graded apples (`−₹1,454.86` vs `−₹2,392.12`), while honestly disclosing exact silent-market break-even (`+₹328.37/qtl` above turn-back / `23.79%` MAR share) and acting strictly as a 6 a.m. alert filter prior to live *arhtiya* phone confirmation."*

---

## 2. Verified Benchmark Numbers (`N = 58,676` Test Episodes, `exploratory: true`, Two-Sided Holm)

| Policy (`lag 1..3` equal menu except `B1`) | Free Params | Dispatch Rate | Mean Net (₹/qtl) | Episode Loss Rate | Cond. Loss Rate | Exact `ES10` (₹/qtl) | Loss Given Loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| **`B1_lagged_screen`** (`spread > 100`, `1..7`d) | 1 | `100.00%` | `₹397.87` | `45.21%` | `45.21%` | `−₹641.26` | `−₹271.24` |
| **`B2_age_matched`** (`road + fee > ₹200`) | 1 | `72.03%` | `₹433.56` | `26.72%` | `37.10%` | `−₹525.25` | `−₹293.73` |
| **`B_simple_activity_matched`** (`rep14>=0.5`, `₹168.04`) | 2 | `70.73%` | `₹440.97` | `23.48%` | `33.20%` | `−₹506.28` | `−₹298.77` |
| **`MG_matched`** (Hard gates `T1..T4`, `₹131.26`) | 4 | `69.51%` | `₹467.90` | `18.57%` | `26.71%` | `−₹512.78` | `−₹331.27` |
| **`RR_Abstain_matched`** (Tuned `k*=5.0`, `m*=₹3.73`) | 2 | `69.02%` | `₹475.36` | `17.23%` | `24.96%` | `−₹460.72` | `−₹308.18` |
| **`Safe_EV_Sunk_m0`** (`p_dow * G_1SD > F`) | **0** | **`63.27%`** | **`₹465.59`** | **`14.93%`** | **`23.61%`** | **`−₹344.09`** | **`−₹260.05`** |
| **`Safe_EV_Sunk_matched`** (val-match `70.71%`) | 1 | `70.90%` | `₹469.94` | `18.51%` | `26.11%` | `−₹366.41` | `−₹243.04` |
| **`RT_2F_Min_m0`** (Class-8 `p_min * G > 2F`) | **0** | `64.92%` | **`₹478.38`** | `16.26%` | `25.05%` | `−₹468.32` | `−₹325.70` |

### Key Stress Tests (`a18_crop_and_state_splits.csv`, `a18_missing_regimes.csv`, `a18_hp_apple.csv`)
- **All 6 States (`Safe_EV_Sunk_m0` vs `B2`):** Strictly positive 95% `ES10` CIs everywhere—Gujarat `[+₹138.05, +₹369.11]`, HP `[+₹59.18, +₹637.28]`, Karnataka `[+₹58.23, +₹184.08]`, MP `[+₹139.94, +₹303.97]`, Maharashtra `[+₹48.71, +₹303.07]`, UP `[+₹48.00, +₹139.86]`.
- **Crops (`Safe_EV_Sunk_m0` vs `B2`):** Non-Apple (`N = 52,207`) `ES10 +₹135.58` (`[+₹108.37, +₹165.94]`), Apple (`N = 6,469`) `ES10 +₹561.37` (`[+₹172.22, +₹1,216.91]`). On Tomato (`N = 17,464`), `Safe_EV_Sunk_m0` keeps mean flat (`₹461.42` vs `₹462.27`) while improving `ES10` (`+₹195.65`), whereas `RT_2F_Min_m0` raises Tomato mean to `₹504.35`. Transparently, on Potato (`N = 14,923`), `Safe_EV_Sunk_m0` (`−₹243.97`) trails `RR_Abstain_matched` (`−₹227.37`) by `−₹16.60/qtl` on `ES10`.
- **HP Graded Apples (`N = 2,802`):** `Safe_EV_Sunk_m0` reaches Mean `₹1,354.85` (beating `B2` `₹1,199.31` & `MG` `₹1,028.05`) and `ES10 −₹1,454.86` (beating `B2 −₹2,392.12`, `MG −₹1,953.20`, `RR −₹2,165.73`), yet `41.38%` cond loss keeps graded apples too volatile for unconfirmed dispatch.
- **Missing-Quote Regimes & Exact Break-Even (`v6_breakeven.csv`):** At `div_0.0_spoil_only` (`+₹173.65 ES10`) and `exact_zero_divert_payoff_0` (`+₹169.79 ES10`, `4.52%` vs `6.55%`, `p_2s = 0.002`), `Safe_EV_Sunk_m0` holds strongly whereas `RR` becomes NS (`p_2s = 0.603..0.797`). At `open_yard_MAR_lagged_price`, `B2` wins Mean (`₹722.66` vs `₹620.08`; `₹707.04` vs `₹606.48` ERA5) while `Safe_EV` wins `ES10` (`+₹190.00`; `+₹196.38` ERA5). Exact break-even requires silent trips `+₹328.37/qtl` uniform shift above turn-back (`+₹95.97` flat constant-payoff counterfactual; `23.79%` MAR share; `+₹363.74` / `+₹119.16` / `26.65%` on `171`-mkt ERA5).
- **Unconditional Origin Panel (`N = 88,014` restoring `29,338` missing-d0 episodes):** `Safe_EV_Sunk_m0` Mean `₹483.03` vs `B2 ₹445.37`, `ES10 −₹335.04` vs `−₹515.93`; `RT_2F_Min_m0` Mean `₹493.15`.

---

## 3. Whiteboard Math in 3 Lines (Zero Magic Parameters!)

<!-- WORKED_EXAMPLE_START -->
**MP Tomato Route:** `road_km = 200`, `fee = 1.5%`, $P_{\text{orig,lag}} = ₹1,500$, $P_{\text{dest,lag}} = ₹2,000$, $F_{\text{road}} = ₹125$, `cv28 = 0.15`:
1. **Plain fee spread:** $G = 2,000(0.985) - 1,500 = +₹470.00/\text{qtl}$; **1-SD spread:** $G_{\text{1SD}} = 2,000(0.85)(0.985) - 1,500 = +₹174.50/\text{qtl}$.
2. **Steady Weekday Yard (`dow8 = 0.90`, `p_min = 0.85`):** `Safe_EV_Sunk`: $0.90(174.50) - 125 = +₹32.05 > 0$; `RT_2F_Min`: $0.85(470) - 250 = +₹149.50 > 0 \implies$ **Dispatch**.
3. **Sunday/Thin Yard (`dow8 = 0.20`, `p_min = 0.20`):** `B2` scores `+₹345`, yet zero-param rules give $0.20(174.50) - 125 = -₹90.10$ and $0.20(470) - 250 = -₹156.00 \implies$ **Abstain**.
<!-- WORKED_EXAMPLE_END -->

---

## 4. Red-Line Defensibility Rules (What You MUST & MUST NOT Claim)

- **DEFEND:** Reproducibility (`make reproduce`), `R3` counterfactual perturbation proof, destination gross-sale fee incidence (`M9`), fixed `171–173` market clustering across 3 schemes and 1-, 2-, 4-week blocks, strict two-sided Holm at `R = 5,000` (`p_holm_2s = 0.0024` for tail/loss/`RT`-mean; `0.0028–0.0436` for `Safe_EV` mean vs `B2`), zero-parameter `Safe_EV_Sunk_m0` / `Safe_EV_Phys_m0` winning across fresh `2024`-only `171` markets, realized ERA5 arrival weather, all 6 states vs `B2`, 36 tornado cells, exact-geocodes (`N = 40,690`), and `N = 88,014` unconditional origin panels.
- **DO NOT CLAIM:** A conformal theorem (`R7`), observed farmer household cash income (`R7`), physical market closures (`R7`), replacing live *arhtiya* phone calls (`A17` #10), ML tree necessity, weather inside decision rules (`98.64%` leaked -> stripped from decisions, used strictly in realized arrival-weather settlement), Stage I `H2` (`+₹6.13`, `p = 0.2699`), solved HP graded apples (`41.38%` cond loss rate), universal Potato dominance over `RR` (`−₹16.60`), or an untouched post-April-2026 bulk holdout (`Gate J = BLOCKED`).
