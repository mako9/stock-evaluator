import math

from src.models.kpis import KPIs
from src.models.stock import Stock
from src.score_engine import ScoringEngine


class DummyKPIs(KPIs):
    pass


def test_score_handles_nan_and_inf_values():
    # Create stocks where some KPI values are nan/inf and others valid
    s1 = Stock(
        ticker="A",
        sector="S",
        kpis=KPIs(
            roic=0.1,
            fcf_yield=float("nan"),
            revenue_cagr=0.05,
            roe=0.2,
            debt_to_equity=0.5,
        ),
    )
    s2 = Stock(
        ticker="B",
        sector="S",
        kpis=KPIs(
            roic=float("nan"),
            fcf_yield=0.02,
            revenue_cagr=float("inf"),
            roe=0.1,
            debt_to_equity=0.3,
        ),
    )
    s3 = Stock(
        ticker="C",
        sector="S",
        kpis=KPIs(
            roic=None, fcf_yield=None, revenue_cagr=None, roe=None, debt_to_equity=None
        ),
    )

    stocks = [s1, s2, s3]

    ScoringEngine.score(stocks)

    # No score should be NaN or infinite
    for s in stocks:
        assert isinstance(s.score, float)
        assert not math.isnan(s.score)
        assert math.isfinite(s.score)
