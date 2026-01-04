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
            self.stocks.append(
                Stock(
                    ticker=t,
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

    def export_csv(self, path: str = "research_output.csv") -> None:
        rows = []
        for s in self.ranking():
            rows.append(
                {
                    "ticker": s.ticker,
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
        df.to_csv(path, index=False)
