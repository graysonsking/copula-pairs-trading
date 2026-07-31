# Copula Pairs Trading

Statistical arbitrage on S&P 100 pairs. Pairs are selected with Johansen cointegration testing, and entry and exit rules are driven by a fitted copula rather than a linear spread Z-score.

## Why Copulas

Standard pairs trading assumes the spread between two cointegrated names is normally distributed, then trades deviations from its mean. That assumption fails in the tails, which is exactly where the trades are. A copula separates the marginal distribution of each leg from the dependence structure between them, so tail dependence can be modeled directly instead of assumed away.

The trade signal becomes a conditional probability. Given where asset A sits in its own distribution, how unusual is asset B's position? Positions open when that conditional probability crosses a threshold.

## Method

**1. Pair formation.** Screen S&P 100 constituents for cointegration using the Johansen trace test. Retain pairs significant at the chosen level over the formation window.

**2. Marginal fitting.** Fit empirical or parametric marginals to each leg's returns.

**3. Copula selection.** Fit candidate families (Gaussian, Student t, Clayton, Gumbel, Frank) and select by Kolmogorov-Smirnov statistic. Clayton and Gumbel are included specifically because they capture asymmetric lower and upper tail dependence.

**4. Signal generation.** Compute the conditional distribution function of each leg given the other. Enter when it breaches the entry threshold, exit on reversion to the neutral band or on stop.

**5. Execution.** Dollar-neutral legs, sized by the cointegration vector.

## Parameters

| Parameter | Default |
|---|---|
| Universe | S&P 100 |
| Formation window | 12 months |
| Trading window | 6 months |
| Entry threshold | 0.05 / 0.95 |
| Exit band | 0.45 to 0.55 |
| Stop | Time-based on trading window close |

## Repository Layout

```
copula-pairs-trading/
|
|-- README.md
|-- LICENSE
|-- .gitignore
|-- requirements.txt
|
|-- src/
|   |-- __init__.py
|   |-- copula.py
|   |-- screen.py
|   `-- signal.py
|
|-- strategies/
|   |-- __init__.py
|   |-- copula_pairs.py
|   `-- zscore_pairs.py
|
|-- docs/
|   |-- methodology.md
|   `-- roadmap.md
|
|-- results/
|   `-- .gitkeep
|
|-- tests/
|   |-- __init__.py
|   |-- test_copula.py
|   `-- test_screen.py
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python -m src.screen --start 2010-01-01 --end 2025-12-31
python -m src.backtest --entry 0.05 --exit-band 0.45 0.55
```

## Tests

```bash
python -m pytest tests -q
```

18 tests covering copula fitting and selection, false discovery rate control, half life estimation, and entry hysteresis.

## Results

Populate with your own output. Report the number of pairs traded and average holding period alongside return statistics, since pair count drives capacity.

## Limitations

Cointegration relationships are unstable and frequently break outside the formation window. The backtest does not model borrow cost or short availability, both of which bind on the smaller names in the universe. Multiple testing across a large pair set inflates the apparent significance of any single selected pair.

## License

MIT

---

*Research code. Not investment advice.*
