import json
from datetime import datetime, timedelta

import pandas as pd
import warnings

from src.data_loader import YahooFinanceLoader


def test_small_universe_warns_and_uses_cache(tmp_path, monkeypatch):
    # Setup a small wikipedia result
    monkeypatch.setattr(
        pd, "read_html", lambda url: [pd.DataFrame({"Symbol": ["AAA"]})]
    )

    # Prepare a cache with many entries
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    data = {f"T{i}": i for i in range(200)}
    payload = {"timestamp": datetime.utcnow().isoformat(), "data": data}
    with open(cache_dir / "market_caps.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh)

    # Should switch to cached tickers and warn
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        top = YahooFinanceLoader.get_top_n_by_marketcap(
            10, cache_dir=str(cache_dir), verbose=True
        )

        assert any(
            "Found only" in str(x.message) for x in w
        ), "Expected a 'Found only' warning"
    assert len(top) == 10


def test_verbose_reports_cache_path(tmp_path, monkeypatch):
    # Mock pd.read_html to return normal set
    monkeypatch.setattr(
        pd, "read_html", lambda url: [pd.DataFrame({"Symbol": ["AAA", "BBB", "CCC"]})]
    )

    # Have yfinance return market caps
    def fake_ticker(t):
        class T:
            def __init__(self, info):
                self.info = {"marketCap": 100}

        return T({})

    monkeypatch.setattr("yfinance.Ticker", fake_ticker)

    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        top = YahooFinanceLoader.get_top_n_by_marketcap(2, verbose=True)
        assert any("returning" in str(x.message) for x in w)
    assert len(top) == 2
