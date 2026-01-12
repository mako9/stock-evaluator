from typing import List

import pandas as pd

from src.backtest_engine import Backtester
from src.data_loader import YahooFinanceLoader
from src.kpi_calculator import KPICalculator
from src.models.kpis import KPIs
from src.models.stock import Stock
from src.score_engine import ScoringEngine


class ResearchTool:

    def __init__(self, tickers: List[str]):
        self.tickers = tickers
        self.stocks: List[Stock] = []

    def load(self):
        for t in self.tickers:
            fin = YahooFinanceLoader.load_financials(t)
            kpis = KPIs(
                roic=KPICalculator.roic(fin),
                roe=KPICalculator.roe(fin),
                fcf_yield=KPICalculator.fcf_yield(fin),
                revenue_cagr=KPICalculator.revenue_cagr(fin),
                debt_to_equity=KPICalculator.debt_to_equity(fin),
            )
            company_name = fin.info.get("longName") or fin.info.get("shortName") or t
            self.stocks.append(
                Stock(
                    ticker=t,
                    name=company_name,
                    sector=fin.info.get("sector", "Unknown"),
                    kpis=kpis,
                )
            )

    def evaluate(self):
        ScoringEngine.score(self.stocks)

    def backtest(self):
        return Backtester.backtest(self.stocks)

    def ranking(self) -> List[Stock]:
        return sorted(self.stocks, key=lambda s: s.score, reverse=True)

    def export_csv(
        self, path: str = "research_output.csv", sep: str = ",", decimal: str = "."
    ) -> None:
        """Export ranked stocks to CSV.

        Parameters
        - path: output file path
        - sep: field separator (use ';' for locales where comma is decimal separator)
        - decimal: decimal point character (default '.')
        """
        rows = []
        for s in self.ranking():
            rows.append(
                {
                    "ticker": s.ticker,
                    "name": s.name or "",
                    "sector": s.sector,
                    "score": round(s.score, 4),
                    "roic": s.kpis.roic,
                    "roe": s.kpis.roe,
                    "fcf_yield": s.kpis.fcf_yield,
                    "revenue_cagr": s.kpis.revenue_cagr,
                    "debt_to_equity": s.kpis.debt_to_equity,
                }
            )

        rows.sort(key=lambda r: r["score"], reverse=True)

        df = pd.DataFrame(rows)
        df.to_csv(path, index=False, sep=sep, decimal=decimal)

    def export_xlsx(self, path: str = "research_output.xlsx") -> None:
        """Export ranked stocks to an Excel file (XLSX).

        This avoids CSV locale/decimal ambiguity and preserves numeric types in
        the spreadsheet as native numeric cells.
        """
        rows = []
        for s in self.ranking():
            rows.append(
                {
                    "ticker": s.ticker,
                    "name": s.name or "",
                    "sector": s.sector,
                    "score": round(s.score, 4),
                    "roic": s.kpis.roic,
                    "roe": s.kpis.roe,
                    "fcf_yield": s.kpis.fcf_yield,
                    "revenue_cagr": s.kpis.revenue_cagr,
                    "debt_to_equity": s.kpis.debt_to_equity,
                }
            )
        rows.sort(key=lambda r: r["score"], reverse=True)
        df = pd.DataFrame(rows)
        # Use pandas to_excel which will write numeric columns as numbers when
        # openpyxl is installed. If openpyxl is missing, pandas will raise a
        # helpful ImportError.
        df.to_excel(path, index=False)
