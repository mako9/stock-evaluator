import json
from datetime import datetime, timezone

import pandas as pd

from src.data_loader import YahooFinanceLoader
import requests


def make_cache(path, data):
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(), "data": data}
    with open(path / "market_caps.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


def test_read_html_failure_uses_cache(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    data = {"AAA": 100, "BBB": 50, "CCC": 200}
    make_cache(cache_dir, data)

    # Make pd.read_html raise
    monkeypatch.setattr(
        pd, "read_html", lambda url: (_ for _ in ()).throw(RuntimeError("no html"))
    )

    top2 = YahooFinanceLoader.get_top_n_by_marketcap(
        2, cache_dir=str(cache_dir), ttl_days=7
    )
    assert top2 == ["CCC", "AAA"]


def test_requests_timeout_uses_cache(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    data = {"AAA": 100, "BBB": 50, "CCC": 200}
    make_cache(cache_dir, data)

    # Simulate requests.get raising a timeout
    def _timeout(*args, **kwargs):
        raise requests.exceptions.Timeout("timed out")

    monkeypatch.setattr("requests.get", _timeout)

    top2 = YahooFinanceLoader.get_top_n_by_marketcap(
        2, cache_dir=str(cache_dir), ttl_days=7
    )
    assert top2 == ["CCC", "AAA"]
