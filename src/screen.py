"""Pair formation via cointegration testing.

Johansen and Engle-Granger both test whether a linear combination of two
non-stationary price series is stationary. If it is, deviations from that
combination are mean reverting and therefore tradeable.

The multiple testing problem is severe here and is the main reason naive pair
screens disappoint. Screening the roughly 5,000 combinations available in a
100 name universe at a 5 percent threshold produces around 250 false positives
by construction, before any real relationship is found. The Benjamini-Hochberg
correction below is not optional decoration.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd

try:
    from statsmodels.tsa.stattools import coint
    from statsmodels.tsa.vector_ar.vecm import coint_johansen
    _HAS_SM = True
except ImportError:  # pragma: no cover
    _HAS_SM = False


@dataclass
class Pair:
    """A candidate pair and its formation window statistics."""

    a: str
    b: str
    pvalue: float
    hedge_ratio: float
    half_life: float


def hedge_ratio(series_a: pd.Series, series_b: pd.Series) -> float:
    """Ordinary least squares hedge ratio of A on B, with intercept."""
    x = np.column_stack([np.ones(len(series_b)), series_b.values])
    beta, *_ = np.linalg.lstsq(x, series_a.values, rcond=None)
    return float(beta[1])


def half_life(spread: pd.Series) -> float:
    """Mean reversion half life from an Ornstein-Uhlenbeck fit.

    A pair that is statistically cointegrated but reverts over three years is
    not tradeable inside a six month window. Half life is the practical filter
    that a p-value alone will not give you.
    """
    s = spread.dropna()
    lagged = s.shift(1).dropna()
    delta = (s - s.shift(1)).dropna()
    aligned = pd.concat([delta, lagged], axis=1).dropna()
    if len(aligned) < 10:
        return np.inf

    x = np.column_stack([np.ones(len(aligned)), aligned.iloc[:, 1].values])
    beta, *_ = np.linalg.lstsq(x, aligned.iloc[:, 0].values, rcond=None)
    lam = beta[1]
    return float(-np.log(2) / lam) if lam < 0 else np.inf


def benjamini_hochberg(pvalues: np.ndarray, fdr: float = 0.10) -> np.ndarray:
    """Return a boolean mask of hypotheses surviving FDR control."""
    n = len(pvalues)
    order = np.argsort(pvalues)
    ranked = pvalues[order]
    thresholds = fdr * np.arange(1, n + 1) / n
    passed = ranked <= thresholds

    mask = np.zeros(n, dtype=bool)
    if passed.any():
        cutoff = np.max(np.where(passed)[0])
        mask[order[: cutoff + 1]] = True
    return mask


def find_pairs(
    prices: pd.DataFrame,
    fdr: float = 0.10,
    max_half_life: float = 60.0,
    max_pairs: int | None = None,
) -> list[Pair]:
    """Screen all combinations, then control the false discovery rate."""
    if not _HAS_SM:
        raise ImportError("statsmodels is required")

    clean = prices.dropna(axis=1, how="any")
    candidates, pvals = [], []

    for a, b in combinations(clean.columns, 2):
        try:
            _, pvalue, _ = coint(clean[a], clean[b])
        except Exception:
            continue
        beta = hedge_ratio(clean[a], clean[b])
        hl = half_life(clean[a] - beta * clean[b])
        if hl > max_half_life:
            continue
        candidates.append(Pair(a, b, float(pvalue), beta, hl))
        pvals.append(pvalue)

    if not candidates:
        return []

    mask = benjamini_hochberg(np.array(pvals), fdr)
    surviving = [p for p, keep in zip(candidates, mask) if keep]
    surviving.sort(key=lambda p: p.pvalue)
    return surviving[:max_pairs] if max_pairs else surviving


def johansen_rank(prices: pd.DataFrame, det_order: int = 0, k_ar_diff: int = 1) -> int:
    """Cointegration rank from the Johansen trace statistic at 95 percent."""
    if not _HAS_SM:
        raise ImportError("statsmodels is required")
    result = coint_johansen(prices.dropna().values, det_order, k_ar_diff)
    return int((result.lr1 > result.cvt[:, 1]).sum())
