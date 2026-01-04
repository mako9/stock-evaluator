from types import SimpleNamespace

import pandas as pd

from src.data_loader import YahooFinanceLoader


def test_fallback_parses_html(monkeypatch):
    # Make pd.read_html raise
    monkeypatch.setattr(
        pd, "read_html", lambda url: (_ for _ in ()).throw(RuntimeError("no html"))
    )

    # Fake requests.get to return a simple HTML table
    html = """
    <html>
    <body>
      <table>
        <thead><tr><th>Symbol</th><th>Security</th></tr></thead>
        <tbody>
          <tr><td>AAA</td><td>Alpha</td></tr>
          <tr><td>BBB</td><td>Beta</td></tr>
          <tr><td>CCC</td><td>Gamma</td></tr>
        </tbody>
      </table>
    </body>
    </html>
    """

    def fake_get(url, timeout=10):
        return SimpleNamespace(status_code=200, text=html)

    monkeypatch.setattr("requests.get", fake_get)

    # Ensure yfinance returns deterministic marketCap values for parsed tickers
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

    top2 = YahooFinanceLoader.get_top_n_by_marketcap(2)
    assert top2 == ["CCC", "AAA"]


def test_fallback_no_parser_and_no_cache_raises(monkeypatch, tmp_path):
    # pd.read_html fails
    monkeypatch.setattr(
        pd, "read_html", lambda url: (_ for _ in ()).throw(RuntimeError("no html"))
    )

    # requests.get raises so fallback also fails
    def fake_get_raise(url, timeout=10):
        raise RuntimeError("no network")

    monkeypatch.setattr("requests.get", fake_get_raise)

    # Use an empty temporary cache directory to ensure no cached market caps exist
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    try:
        YahooFinanceLoader.get_top_n_by_marketcap(2, cache_dir=str(cache_dir))
        assert False, "Expected RuntimeError"
    except RuntimeError as e:
        assert "Install 'lxml' or 'beautifulsoup4'" in str(
            e
        ) or "no cached market caps" in str(e)
