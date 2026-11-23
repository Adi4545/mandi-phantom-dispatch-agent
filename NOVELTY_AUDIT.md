> **Archival Note (Superseded Stage-I/II Audit):** This historical audit predates **Revision v5** (`Safe_EV_Sunk_m0`, `RT_2F_Min_m0`, `8.7/10`, `DIFFICULTY.md`, stripped ERA5 weather/GBDT/conformal claims). For the active canonical novelty classification, see `final/NOVELTY_V2.md`, `final/AUDIT_V4.md`, and `paper/manuscript.md`.

> **Superseded downside numbers.** Any CVaR, worst-10%, or `cvar_10` figure in this file is the mean of points below a sample quantile. It is not ES10. The current definition and the current tables are `revision/es10.py` and `revision/results/`. The Stage I comparison with the road rule remains inconclusive.

# Adversarial Novelty Audit — `MandiGuard`

**Project Title:** *Empirical Measurement of Phantom Spatial Arbitrage in Indian Mandis and a Four-Step Risk-Gated Dispatch Decision-Support System (`MandiGuard`)*  
**Purpose of Document:** This audit strictly classifies what is **genuinely novel and defensible** for an M.Tech thesis versus what is **borrowed or applied** from existing literature, ensuring zero exaggerated algorithmic claims during peer review or thesis viva defense.  
**Literature Anchor:** Grounded in [research/literature_matrix.md](research/literature_matrix.md) and the multi-state extraction scope implemented in [src/data/extract_agmarknet_multistate.py](src/data/extract_agmarknet_multistate.py).

---

## 1. Executive Classification of Target M.Tech Novelty

`MandiGuard` does **not** claim to invent new statistical learning theorems, new conformal coverage proofs, LLM reasoning algorithms, reinforcement-learning policies, or thermodynamic food-spoilage laws. Structurally, `MandiGuard` is a **risk-gated dispatch decision-support system** using a deterministic four-step verification cascade (`T1 -> T2 -> T3 -> T4`), a frozen tree model (`HistGradientBoostingRegressor`), and a causal empirical conformal cushion—with **no LLM or RL policy**. Its M.Tech novelty is **empirical, decision-formulation, systems-architectural, and benchmark-oriented**, spanning four concrete, testable axes:

| Novelty Axis | Type of Novelty | Specific Claim Defended by `MandiGuard` | Primary Anchor Literature Built Upon |
|:---|:---|:---|:---|
| **Axis 1: Empirical Anatomy of Phantom Spatial Arbitrage** | **Empirical / Domain-Measurement** | First multi-state, multi-crop quantitative decomposition of apparent AGMARKNET spatial arbitrage across 6 Indian states (Maharashtra, Uttar Pradesh, Karnataka, Madhya Pradesh, Gujarat, Himachal Pradesh) and 4 perishable crops (Onion, Potato, Tomato, Apple; 2017–2026, primary holdout Jun 2025–Apr 2026) into four mechanisms: (1) variety/grade mismatch, (2) closed-yard / non-reporting hazard, (3) Haversine-vs-OSRM road-network distance/time gap, and (4) ERA5 / NASA POWER ambient thermal spoilage. | Jensen (2007); Sekhar (2012); Chatterjee & Kapur (2016/2017); Negi et al. (2018); Hersbach et al. (2020); Sparks (2018); Jha et al. (2015); NABCONS (2022) |
| **Axis 2: Asymmetric-Cost Selective Dispatch Formulation** | **Problem Formulation & Applied ML** | Reframes mandi market selection from naive symmetric RMSE price prediction or point-estimate profit ranking to **cost-sensitive selective dispatch** with an explicit `REFUSE_PHANTOM_SPREAD` (`SELL_LOCAL`) abstention rule driven by calibrated downside risk bounds (`LCB` on net realized profit after freight, yard risk, and heat decay), evaluated under both modeled trap penalties (View 1) and fair matched complete-observation cohorts / crossover sweeps (View 2, `Exp 15`). | Chow (1970); Franc, Průša, & Voráček (2023); Angelopoulos & Bates (2023); Mitra et al. (2018) |
| **Axis 3: Four-Step Verification Cascade** | **Systems & Budgeted Decision-Support** | Organizes external data checks in ascending marginal cost (`T1` market vitality/variety -> `T2` OSRM road freight & state fees -> `T3` corridor heat/rain spoilage -> `T4` causal conformal lower bound) rather than querying all external services upfront on all candidates—tracing the realized utility vs. query-budget Pareto frontier (`H4`, `Exp 5`). | Yao et al. (2023); Kachuee et al. (2019); Han, Buntine, & Shareghi (2024); Luxen & Vetter (2011) |
| **Axis 4: Pre-Registered, Leak-Free Multi-Modal Benchmark** | **Benchmark & Reproducibility** | Delivers an open, SHA-256-verified multi-modal pipeline harmonizing 2017–2026 AGMARKNET archive schema/district renames, causal 2024-ranked market selection (eliminating holdout survivorship bias), strict temporal train/calibration/holdout splits, Dual-Tier official parity (`Exp 14`), and pre-registered baselines/ablations. | Madaan et al. (2019); Ma et al. (2019); Guo et al. (2020); Deka (2026); Divyashree & Biradar (2026); Manimegalai et al. (2026) |

---

## 2. Adversarial Component-by-Component Audit: Borrowed vs. Novel

### A. Econometric & Mandi Price Analysis
* **What Already Exists (Borrowed / Prior):**
  * Long-run spatial cointegration and market segmentation across Indian mandis (Sekhar 2012; Chatterjee & Kapur 2016/2017).
  * Survey evidence that transport/communication frictions depress farmer prices (Negi et al. 2018), while raw price announcements alone fail without outside market access (Mitra et al. 2018).
  * Missing AGMARKNET entries tied to non-trading/closed market days (noted as a data-cleaning step by Guo et al. 2020 and imputed statistically by Ma et al. 2019 and Deka 2026).
  * Naive net-profit mandi recommenders combining AGMARKNET + XGBoost/SARIMA + OpenWeatherMap or Haversine distance (*Mandi Cast* 2026; *AgriMarket AI* 2026).
* **What `MandiGuard` Adds (Novel):**
  * Shifts from *macro price dispersion* or *price MSE* to **operational decision-time arbitrage auditing**: measuring what share of apparently profitable daily inter-mandi trades turns negative or unexecutable once variety/grade equivalence, yard trading availability on arrival day, real OSRM road routes, and corridor thermal exposure are enforced—and separating open-yard forecasting accuracy from closed-yard screening failure (`Exp 15`).

### B. Climate & Freshness Degradation Modeling
* **What Already Exists (Borrowed / Prior):**
  * ERA5 reanalysis (Hersbach et al. 2020) and NASA POWER (Sparks 2018) for gridded daily ambient meteorology.
  * National Indian post-harvest loss surveys (ICAR-CIPHET, Jha et al. 2015; MoFPI/NABCONS 2022) and standard $Q_{10}$ post-harvest spoilage kinetics in food engineering.
* **What `MandiGuard` Adds (Novel):**
  * **Operational coupling** of ERA5 / NASA POWER corridor weather and OSRM transit duration into a per-route freshness penalty benchmarked across contrasting Indian agro-climatic regimes (e.g., temperate HP Apple corridors vs. hot plains Onion/Tomato/Potato corridors).
* **Mandatory Honesty Disclosure (Ground-Truth Limitation):**
  * AGMARKNET reports daily market modal/min/max prices and reporting presence—it does **not** record truck-level consignment spoilage receipts, actual freight invoices (`₹35 + ₹0.45/km`), or closed-yard distress discounts. Consequently, trucking costs, transit freshness loss, and closed-yard diversion penalties in our benchmark are **physics-informed, literature-anchored structural models** evaluated across sensitivity sweeps (`Exp 6`, `Exp 15`), *not* field weighment receipts or farmer survey measurements. Likewise, our 22 passing automated `pytest` unit tests verify **deterministic code execution, Dual-Tier data parity, Stage-II invariants, and chronological split hygiene—not real-world economic truth**.

### C. Selective Prediction, Asymmetric Risk & Conformal Calibration
* **What Already Exists (Borrowed / Prior):**
  * Optimal error–reject tradeoff under asymmetric costs (Chow 1970) and proper uncertainty scores for reject-option classifiers (Franc et al. 2023).
  * Split conformal prediction and adaptive conformal inference (Angelopoulos & Bates 2023; Gibbs & Candès 2021).
* **What `MandiGuard` Adds (Novel):**
  * **Domain instantiation & Stage-II mechanistic autopsy (`Exp 16`–`Exp 17`):** First, translates reject-option bounds into `REFUSE_PHANTOM_SPREAD` (`SELL_LOCAL`) vs. `DISPATCH`. Second, Stage-II diagnostics (`Exp 16`) measure two pitfalls of baseline mandi ML: (i) *Censored-Arrival Survivorship Bias* (`dropna(target_ret)` drops 55.83% of `Train_2024` corridors and understates Q20 downside by 1.82x–2.00x in Train / up to 2.54x in Holdout across `age = 0..3d`), and (ii) the *Heteroscedastic Coverage Illusion* (88.91%–90.46% over-coverage in calm `Q1` markets vs. 67.84%–67.80% under-coverage in volatile `Q4` markets). Third, `MandiGuard-CRC` adapts the validation-set CRC heuristic (`(n_l+1)/(n_d+1) <= beta`, $\beta_{\text{target}} = 0.095$ on `Val_2025H1` `N = 42,794`, $\lambda^* = 0.15$) over joint uncensored return + price-scaled loss probability (`Exp 17`).
* **Mandatory Honesty Disclosure (Statistical Assumption Gap):**
  * Standard split conformal and CRC Theorem 1 guarantees require exchangeability (and fixed-denominator monotone losses per Angelopoulos et al. 2024 Theorem 1). Daily agricultural prices violate exchangeability across seasons, and `(n_l+1)/(n_d+1)` uses selection-dependent `n_d(lambda)`. Therefore `MandiGuard` (`v1`: 78.85% val, 79.07% holdout) and Stage-II `MandiGuard-CRC` (`10.48%` holdout LTR at `lambda* = 0.15`) are strictly empirical chronological risk calibrations—never claiming Theorem 1 proofs.

### D. Four-Step Verification Cascade (`T1 -> T2 -> T3 -> T4`)
* **What Already Exists (Borrowed / Prior):**
  * Tool-interleaved decision loops (ReAct, Yao et al. 2023), budgeted test-time feature acquisition (Kachuee et al. 2019), and uncertainty-gated tool calling (UALA, Han et al. 2024), plus Indian agri-market grade fragmentation insights (Levi et al. 2020; Goyal 2010).
* **What `MandiGuard` Adds (Novel):**
  * **Domain-specific ordered verification cascade & sub-grade thinness discovery:** Executes gates in ascending cost (`T1 -> T2 -> T3 -> T4`, no LLM or RL policy). Stage-II `Exp 16` further proves that rigid `T1` frequency windows (`open_prob >= 0.50`)—not `T4` conformal width—blocked `77.82%–82.75%` of `B2`-profitable HP Apple dispatches (`exp16`), motivating an `age == 0` fresh-arrival exception (`thin_grade_aware_t1`) that lifts HP Apple mean profit `+34.2%` (`₹605.06 -> ₹812.08/qtl`, `Exp 17`) while preserving 6-state tail safety (`-₹44.03` CVaR).
  * **Honest framing of `H4`:** Achieving 44.4% fewer tool calls than `B4` (`8.75` vs `15.74` in Stage I; `9.07` = `-42.4%` in `MandiGuard-CRC`) is an expected design consequence of ordering cheap checks first. Its practical benefit appears under tight query or latency budgets (`B = 6`: `+₹104.54/qtl` over `B4`), whereas direct API rupee savings (modeled at ₹0.05/call) are minor relative to per-quintal crop profit.

---

## 3. Red-Line Check: Claims We MUST NOT Make

To protect academic integrity in the thesis text and viva, **strictly prohibit** the following overclaims:

1. **DO NOT claim** *"We prove a new conformal / CRC theorem or new Bayes-optimal reject theory."*  
   *Truth:* We apply Chow (1970), Franc et al. (2023), Angelopoulos & Bates (2023), and adapt the validation `(n_l+1)/(n_d+1)` CRC heuristic inspired by Angelopoulos et al. (2024) without claiming Theorem 1 exchangeability guarantees.
2. **DO NOT claim** *"We built an autonomous LLM- or RL-driven agent."*  
   *Truth:* `MandiGuard` and `MandiGuard-CRC` are deterministic risk-gated dispatch decision-support systems (`T1`–`T4` + tree models + validation-calibrated risk controls).
3. **DO NOT claim** *"Stage I `H2` was rescued, or Stage-II `MandiGuard-CRC` is pre-registered, or we beat `B3` mean on open yards / `B2` mean on HP Apples."*  
   *Truth:* Stage-I `H2` failed on mean profit (`+₹6.13/qtl`, $p_{\text{Holm}} = 0.2699$). Stage-II `MandiGuard-CRC` (`+₹32.51/qtl` over `B2` on 6-state holdout, `p = 0.0016`) is explicitly labeled `[POST-DIAGNOSTIC / VALIDATION-CALIBRATED]` (`lambda* = 0.15` frozen on `Val_2025H1`). On `Matched_AllTopK_Observed_d0` (`N = 10,162`), `B3` earns `₹553.22` above `MandiGuard-CRC` (`₹533.75`) at 2.1x LTR and 10.4x deeper tail loss; on HP Apples, `B2` (`₹1,150.83`) remains above `MandiGuard-CRC` (`₹812.08`).
4. **DO NOT claim** *"We verified 100% of the 2017–2026 dataset directly from official live government servers, or measured real truck weighment losses."*  
   *Truth:* Bulk 2017–2026 CSVs came from an archive mirror, checked in Dual-Tier `Exp 14` against a single-day official `data.gov.in` XML (`2023-10-18`, `172` matched keys: 100.00% Min/Max, 99.42% Modal) AND `149`-day official AGMARKNET 2.0 direct exports (`2,042` matched keys: 100.00% Min/Max/Modal) alongside 22 live Nov-2026 queries (`Exp 8`). Trucking costs (`₹35 + ₹0.45/km`), $Q_{10}$ spoilage, and closed-yard penalties lack field weighment receipts or farmer survey validation, and our 22 unit tests verify code/schema/split integrity rather than real-world economic truth.
5. **DO NOT claim** *"OSRM + ERA5 eliminates all real-world mandi frictions."*  
   *Truth:* Unobserved institutional frictions—local *arhtiya* credit ties, weighment/commission variations, sudden truck strikes, or intra-day arrival gluts—remain uncaptured in public portals and are stated as boundary limitations.

---

## 4. Likely Viva / Peer-Reviewer Objections & Candid Answers

| Adversarial Question from Examiner / Reviewer | Honest, Defensible Answer |
|:---|:---|
| *"Isn't your 'four-step cascade' just standard ordered filtering, and isn't `H4` obvious by construction?"* | Yes—structurally it is deterministic ordered gating inspired by Kachuee et al. (2019) and Han et al. (2024), and `H4` (44.4% fewer calls than upfront `B4`) follows by design of placing cheap `T1` checks first. Its operational significance shows up under tight query caps (`B = 6`: +₹104.54/qtl over `B4`), whereas direct per-call API rupee savings (₹0.05/call) are minor relative to crop profit. |
| *"How do you know `MandiGuard`'s gains aren't purely an artifact of your modeled `1.5x` closed-yard penalty?"* | That is exactly why `Exp 15` reports View 2: (a) across the Trap-Penalty Crossover Curve (`N = 69,526`), `MandiGuard` leads `B1` and `B3` down through 0.5x return freight / 5% discount (+₹42.43 / +₹46.12) and `₹0` missing-3d break-even (+₹82.26), crossing below on mean only at the unrealistic 0.0x / 0% boundary (-₹10.00 vs `B1`, -₹20.93 vs `B3`, where LTR is still cut roughly three-fold to 6.09%); and (b) on `N = 10,162` identical guaranteed-open episodes (`Matched_AllTopK_Observed_d0`, zero simulated trap rules), `MandiGuard` still beats `B1` (+₹38.38) and `B2` (+₹40.91) while exposing where `B3` wins on mean (+₹42.33) at 2.2x LTR and 10x deeper tail losses. |
| *"Why did `H2` fail (`p = 0.27`), and aren't you cherry-picking the 4-state NWP subset?"* | `H2` failed on mean profit (`+₹6.13/qtl` is within sampling noise) because `MandiGuard` abstains on marginal trips (`48.66%` vs `62.11%` dispatch) to cut loss trips roughly in half (`9.97%` vs `18.11%`) and reduce `CVaR_10%` from -₹436.67 to -₹37.89/qtl. We explicitly state `H2` failed and treat the 4-state NWP check (`+₹31.82/qtl`) solely as an exploratory check that causal Ridge weather estimation on 43/145 northern grids did not depress performance—not as a rescue of `H2`. |
| *"How can you claim thermal spoilage effects without truck-level spoilage ground truth?"* | We explicitly distinguish observed data layers (AGMARKNET prices and reporting flags, OSRM road travel times, ERA5 / NASA POWER temperatures) from our modeled freight and $Q_{10}$ spoilage terms anchored to ICAR-CIPHET (2015) and NABCONS (2022). We state candidly that field weighment receipts and farmer survey validation are absent, and evaluate results across a $3\times 3$ freight $\times$ spoilage sensitivity grid (`Exp 6`). |
| *"Why use a public mirror for 2017–2026 data, and what do your 22 unit tests actually prove?"* | Bulk 2017–2026 CSVs came from a public archive mirror; Dual-Tier `Exp 14` verified parity on a single-day official `data.gov.in` XML spot-check (`2023-10-18`, 172 matched keys: 100.00% Min/Max, 99.42% Modal) AND a **149-day direct official AGMARKNET 2.0 export** (`2,042` matched market-variety-grade-day rows: 100.00% Min/Max/Modal) alongside 22 live `agmarknet.gov.in` queries (`Exp 8`). And our 22/22 unit tests verify deterministic code execution, schema/checksum parity, Stage-II leakage guards, and chronological split hygiene—not real-world economic truth. |

---

## 5. Summary Verdict on Thesis Readiness

* **Novelty Profile:** **Applied Empirical + Mechanistic Diagnostic + Systems-Benchmark Novelty** (Two-Stage design: pre-registered Stage-I cascade + post-diagnostic validation-calibrated `MandiGuard-CRC`, well suited for an M.Tech thesis / applied ICTD or ACM COMPASS-style venue).
* **Core Strength:** Combines a multi-year empirical measurement of phantom spatial arbitrage across Indian mandis with a simple, deterministic, leak-free risk-gated decision-support cascade AND a mechanistic autopsy resolving why standard censored arrival regression stalls on volatile or sub-grade markets—while remaining candid about failed Stage-I `H2` mean superiority, post-diagnostic Stage-II quarantine, open-yard `B3` tradeoffs, Dual-Tier official parity boundaries, and unvalidated field-cost parameters.
