import pandas as pd
import math

from src.backtest_engine import Backtester


def test_cumulative_returns():
    r = pd.Series([0.01, 0.02, -0.01])

    cum = Backtester.cumulative_returns(r)

    # manual computation
    v1 = 1.01 - 1
    v2 = 1.01 * 1.02 - 1
    v3 = 1.01 * 1.02 * 0.99 - 1

    assert math.isclose(cum.iloc[0], v1, rel_tol=1e-12)
    assert math.isclose(cum.iloc[1], v2, rel_tol=1e-12)
    assert math.isclose(cum.iloc[2], v3, rel_tol=1e-12)


def test_metrics_constant_returns():
    # constant returns => zero volatility, zero drawdown, NaN sharpe
    r = pd.Series([0.01] * 5)

    vol = Backtester.annualized_volatility(r)
    assert math.isclose(vol, 0.0, rel_tol=1e-12)

    dd = Backtester.max_drawdown(r)
    assert math.isclose(dd, 0.0, rel_tol=1e-12)

    sr = Backtester.sharpe_ratio(r)
    assert math.isnan(sr)


def test_max_drawdown_example():
    # returns with a drop producing a clear drawdown: +10% then -5%
    r = pd.Series([0.10, -0.05])
    dd = Backtester.max_drawdown(r)

    # cumulative: after first -> +0.10; after second -> (1.1 * 0.95) -1 = 0.045
    # drawdown from peak value 1.10 to 1.045 => (1.045 / 1.10) - 1 = -0.05 -> max drawdown 0.05
    assert math.isclose(dd, 0.05, rel_tol=1e-12)
