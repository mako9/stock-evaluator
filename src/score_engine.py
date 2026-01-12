from collections import defaultdict
from typing import List
from scipy.stats import percentileofscore
import math
import warnings

from src.models.stock import Stock


class ScoringEngine:

    KPI_WEIGHTS = {
        "roic": 0.30,
        "fcf_yield": 0.25,
        "revenue_cagr": 0.20,
        "roe": 0.15,
        "debt_to_equity": 0.10,
    }

    INVERSE_KPIS = {"debt_to_equity"}

    @staticmethod
    def score(stocks: List[Stock]) -> None:
        # Reset scores before computing to avoid accumulation across runs
        for s in stocks:
            s.score = 0.0

        grouped = defaultdict(list)

        for stock in stocks:
            grouped[stock.sector].append(stock)

        for kpi, weight in ScoringEngine.KPI_WEIGHTS.items():
            for sector, sector_stocks in grouped.items():
                # Exclude None/NaN/inf values from percentile calculations
                values = [
                    v
                    for v in (getattr(s.kpis, kpi) for s in sector_stocks)
                    if v is not None
                    and isinstance(v, (int, float))
                    and math.isfinite(v)
                ]

                if not values:
                    continue

                for s in sector_stocks:
                    value = getattr(s.kpis, kpi)
                    if (
                        value is None
                        or not isinstance(value, (int, float))
                        or not math.isfinite(value)
                    ):
                        continue

                    pct = percentileofscore(values, value) / 100
                    if kpi in ScoringEngine.INVERSE_KPIS:
                        pct = 1 - pct

                    # Guard against NaN propagation
                    if not math.isfinite(pct):
                        continue

                    s.score += pct * weight

        # After scoring, warn about stocks with many missing KPI values and ensure finite scores
        for s in stocks:
            missing = sum(
                1 for k in ScoringEngine.KPI_WEIGHTS if getattr(s.kpis, k) is None
            )
            if missing >= len(ScoringEngine.KPI_WEIGHTS) / 2:
                warnings.warn(
                    f"Stock {s.ticker} has {missing} missing KPI(s); score may be unreliable."
                )

            if not math.isfinite(s.score):
                s.score = 0.0
