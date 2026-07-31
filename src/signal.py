"""Trade signal generation and position sizing.

The signal is a conditional probability rather than a Z-score. Given where
leg B sits in its own distribution, how unusual is leg A's position? When that
probability breaches the entry threshold in either direction, the pair is
dislocated and a position opens.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .copula import FittedCopula, select_best, to_uniform

ENTRY_LOW = 0.05
ENTRY_HIGH = 0.95
EXIT_LOW = 0.45
EXIT_HIGH = 0.55


@dataclass
class PairPosition:
    """An open pair position."""

    a: str
    b: str
    direction: int  # +1 long A short B, -1 short A long B
    hedge_ratio: float
    opened: pd.Timestamp


def conditional_probabilities(
    returns_a: pd.Series,
    returns_b: pd.Series,
    fitted: FittedCopula | None = None,
) -> pd.Series:
    """Conditional probability of A given B across the sample."""
    u = to_uniform(returns_a)
    v = to_uniform(returns_b)
    model = fitted or select_best(u, v)
    return pd.Series(
        model.conditional_u_given_v(u.values, v.values),
        index=returns_a.index,
    )


def signal_state(
    prob: float,
    current: int = 0,
    entry_low: float = ENTRY_LOW,
    entry_high: float = ENTRY_HIGH,
    exit_low: float = EXIT_LOW,
    exit_high: float = EXIT_HIGH,
) -> int:
    """Target position given the conditional probability and current state.

    Hysteresis matters. Entry and exit use different thresholds so a
    probability oscillating around a single level does not generate a stream
    of round trips that costs more than the spread is worth.
    """
    if current == 0:
        if prob <= entry_low:
            return 1   # A is unusually low given B. Buy A, sell B.
        if prob >= entry_high:
            return -1  # A is unusually high given B. Sell A, buy B.
        return 0

    # Already positioned. Exit only on reversion into the neutral band.
    if exit_low <= prob <= exit_high:
        return 0
    return current


def zscore_signal(
    price_a: pd.Series,
    price_b: pd.Series,
    hedge_ratio: float,
    window: int = 60,
) -> pd.Series:
    """Classic standardized spread. The comparison baseline.

    Included so the copula approach can be measured against the conventional
    method rather than against buy and hold. If the copula does not beat this,
    the added complexity is not earning its keep.
    """
    spread = price_a - hedge_ratio * price_b
    mean = spread.rolling(window, min_periods=window // 2).mean()
    sd = spread.rolling(window, min_periods=window // 2).std(ddof=1)
    return (spread - mean) / sd.replace(0, np.nan)


def positions_to_weights(
    positions: list[PairPosition],
    universe: pd.Index,
) -> pd.Series:
    """Convert open pair positions into a dollar neutral weight vector.

    Capital is split evenly across active pairs, and each pair is internally
    balanced so the book carries no net market exposure.
    """
    w = pd.Series(0.0, index=universe)
    if not positions:
        return w

    per_pair = 1.0 / (2.0 * len(positions))
    for p in positions:
        if p.a in w.index:
            w[p.a] += p.direction * per_pair
        if p.b in w.index:
            w[p.b] -= p.direction * per_pair
    return w
