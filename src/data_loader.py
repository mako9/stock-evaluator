import yfinance as yf
import pandas as pd
from typing import List
from pathlib import Path
import json
from datetime import datetime, timedelta
import warnings
import requests
import re

from src.models.financials import Financials


class YahooFinanceLoader:
    @staticmethod
    def load_financials(ticker: str) -> Financials:
        stock = yf.Ticker(ticker)
        return Financials(
            income=stock.financials,
            balance=stock.balance_sheet,
            cashflow=stock.cashflow,
            info=stock.info,
        )

    @staticmethod
    def get_top_n_by_marketcap(
        n: int = 500,
        cache_dir: str | None = None,
        ttl_days: int = 7,
        verbose: bool = False,
        min_tickers: int = 100,
    ) -> List[str]:
        """Return top `n` tickers by market capitalization.

        This implementation pulls the S&P 500 constituents from Wikipedia and
        queries Yahoo Finance for `marketCap` values, then returns the top N
        tickers sorted by market cap (descending).

        Caching:
        - If `cache_dir` is provided (or default `.cache/` in repo root), a
          JSON cache file `market_caps.json` will be stored.
        - Cache entries expire after `ttl_days` days.
        """

        repo_root = Path(__file__).resolve().parents[1]
        cache_path = Path(cache_dir) if cache_dir else repo_root / ".cache"
        cache_path.mkdir(parents=True, exist_ok=True)
        cache_file = cache_path / "market_caps.json"

        def _load_cache() -> dict:
            if not cache_file.exists():
                return {}
            try:
                with cache_file.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception:
                return {}

        def _save_cache(data: dict) -> None:
            payload = {"timestamp": datetime.utcnow().isoformat(), "data": data}
            with cache_file.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh)

        cache = _load_cache()
        cached_timestamp = None
        cached_data = {}
        if cache:
            try:
                cached_timestamp = datetime.fromisoformat(cache.get("timestamp"))
                cached_data = cache.get("data", {})
            except Exception:
                cached_timestamp = None
                cached_data = {}

        # Helper: expose cache contents optionally via attribute (useful for debugging)
        # Do not import logging at top-level to keep dependencies minimal
        YahooFinanceLoader._last_cache_path = cache_file
        YahooFinanceLoader._last_cached_timestamp = cached_timestamp
        YahooFinanceLoader._last_cached_data = cached_data

        # Get S&P 500 list from Wikipedia
        try:
            tables = pd.read_html(
                "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            )
            df = tables[0]
            tickers = df["Symbol"].astype(str).tolist()
        except Exception:
            # Try a lightweight fallback using requests + regex to extract the 'Symbol' column
            try:
                import requests
                import re
                from io import StringIO

                url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
                headers = {
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
                }

                resp = requests.get(url, timeout=10, headers=headers)

                tickers = []
                if resp.status_code != 200:
                    # Try a second source (raw GitHub dataset)
                    gh_url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
                    gh_resp = requests.get(gh_url, timeout=10, headers=headers)
                    if gh_resp.status_code == 200:
                        try:
                            df2 = pd.read_csv(StringIO(gh_resp.text))
                            tickers = df2["Symbol"].astype(str).tolist()
                        except Exception:
                            tickers = []
                    else:
                        raise RuntimeError(
                            f"HTTP {resp.status_code} fetching {url}; GitHub fallback returned {gh_resp.status_code}"
                        )
                else:
                    html = resp.text
                    # find the first table containing the header 'Symbol'
                    table_match = None
                    tables = re.findall(
                        r"<table.*?>.*?</table>", html, flags=re.DOTALL | re.IGNORECASE
                    )
                    for t in tables:
                        if re.search(r">\s*Symbol\s*<", t, flags=re.IGNORECASE):
                            table_match = t
                            break

                    if table_match:
                        # Extract rows
                        rows = re.findall(
                            r"<tr.*?>.*?</tr>",
                            table_match,
                            flags=re.DOTALL | re.IGNORECASE,
                        )
                        for r in rows[1:]:
                            cols = re.findall(
                                r"<t[dh].*?>\s*(.*?)\s*</t[dh]>",
                                r,
                                flags=re.DOTALL | re.IGNORECASE,
                            )
                            if cols:
                                sym = re.sub(r"<.*?>", "", cols[0]).strip()
                                if sym:
                                    tickers.append(sym)
                        # remove duplicates while preserving order
                        seen = set()
                        uniq = []
                        for s in tickers:
                            if s not in seen:
                                seen.add(s)
                                uniq.append(s)
                        tickers = uniq

                if not tickers and cached_data:
                    tickers = list(cached_data.keys())

                if not tickers:
                    raise RuntimeError(
                        "Unable to parse S&P 500 tickers from Wikipedia HTML or GitHub fallback. Install 'lxml' or 'beautifulsoup4', or provide a `cache_dir` with `market_caps.json`."
                    )
            except Exception as e:
                # If fallback fails and cache exists, use cached tickers
                if cached_data:
                    tickers = list(cached_data.keys())
                else:
                    raise RuntimeError(
                        f"Unable to retrieve S&P 500 list (pd.read_html failed) and no cached market caps available. "
                        f"Error: {e}. Install 'lxml' or 'beautifulsoup4' and 'requests', or provide a `cache_dir` with `market_caps.json`."
                    )

        # Normalize tickers (Yahoo uses '-' for some tickers like BRK-B)
        tickers = [t.replace(".", "-") for t in tickers]

        # Sanity check: warn if we found a very small universe (likely fallback/cache-only)
        if len(tickers) < min_tickers:

            if cached_data and len(cached_data) >= min_tickers:
                if verbose:
                    warnings.warn(
                        f"Found only {len(tickers)} tickers from Wikipedia/fallback; using {len(cached_data)} cached tickers instead."
                    )
                tickers = list(cached_data.keys())
            else:
                if verbose:
                    warnings.warn(
                        f"Found only {len(tickers)} tickers from Wikipedia/fallback; this is unusually small (min_tickers={min_tickers})."
                    )

        # Normalize tickers (Yahoo uses '-' for some tickers like BRK-B)
        tickers = [t.replace(".", "-") for t in tickers]

        now = datetime.utcnow()
        needs_refresh = (cached_timestamp is None) or (
            now - cached_timestamp > timedelta(days=ttl_days)
        )

        caps = []

        # If cache is fresh, use cached values for tickers present there; only fetch missing/expired ones.
        if not needs_refresh:
            for t in tickers:
                val = cached_data.get(t)
                if val is not None:
                    caps.append((t, val))
            # If cache contained all tickers, return sorted top N
            if len(caps) == len(tickers):
                caps.sort(key=lambda x: x[1], reverse=True)
                if verbose:
                    warnings.warn(
                        f"get_top_n_by_marketcap: returning {len(caps)} tickers (source: fresh cache). Cache path: {cache_file}"
                    )
                return [t for t, _ in caps][:n]

        # Otherwise, fetch market caps for tickers (use cache where available)
        updated = dict(cached_data)
        for t in tickers:
            if t in updated and not needs_refresh:
                caps.append((t, updated[t]))
                continue
            try:
                info = yf.Ticker(t).info
                cap = info.get("marketCap")
                if cap is not None:
                    caps.append((t, cap))
                    updated[t] = cap
            except Exception:
                # skip tickers that fail
                continue

        # Save updated cache
        try:
            _save_cache(updated)
        except Exception:
            pass

        caps.sort(key=lambda x: x[1], reverse=True)
        top = [t for t, _ in caps][:n]

        if verbose:
            warnings.warn(
                f"get_top_n_by_marketcap: returning {len(top)} tickers (requested {n}). Cache path: {cache_file}"
            )

        return top
