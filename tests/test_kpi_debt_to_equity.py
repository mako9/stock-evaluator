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


def test_debt_to_equity_normal():
    balance = pd.DataFrame(
        {"2020": [40, 80]}, index=["Long Term Debt", "Stockholders Equity"]
    )
    fin = make_financials({}, balance)
    r = KPICalculator.debt_to_equity(fin)
    assert r == 0.5


def test_debt_to_equity_zero_or_tiny_equity():
    # zero equity -> None
    balance = pd.DataFrame(
        {"2020": [40, 0]}, index=["Long Term Debt", "Stockholders Equity"]
    )
    fin = make_financials({}, balance)
    assert KPICalculator.debt_to_equity(fin) is None

    # tiny equity -> None
    balance = pd.DataFrame(
        {"2020": [40, 1e-9]}, index=["Long Term Debt", "Stockholders Equity"]
    )
    fin = make_financials({}, balance)
    assert KPICalculator.debt_to_equity(fin) is None


def test_debt_to_equity_handles_non_numeric():
    balance = pd.DataFrame(
        {"2020": ["100", "50"]}, index=["Long Term Debt", "Stockholders Equity"]
    )
    fin = make_financials({}, balance)
    r = KPICalculator.debt_to_equity(fin)
    assert r == 2.0
