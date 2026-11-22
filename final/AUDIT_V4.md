# Independent Audit Report (`AUDIT_V4.md` — Agents `A16`, `A17`, & `A18` Revision v5)

**Audit Chain:** External Review 3 (`6.0/10`) $\to$ Agent `A16` Cleanroom Audit (`8.4/10`) $\to$ Agent `A17` Adversarial Re-Examiner (`6.8/10` on v4) + Agent `A18` Zero-Parameter Simplification $\to$ **`A17` Post-Remediation Re-Audit (`Revision v5 @ 84cc435` + Minor Fixes): `8.7 / 10 — CONDITIONAL PASS` (`0` Critical, `0` Major defects; Ready / Strong Accept for M.Tech Defense & Exploratory Policy Audit, Conditional Externally on Gate J Prospective Field Pilot).**  
**Branch:** `finalization` (PR #1; zero merge to `main`, full history preserved).

---

## 1. Independent Cleanroom Re-Derivation (`scripts/a16_independent_audit.py`)

Without importing any module from `revision/`, `scripts/a16_independent_audit.py` loads tracked raw parquets/CSVs from scratch, re-derives `rep28`, `dow8`, `cv28`, sequential settlement, destination fees, and exact `ES10`, and verifies **exact `₹0.00` agreement across ALL EIGHT primary & zero-parameter policies** (and `n_clusters <= 178` across all bootstrap CSVs):

| Policy Audited Independently (`N = 58,676`) | Published (`a10_results` / `a18_results`) | Cleanroom `A16` Re-Derivation | Abs Diff | Status |
|---|---|---|---|---|
| `B1_lagged_screen` (`disp / mean / ES10`) | `1.0000` / `₹397.87` / `−₹641.26` | `1.0000` / `₹397.87` / `−₹641.26` | `₹0.00` | **EXACT MATCH** |
| `B2_age_matched` (`disp / mean / ES10`) | `0.7203` / `₹433.56` / `−₹525.25` | `0.7203` / `₹433.56` / `−₹525.25` | `₹0.00` | **EXACT MATCH** |
| `RR_Abstain_matched` (`disp / mean / ES10`) | `0.6902` / `₹475.36` / `−₹460.72` | `0.6902` / `₹475.36` / `−₹460.72` | `₹0.00` | **EXACT MATCH** |
| `RR_Abstain_m0` (`disp / mean / ES10`) | `0.6952` / `₹475.76` / `−₹461.74` | `0.6952` / `₹475.76` / `−₹461.74` | `₹0.00` | **EXACT MATCH** |
| **`Safe_EV_Sunk_m0`** (`0` free params) | `0.6327` / `₹465.59` / **`−₹344.09`** | `0.6327` / `₹465.59` / **`−₹344.09`** | `₹0.00` | **EXACT MATCH** |
| **`Safe_EV_Phys_m0`** (`1.5F`, `0` tuned) | `0.6085` / `₹462.16` / **`−₹333.57`** | `0.6085` / `₹462.16` / **`−₹333.57`** | `₹0.00` | **EXACT MATCH** |
| **`RT_2F_Min_m0`** (`0` free params, Class-8) | `0.6492` / **`₹478.38`** / `−₹468.32` | `0.6492` / **`₹478.38`** / `−₹468.32` | `₹0.00` | **EXACT MATCH** |
| **`RT_2F_Dow_m0`** (`1` lookback, `0` tuned) | `0.6736` / `₹476.72` / `−₹484.97` | `0.6736` / `₹476.72` / `−₹484.97` | `₹0.00` | **EXACT MATCH** |

*(Also noted transparently: `scripts/a16_independent_audit.py` explicitly verifies deterministic point estimates and `n_clusters <= 178` invariants; `PREREG_A10.md` line 32 retained an unedited inline parenthetical drafting note preserved untouched per `R8`.)*

---

## 2. How Revision v5 Resolved Every `A17` Critical & Major Finding

1. **`A17-1` Cluster Bug (`336 -> 172`):** Fixed `State + "|"` prefix on destination cluster keys (`bootstrap.csv`, `a10_bootstrap.csv`, `a18_bootstrap.csv`), added policy-specific 3rd clustering (`170–173` clusters), locked `n_clusters <= 178` in `pytest` & `A16`.
2. **`A17-2` `div = 0.0` Illusion & MAR Bounds:** Published `div_0.0_spoil_only`, `exact_zero_divert_payoff_0`, `open_yard_MAR_lagged_price`, and `realized_exact_d0_dispatched_only`. Where `RR` lost to `B2` at `div=0` (`p_2s = 0.603`) and Open-MAR, zero-param `Safe_EV_Sunk_m0` maintains `+₹169.79..+₹190.00` `ES10` (`p_2s = 0.002`) while openly disclosing `B2`'s `+₹102.58` Open-MAR Mean advantage.
3. **`A17-3` `kappa* = 5.0` Ceiling:** Published `kappa 0..20` profile in `a10_summary.json` and superseded tuned `RR` with genuinely **zero-parameter `Safe_EV_Sunk_m0` & `RT_2F_Min_m0`**.
4. **`A17-4` Day-$t$ Origin Conditioning (`29,338 / 88,014`):** Built and scored full unconditional `N = 88,014` origin panel + `origin_lag_age 1..3` (`N = 56,648`) -> `Safe_EV_Sunk_m0` & `RT_2F_Min_m0` strengthen cleanly (`ES10 −₹335.04` vs `−₹515.93`).
5. **`A17-5..8` Coverage, Fair Controls, Centroids, Typos, Holm:** Published two-sided `p_holm_2s = 0.0040`, all 6 states, all 36 frozen+rescored tornado cells, exact-geocoded (`N = 40,690`) & clean-key (`N = 56,857`) slices, `MG_val_es10_tuned` & `Safe_EV_fixed10pct` ablations, reconciled `B2 th=200.0`, fixed `manuscript:217` & typo, pruned weak `IJEDR` foil.
6. **`A17-9/10` Scope & Realism:** Reframed as automated 6 a.m. portal-alert triage prior to trader confirmation calls, and explicitly labeled both `PREREG_A10` & `PREREG_A18` exploratory wrt exposed 2025–2026 dates (`Gate J = BLOCKED`, `R5`).
