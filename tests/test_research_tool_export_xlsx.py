import pandas as pd
import pytest
from src.models.financials import Financials
from src.research_tool import ResearchTool


def make_financials(income_dict, balance_dict, cashflow_dict=None, info=None):
    if cashflow_dict is None:
        cashflow_dict = {}
    if info is None:
        info = {}
    income = pd.DataFrame(income_dict)
    balance = pd.DataFrame(balance_dict)
    cashflow = pd.DataFrame(cashflow_dict)
    return Financials(income=income, balance=balance, cashflow=cashflow, info=info)


@pytest.mark.skipif(
    pytest.importorskip("openpyxl") is None,
    reason="openpyxl is required to run this test",
)
def test_export_xlsx_preserves_numeric_types(tmp_path, monkeypatch):
    # Prepare two tickers with deterministic KPIs
    tickers = ["AAA", "BBB"]

    def _load_financials(ticker):
        return make_financials(
            {},
            {"2020": [10, 20]},
            cashflow_dict={},
            info={"longName": f"Company {ticker}", "sector": "Tech"},
        )

    monkeypatch.setattr(
        "src.data_loader.YahooFinanceLoader.load_financials", _load_financials
    )
    monkeypatch.setattr("src.kpi_calculator.KPICalculator.roic", lambda fin: 0.1)
    monkeypatch.setattr(
        "src.kpi_calculator.KPICalculator.roe",
        lambda fin: 0.2 if fin is not None else None,
    )
    monkeypatch.setattr("src.kpi_calculator.KPICalculator.fcf_yield", lambda fin: None)
    monkeypatch.setattr(
        "src.kpi_calculator.KPICalculator.revenue_cagr", lambda fin: 0.05
    )
    monkeypatch.setattr(
        "src.kpi_calculator.KPICalculator.debt_to_equity", lambda fin: 0.5
    )

    def _score(stocks):
        for i, s in enumerate(stocks):
            s.score = float(i + 1)

    monkeypatch.setattr("src.score_engine.ScoringEngine.score", _score)

    tool = ResearchTool(tickers)
    tool.load()
    tool.evaluate()

    out = tmp_path / "out.xlsx"
    tool.export_xlsx(str(out))

    # Read back the XLSX and assert numeric preservation
    df = pd.read_excel(out, engine="openpyxl")
    assert "name" in df.columns
    assert df.loc[0, "debt_to_equity"] == 0.5
    # fcf_yield was None -> should be NaN in the read back DataFrame
    assert pd.isna(df.loc[0, "fcf_yield"])
