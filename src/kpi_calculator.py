from typing import Optional
import math
from src.models.financials import Financials


class KPICalculator:

    @staticmethod
    def roic(fin: Financials) -> Optional[float]:
        try:
            income = fin.income
            tax_rate = fin.info.get("taxRate", 0.21)

            # Try common labels for EBIT/operating profit
            ebit = None
            for key in ["Ebit", "EBIT", "Operating Income", "OperatingIncome"]:
                if key in income.index:
                    ebit = income.loc[key].iloc[0]
                    break

            # Fallback: compute EBIT from Net Income and Interest Expense if available
            if ebit is None:
                if "Net Income" in income.index:
                    net_income = income.loc["Net Income"].iloc[0]
                    interest = (
                        income.loc["Interest Expense"].iloc[0]
                        if "Interest Expense" in income.index
                        else 0.0
                    )
                    # Net Income = (EBIT - Interest) * (1 - tax_rate)
                    ebit = net_income / (1 - tax_rate) + interest
                else:
                    raise KeyError("EBIT not found in income statement")

            nopat = ebit * (1 - tax_rate)
            debt = fin.balance.loc["Long Term Debt"].iloc[0]
            equity = fin.balance.loc["Stockholders Equity"].iloc[0]
            debt = float(debt)
            equity = float(equity)
            if not math.isfinite(debt) or not math.isfinite(equity):
                return None
            if abs(debt + equity) < 1e-6:
                return None
            return nopat / (debt + equity)
        except Exception:
            return None

    @staticmethod
    def roe(fin: Financials) -> Optional[float]:
        try:
            net_income = fin.income.loc["Net Income"].iloc[0]
            equity = fin.balance.loc["Stockholders Equity"].iloc[0]
            net_income = float(net_income)
            equity = float(equity)
            if not math.isfinite(net_income) or not math.isfinite(equity):
                return None
            if abs(equity) < 1e-6:
                return None
            return net_income / equity
        except Exception:
            return None

    @staticmethod
    def fcf_yield(fin: Financials) -> Optional[float]:
        try:
            fcf = fin.cashflow.loc["Free Cash Flow"].iloc[0]
            market_cap = fin.info.get("marketCap")
            fcf = float(fcf)
            market_cap = float(market_cap) if market_cap is not None else float("nan")
            if not math.isfinite(fcf) or not math.isfinite(market_cap):
                return None
            if abs(market_cap) < 1e-6:
                return None
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
            # Ensure numeric and finite values to avoid extreme ratios from tiny denominators
            debt = float(debt)
            equity = float(equity)
            if not math.isfinite(debt) or not math.isfinite(equity):
                return None
            # Guard against near-zero equity which would produce implausibly large ratios
            if abs(equity) < 1e-6:
                return None
            return debt / equity
        except Exception:
            return None
