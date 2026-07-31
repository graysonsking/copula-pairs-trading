# Methodology

## Why Copulas

Conventional pairs trading models the spread between two cointegrated names as normally distributed and trades deviations from its mean. The assumption fails hardest in the tails, which is exactly where the trades are placed.

A copula separates each leg's marginal distribution from the dependence structure linking them. That separation lets tail behavior be modeled rather than assumed. Concretely, Gaussian and Student t copulas impose symmetric dependence, while Clayton captures stronger co-movement in the lower tail and Gumbel in the upper. Equity pairs frequently crash together and rally apart. A Gaussian copula cannot represent that asymmetry, so it misprices precisely the states that determine whether a pairs book survives.

The trade signal becomes a conditional probability: given where leg B sits in its own distribution, how unusual is leg A's position?

## Pipeline

**1. Formation.** Screen all pairs in the universe for cointegration over a 12 month window.

**2. Filtering.** Two filters beyond the p-value.

**3. Fitting.** Transform both legs to uniform margins with the empirical CDF, then fit candidate copula families and select by Kolmogorov-Smirnov distance.

**4. Trading.** Compute the conditional probability at each rebalance. Open when it breaches the entry threshold, close on reversion into the neutral band.

**5. Sizing.** Dollar neutral legs sized by the hedge ratio, capital split evenly across active pairs.

## The Multiple Testing Problem

This is the main reason naive pair screens disappoint out of sample, and it is usually ignored.

A 100 name universe contains 4,950 possible pairs. Testing all of them at a 5 percent significance threshold produces roughly 250 false positives by construction, before a single genuine relationship is found. Selecting the "most significant" pairs from that set is largely selecting the luckiest noise.

`screen.benjamini_hochberg` applies false discovery rate control at 10 percent. A test asserts it is strictly more conservative than an uncorrected threshold on uniform p-values.

## Half Life Filter

Statistical cointegration is necessary but not sufficient. A pair that is genuinely cointegrated but reverts over three years cannot be traded inside a six month window.

Half life is estimated from an Ornstein-Uhlenbeck fit on the spread and pairs exceeding the maximum are dropped at formation. Tests confirm the estimator returns effectively infinite half life for a random walk and a short finite value for a mean reverting series.

## Marginals

Empirical CDF rather than a fitted parametric distribution. Committing to a parametric marginal introduces misspecification that contaminates the dependence estimate, and the dependence structure is the object of interest here.

## Family Selection

KS distance rather than AIC. The candidate families carry the same parameter count, so an information criterion penalty would not discriminate between them.

Student t is listed but excluded from automatic selection because it requires a separate degrees of freedom estimate that the tau inversion used for the other families does not provide.

**A limitation found while testing this.** KS distance cannot reliably distinguish Gaussian from Frank on symmetric data. On simulated Gaussian-dependent samples the two statistics differ by less than 0.0005, which is well inside sampling noise, and which family "wins" flips with the sample size. Both families are symmetric with zero tail dependence, so they describe nearly the same structure and KS has almost nothing to separate them on.

What selection does do reliably is reject families implying tail dependence the data does not have. Clayton is cleanly rejected on symmetric samples (KS roughly double the alternatives), and is correctly recovered on samples simulated from a Clayton copula. Both directions are asserted in `tests/test_copula.py`.

The practical implication for interpreting results: treat the selected family as a statement about tail dependence present or absent, not as an identification of the true generating family. A reported "Frank was selected" should not be read as evidence against Gaussian. If family selection is going to carry weight in a conclusion, report the full KS table rather than the winner alone.

## Entry, Exit, and Hysteresis

Entry at 0.05 and 0.95. Exit on reversion into the 0.45 to 0.55 band.

The bands deliberately do not touch. A single threshold applied to a probability oscillating around that level generates a stream of round trips that costs more than the spread is worth. The gap between entry and exit is what prevents it.

## The Honest Baseline

`strategies/zscore_pairs.py` implements conventional Z-score trading on the same pairs, same schedule, same cost model.

The copula approach must beat this, not merely beat buy and hold. If it does not, the added complexity is not earning its keep, and that is a result worth reporting.

## Limitations

- Cointegration relationships are unstable and frequently break outside the formation window. This is a property of the phenomenon, not of the implementation.
- Borrow cost and short availability are not modeled, and both bind on the smaller names in the universe.
- The Gaussian copula CDF is evaluated pointwise, which is slow on large samples.
- Even with FDR control, pairs are selected from the same history used to evaluate them. Genuine out of sample validation requires a holdout period that has not been examined.
