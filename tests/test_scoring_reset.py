from src.score_engine import ScoringEngine
from src.models.stock import Stock
from src.models.kpis import KPIs


def test_scores_reset_between_runs():
    s1 = Stock(ticker="AAA", sector="S", kpis=KPIs(0.1, 0.1, 0.1, 0.1, 0.1))
    s2 = Stock(ticker="BBB", sector="S", kpis=KPIs(0.2, 0.2, 0.2, 0.2, 0.2))

    # run scoring once
    ScoringEngine.score([s1, s2])
    first_scores = (s1.score, s2.score)

    # modify scores manually and run again; scores should be recomputed not accumulated
    s1.score = 10.0
    s2.score = 10.0
    ScoringEngine.score([s1, s2])
    second_scores = (s1.score, s2.score)

    assert second_scores != (10.0, 10.0)
    # Scores should be deterministic and match the first computation
    assert second_scores == first_scores
