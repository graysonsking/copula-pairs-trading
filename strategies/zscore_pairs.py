"""Conventional Z-score pair trading. The baseline.

The copula approach has to beat this, not just beat buy and hold. If it does
not, the extra machinery is complexity without payoff, and that is a result
worth reporting honestly.
"""

from __future__ import annotations

import pandas as pd

from src import signal
from src.screen import Pair

ENTRY = 2.0
EXIT = 0.5


def weights_fn(
    returns: pd.DataFrame,
    date: pd.Timestamp,
    pairs: list[Pair] | None = None,
    state: dict | None = None,
    window: int = 60,
    **kwargs,
) -> pd.Series:
    if not pairs:
        return pd.Series(0.0, index=returns.columns)

    state = state if state is not None else {}
    prices = (1.0 + returns).cumprod()
    open_positions = []
    entry = kwargs.get("entry", ENTRY)
    exit_level = kwargs.get("exit", EXIT)

    for pair in pairs:
        if pair.a not in prices.columns or pair.b not in prices.columns:
            continue

        z = signal.zscore_signal(prices[pair.a], prices[pair.b], pair.hedge_ratio, window)
        latest = z.iloc[-1]
        if pd.isna(latest):
            continue

        key = (pair.a, pair.b)
        current = state.get(key, 0)

        if current == 0:
            target = -1 if latest >= entry else (1 if latest <= -entry else 0)
        else:
            target = 0 if abs(latest) <= exit_level else current

        state[key] = target
        if target != 0:
            open_positions.append(
                signal.PairPosition(pair.a, pair.b, target, pair.hedge_ratio, date)
            )

    return signal.positions_to_weights(open_positions, returns.columns)
