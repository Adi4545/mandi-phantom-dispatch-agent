"""Official-survey-anchored freight, spoilage, and destination auction payoff model.

Ground-truth physical & statutory parameters anchored to Government of India sources:
  - Freight: Rs 35/qtl loading + Rs 0.45/qtl/km (1.45x per-km on HP hill roads, justified by
    GoHP Economic Survey 2025-26 Table 28 showing 91.6% motorable roads are single-lane).
  - Out-of-district statutory yard / handling charges anchored to GoI PIB relid=154554 & State APMC rules
    (when `use_state_statutory_fees=True`, falls back to uniform `out_of_district_fee=1.5%` when False):
      * Karnataka & Gujarat: 0.5% user charge (F&V market fee exempted)
      * Himachal Pradesh: 0.5% service charge on vegetables, 1.0% on Apple (Apple excluded from exemption)
      * Maharashtra: 1.0% regulated yard supervision/handling inside notified APMCs
      * Madhya Pradesh & Uttar Pradesh: 1.5% regulated mandi yard fee/user friction
  - Biological Q10 transit spoilage anchored directly to MoFPI / NABCONS (2022) market-level loss rates
    (PIB PRID=2151371 Annexure-II Table-2): Tomato 3.25%, Onion 1.96%, Apple 1.64%, Potato 0.86%
  - Heavy-rain highway moisture/grade penalty (>= 35 mm/day realized ERA5 rain)
  - Primary destination auction lookup (+0, +1, +2 wait days; fallback to any-variety
    Min_Price - 10% distress discount; or -1.5x freight diversion if yard completely closed)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np

# Exact MoFPI / NABCONS (2022) Annexure-II Table-2 market-level loss fractions at reference 20C
BASE_SPOIL_24H: Dict[str, float] = {
    "Tomato": 0.0325,
    "Onion": 0.0196,
    "Apple": 0.0164,
    "Potato": 0.0086,
}

# GoI PIB relid=154554 & State APMC statutory seller-side fee / user-charge schedule
STATE_STATUTORY_SELLER_FEE_PCT: Dict[str, Dict[str, float]] = {
    "Karnataka": {"default": 0.005},
    "Gujarat": {"default": 0.005},
    "Himachal Pradesh": {"default": 0.005, "Apple": 0.010},
    "Maharashtra": {"default": 0.010},
    "Madhya Pradesh": {"default": 0.015},
    "Uttar Pradesh": {"default": 0.015},
}


@dataclass(frozen=True)
class PayoffParams:
    freight_mult: float = 1.0
    spoilage_mult: float = 1.0
    freight_base: float = 35.0
    freight_per_km: float = 0.45
    hp_km_mult: float = 1.45
    out_of_district_fee: float = 0.015
    use_state_statutory_fees: bool = True
    detention_per_day: float = 25.0
    diversion_freight_mult: float = 1.5
    other_var_discount: float = 0.10
    heavy_rain_mm: float = 35.0
    heavy_rain_extra_spoil: float = 0.02
    heavy_rain_min_blend: float = 0.50


def get_statutory_fee_rate(state: str, commodity: Optional[str] = None, params: PayoffParams = PayoffParams()) -> float:
    """Return out-of-district statutory yard / handling charge rate for (state, commodity)."""
    if not params.use_state_statutory_fees:
        return params.out_of_district_fee
    st_map = STATE_STATUTORY_SELLER_FEE_PCT.get(state)
    if st_map is None:
        return params.out_of_district_fee
    if commodity is not None and commodity in st_map:
        return st_map[commodity]
    return st_map["default"]


def compute_freight_inr(
    state: str,
    road_km: float,
    same_district: bool,
    local_price: float,
    params: PayoffParams = PayoffParams(),
    commodity: Optional[str] = None,
) -> float:
    """Compute realistic truck freight + out-of-district APMC user/handling charges (INR/qtl)."""
    km_mult = params.hp_km_mult if state == "Himachal Pradesh" else 1.0
    base_freight = (params.freight_base + params.freight_per_km * km_mult * road_km) * params.freight_mult
    fee_rate = get_statutory_fee_rate(state, commodity=commodity, params=params)
    fee = 0.0 if same_district else fee_rate * max(0.0, local_price)
    return float(base_freight + fee)


def compute_spoilage_fraction(
    commodity: str,
    truck_hours: float,
    tmax_c: float,
    rh_mean: float,
    rain_mm: float,
    wait_days: int = 0,
    params: PayoffParams = PayoffParams(),
) -> float:
    """Compute biological Q10 transit + waiting spoilage fraction in [0, 0.55]."""
    base_24h = BASE_SPOIL_24H.get(commodity, 0.02)
    t_eff = float(np.clip(tmax_c if np.isfinite(tmax_c) else 25.0, 5.0, 48.0))
    rh_eff = float(np.clip(rh_mean if np.isfinite(rh_mean) else 65.0, 20.0, 100.0))
    rain_eff = float(rain_mm if np.isfinite(rain_mm) else 0.0)

    q10 = 2.0 ** ((t_eff - 20.0) / 10.0)
    rh_factor = 1.0 + 0.25 * max(0.0, (rh_eff - 70.0) / 30.0)
    total_hours = max(1.0, truck_hours + 24.0 * max(0, wait_days))
    bio_loss = base_24h * (total_hours / 24.0) * q10 * rh_factor
    if rain_eff >= params.heavy_rain_mm:
        bio_loss += params.heavy_rain_extra_spoil
    frac = bio_loss * params.spoilage_mult
    return float(np.clip(frac, 0.0, 0.55))


def compute_realized_dispatch_outcome(
    state: str,
    commodity: str,
    local_price: float,
    road_km: float,
    truck_hours: float,
    same_district: bool,
    arrival_lag_days: int,
    dest_exact_prices: tuple,  # (p_modal_d0, p_min_d0, p_modal_d1, p_min_d1, p_modal_d2, p_min_d2)
    dest_any_var_min_d0: float,
    dest_any_open_d0: bool,
    route_tmax: float,
    route_rh: float,
    route_rain: float,
    params: PayoffParams = PayoffParams(),
) -> Dict[str, float | str | int | bool]:
    """Compute realized net gain over SELL_LOCAL (INR/qtl) plus exact physical trap diagnostics."""
    freight = compute_freight_inr(state, road_km, same_district, local_price, params, commodity=commodity)

    # Check exact-variety auction availability on arrival day t+tau (wait 0), then +1, +2
    p_modal_exact = np.nan
    p_min_exact = np.nan
    wait_days = -1
    for w_idx, (pm, pmn) in enumerate(
        [
            (dest_exact_prices[0], dest_exact_prices[1]),
            (dest_exact_prices[2], dest_exact_prices[3]),
            (dest_exact_prices[4], dest_exact_prices[5]),
        ]
    ):
        if np.isfinite(pm) and pm > 0:
            p_modal_exact = float(pm)
            p_min_exact = float(pmn) if (np.isfinite(pmn) and pmn > 0) else float(pm)
            wait_days = w_idx
            break

    if wait_days >= 0:
        # Lot sold at exact variety within [t+tau, t+tau+2]
        spoil_frac = compute_spoilage_fraction(
            commodity, truck_hours, route_tmax, route_rh, route_rain, wait_days=wait_days, params=params
        )
        # Heavy rain en-route degrades modal quality 50% toward Min_Price
        sale_price = p_modal_exact
        if np.isfinite(route_rain) and route_rain >= params.heavy_rain_mm:
            sale_price = (1.0 - params.heavy_rain_min_blend) * p_modal_exact + params.heavy_rain_min_blend * p_min_exact
        detention = params.detention_per_day * wait_days
        net_realization = sale_price * (1.0 - spoil_frac) - freight - detention
        delta_net = net_realization - local_price
        closed_trap = bool(wait_days > 0)
        outcome_type = "exact_open_d0" if wait_days == 0 else f"exact_wait_d{wait_days}"
        arrival_drop_flag = bool(sale_price < local_price)
        open_d0_delta_net = float(delta_net) if wait_days == 0 else np.nan
        return {
            "delta_net_inr": float(delta_net),
            "open_d0_delta_net_inr": open_d0_delta_net,
            "freight_inr": float(freight),
            "spoil_frac": float(spoil_frac),
            "detention_inr": float(detention),
            "sale_price_inr": float(sale_price),
            "wait_days": int(wait_days),
            "closed_or_no_variety_trap": closed_trap,
            "no_exact_variety_3d": False,
            "arrival_price_dropped": arrival_drop_flag,
            "outcome_type": outcome_type,
        }

    # Exact variety NEVER traded in [t+tau, t+tau+2] -> Closed/No-Variety Trap!
    spoil_frac = compute_spoilage_fraction(
        commodity, truck_hours, route_tmax, route_rh, route_rain, wait_days=0, params=params
    )
    if np.isfinite(dest_any_var_min_d0) and dest_any_var_min_d0 > 0:
        # Mandi traded other varieties of the same crop; liquidate at other-variety Min_Price - 10% distress discount
        sale_price = float(dest_any_var_min_d0) * (1.0 - params.other_var_discount)
        net_realization = sale_price * (1.0 - spoil_frac) - freight
        delta_net = net_realization - local_price
        outcome_type = "other_variety_distress"
    elif dest_any_open_d0:
        # Yard open for other crops, zero trade for this commodity -> divert back / distress
        delta_net = -params.diversion_freight_mult * freight - local_price * spoil_frac
        sale_price = local_price
        outcome_type = "no_commodity_divert"
    else:
        # Yard completely closed for 3 consecutive days -> divert back / distress
        delta_net = -params.diversion_freight_mult * freight - local_price * spoil_frac
        sale_price = local_price
        outcome_type = "closed_yard_divert"

    return {
        "delta_net_inr": float(delta_net),
        "open_d0_delta_net_inr": np.nan,
        "freight_inr": float(freight),
        "spoil_frac": float(spoil_frac),
        "detention_inr": 0.0,
        "sale_price_inr": float(sale_price),
        "wait_days": 3,
        "closed_or_no_variety_trap": True,
        "no_exact_variety_3d": True,
        "arrival_price_dropped": True,
        "outcome_type": outcome_type,
    }
