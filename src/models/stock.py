from dataclasses import dataclass

from src.models.kpis import KPIs


@dataclass
class Stock:
    ticker: str
    sector: str
    kpis: KPIs
    score: float = 0.0
