import pandas as pd

from src.kpi_calculator import KPICalculator
from src.models.financials import Financials


def make_financials(income_dict, balance_dict, cashflow_dict=None, info=None):
    if cashflow_dict is None:
        cashflow_dict = {}
    if info is None:
        info = {}
    income = pd.DataFrame(income_dict)
    balance = pd.DataFrame(balance_dict)
    cashflow = pd.DataFrame(cashflow_dict)
    return Financials(income=income, balance=balance, cashflow=cashflow, info=info)


def test_roic_from_ebit():
    income = pd.DataFrame({"2020": [100]}, index=["Ebit"])
    balance = pd.DataFrame(
        {"2020": [50, 150]}, index=["Long Term Debt", "Stockholders Equity"]
    )
    fin = make_financials(income, balance, info={"taxRate": 0.2})

    r = KPICalculator.roic(fin)
    assert r is not None
    assert abs(r - 0.4) < 1e-12


def test_roic_from_operating_income():
    income = pd.DataFrame({"2020": [200]}, index=["Operating Income"])
    balance = pd.DataFrame(
        {"2020": [40, 160]}, index=["Long Term Debt", "Stockholders Equity"]
    )
    fin = make_financials(income, balance, info={"taxRate": 0.2})

    r = KPICalculator.roic(fin)
    assert r is not None
    assert abs(r - 0.8) < 1e-12


def test_roic_computed_from_net_income_and_interest():
    income = pd.DataFrame({"2020": [64, 10]}, index=["Net Income", "Interest Expense"])
    balance = pd.DataFrame(
        {"2020": [40, 80]}, index=["Long Term Debt", "Stockholders Equity"]
    )
    fin = make_financials(income, balance, info={"taxRate": 0.2})

    # EBIT = NetIncome / (1 - tax) + Interest = 64/0.8 + 10 = 90
    # NOPAT = 90 * 0.8 = 72, invested = 40 + 80 = 120 => 72/120 = 0.6
    r = KPICalculator.roic(fin)
    assert r is not None
    assert abs(r - 0.6) < 1e-12


def test_roic_missing_returns_none():
    income = pd.DataFrame({"2020": [123]}, index=["Some Other Metric"])
    balance = pd.DataFrame(
        {"2020": [10, 20]}, index=["Long Term Debt", "Stockholders Equity"]
    )
    fin = make_financials(income, balance)

    r = KPICalculator.roic(fin)
    assert r is None
