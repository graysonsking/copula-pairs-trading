"""Run configuration.

Everything you would want to change lives here. `run_results.py` reads this
and does not need editing.

No credentials are required. yfinance is unauthenticated.
"""

from __future__ import annotations

from pathlib import Path

# ================================================================= universe
# Liquid S&P 100 names with continuous history. Screening is O(n^2) in the
# number of names, so this list is the main runtime lever: 50 names is about
# 1,200 cointegration tests per formation window, 100 names is about 5,000.

UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "JPM", "UNH", "XOM", "V",
    "PG", "JNJ", "MA", "HD", "MRK", "PEP", "ABBV", "CVX", "KO", "BAC",
    "ADBE", "COST", "PFE", "WMT", "CSCO", "ACN", "TMO", "INTC", "VZ", "ABT",
    "CRM", "MCD", "TXN", "NEE", "AMGN", "LOW", "HON", "BMY", "UNP", "QCOM",
    "MDT", "GS", "RTX", "IBM", "SBUX", "CAT", "GE", "BLK", "AXP", "DE",
]

# ============================================================ backtest knobs

START = "2010-01-01"
END = None

FORMATION_DAYS = 252    # screen pairs on 12 months
TRADING_DAYS = 126      # trade them for the following 6 months
REBALANCE_DAYS = 5      # evaluate signals weekly
SIGNAL_LOOKBACK = 252   # history handed to the signal functions

FDR = 0.10              # Benjamini-Hochberg false discovery rate
MAX_HALF_LIFE = 60.0    # days; slower reverters are untradeable in 6 months
MAX_PAIRS = 10          # cap per formation window

COST_BPS = 10.0         # one way, on turnover

# ==================================================================== paths

ROOT = Path(__file__).parent
CACHE_DIR = ROOT / "cache"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "docs" / "images"
