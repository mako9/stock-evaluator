import pandas as pd

from src.data_loader import YahooFinanceLoader


class DummyTicker:
    def __init__(self, info):
        self.info = info


def test_get_top_n_by_marketcap(monkeypatch):
    # Fake the Wikipedia table
    df = pd.DataFrame({"Symbol": ["AAA", "BBB", "CCC"]})
    monkeypatch.setattr(pd, "read_html", lambda url: [df])

    # Fake yfinance Ticker to return marketCap values
    def fake_ticker(ticker):
        mapping = {
            "AAA": {"marketCap": 100},
            "BBB": {"marketCap": 50},
            "CCC": {"marketCap": 200},
        }

        return DummyTicker(mapping.get(ticker, {}))

    monkeypatch.setattr("yfinance.Ticker", fake_ticker)

    top2 = YahooFinanceLoader.get_top_n_by_marketcap(2)
    assert top2 == ["CCC", "AAA"]
