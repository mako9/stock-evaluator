from src.backtest_engine import Backtester
from src.models.stock import Stock
from src.models.kpis import KPIs
import pandas as pd
import math


def test_backtest_cagr_geometric(monkeypatch):
    # constant daily return r -> geometric CAGR should be (1 + r) ** 252 - 1
    r = 0.01
    n = 5
    series = pd.Series([r] * n)

    def fake_returns(ticker, start, end):
        return series.copy()

    monkeypatch.setattr(Backtester, "returns", staticmethod(fake_returns))

    s = Stock(ticker="AAA", sector="S", kpis=KPIs(0, 0, 0, 0, 0), score=1.0)
    res = Backtester.backtest([s], index="^GSPC")

    expected = (1 + r) ** 252 - 1
    assert math.isclose(res["portfolio_cagr"], expected, rel_tol=1e-9)
    assert math.isclose(res["index_cagr"], expected, rel_tol=1e-9)
