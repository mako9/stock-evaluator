import pandas as pd
from types import SimpleNamespace

from src.research_tool import ResearchTool


def test_export_scores_are_finite(tmp_path, monkeypatch):
    # Small deterministic universe
    tickers = ["AAA", "BBB", "CCC"]

    # Fake YahooFinanceLoader.load_financials to provide simple KPIs
    def _load_financials(t):
        return SimpleNamespace(
            info={"longName": f"Company {t}", "sector": "S"},
            income=None,
            balance=None,
            cashflow=None,
        )

    monkeypatch.setattr(
        "src.data_loader.YahooFinanceLoader.load_financials", _load_financials
    )

    # Provide deterministic KPI values by monkeypatching KPICalculator
    monkeypatch.setattr("src.kpi_calculator.KPICalculator.roic", lambda fin: 0.1)
    monkeypatch.setattr("src.kpi_calculator.KPICalculator.roe", lambda fin: 0.2)
    monkeypatch.setattr("src.kpi_calculator.KPICalculator.fcf_yield", lambda fin: 0.03)
    monkeypatch.setattr(
        "src.kpi_calculator.KPICalculator.revenue_cagr", lambda fin: 0.05
    )
    monkeypatch.setattr(
        "src.kpi_calculator.KPICalculator.debt_to_equity", lambda fin: 0.5
    )

    # Make scoring deterministic
    def _score(stocks):
        for i, s in enumerate(stocks):
            s.score = float(i + 1)

    monkeypatch.setattr("src.score_engine.ScoringEngine.score", _score)

    tool = ResearchTool(tickers)
    tool.load()
    tool.evaluate()

    out = tmp_path / "out.csv"
    tool.export_csv(str(out))

    df = pd.read_csv(out)
    # No missing scores
    assert df["score"].notna().all()
    # All scores are finite numbers
    assert df["score"].apply(lambda x: pd.notna(x) and pd.api.types.is_number(x)).all()
