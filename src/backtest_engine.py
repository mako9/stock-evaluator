from typing import Dict, List

import yfinance as yf
import pandas as pd

from src.models.stock import Stock


class Backtester:

    @staticmethod
    def returns(ticker: str, start: str, end: str) -> pd.Series:
        hist = yf.Ticker(ticker).history(start=start, end=end)
        return hist["Close"].pct_change().dropna()

    @staticmethod
    def backtest(stocks: List[Stock], index: str = "^GSPC") -> Dict:
        top = sorted(stocks, key=lambda s: s.score, reverse=True)[:10]
        # Collect returns per ticker, skipping tickers with no data and warning
        import warnings

        columns = {}
        for s in top:
            try:
                r = Backtester.returns(s.ticker, "2019-01-01", "2024-01-01")
                if r.empty:
                    warnings.warn(
                        f"{s.ticker}: no price data found; skipping from backtest"
                    )
                    continue
                columns[s.ticker] = r
            except Exception as e:
                warnings.warn(f"{s.ticker}: error retrieving returns; skipping ({e})")

        if not columns:
            warnings.warn(
                "No valid ticker returns available for backtest; returning NaN results"
            )
            return {"portfolio_cagr": float("nan"), "index_cagr": float("nan")}

        df = pd.concat(columns, axis=1)

        # Drop columns that are entirely NaN (defensive)
        df = df.dropna(axis=1, how="all")

        portfolio = df.mean(axis=1)
        index_ret = Backtester.returns(index, "2019-01-01", "2024-01-01")

        # Use geometric (cumulative product) approach to compute annualized CAGR
        n_port = len(portfolio)
        n_idx = len(index_ret)

        portfolio_cagr = (
            ((1 + portfolio).prod() ** (252 / n_port) - 1)
            if n_port > 0
            else float("nan")
        )

        index_cagr = (
            ((1 + index_ret).prod() ** (252 / n_idx) - 1) if n_idx > 0 else float("nan")
        )

        return {
            "portfolio_cagr": float(portfolio_cagr),
            "index_cagr": float(index_cagr),
        }

    @staticmethod
    def cumulative_returns(returns: pd.Series) -> pd.Series:
        """Convert a returns series to cumulative returns (decimal).

        Example: returns [0.01, 0.02] -> cumulative [0.01, 0.0302]
        """
        return (1 + returns).cumprod() - 1

    @staticmethod
    def annualized_volatility(returns: pd.Series) -> float:
        """Annualized volatility (sample std dev assumed population)"""
        if returns.empty:
            return float("nan")
        return float(returns.std(ddof=0) * (252**0.5))

    @staticmethod
    def sharpe_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
        """Annualized Sharpe ratio (risk-free rate in annual terms). Returns NaN when volatility is zero."""
        if returns.empty:
            return float("nan")
        ann_ret = float(returns.mean()) * 252
        ann_vol = Backtester.annualized_volatility(returns)
        if ann_vol == 0 or ann_vol != ann_vol:  # handles NaN
            return float("nan")
        return (ann_ret - risk_free) / ann_vol

    @staticmethod
    def max_drawdown(returns_or_cum: pd.Series) -> float:
        """Compute maximum drawdown. Accepts either returns or cumulative returns series.

        Returns positive float (e.g., 0.55 for 55% drawdown).
        """
        if returns_or_cum.empty:
            return float("nan")

        # if values look like returns (not already cumulative), convert
        if (returns_or_cum.iloc[-1] <= 1) and (returns_or_cum.abs().max() < 10):
            cum = Backtester.cumulative_returns(returns_or_cum)
        else:
            cum = returns_or_cum

        running_max = (1 + cum).cummax()
        drawdowns = (1 + cum) / running_max - 1
        max_dd = drawdowns.min()
        return float(-max_dd)
