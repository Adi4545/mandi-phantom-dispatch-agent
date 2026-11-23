# MandiGuard Revision v7 — Career Defense Master Sheet (`C2` & `A17`/`A18`/`v7` Audited)

> **Audit Guarantee (`R2` & `C2`):** Synced strictly to Revision v7 + Phase 6 stress outputs (`revision/results/v7_*.csv`, `v7_exp1..5*.csv`, `v7_summary.json`, `v7_exp_summary.json`). Zero Stage-I proxies, zero Stage-II conformal claims, zero weather in decisions, `59/59` verified citations, and zero untraceable numbers (`0` across `23/23` active docs). Supervised by Dr. Sonia, Shoolini University.

---

## 1. Your 45-Second Core Thesis Pitch

> *"Sir/Ma'am, online mandi portals like AGMARKNET show tempting spreads between home and distant wholesale markets, but a portal screen spread is not cash. Across `57,634` strictly lagged (`<= t - 1`) test episodes on our zero-lookahead `2024`-selected `171`-market panel in 6 states and 4 crops with sequential settlement and stylized APMC fees, chasing top lagged spreads loses money **`45.07%`** of the time (`ES10 = −₹642.15/qtl`, with `28.67%` turning back sequentially). Early prototypes leaked ERA5 weather, hit grid ceilings at `kappa* = 5.0`, and stayed inconclusive on `H2`. We stripped all ML and tuning down to **zero-parameter Class-10 arithmetic (`Safe_EV_Sunk_m0`: $p_{\text{dow}} G_{\text{1SD}} > F$)**, settlement-matched **`Safe_EV_Phys_m0` (`1.5F`)**, and a 4-function phone rule (**`RT_2F_Min_m0`: $p_{\min} G > 2F$**). Across the locked four-test `PREREG_A18` `R = 2,000` cluster bootstrap family (`p_holm_2s_prereg4 = 0.0040`, three clusterings), **`Safe_EV_Sunk_m0`** achieves `₹452.74/qtl` mean (`+₹33.12`), cuts losses to **`14.88%`** (`−11.56 pp`), strengthens **`ES10` to `−₹345.53/qtl`** (`+₹179.24` vs `B2`; `+₹91.67` matched vs `RR`), and improves dispatched-only **`cond_ES10` to `−₹447.48/qtl` (`+₹180.89`)** — outperforming retrained `Ridge`, `HGBR`, and `OR_Vargas` models on `cond_ES10`, surviving `<= t - 2` latency (`p = 0.001`) and coupled `S6_Frozen x Stoch_CondMAR` (`+₹366.85 cond_ES10`), and transferring without retuning across clean `166` markets (`2018–2023`, `N = 383,952`, winning `ES10` & `cond_ES10` in `6/6` years) — while openly disclosing Open-MAR (`B2 +₹97.01` Mean, break-even `25.45%`), free-return NS Mean, `HP B=12` (`cond_ES10 p = 0.1239`), `2020/2023` NS Mean, and 6 a.m. alert-triage scope prior to live *arhtiya* phone calls."*

---

## 2. Verified Benchmark Numbers (`171`-Mkt Primary `N = 57,634` + Clean `166`-Mkt `2018–2023` `N = 383,952`)

| Policy (`171`-Mkt Equal Menu Except `B1`) | Free Params | Dispatch Rate | Mean Net (₹/qtl) | Episode Loss Rate | Cond. Loss Rate | Exact `ES10` (₹/qtl) | Exact `cond_ES10` |
|---|---:|---:|---:|---:|---:|---:|---:|
| **`B1_lagged_screen`** (`spread > 100`, `1..7`d) | 1 | `100.00%` | `₹384.61` | `45.07%` | `45.07%` | `−₹642.15` | `−₹642.15` |
| **`B2_age_matched`** (`road + fee > ₹200`) | 1 | `71.73%` | `₹419.62` | `26.43%` | `36.85%` | `−₹524.78` | `−₹628.37` |
| **`MG_matched`** (Hard gates `T1..T4`, `₹133.03`) | 4 | `69.16%` | `₹454.07` | `18.35%` | `26.53%` | `−₹508.72` | `−₹638.55` |
| **`RR_Abstain_matched`** (Tuned `k*=5.0`, `m*=₹5.40`) | 2 | `68.75%` | `₹461.41` | `17.07%` | `24.84%` | `−₹459.46` | `−₹584.66` |
| **`Safe_EV_Sunk_m0`** (`p_dow * G_1SD > F`) | **0** | **`63.23%`** | **`₹452.74`** | **`14.88%`** | **`23.53%`** | **`−₹345.53`** | **`−₹447.48`** |
| **`Safe_EV_Phys_m0`** (`1.5F`, `0` tuned) | **0** | `60.84%` | `₹449.52` | **`13.70%`** | **`22.51%`** | **`−₹334.80`** | **`−₹447.33`** |
| **`RT_2F_Min_m0`** (Class-8 `p_min * G > 2F`) | **0** | `64.79%` | **`₹463.98`** | `16.21%` | `25.02%` | `−₹464.84` | `−₹618.35` |

### Key Stress Tests & Clean `166`-Mkt `2018–2023` Generalization (`v7_*.csv`, `v7_exp1..5*.csv`)
- **Subgroup Honesty (`6` States & `5` Crop Slices):** Unconditional `ES10` CIs are positive everywhere (`Safe_EV_Sunk_m0` vs `B2`), yet **HP (`B = 12`) fails significance on `cond_ES10` (`+₹250.82`, `p = 0.1239`, `p_stud = 0.1864`, `p_cgm_gstar = 0.2879`)** and Apple is borderline (`p = 0.0550`). Mean CIs cross zero in GJ (`p = 0.940`), MH (`p = 0.160`), UP (`p = 0.116`), Tomato (`p = 0.877`), and Apple (`p = 0.143`); Potato `Safe_EV` (`−₹242.00`) trails `RR` (`−₹224.80`) by `−₹17.20`. `RT_2F_Min_m0` keeps positive Mean CIs in all 6 states and all 5 slices (`p = 0.001–0.032`).
- **Clean `166`-Mkt `2018–2023` (`N = 383,952`, `0` Retuning):** Removing all `7` post-`2024` lookahead yards (`171 ∩ 173`) yields `Safe_EV_Sunk_m0` `₹356.57` vs `B2 ₹321.57` (`+₹35.00`), `12.64%` vs `25.21%` losses, `−₹304.29` vs `−₹473.56 ES10` (`+₹169.27`), and **`−₹421.35` vs `−₹576.44 cond_ES10`** (`+₹155.08`; `+₹174.27` vs equal-dispatch `B2_eq_SafeM0`, `p = 0.001`), holding on `115`-mkt (`N = 325,993`, `+₹159.83 ES10`) and NASA POWER × Sched #7 (`₹330.84` vs `₹291.41`). `ES10` & `cond_ES10` pass in `6/6` years (`p = 0.001`), while `2020` (`+₹12.93`, `p = 0.208`) and `2023` (`+₹20.35`, `p = 0.077`) Means are NS.
- **Phase 6 Adversarial Stress (`v7_exp1..5`):** Under `<= t-2` (`N = 57,047`, `t2_age_2_3`, `th = ₹300.0`), `Safe_EV_Sunk_m0` preserves `ES10 −₹364.48` vs `−₹508.36` & `cond_ES10 −₹484.32` vs `−₹672.39` (`p = 0.001`), while `RT_2F` loses `ES10` (`p = 0.363`) and `cond_ES10` (`p = 0.981`). Under coupled `S6_Frozen x Stoch_CondMAR_p1.00`, `Safe_EV` retains `+₹366.85 cond_ES10`. Retrained ML/OR Pareto (`v7_exp4`) shows `Safe_EV` `cond_ES10` (`−₹447.48`) beating `Ridge` (`−₹530.30`), `HGBR_RiskAverse_L500` (`−₹512.43`), and `OR_Vargas_MeanVar_g0002` (`−₹496.76`).
- **Missing-Quote Regimes, Hindsight & SUTVA (`v7_exp3`, `v7_exp5`):** At `div=0` (`+₹12.03`, `p = 0.220` / `₹0` `+₹11.21`, `p = 0.256`), Mean is NS (`ES10 +₹174.40`). At Open-MAR, `B2` wins Mean (`+₹97.01`; break-even `25.45%` / `+₹348.61` shift). Coupled Manski `Supp1..3` Mean shifts hit `−₹124.95` to `−₹325.40`. At `SUTVA 10%` crowding, `Safe_EV` Mean drops to `−₹5.31` (vs `B2 −₹75.37`); `k <= 2` cap keeps `₹207.00` Mean / `−₹230.30 ES10`. HP Apple (`N = 2,802`) keeps `41.38%` loss & `cond_ES10 p = 0.0940` NS.

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

- **DEFEND:** Deterministic single-command cleanroom rebuild, `R3` counterfactual perturbation + `<= t-2` proof, stylized `PIB relid=154554` / cumulative NABCONS / `30 qtl` load calibrations, locked `4`-test `R = 2,000` `p_holm_2s_prereg4 = 0.0040`, `cond_ES10 −₹447.48` vs `−₹628.37` & Pareto vs retrained `Ridge/HGBR/OR_Vargas`, coupled `S6_Frozen x Stoch_CondMAR`, clean `166`-mkt `2018–2023` (`N = 383,952`) + `115`-mkt (`325,993`), `59/59` verified citations, and `18`-work overlap with non-theorem humility.
- **DO NOT CLAIM:** A new statistical/conformal theorem, observed farmer household cash income, physical gate closures, universal Mean superiority (`div=0`, `hindsight_3d`, Open-MAR, `Supp1..3`, `2020/2023`, `SUTVA 10%`), `HP B=12` or HP Graded Apple `cond_ES10` significance, Potato `ES10` beating `RR`, replacing *arhtiya* phone calls, or a prospective live pilot (`Gate J = BLOCKED`).
