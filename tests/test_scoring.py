from src.score_engine import ScoringEngine
from src.models.stock import Stock
from src.models.kpis import KPIs


def test_scoring_applies_per_sector():
    # Two stocks in different sectors with complete KPI values
    s1 = Stock(ticker="AAA", sector="SectA", kpis=KPIs(1, 1, 1, 1, 1))
    s2 = Stock(ticker="BBB", sector="SectB", kpis=KPIs(1, 1, 1, 1, 1))

    ScoringEngine.score([s1, s2])

    assert s1.score > 0, "s1 should receive a positive score"
    assert s2.score > 0, "s2 should receive a positive score"
