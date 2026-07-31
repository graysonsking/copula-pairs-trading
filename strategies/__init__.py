"""Strategy configurations."""

from . import copula_pairs, zscore_pairs

REGISTRY = {
    "copula_pairs": copula_pairs.weights_fn,
    "zscore_pairs": zscore_pairs.weights_fn,
}

__all__ = ["REGISTRY", "copula_pairs", "zscore_pairs"]
