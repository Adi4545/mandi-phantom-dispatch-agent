# Spoken Pitches (1-Minute, 5-Minute, and 15-Minute Outlines — Verified Revision v5 Only)

> **Verification Guarantee (`R2` & `C2`):** Zero untraceable numbers (`scripts/verify_traceability.py`), `₹0.00` independent `A16` parity across all 8 policies, two-sided Holm `p_holm_2s`, `170–173` market clusters.

## 1-Minute Elevator Pitch
*"Online wholesale portals like AGMARKNET tempt farmer cooperatives with ₹500 spreads that disappear in transit. Auditing 58,676 strictly lagged episodes across 6 states and 4 crops with sequential arrival settlement and destination APMC fees, naive spread-chasing loses money 45.21% of the time with worst-10% shortfall ES10 of −₹641.26 per quintal. Replacing ML trees, hard cutoffs, and tuned penalties with two zero-parameter calculator formulas—**Safe_EV_Sunk_m0** (weekday reporting frequency times 1-SD safe spread minus freight > 0) and 4-function **RT_2F_Min_m0** (reporting reliability times spread minus round-trip freight > 0)—Safe_EV_Sunk_m0 cuts episode losses to 14.93% (−11.79 pp, two-sided Holm p = 0.0040) and strengthens ES10 to −₹344.09 per quintal (+₹181.17 over road dispatch, +₹168.69 over hard gates, +₹116.63 over tuned RR-Abstain across all 3 clusterings and all 6 states), while acting cleanly as an alert filter ahead of a trader phone call and keeping HP graded apples (41.38% conditional loss) and Gate J limitations open."*

## 5-Minute Examination Summary (5 Slides)
1. **Timing Trap (`B1`):** `45.21%` losses across `58,676` lagged episodes; `28.98%` turn back sequentially; 3d hindsight masks losses to `31.35%`.
2. **Firewall & Economic Fixes (`R3`, `M9`):** Zero gitignored inputs, counterfactual `>= t*` price-corruption proof, `98.64%` ERA5 weather leak removed, destination fee base fixed, exact `State|` clustering (`170–173` vs buggy `336`).
3. **Zero-Parameter Discovery (`A18`):** Hard gates (`MG_matched`) failed `ES10` (`p_holm_2s = 1.000`), and tuned `RR-Abstain` collided with grid ceiling `kappa*=5.0` and missed Sunday holidays + price volatility (`cv28`). `Safe_EV_Sunk_m0` (`0` params) wins `ES10` by `+₹181.17` vs `B2` and `+₹116.63` vs `RR` (`p_holm_2s = 0.0040`), while Class-8 `RT_2F_Min_m0` raises mean to `₹478.38`.
4. **Global Robustness (`M3`, `A8`, `A17`):** Wins in ALL 6 states, all crops on `ES10`, all `36/36` frozen+rescored tornado cells, `exact_zero_divert_payoff_0` (`+₹169.79 ES10`), exact-geocode (`N = 40,690`), and `N = 88,014` unconditional origin panel (`ES10 −₹335.04` vs `−₹515.93`).
5. **Honest Boundaries (`R5`–`R7`):** Alert triage before live *arhtiya* phone confirmation (Open-MAR gives `B2 +₹102.58` mean vs `Safe_EV +₹190.00 ES10`), HP apples stay risky (`41.38%` cond loss despite `−₹1,454.86 ES10`), Stage I `H2` inconclusive (`+₹6.13`), Gate J = `BLOCKED`.

## 15-Minute Defense Walkthrough Structure
- **Min 0–3:** Motivate with Worked Example 1 (`₹125` freight, `0.8125%` decay, destination 1.5% fee) and Worked Example 2 (Sequential `−₹199.69` vs Hindsight `+₹239.97`).
- **Min 3–6:** Reconcile data funnel (`260,043 -> 259,284 -> 248,302 -> 58,676`), `98.64%` ERA5 weather removal, and `R3` property test.
- **Min 6–10:** Show why `MG` (`ES10` NS) & tuned `RR` (`kappa*=5.0` ceiling) gave way to zero-parameter `Safe_EV_Sunk_m0` & `RT_2F_Min_m0` (`Worked Example 3`) and fair test-matched/volatility ablations (`+₹156.66 ES10` equal-disp, `+₹100.66 ES10` from `cv28`).
- **Min 10–13:** Walk through `H_A18_1..4` (`p_holm_2s = 0.0040`, all 3 schemes), 6-state & 5-crop consistency, `36/36` tornado win, Open-MAR/`exact_zero_divert` bounds, and `N = 88,014` unconditional origin check.
- **Min 13–15:** Disclose HP Apple `41.38%` cond loss, Tomato flat mean (`₹461.42` vs `₹462.27`), phone-call triage scope, `Gate J = BLOCKED`, and live FPO pilot plan.
