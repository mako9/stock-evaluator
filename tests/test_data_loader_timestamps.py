import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.data_loader import YahooFinanceLoader


def test_offset_aware_and_naive_cache_timestamps(tmp_path, monkeypatch):
    # Create a cache file with an offset-aware timestamp (ISO with +00:00)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    payload = {"timestamp": datetime.now(timezone.utc).isoformat(), "data": {"AAA": 1}}
    with open(cache_dir / "market_caps.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh)

    # Monkeypatch pd.read_html to return a small list so we don't hit network
    import pandas as pd

    monkeypatch.setattr(
        pd, "read_html", lambda url: [pd.DataFrame({"Symbol": ["AAA"]})]
    )

    # Should not raise and should use the cached timestamp without TypeError
    top = YahooFinanceLoader.get_top_n_by_marketcap(
        1, cache_dir=str(cache_dir), ttl_days=7
    )
    assert top == ["AAA"]


def test_old_naive_timestamp_is_treated_as_utc(tmp_path, monkeypatch):
    # Create a cache file with a naive UTC timestamp (old behavior)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    # Build a naive timestamp from a timezone-aware value to avoid using utcnow()
    naive_ts = (
        (datetime.now(timezone.utc) - timedelta(days=1))
        .replace(tzinfo=None)
        .isoformat()
    )
    payload = {"timestamp": naive_ts, "data": {"AAA": 1}}
    with open(cache_dir / "market_caps.json", "w", encoding="utf-8") as fh:
        json.dump(payload, fh)

    import pandas as pd

    monkeypatch.setattr(
        pd, "read_html", lambda url: [pd.DataFrame({"Symbol": ["AAA"]})]
    )

    top = YahooFinanceLoader.get_top_n_by_marketcap(
        1, cache_dir=str(cache_dir), ttl_days=7
    )
    assert top == ["AAA"]
