# stock-evaluator

A small toolkit for scoring stocks by financial KPIs and backtesting a simple equal-weight portfolio of top-ranked tickers.

---

## Best Practices ✅

This section documents guidance for contributors and maintainers to keep the project robust, reproducible, and easy to use.

### Project structure 🔧
- **src/**: core implementation (`score_engine`, `backtest_engine`, `data_loader`, `kpi_calculator`, `research_tool`).
- **tests/**: unit tests (use `pytest`).
- **main.py**: simple CLI to run a sample evaluation and backtest.

### Development & setup ⚙️
- Use **Poetry** to manage dependencies and virtual environments.
  - Install: `poetry install`
  - Run tests: `poetry run pytest`
  - Run the demo: `poetry run python main.py`
- Keep Python pinned (e.g., 3.12) in `pyproject.toml` for consistent environments.

### Formatting & linting 🧼
- Use **Black** for consistent formatting: `poetry run black .`
- Add **pre-commit** hooks to run formatters and linters before commits (recommended).

### Testing & CI ✅
- Write unit tests for any logic changes, especially scoring and backtesting code.
- Aim for fast, deterministic tests: mock external calls (e.g., `yfinance`) and use small fixtures.
- Add a CI workflow (GitHub Actions) to run tests and format checks on pull requests.

### Data & reproducibility 📊
- Avoid relying on live network calls in tests — mock or cache API responses.
- Where practical, enable caching for slow or rate-limited network lookups (e.g., market caps); `YahooFinanceLoader.get_top_n_by_marketcap` supports a `cache_dir` and `ttl_days` parameter.
- Record date ranges and seeds for backtests to ensure reproducible results.
- Be explicit about how returns are computed (geometric vs. arithmetic); prefer geometric (cumulative) for accurate CAGR in backtests.

> Tip: Backtester computes annualized CAGR using the geometric cumulative product approach: `(1 + returns).prod() ** (252 / n_days) - 1`.

### Design & implementation notes 💡
- Reset per-stock `score` before re-scoring if evaluations may be rerun.
- Score stocks per-sector to avoid cross-sector distortions (this repo groups by `sector`).
- Handle missing KPI values (`None`) gracefully and add tests for these edge cases.

### Contributing 🤝
- Add tests and update documentation for any new behavior.
- Use clear commit messages and open PRs for review.

---

## CSV export & Backtest interpretation 🔍

This project provides a CSV export of the ranked stocks and a simple backtest summary. Below is an explanation of the fields and how to interpret the backtest results.

### CSV fields (via `ResearchTool.export_csv(path)`) ✅
- **ticker** — Stock ticker symbol (e.g., `AAPL`).
- **name** — Official company name (from data provider, e.g., `Apple Inc.`).
- **sector** — The sector string pulled from the data provider (used for per-sector scoring).
- **score** — Composite score (rounded to 4 decimals) produced by `ScoringEngine`. Higher is better. It is a weighted sum of KPI percentiles computed within each sector; scores are typically in the range **0.0–1.0** (weights sum to 1.0).
- **roic** — Return on Invested Capital (ratio). Example: `0.12` means 12% ROIC.
- **roe** — Return on Equity (ratio). Example: `0.18` means 18% ROE.
- **fcf_yield** — Free Cash Flow yield (FCF / market cap). A ratio (e.g., `0.03` = 3%).
- **revenue_cagr** — Revenue compound annual growth rate (decimal). Example: `0.10` means 10% annual growth.
- **debt_to_equity** — Debt-to-equity ratio. Lower is generally preferable for this repo's scoring (it is an **inverse KPI**).

Notes:
- Missing or uncomputable KPIs are exported as empty/`NaN` values.
- The exported `score` is rounded for readability; the internal value may be used for tie-breaks or further calculations.

### Interpreting the backtest output 📈
The `Backtester.backtest` method returns a small summary dictionary with two keys:

- **`portfolio_cagr`** — The annualized compound growth rate (CAGR) of the equal-weight portfolio composed of the top-ranked stocks (default top 10). Calculation used: geometric approach across daily returns: `(1 + returns).prod() ** (252 / n_days) - 1`.
- **`index_cagr`** — The same CAGR calculation applied to the benchmark index (default `^GSPC`).

How to read it:
- If `portfolio_cagr` > `index_cagr`, the strategy outperformed the index over the selected sample period.
- These numbers are simple point-estimates of annualized return and do **not** capture risk, drawdowns, transaction costs, slippage, or turnover.

Caveats & best practices:
- The portfolio is equally weighted across the selected tickers and uses daily returns averaged across constituents (simple rebalancing assumption). It does not simulate realistic rebalancing frequency, transaction costs, or position sizing beyond equal weight.
- Prefer visualizing cumulative returns and computing risk-adjusted metrics (e.g., volatility, maximum drawdown, Sharpe ratio) to get a fuller picture.
- Ensure consistent date ranges and data availability across constituents to avoid biases (this backtest aligns by using the return series of tickers as returned by `yfinance`).

If you want, I can add a small helper to export cumulative return series or compute additional metrics like volatility and Sharpe ratio — would you like that added? 
