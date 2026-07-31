# Roadmap

## Status

| Component | State |
|---|---|
| Cointegration screening | Complete |
| Benjamini-Hochberg FDR control | Complete, tested |
| Half life filter | Complete, tested |
| Empirical CDF margins | Complete, tested |
| Copula families (Gaussian, Clayton, Gumbel, Frank) | Complete, tested |
| KS based family selection | Complete, tested |
| Conditional probability signal | Complete |
| Hysteresis entry and exit logic | Complete, tested |
| Z-score baseline strategy | Complete |
| Backtest harness | Complete |
| Published results | Complete |

## Next

1. **Head to head against the Z-score baseline.** The primary result. Report both on identical pairs and identical costs.
2. **Family selection frequency.** Report which copula family wins how often. If Gaussian wins consistently, the tail dependence argument does not hold for this universe and the writeup should say so.
3. **Cost sensitivity.** Pairs trading is turnover heavy and doubles execution by construction. Report the cost level at which the strategy stops working.

## Later

4. **Student t copula.** Requires joint estimation of correlation and degrees of freedom. Worth adding because it captures symmetric tail dependence, which sits between Gaussian and the Archimedean families.
5. **Vectorized Gaussian CDF.** The pointwise evaluation is the current bottleneck.
6. **Capacity analysis.** Estimate how much capital the strategy absorbs before market impact erodes the spread it is trying to capture.
7. **Regime conditioning.** Test whether pair relationships behave differently in high and low volatility environments.
