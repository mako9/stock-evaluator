from typing import Optional
from src.models.financials import Financials


class KPICalculator:

    @staticmethod
    def roic(fin: Financials) -> Optional[float]:
        try:
            ebit = fin.income.loc["Ebit"].iloc[0]
            tax_rate = fin.info.get("taxRate", 0.21)
            nopat = ebit * (1 - tax_rate)
            debt = fin.balance.loc["Long Term Debt"].iloc[0]
            equity = fin.balance.loc["Stockholders Equity"].iloc[0]
            return nopat / (debt + equity)
        except Exception:
            return None

    @staticmethod
    def roe(fin: Financials) -> Optional[float]:
        try:
            net_income = fin.income.loc["Net Income"].iloc[0]
            equity = fin.balance.loc["Stockholders Equity"].iloc[0]
            return net_income / equity
        except Exception:
            return None

    @staticmethod
    def fcf_yield(fin: Financials) -> Optional[float]:
        try:
            fcf = fin.cashflow.loc["Free Cash Flow"].iloc[0]
            market_cap = fin.info.get("marketCap")
            return fcf / market_cap
        except Exception:
            return None

    @staticmethod
    def revenue_cagr(fin: Financials, years: int = 3) -> Optional[float]:
        try:
            rev = fin.income.loc["Total Revenue"].iloc[: years + 1]
            return (rev.iloc[0] / rev.iloc[-1]) ** (1 / years) - 1
        except Exception:
            return None

    @staticmethod
    def debt_to_equity(fin: Financials) -> Optional[float]:
        try:
            debt = fin.balance.loc["Long Term Debt"].iloc[0]
            equity = fin.balance.loc["Stockholders Equity"].iloc[0]
            return debt / equity
        except Exception:
            return None
