"""Copula fitting and selection.

Why bother. Standard pairs trading assumes the spread is normally distributed
and trades deviations from its mean. That assumption is weakest in the tails,
which is precisely where the trades are placed. A copula separates each leg's
marginal distribution from the dependence structure between them, so tail
dependence can be modeled instead of assumed away.

The practical consequence: Gaussian and Student t copulas impose symmetric
dependence, while Clayton captures stronger co-movement in the lower tail and
Gumbel in the upper. Equity pairs frequently crash together and rally apart,
which is exactly the asymmetry a Gaussian copula cannot represent.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize_scalar

FAMILIES = ("gaussian", "student_t", "clayton", "gumbel", "frank")


def to_uniform(series: pd.Series) -> pd.Series:
    """Empirical CDF transform to uniform margins.

    Using the empirical CDF avoids committing to a parametric marginal, which
    keeps marginal misspecification from contaminating the dependence estimate.
    """
    return series.rank(method="average") / (len(series) + 1.0)


# --------------------------------------------------------------- generators


def _clayton_cdf(u: np.ndarray, v: np.ndarray, theta: float) -> np.ndarray:
    if theta <= 0:
        return u * v
    return np.power(np.maximum(u ** -theta + v ** -theta - 1.0, 1e-12), -1.0 / theta)


def _gumbel_cdf(u: np.ndarray, v: np.ndarray, theta: float) -> np.ndarray:
    if theta <= 1:
        return u * v
    lu, lv = -np.log(np.clip(u, 1e-12, 1)), -np.log(np.clip(v, 1e-12, 1))
    return np.exp(-np.power(lu ** theta + lv ** theta, 1.0 / theta))


def _frank_cdf(u: np.ndarray, v: np.ndarray, theta: float) -> np.ndarray:
    if abs(theta) < 1e-8:
        return u * v
    num = (np.exp(-theta * u) - 1.0) * (np.exp(-theta * v) - 1.0)
    return -np.log1p(num / (np.exp(-theta) - 1.0)) / theta


def _gaussian_cdf(u: np.ndarray, v: np.ndarray, rho: float) -> np.ndarray:
    from scipy.stats import multivariate_normal

    x, y = stats.norm.ppf(np.clip(u, 1e-9, 1 - 1e-9)), stats.norm.ppf(np.clip(v, 1e-9, 1 - 1e-9))
    cov = [[1.0, rho], [rho, 1.0]]
    return np.array([multivariate_normal.cdf([xi, yi], mean=[0, 0], cov=cov) for xi, yi in zip(x, y)])


CDFS = {
    "gaussian": _gaussian_cdf,
    "clayton": _clayton_cdf,
    "gumbel": _gumbel_cdf,
    "frank": _frank_cdf,
}


@dataclass
class FittedCopula:
    """A fitted copula family with its selection statistic."""

    family: str
    theta: float
    ks_stat: float

    def conditional_u_given_v(self, u: np.ndarray, v: np.ndarray, eps: float = 1e-5) -> np.ndarray:
        """P(U <= u | V = v), computed by numerical differentiation.

        This is the trade signal. It answers: given where leg B sits in its own
        distribution, how unusual is leg A's position? Values near zero or one
        mark a dislocation.
        """
        cdf = CDFS[self.family]
        upper = cdf(u, np.clip(v + eps, 1e-9, 1 - 1e-9), self.theta)
        lower = cdf(u, np.clip(v - eps, 1e-9, 1 - 1e-9), self.theta)
        return np.clip((upper - lower) / (2 * eps), 0.0, 1.0)


def _kendall_tau_to_theta(family: str, tau: float) -> float:
    """Closed form inversion of Kendall's tau for Archimedean families."""
    tau = float(np.clip(tau, -0.95, 0.95))
    if family == "clayton":
        return max(2 * tau / (1 - tau), 1e-6) if tau > 0 else 1e-6
    if family == "gumbel":
        return max(1.0 / (1 - tau), 1.0 + 1e-6) if tau < 1 else 1.0 + 1e-6
    if family == "gaussian":
        return float(np.sin(np.pi * tau / 2))
    return 1.0


def fit(u: pd.Series, v: pd.Series, family: str) -> FittedCopula:
    """Fit one family and score it by Kolmogorov-Smirnov distance."""
    uu, vv = u.values, v.values
    tau = stats.kendalltau(uu, vv).correlation

    if family == "frank":
        def neg_fit(theta):
            model = _frank_cdf(uu, vv, theta)
            empirical = np.array([np.mean((uu <= a) & (vv <= b)) for a, b in zip(uu, vv)])
            return np.max(np.abs(model - empirical))

        res = minimize_scalar(neg_fit, bounds=(-30, 30), method="bounded")
        theta, ks = float(res.x), float(res.fun)
    else:
        theta = _kendall_tau_to_theta(family, tau)
        model = CDFS[family](uu, vv, theta)
        empirical = np.array([np.mean((uu <= a) & (vv <= b)) for a, b in zip(uu, vv)])
        ks = float(np.max(np.abs(model - empirical)))

    return FittedCopula(family, theta, ks)


def select_best(u: pd.Series, v: pd.Series, families=FAMILIES) -> FittedCopula:
    """Fit every family and keep the lowest KS statistic.

    KS is used rather than AIC because these families have the same parameter
    count, so the penalty term would not discriminate between them.
    """
    fitted = []
    for f in families:
        if f == "student_t":
            continue  # requires a separate degrees of freedom estimate
        try:
            fitted.append(fit(u, v, f))
        except Exception:
            continue
    if not fitted:
        raise RuntimeError("no copula family could be fitted")
    return min(fitted, key=lambda c: c.ks_stat)


def tail_dependence(fitted: FittedCopula) -> tuple[float, float]:
    """Lower and upper tail dependence coefficients."""
    if fitted.family == "clayton":
        return (2 ** (-1 / fitted.theta), 0.0)
    if fitted.family == "gumbel":
        return (0.0, 2 - 2 ** (1 / fitted.theta))
    return (0.0, 0.0)
