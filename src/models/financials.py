from dataclasses import dataclass
import pandas as pd
from typing import Dict


@dataclass
class Financials:
    income: pd.DataFrame
    balance: pd.DataFrame
    cashflow: pd.DataFrame
    info: Dict
