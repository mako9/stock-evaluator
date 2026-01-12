from dataclasses import dataclass

from src.models.kpis import KPIs


@dataclass
class Stock:
    ticker: str
    name: str | None = None
    sector: str = "Unknown"
    kpis: KPIs | None = None
    score: float = 0.0
