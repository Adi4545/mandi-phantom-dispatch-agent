# Simplified Two-Stage Design — Zero-Parameter Decision Architecture (Revision v7)

This architecture avoids black-box ML overfitting (`PREREG_A10` `H2` inconclusive at `+₹6.13/qtl`, Holm `p = 0.2699`) in favor of transparent, zero-hyperparameter arithmetic evaluated strictly on `<= t - 1` public features across Candidate menus of `K <= 5` reachable destination mandis (`lag_spread > ₹100/qtl`, `dest_lag_age in 1..3` days; loosening `top_k = None` yields `Mean ₹454.37`, `ES10 −₹344.47`, `v7_exp4`).

## 1. Closed-Form Zero-Parameter Policy Family (`m = 0`)
For every eligible corridor `c = (o -> d)` in state `s` and commodity `k`, define road freight `F_road(c) = 35.0 + 0.45 * h_s * road_km(c)` (`h_s = 1.45` in Himachal Pradesh, `1.0` elsewhere; `30 qtl` load tier) and plain fee-adjusted lagged spread `G(c, t) = P_dest,lag * (1 - tau_fee) - P_orig,lag`:

1. **Historical Arrival-Weekday Reliability & 1-SD Volatility Haircut:**
   - `p_dow = dest_dow_exact_rep_8w`: `8`-week arrival-weekday Laplace reporting frequency (`(k + 1) / (n + 2)` in `{1/10, ..., 9/10}`), preventing `rep28` Sunday smoothing.
   - `G_1SD(c, t) = P_dest,lag * (1 - cv28) * (1 - tau_fee) - P_orig,lag`, where `cv28` is the `28`-day coefficient of variation (`0.05` fallback when `cnt28 < 2`, affecting only `77 / 36,441 = 0.21%` of dispatched test episodes; extending the `0.05` guard to `cv28 == 0` adjusts `5,274` rows cleanly to `452.10 / -345.52 / -447.65`, `v7_exp4`).
2. **`Safe_EV_Sunk_m0` (`0` tuned parameters — Primary Tail-Risk Filter):**
   - Dispatch rule (selecting best `c*` by INR surplus `p_dow * G_1SD - F_road` > `0`; note ratio argmax changes `5,113` destinations at Mean `₹437.28`, `v7_exp4`): threshold check `p_dow * G_1SD(c, t) > F_road(c)` (equivalently `G_1SD / F_road > 1 / p_dow`).
   - Achieves `63.23%` dispatch on `171` zero-lookahead markets (`N = 57,634`), cutting EpLoss from `26.43%` (`B2_age_matched`) to `14.88%` (`−11.56 pp`), improving `ES10` from `−₹524.78` to `−₹345.53/qtl` (`+₹179.24/qtl`), improving conditional `cond_ES10` from `−₹628.37` to `−₹447.48/qtl` (`+₹180.89`), and reaching Mean `₹452.74/qtl` (`+₹33.12/qtl`).
3. **`Safe_EV_Phys_m0` (`0` tuned parameters — Settlement-Matched `1.5F` Variant):**
   - Score: `p_dow * (G_1SD - F_road) - (1 - p_dow) * 1.5 * F_road > 0`.
   - Tightens EpLoss to `13.70%` and `ES10` to `−₹334.80/qtl` (`+₹189.97/qtl` vs `B2`) at `60.84%` dispatch (`Mean ₹449.52/qtl`, `cond_ES10 −₹447.33/qtl`).
4. **`RT_2F_Min_m0` (`0` tuned parameters — Class-8 Phone-Calculator Rule, NO `cv28`, NO spoilage):**
   - Score: `p_min * G(c, t) - 2 * F_road(c) > 0` where `p_min = min(rep28, p_dow)`.
   - Leads Mean payoff at `₹463.98/qtl` (`+₹44.36/qtl` vs `B2`) with positive 95% Mean CIs across `6/6` states & `5/5` crop slices (`Tomato ₹501.08/qtl`), at higher tail exposure (`ES10 −₹464.84/qtl`, `cond_ES10 −₹618.35/qtl`, EpLoss `16.21%`) and loses `cond_ES10` significance under `<= t-2` latency (`p = 0.9805`) and `166`-mkt pooled `b2dest` (`p = 0.079`).

## 2. Clean Non-Lookahead & Multi-Year Generalization
- **Locked Primary Panel:** Using `171` markets filtered strictly on `2024` history (`>= 80` days, `<= 30`/state) removes future market-survival lookahead while passing all four `PREREG_A18` hypotheses at `p_holm_2s_prereg4 = 0.0040` (`R = 2,000`) across `3` clusterings; purged `val` (`−939` eps, `v7_exp4`) preserves `th_b2 = 200.0` identically.
- **Clean `166`-Mkt `2018–2023` Validation (`N = 383,952`):** Dropping all 7 post-2024 lookahead yards (`171 ∩ 173`) yields `N = 383,952` (`115`-mkt `2017`-active `N = 325,993`), where frozen `Safe_EV_Sunk_m0` gains `+₹169.27 ES10` (`−₹304.29` vs `−₹473.56`), `+₹155.08 cond_ES10` (`−₹421.35` vs `−₹576.44`, `+₹174.27` vs equal-dispatch `B2_eq_SafeM0`), and passes `ES10` & `cond_ES10` in all `6/6` individual years (`p = 0.001`; `2020/2023` Means NS).
