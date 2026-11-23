"""Expected shortfall of the worst 10% with exact mass and a fractional boundary.

For finite values x_(1) <= ... <= x_(n) (worst first) and mass m = 0.1 * n,

    ES10 = (sum_{i=1}^{k} x_(i) + f * x_(k+1)) / m

where k = floor(m) and f = m - k. If f = 0 the boundary term is omitted.
This is the lower-tail expected shortfall at level 0.10, not the mean of all
observations at or below a sample quantile (that older estimator can include
more or less than 10% of the sample).
"""

from __future__ import annotations

import numpy as np


def es10(vals: np.ndarray) -> float:
    x = np.sort(np.asarray(vals, dtype=np.float64))
    x = x[np.isfinite(x)]
    n = int(x.size)
    if n == 0:
        return float("nan")
    mass = 0.1 * n
    k = int(np.floor(mass))
    frac = mass - k
    total = float(x[:k].sum()) if k else 0.0
    if frac > 1e-12:
        if k >= n:
            return float("nan")
        total += frac * float(x[k])
    return float(total / mass)
