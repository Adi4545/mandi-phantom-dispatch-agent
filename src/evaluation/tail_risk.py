"""Empirical lower-tail statistics for equal-weight episode payoffs."""
import numpy as np


def lower_decile_mean(values: np.ndarray) -> float:
    """Mean of the worst 10% of finite payoffs, splitting boundary mass exactly."""
    values = np.asarray(values, dtype=float)
    ordered = np.sort(values[np.isfinite(values)])
    if ordered.size == 0:
        return float("nan")
    n_full, tenths = divmod(ordered.size, 10)
    # Give each full observation ten units of mass and the next one the remainder.
    return float((10 * ordered[:n_full].sum() + tenths * ordered[n_full]) / ordered.size)
