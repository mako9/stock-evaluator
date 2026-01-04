import pandas as pd
import math

from src.backtest_engine import Backtester
from src.models.stock import Stock
from src.models.kpis import KPIs


def test_backtest_skips_empty_returns(monkeypatch):
    # ticker AAA has data, BBB returns empty
    def fake_returns(ticker, start, end):
        if ticker == "AAA":
            return pd.Series([0.01, 0.02, 0.03])
        return pd.Series([], dtype=float)

    monkeypatch.setattr(Backtester, "returns", staticmethod(fake_returns))

    s1 = Stock(ticker="AAA", sector="S", kpis=KPIs(0, 0, 0, 0, 0), score=1.0)
    s2 = Stock(ticker="BBB", sector="S", kpis=KPIs(0, 0, 0, 0, 0), score=0.5)

    res = Backtester.backtest([s1, s2], index="^GSPC")

    # portfolio CAGR computed from AAA only
    expected = (1 + pd.Series([0.01, 0.02, 0.03])).prod() ** (252 / 3) - 1
    assert math.isclose(res["portfolio_cagr"], float(expected), rel_tol=1e-9)
