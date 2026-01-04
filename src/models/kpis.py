from dataclasses import dataclass
from typing import Optional


@dataclass
class KPIs:
    roic: Optional[float]
    roe: Optional[float]
    fcf_yield: Optional[float]
    revenue_cagr: Optional[float]
    debt_to_equity: Optional[float]
