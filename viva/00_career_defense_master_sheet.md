# M.Tech Viva Career Defense Master Sheet (`MandiGuard` Stage I + `MandiGuard-CRC` Stage II)
### *Read This 10 Minutes Before Walking Into Your Thesis Defense Room*

---

## 1. Your 45-Second Core Story (Memorize Word-for-Word)
> *"Sir/Ma'am, most mandi AI papers only predict prices and get farmers hurt when distant yards are closed, lack their exact crop variety, or lose perishable vegetables in summer heat. Across 69,526 holdout opportunities and 661,192 historical episodes spanning nearly 10 years (2017–2026), naive price-board chasing loses money 40.46% of the time and standard point-ML loses 45.28%. My thesis follows a strict Two-Stage scientific methodology:*  
> *In **Stage I (Pre-Registered Confirmatory System)**, I built **`MandiGuard` v1**: a deterministic four-step verification cascade (`T1` market vitality → `T2` OSRM road and statutory APMC fee → `T3` Q10 weather spoilage → `T4` 80% conformal safety cushion) with an explicit `REFUSE_PHANTOM_SPREAD` option. Across `N = 69,526`, it beats naive chasing by **+₹102.78/qtl** (+₹3,083.5 per 30-qtl truck), cuts episode losses by 37.29 pp vs point-ML, limits worst-10% tail loss to -₹37.89/qtl, and matches upfront verification using 44.4% fewer lookups—while transparently failing `H2` against same-day fresh road greedy `B2` (+₹6.13/qtl, p = 0.2699).*  
> *In **Stage II (`[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]`)**, I audited why Stage I stalled against `B2` and under-dispatched HP Graded Apples (`Exp 16`): dropping missing arrival rows (`dropna`) understated 3-day downside tail risk by up to **2.54x**, pooled conformal bounds swung from 90.46% (`Q1_Calm`) to 67.80% (`Q4_Volatile`), and sub-grade `T1` sparsity blocked **77.82%** of holdout `B2`-profitable HP Apple lots. Training dual-head estimators directly on uncensored payoff `Y_full` with validation-frozen CRC penalty `lambda* = 0.15` (`Exp 17`, zero holdout tuning) plus grade-aware `T1` raises holdout return to **₹479.17/qtl** (`₹14,375.1` per truck)—beating `B1` (+₹129.16/qtl, p = 0.0004), **`B2` (+₹32.51/qtl, p = 0.0016)**, and `MG_v1` (+₹26.38/qtl, p = 0.0002), winning cleanly on trap-free `N = 10,162` open yards (**₹533.75/qtl**, 7.14% LTR), and lifting 2026 HP Graded Apples +34.2% (**₹812.08/qtl**)."*

---

## 2. The 4 Minimal Numbers to Keep on Your Fingertips

### View 1: Full Holdout (`N = 69,526`, Modeled Trap Penalties)
| Minimal Metric (`N = 69,526`) | Naive `B1` | Fresh+Road `B2` | Point ML `B3` | `MandiGuard` Stage I (`MG_v1`) | **`MandiGuard-CRC` Stage II (`Post-Diag`)** |
|:---|---:|---:|---:|---:|---:|
| **1. Mean Net Gain (₹/qtl)** | ₹350.01 | ₹446.66 | ₹330.85 | ₹452.79 (+₹102.78 vs `B1`) | **₹479.17** (+₹129.16 vs `B1`, **+₹32.51 vs `B2`**) |
| **2. Loss-Trip Rate (%)** | 40.46% | 18.11% | 45.28% | **9.97%** | **10.48%** |
| **3. Worst-10% Loss (₹/qtl)** | -₹1,062.66 | -₹436.67 | -₹1,097.80 | **-₹37.89** | **-₹44.03** |
| **4. Live API Calls / Query** | 0 *(blind)* | 7.87 | 7.87 | **8.75** (-44.4% vs `B4` 15.74) | **9.07** |

### View 2: Fair Matched Complete-Observation Cohort (`N = 10,162`, Identical Episodes, Zero Simulated Traps)
| Minimal Metric (`Matched_AllTopK_Observed_d0`, `N = 10,162`) | Naive `B1` | Fresh+Road `B2` | Point ML `B3` | Stage I `MG_v1` | **Stage II `MandiGuard-CRC`** |
|:---|---:|---:|---:|---:|---:|
| **1. Mean Net Gain (₹/qtl)** | ₹472.51 | ₹469.99 | ₹553.22 | ₹510.89 | **₹533.75** (+₹61.24 vs `B1`, +₹63.76 vs `B2`, +₹22.86 vs `MG_v1`) |
| **2. Dispatch Rate (%)** | 74.78% | 64.38% | 73.47% | 47.31% | **55.41%** |
| **3. Loss-Trip Rate (%)** | 19.84% | 15.09% | 14.77% | **6.82%** | **7.14%** |
| **4. Worst-10% Loss (₹/qtl)** | -₹694.72 | -₹94.70 | -₹362.40 | -₹36.07 | **-₹35.00** |

*(Exploratory Appendix illustrations `Exp 11`–`Exp 13b`—not main thesis contributions—separately illustrate `ACI`, `ZeroCloud` [3.84–5.53 calls], and 90-qtl `FPO` pooling [₹477.28/qtl].)*

---

## 3. Whiteboard Math in 5 Lines (Stage I vs Stage II!)
**Setup (30-qtl Madhya Pradesh Tomato, 200 km / 6 hrs, 40°C May heat, ₹1,400 home vs ₹2,000 portal):**
1. **Portal Price:** ₹2,000.00/qtl
2. **Heat Rot (Q10):** At 20°C, NABCONS loss = 3.25%/24h. At 40°C (+20°C), decay speed is 4×; over 6h (1/4 day), 3.25% × 1/4 × 4 = 3.25% rots → **-₹65.00** (₹1,935.00 left)
3. **Truck + MP Tax (1.5%):** ₹35 + (₹0.45 × 200) + (1.5% × ₹1,400) = **-₹146.00** (₹1,789.00 left)
4. **Stage-I 80% Cushion (8% dip) vs Stage-II CRC Penalty (`lambda* = 0.15`):**
   * *Stage I (`MG_v1`):* Subtract 8% × ₹1,935 = **-₹154.80** → ₹1,634.20 − ₹1,400 = **+₹234.20/qtl** (`> ₹50` → `DISPATCH`).
   * *Stage II (`MandiGuard-CRC`):* Train on uncensored `Y_full` to get `mu_hat = +₹320/qtl` and loss probability `p_loss = 0.08`; score = `320 - 0.15 * 1400 * 0.08 = 320 - 16.80 = +₹303.20/qtl` (`> ₹50` → `DISPATCH`), automatically avoiding calm-market over-cushioning while penalizing high `p_loss` crash routes!

---

## 4. 16 Tough Examiner Questions (Calm, Direct Answers)

1. **Q: Why did `H2` against `B2_FreshRoadGreedy` fail statistical significance (p = 0.2699)?**  
   **A:** We admit cleanly that `B2` ties `MandiGuard` on overall mean profit (₹446.66 vs ₹452.79/qtl; the +₹6.13/qtl difference is within sampling noise). Rather than higher average return, `MandiGuard` trades away borderline high-variance trips (48.66% vs 62.11% dispatch) to halve loss trips (9.97% vs 18.11%) and limit worst-10% tail losses (-₹37.89 vs -₹436.67/qtl); the 4-state native-NWP check (+₹31.82/qtl over `B2` across 42,766 episodes, `Exp 2b`) is exploratory subgroup context only.

2. **Q: Isn't `H4` (44.4% fewer calls than `B4`) true simply by design?**  
   **A:** Yes—we agree immediately that fewer average calls (8.75 vs 15.74) follow directly from cheap-first early pruning by design. The substantive empirical payoff appears under tight query budgets (`Exp 5`): when capped at `B = 6` calls per episode, `MandiGuard` achieves ₹403.85/qtl (5.05 calls) vs `B4`'s ₹299.31/qtl (5.75 calls), a +₹104.54/qtl margin.

3. **Q: On HP Graded Apples (`Exp 3` & Stage-II `Exp 16`–`17`), why does `B2` earn ₹1,150.83/qtl while Stage-I `MandiGuard` earns ₹605.06/qtl (`Grade A` 5.39%)—and what really caused it?**  
   **A:** Stage-II `Exp 16` overturned our initial wide-conformal-interval guess: on `B2`-dispatched / `MG_v1`-refused HP Apple lots, **`77.82%` on holdout** (`82.75%` warmup) were blocked at **`T1`** (`open_prob_14d < 0.50` due to sparse `Grade A`/`Range-1` tags), vs only `22.18%` (`16.59%`) at `T4`. Stage I still cut traps 7x (`94.14% → 13.24%`) and `CVaR10` (`-₹8,487.24 → -₹102.76`). Adding Stage-II grade-aware `T1` liquidity (`MandiGuard-CRC`) lifts Apple mean **+34.2% to ₹812.08/qtl** (`Grade A` `₹205.46 → ₹477.56/qtl`, LTR `20.0% → 11.54%`), while candidly remaining below `B2` (`₹1,150.83`) at 2.4x safer tail (`-₹113.40` vs `-₹272.50`).

4. **Q: Why does removing Weather `T3` slightly raise unconditional profit by ₹2.46/qtl (₹455.25 vs ₹452.79)?**  
   **A:** Dropping `T3` admits 1.52% extra hot or rainy trips (50.18% vs 48.66% dispatch) where a few spot price spikes offset spoilage. Keeping `T3` improves safety on the 21,656 extreme heat/rain episodes, cutting heat/rain loss rate (11.39% → 10.10%) and tail loss (-₹67.49 → -₹57.11/qtl).

5. **Q: Why did 8 years of training data (2017–2024, 3.44M rows) add only +₹2.15/qtl over 1 year (2024)?**  
   **A:** This indicates Indian mandi spreads shift across macro regimes (GST, COVID, El-Niño), so older pre-2024 spreads add diminishing value (₹452.79 → ₹454.94/qtl). A single recent prior year plus causal conformal cushions is simpler and nearly as effective.

6. **Q: You have no live farmer receipts or field interviews—doesn't modeling freight, Q10 rot, and closed-yard penalties weaken the economic claims?**  
   **A:** Yes, we state that limitation openly: truck freight (₹35 + ₹0.45/km), Q10 rot, and closed-yard diversion penalties have no live farmer receipts or field interviews yet and are modeled from published government anchors. NABCONS (2022) spoilage accounts for ₹68.76/qtl of naive erosion compared with ₹714.90/qtl from observed AGMARKNET price drops and missing-yard episodes, `MandiGuard` stays ahead of `B1` across all 9/9 `[0.5×..1.5×]` sensitivity scenarios (+₹82.62 to +₹121.42/qtl), and `Exp 15` / `Exp 17` test the full crossover curve and matched complete-observation cohorts directly.

7. **Q: How did you prevent data leakage and hindsight margin tuning, and what do your 22/22 `pytest` checks verify?**  
   **A:** Stage-I model weights trained strictly on 2024 (701,932 rows), the ₹50/qtl threshold froze on Jan–May 2025 (`Val_2025H1`, 280,697 rows), `H1`–`H4` were logged in Git commit `e421d15` before holdout ran, and conformal residuals update only once `arrival_date <= decision_date`. Stage-II `MandiGuard-CRC` trains strictly on settled `Train_2024` (`arrival_date + 2d <= 2024-12-31`) and freezes `lambda* = 0.15` strictly on `Val_2025H1` (`[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]`). All 22/22 automated tests pass—and we note clearly that they verify code reproducibility, data manifests, Dual-Tier parity, and temporal leakage guards rather than field economics.

8. **Q: Why didn't you run GPT-4, LSTMs, or Deep RL at runtime—and is `MandiGuard` an autonomous agent?**  
   **A:** `MandiGuard` is a deterministic, **risk-gated dispatch decision-support system** (four-step verification cascade), not an autonomous LLM agent—so it needs no cloud LLM API calls, incurs zero token cost, and runs locally in 0.075–0.099 ms/query. Even inside the same `T1`–`T4` cascade (`Exp 11` Appendix illustration), `Deep_MLP_Conformal` (₹435.38/qtl) and `Contextual_UCB_Bandit` (₹406.47/qtl) trailed `MandiGuard_Standard` (₹452.79/qtl) on the 6-state holdout.

9. **Q: Explain "80% Conformal LCB" and "Two-Way Cluster Bootstrap" in 2 sentences each.**  
   **A:** **80% Conformal LCB:** Subtract the 80th-percentile worst recent forecast mistake so realized arrival prices meet or exceed our floor roughly 80% of the time (78.85% validation, 79.07% holdout). **Two-Way Cluster Bootstrap:** Resample whole origin mandis (174) and whole 2-week blocks (23) together 5,000 times so correlated market shocks never produce artificially narrow confidence intervals.

10. **Q: (`Exp 12` Appendix illustration) How can `ZeroCloud_Full` earn +₹2.54/qtl more than Standard (₹455.33 vs ₹452.79) with fewer calls?**  
    **A:** *(Presented strictly as an Appendix illustration, not a main contribution:)* Standard sorts Step-0 candidates by raw portal spread before checking roads (`T2`), letting distant high-freight traps crowd the top 5; caching `T2` locally lets `ZeroCloud_Full` pre-rank Step-0 options by freight-adjusted spread first, promoting profitable nearby mandis into the top-5 shortlist.

11. **Q: What about the 43 Open-Meteo grid cells that hit API rate limits?**  
    **A:** All 145/145 realized ERA5 cells (2024–2026) and all 114 NASA POWER cells (2017–2023) have complete coverage with no missing weather rows; the 43 remaining historical-NWP cells use a causal `<= t` Ridge nowcaster trained strictly on 2024 data (1.047°C MAE), and exploratory `Exp 2b` isolates the 42,766 episodes in the 4 states with full native NWP forecasts (+₹59.53/qtl vs `B1`, +₹31.82/qtl vs `B2`).

12. **Q: Why does Tomato show higher naive `B1` mean (₹547.64) than `MandiGuard` (₹522.48/qtl)?**  
    **A:** Naive `B1` earns +₹25.16/qtl higher average revenue only by chasing high-variance scarcity spikes that lose money on 32.38% of episodes (nearly 1 in 3); `MandiGuard` still beats `B2` (₹484.64) and `B3` (₹515.05) while cutting Tomato episode losses from 32.38% to 5.09%.

13. **Q: Why does Onion fail 48.69% of the time under `B1` even though Tomato rots faster?**  
    **A:** Onion's average screen spread (₹704.50/qtl) is small relative to Apple (₹3,499.80), so highway freight (₹138.07), spoilage (₹28.60), and ₹484.23 from variety traps and arrival reversion (57.26% closed/variety traps) leave only +₹53.61/qtl conditional net. Across all Onion episodes, `MandiGuard` increases per-episode mean gain from ₹46.50 (`B1`) to ₹163.41/qtl.

14. **Q: Why did the three-module quantized coordinator `B5` lose -₹15.40/qtl vs unified `MandiGuard`?**  
    **A:** Splitting into `Scout -> Weather -> RiskGate` communicating over discrete ₹150 profit buckets rounds off borderline opportunities near the ₹50 cutoff, cutting dispatch rate (41.59% vs 48.66%) while spending virtually the same live calls (8.76 vs 8.75).

15. **Q: (`Exp 11` Appendix illustration) How does `MandiGuard_ACI` reduce HP Apple tail risk without retraining?**  
    **A:** *(Shown in Appendix A.1 as an exploratory extension:)* When realized arrivals break 20% error rates, online Gibbs–Candès ACI lowers α_Apple (0.200 → 0.164, and 6-state Tomato to 0.038), trimming 1.49 pp of risky trips and reducing HP Apple worst-10% loss by 27.6% (-₹102.76 → -₹74.42/qtl).

16. **Q: (`Exp 13`/`13b` Appendix illustrations) What do `FPO 90-qtl`, `Split_Top2`, and `Biological Spoilage Clock` illustrate?**  
    **A:** *(Presented strictly as Appendix deployment illustrations, not main contributions:)* Under an illustrative 0.70× truck factor, sharing one 90-qtl FPO truck lifts net gain to ₹477.28/qtl (+₹24.49 over solo 30-qtl, +₹67.75 over solo 10-qtl); splitting 50/50 across top-2 markets lowers closed traps from 16.17% to 9.85%; and the Q10 Spoilage Clock estimates safe transit life compressing from 110.8 h (20°C) to 24.1 h (42°C) on Tomato before formatting ≤ 160-char SMS cards.

---

## 5. Dual-Tier Data Verification (`Exp 14`), Open-Yard Defense (`Exp 15`) & Stage-II `MandiGuard-CRC` (`Exp 16`–`17`)

* **"Didn't your 10-year CSVs come from a public mirror? How closely do they match official `data.gov.in` / AGMARKNET 2.0?" (`Exp 14`):**  
  Our bulk 2017–2026 CSVs came from a public AGMARKNET archive mirror. `Exp 14` audits two official tiers: **Tier 1** (`2023-10-18`, 172 matched core-panel keys out of 6,434 all-India XML rows from official `data.gov.in` Resource `9ef84268-d588-465a-a308-a864a43d0070`) shows `100.0%` exact parity on `Min_Price` and `Max_Price` and `99.42%` (`171/172`) on `Modal_Price`; **Tier 2** (**149-day direct official `AGMARKNET 2.0` export** `2025-11-07..2026-04-13`, `2,042` matched market–variety–grade–day rows) shows **`100.00%` exact parity across all three price columns (`Min_Price`, `Max_Price`, `Modal_Price`)**—plus 22 live Nov-2026 queries against `agmarknet.gov.in` (11/22 non-reporting across 7 days).

* **"Stage-II `[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]` Findings (`Exp 16`–`17`, `Val lambda* = 0.15`):"**
  * **`Exp 16` Root Causes:** (1) `dropna(target_ret)` discarded `55.83%` of raw `Train_2024` corridors (`12.64%` post-`T1`) and understated 3-day Q20 downside drops up to **2.54x** (`Holdout` `age_3d`: `-10.55%` vs `-26.82%`); (2) commodity-pooled conformal bounds collapsed from **90.46%** (`Q1_Calm`) to **67.80%** (`Q4_Volatile`, true Q80 error `17.08%` vs `8.89%` cushion); (3) sub-grade `T1` sparsity blocked **77.82%** of holdout HP Apple lots where `B2` dispatched (`+₹3,511.16/qtl`), vs only `22.18%` at `T4`.
  * **`Exp 17` (`MandiGuard-CRC`):** Rung ladder on `Holdout_2025_2026` (`N=69,526`): `MG_v1` `₹452.79` → `Rung1` `₹455.15` → `Rung2` `₹469.29` → **`Rung3` `₹479.17/qtl`** (`₹14,375.1` truck, `55.09%` disp, `10.48%` LTR, `-₹44.03` CVaR10, `9.07` calls; `+₹129.16` vs `B1` `p=0.0004`, **`+₹32.51` vs `B2`** `p=0.0016`, `+₹26.38` vs `MG_v1` `p=0.0002`); on trap-free `N=10,162`: **`₹533.75/qtl`** (`7.14%` LTR, `-₹35.00` CVaR10); on HP Apple `2026`: **`₹812.08/qtl`** (`+34.2%`, Grade A `₹205.46 → ₹477.56`). *(Adapted CRC validation heuristic on `Val_2025H1`; no Theorem 1 exchangeability claim.)*

* **"What if 3-day missing portal entries aren't closed yards—what happens under milder penalties or strictly observed arrivals?" (`Exp 15` Dual-View Defense):**
  * **View 1 — Trap-Penalty Crossover Curve (`All_Shortlisted_Episodes`, N = 69,526):**
    1. `1_Baseline_Div1.5x_Disc10pct` (1.5× return freight, 10% variety discount): `B1` ₹350.01 (40.46% LTR, -₹1,062.66 CVaR10), `B2` ₹446.66 (18.11% LTR, -₹436.67), `B3` ₹330.85 (45.28% LTR, -₹1,097.80), `MandiGuard` ₹452.79 (48.66% disp, 9.97% LTR, -₹37.89) → `MG - B1` = +₹102.78, `MG - B2` = +₹6.13, `MG - B3` = +₹121.94.
    2. `2_OneWayDiv_Div1.0x_Disc10pct`: `B1` ₹362.61, `B2` ₹449.33, `B3` ₹344.88, `MandiGuard` ₹454.27 (9.97% LTR) → `MG - B1` = +₹91.66, `MG - B2` = +₹4.94, `MG - B3` = +₹109.39.
    3. `3_HalfDiv_Div0.5x_Disc5pct`: `B1` ₹413.57 (38.01% LTR), `B2` ₹452.32, `B3` ₹409.88 (42.07% LTR), `MandiGuard` ₹456.00 (9.97% LTR) → `MG - B1` = +₹42.43, `MG - B2` = +₹3.68, `MG - B3` = +₹46.12.
    4. `4_ZeroDiv_Div0.0x_Disc0pct` *(crossover boundary: 0.0× return freight, 0% discount)*: `B1` ₹468.17 (18.52% LTR, -₹877.41), `B2` ₹456.09 (12.50% LTR, -₹70.80), `B3` ₹479.09 (20.40% LTR, -₹851.02), `MandiGuard` ₹458.17 (6.09% LTR, -₹28.70) → `MG - B1` = -₹10.00, `MG - B2` = +₹2.08, `MG - B3` = -₹20.93.
    5. `5_ZeroTrap_BreakEven0_Missing3d` *(missing 3d yields ₹0.00 break-even)*: `B1` ₹376.77 (8.33% LTR), `B2` ₹457.24, `B3` ₹385.42 (4.93% LTR), `MandiGuard` ₹459.03 (5.96% LTR) → `MG - B1` = +₹82.26, `MG - B2` = +₹1.79, `MG - B3` = +₹73.61.
  * **View 2 — Fair Matched Complete-Observation Cohorts *(identical episode set across ALL 4 policies — zero simulated trap rules, zero selection bias)*:**
    * `6_Fair_Matched_AllTopK_Observed_d0` (N = 10,162 identical episodes where every top-5 candidate has observed arrival-day `d0` price): `MandiGuard` Stage I ₹510.89 (47.31% disp, 6.82% LTR, -₹36.07 CVaR10) and **Stage II `MandiGuard-CRC` ₹533.75 (55.41% disp, 7.14% LTR, -₹35.00 CVaR10)** beat `B1` ₹472.51 (74.78% disp, 19.84% LTR, -₹694.72) and `B2` ₹469.99 (64.38% disp, 15.09% LTR, -₹94.70). Point-ML `B3` earns ₹553.22 (73.47% disp) at 14.77% LTR and -₹362.40 tail loss.
    * `7_Fair_Matched_AllTopK_Observed_3d` (N = 16,849 identical episodes where every top-5 candidate trades exact variety in `d0..d2`): `MandiGuard` Stage I ₹592.53 (54.31% disp, 7.74% LTR, -₹48.25 CVaR10) beats `B1` ₹581.06 (81.45% disp, 20.63% LTR, -₹829.21; +₹11.47) and `B2` ₹572.09 (70.97% disp, 15.81% LTR, -₹588.86; +₹20.44), while `B3` earns ₹670.38 (79.16% disp) at 15.02% LTR and -₹464.35 CVaR10.

---

## 6. 60-Second Live Examiner Demo Commands
```bash
cd /Users/adityasharma/.gemini/antigravity/scratch/mandi-phantom-dispatch-agent
PYTHONPATH=. /Users/adityasharma/anaconda3/bin/python3 -m pytest -v tests
```
Or open `notebooks/colab_standalone_reproduction.ipynb` + `data/processed/colab_data_pack.tar.gz` (4.83 MB) in Google Colab and click **Run all** (< 3 minutes). *(Note: freight, Q10 rot, and closed-yard penalties are modeled rather than field-measured, and our 22/22 `pytest` checks verify code reproducibility, Dual-Tier parity, Stage-II invariants, and leakage guards rather than field economics.)*

---

## 7. University AI-Disclosure & Whiteboard Mastery Checklist
1. **University AI-Assistance Disclosure Policy:** Check your university and department rules on AI coding, writing, or editing assistance before submission. Follow the exact disclosure policy in your thesis front-matter, acknowledgments, and viva slides (stating accurately what tools were used and confirming all results, code, and defense answers are verified by you).
2. **Whiteboard Practice From Memory (Blank Sheet Drill Before Viva):**
   - [ ] **5-Line Tomato Arithmetic (Stage I & II):** ₹2,000 portal → -₹65.00 Q10 heat rot (3.25% at 40°C, 6h) → -₹146.00 truck + 1.5% MP tax → Stage I (`-₹154.80` 8% LCB = `+₹234.20/qtl`) vs Stage II (`mu_hat +320 - 0.15*1400*0.08 = +₹303.20/qtl` → `DISPATCH`).
   - [ ] **Holdout Table (N = 69,526):** `B1` (`₹350.01`, `40.46%`), `B2` (`₹446.66`, `18.11%`), `B3` (`₹330.85`, `45.28%`), Stage-I `MG_v1` (`₹452.79`, `9.97%`), Stage-II `MandiGuard-CRC` (`₹479.17`, `10.48%`, `+₹32.51` vs `B2` `p=0.0016`).
   - [ ] **Matched Observed-d0 Cohort (N = 10,162):** `B1` (`₹472.51`), `B2` (`₹469.99`), `B3` (`₹553.22`, `14.77%`), Stage-I `MG_v1` (`₹510.89`, `6.82%`), Stage-II `MandiGuard-CRC` (`₹533.75`, `7.14%`).
