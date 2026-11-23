"""ES10 uses exact worst-10% mass, including a fractional boundary weight."""

import numpy as np

from revision.es10 import es10


def test_es10_integer_mass_is_mean_of_worst_tenth() -> None:
    # 10 outcomes. Worst 10% is exactly the single worst value.
    x = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100], dtype=float)
    assert es10(x) == 10.0


def test_es10_fractional_boundary() -> None:
    # n = 5, mass = 0.5. Only half a weight on the worst observation.
    x = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    assert abs(es10(x) - 10.0) < 1e-12
    # n = 15, mass = 1.5 = worst value plus half of the next.
    y = np.arange(1, 16, dtype=float)  # 1 is worst
    assert abs(es10(y) - (1.0 + 0.5 * 2.0) / 1.5) < 1e-12


def test_es10_ignores_nonfinite_and_is_not_the_quantile_mean() -> None:
    x = np.array([np.nan, -100.0, -10.0, 0.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0])
    # 10 finite values, ES10 = -100.
    assert es10(x) == -100.0
    # The old "mean of observations <= 10% quantile" also returns -100 here.
    # A case where the two differ: quantile 0.10 of 1..20 pulls extra points.
    z = np.arange(1, 12, dtype=float)  # n=11, mass=1.1
    q = np.quantile(z, 0.10)
    old = float(z[z <= q].mean())
    # Exact mass puts weight 1 on 1 and weight 0.1 on 2. The quantile mean uses both fully.
    assert abs(es10(z) - (1.0 + 0.1 * 2.0) / 1.1) < 1e-12
    assert es10(z) != old
