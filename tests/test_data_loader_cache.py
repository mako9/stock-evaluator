import json
from datetime import datetime, timedelta, timezone

import pandas as pd

from src.data_loader import YahooFinanceLoader


class DummyTicker:
    def __init__(self, info):
        self.info = info


def make_cache(path, data, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    payload = {"timestamp": timestamp, "data": data}
    with open(path / "market_caps.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


def test_uses_cache_when_fresh(tmp_path, monkeypatch):
    # Prepare a cache with values and a fresh timestamp
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    data = {"AAA": 100, "BBB": 50, "CCC": 200}
    make_cache(cache_dir, data)

    # Mock pandas read_html to return tickers AAA/BBB/CCC
    df = pd.DataFrame({"Symbol": ["AAA", "BBB", "CCC"]})
    monkeypatch.setattr(pd, "read_html", lambda url: [df])

    # Mock yfinance.Ticker to fail if called (to ensure cache is used)
    def fake_ticker(ticker):
        raise RuntimeError("Should not call yfinance when cache is fresh")

    monkeypatch.setattr("yfinance.Ticker", fake_ticker)

    top2 = YahooFinanceLoader.get_top_n_by_marketcap(
        2, cache_dir=str(cache_dir), ttl_days=7
    )
    assert top2 == ["CCC", "AAA"]


def test_refreshes_cache_when_expired(tmp_path, monkeypatch):
    # Prepare a cache with old timestamp
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    old_ts = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    data = {"AAA": 100, "BBB": 50, "CCC": 200}
    make_cache(cache_dir, data, timestamp=old_ts)

    # Mock pandas read_html to return tickers AAA/BBB/CCC
    df = pd.DataFrame({"Symbol": ["AAA", "BBB", "CCC"]})
    monkeypatch.setattr(pd, "read_html", lambda url: [df])

    # Make yfinance return updated caps so we can detect the refresh
    mapping = {
        "AAA": {"marketCap": 5},
        "BBB": {"marketCap": 10},
        "CCC": {"marketCap": 1},
    }

    def fake_ticker(ticker):
        class T:
            def __init__(self, info):
                self.info = info

        return T(mapping.get(ticker, {}))

    monkeypatch.setattr("yfinance.Ticker", fake_ticker)

    top2 = YahooFinanceLoader.get_top_n_by_marketcap(
        2, cache_dir=str(cache_dir), ttl_days=7
    )
    # Based on new mapping, top2 should be BBB then AAA
    assert top2 == ["BBB", "AAA"]

    # Cache file should have been updated with new timestamp
    with open(cache_dir / "market_caps.json", "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    assert payload.get("timestamp") is not None
    assert payload.get("data", {}).get("BBB") == 10
