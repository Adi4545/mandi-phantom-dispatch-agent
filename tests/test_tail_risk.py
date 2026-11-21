import numpy as np

from src.evaluation.tail_risk import lower_decile_mean


def test_abstention_ties_do_not_dilute_tail():
    # Worst 10% of 20 episodes: exactly two episodes, even with many zero ties.
    values = np.array([-100] + [0] * 17 + [5, 7])
    assert lower_decile_mean(values) == -50


def test_fractional_boundary_and_missing_values():
    # Of 15 outcomes, the lower decile uses all of -10 and half of -4.
    values = np.array([-4, -10] + [1] * 13 + [np.nan, np.inf])
    assert lower_decile_mean(values) == -8
    assert lower_decile_mean(np.array([7, -3])) == -3
    assert np.isnan(lower_decile_mean(np.array([np.nan])))
