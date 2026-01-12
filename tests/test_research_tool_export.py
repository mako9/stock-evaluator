import pandas as pd

from src.models.financials import Financials
from src.research_tool import ResearchTool


def test_export_includes_company_name(tmp_path, monkeypatch):
    tickers = ["AAA", "BBB"]

    # Stub YahooFinanceLoader.load_financials to return predictable info
    def _load_financials(ticker):
        return Financials(
            income=pd.DataFrame(),
            balance=pd.DataFrame(),
            cashflow=pd.DataFrame(),
            info={"longName": f"Company {ticker}", "sector": "Tech"},
        )

    monkeypatch.setattr(
        "src.data_loader.YahooFinanceLoader.load_financials", _load_financials
    )

    # Keep KPI calculations simple and deterministic
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
    assert "name" in df.columns
    assert set(df["name"].tolist()) == {"Company AAA", "Company BBB"}
