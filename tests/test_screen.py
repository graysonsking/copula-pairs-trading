"""Tests for pair screening, multiple testing control, and signal logic."""

import numpy as np
import pandas as pd
import pytest

from src import screen, signal


def test_bh_rejects_nothing_when_all_null():
    p = np.linspace(0.2, 0.99, 50)
    assert screen.benjamini_hochberg(p, 0.10).sum() == 0


def test_bh_accepts_clear_signals():
    p = np.array([1e-6, 1e-5, 0.4, 0.6, 0.9])
    assert screen.benjamini_hochberg(p, 0.10)[:2].all()


def test_bh_is_stricter_than_uncorrected():
    rng = np.random.default_rng(1)
    p = rng.uniform(size=1000)
    assert screen.benjamini_hochberg(p, 0.10).sum() < (p < 0.05).sum()


def test_hedge_ratio_recovers_known_slope():
    b = pd.Series(np.linspace(1, 100, 200))
    a = 2.5 * b
    assert screen.hedge_ratio(a, b) == pytest.approx(2.5, rel=1e-6)


def test_half_life_infinite_for_random_walk():
    rng = np.random.default_rng(2)
    rw = pd.Series(np.cumsum(rng.normal(size=500)))
    assert screen.half_life(rw) > 50


def test_half_life_finite_for_mean_reverting_series():
    rng = np.random.default_rng(3)
    x, out = 0.0, []
    for _ in range(1000):
        x = 0.9 * x + rng.normal(0, 0.1)
        out.append(x)
    assert screen.half_life(pd.Series(out)) < 30


def test_entry_only_outside_thresholds():
    assert signal.signal_state(0.50, current=0) == 0
    assert signal.signal_state(0.02, current=0) == 1
    assert signal.signal_state(0.98, current=0) == -1


def test_hysteresis_holds_position_outside_exit_band():
    assert signal.signal_state(0.30, current=1) == 1
    assert signal.signal_state(0.50, current=1) == 0


def test_weights_are_dollar_neutral():
    pos = [
        signal.PairPosition("A", "B", 1, 1.0, pd.Timestamp("2024-01-01")),
        signal.PairPosition("C", "D", -1, 1.0, pd.Timestamp("2024-01-01")),
    ]
    w = signal.positions_to_weights(pos, pd.Index(list("ABCD")))
    assert w.sum() == pytest.approx(0.0)
    assert w.abs().sum() == pytest.approx(1.0)
