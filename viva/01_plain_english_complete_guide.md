# MandiGuard Revision v4 — Plain-English Complete Guide (Class-12 Level)

> **Note (`C2` & `R2`):** This guide replaces earlier Stage I/II drafts that cited quantile-mean `cvar_10`, live ERA5 weather, pickled ML trees, and pseudo-conformal bounds. Every number below comes from `revision/results/` on branch `finalization`.

## 1. The Everyday Problem in One Story
Imagine a farmer in Indore looking at a mobile price portal at 6 a.m. Tomato sells locally near home for about `₹1,500/qtl`, while a wholesale portal shows yesterday's modal price at another mandi `200 km` away at `₹2,000/qtl`. Hiring a small truck looks like an easy `+₹500/qtl` win.

Why does that trip still lose money **`45.21%`** of the time (`B1_lagged_screen`, `N = 58,676` test episodes, mean `₹397.87/qtl`, worst-10% `ES10 = −₹641.26/qtl`)? Four plain reasons:
1. **Truck freight:** Paying `₹35/qtl + ₹0.45/qtl-km` (and `1.45×` distance factor on Himachal Pradesh hill roads, where GoHP Economic Survey 2025–26 reports `91.59%` single-lane roads).
2. **Destination mandi fee:** When you sell outside your home district, statutory APMC fees (`0.5%–1.5%`) come out of your surviving destination auction sale—not out of thin air.
3. **Hot-weather shrinkage:** Over `6` to `24+` hours in transit, NABCONS (2022) benchmarks measure `0.86%` to `3.25%` 24-hour market-level loss (`Potato` to `Tomato`).
4. **Yesterday's price may not trade today:** On `28.98%` of naive `B1` trips, *no tomato price at all* appears on the destination portal when the truck reaches the gate (`16,426` day-0 + `373` day-1 + `206` day-2 no-commodity turn-backs). Waiting costs `₹25/qtl-day` plus extra spoilage, and returning without selling still burns return freight (though statutory APMC selling fee is `₹0`).

## 2. The Simple Solution (`RR-Abstain`): One Weighted Average
Older prototypes used gradient-boosted trees, leaked weather, and complex multi-step hard rules (`MG`). Ablations in `revision/results/matched_dispatch.csv` proved those extra pieces added complexity without reducing tail losses at equal dispatch (`MG_matched ES10 +₹12.49`, Holm `p = 0.589`).

So Revision v4 keeps **only one Class-12 formula** (`RR-Abstain`, pre-registered in `final/PREREG_A10.md`, SHA `87a0b62`):
- Look at yesterday's reporting probability $\hat{p}_{\text{rep}}$ (`0` to `1`): how reliably did this destination publish exact-variety prices over the last 28 days and on the arrival weekday strictly before today?
- Compute open-market expected gain $\widehat{\Delta}_{\text{open}}$ (lagged spread minus shrinkage, destination fee, and freight).
- Compute a worst-case no-quote loss bound $\widehat{\Delta}_{\text{miss}} = -\kappa F_{\text{road}} - P_{\text{orig,lag}} s_{\text{ref,0}}$ (`kappa* = 5.0` chosen strictly on Jan–May 2025 validation).
- Mix them: `Score = p_rep * Delta_open + (1 - p_rep) * Delta_miss`. Dispatch to the best fresh quote (`1–3` days old) only if `Score > ₹3.73/qtl` (or simply `Score > 0`, which gives `₹475.76/qtl`).

## 3. Verified Headline Results (`N = 58,676` Test Episodes)
- **Versus age-matched road dispatch (`B2_age_matched`, `72.03%` disp):** `RR_Abstain_matched` (`69.02%` disp) lifts Mean net gain from `₹433.56` to **`₹475.36/qtl`** (`+₹41.80`), cuts episode loss rate from `26.72%` to **`17.23%`** (`−9.49 pp`), and improves **`ES10` from `−₹525.25` to `−₹460.72/qtl`** (`+₹64.54`, Holm `p = 0.0020` across both origin & destination clusterings).
- **Works across everyday vegetables (`NonApple`, `N = 52,207`):** Mean `+₹34.82/qtl`, **`ES10 +₹78.10/qtl`** (improving Onion `+₹101.93`, Potato `+₹88.91`, Tomato `+₹49.31` individually).
- **Honest Failure Cases (`R6`):** Generic `Apple` `ES10` is tied (`−₹1,537.30` vs `−₹1,533.29`), HP graded apples (`N = 2,802`) still suffer `44.63%` conditional losses, legacy Stage I `H2` stays inconclusive (`+₹6.13`, `p = 0.270`), and the June 2025–April 2026 calendar split is `exploratory` (Gate J = `BLOCKED`, disclosed).
