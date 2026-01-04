import pandas as pd
from types import SimpleNamespace

from src.data_loader import YahooFinanceLoader


def test_github_fallback(monkeypatch, tmp_path):
    # pd.read_html fails
    monkeypatch.setattr(
        pd, "read_html", lambda url: (_ for _ in ()).throw(RuntimeError("no html"))
    )

    # requests.get first call returns 403 for Wikipedia
    def fake_get(url, timeout=10, headers=None):
        if "raw.githubusercontent.com" in url:
            # return CSV data
            csv = "Symbol,Name\nAAA,Alpha\nBBB,Beta\nCCC,Gamma\n"
            return SimpleNamespace(status_code=200, text=csv)
        return SimpleNamespace(status_code=403, text="Forbidden")

    monkeypatch.setattr("requests.get", fake_get)

    # Also patch yfinance.Ticker to provide marketCap values
    def fake_ticker(ticker):
        mapping = {
            "AAA": {"marketCap": 100},
            "BBB": {"marketCap": 50},
            "CCC": {"marketCap": 200},
        }

        class T:
            def __init__(self, info):
                self.info = info

        return T(mapping.get(ticker, {}))

    monkeypatch.setattr("yfinance.Ticker", fake_ticker)

    top = YahooFinanceLoader.get_top_n_by_marketcap(2, cache_dir=str(tmp_path))
    assert top == ["CCC", "AAA"]


def test_403_no_cache_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(
        pd, "read_html", lambda url: (_ for _ in ()).throw(RuntimeError("no html"))
    )

    def fake_get(url, timeout=10, headers=None):
        return SimpleNamespace(status_code=403, text="Forbidden")

    monkeypatch.setattr("requests.get", fake_get)

    try:
        YahooFinanceLoader.get_top_n_by_marketcap(2, cache_dir=str(tmp_path))
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "HTTP 403" in str(e) or "no cached market caps" in str(e)
