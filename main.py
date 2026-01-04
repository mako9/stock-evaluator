from src.research_tool import ResearchTool
from src.data_loader import YahooFinanceLoader


if __name__ == "__main__":

    universe = YahooFinanceLoader.get_top_n_by_marketcap(500, verbose=True, ttl_days=0)
    print("\nSelected universe:")
    print(universe)

    tool = ResearchTool(universe)
    tool.load()
    tool.evaluate()
    tool.export_csv("investment_research.csv")

    for s in tool.ranking():
        print(f"{s.ticker}: {round(s.score, 3)}")

    print("\nBacktest:")
    print(tool.backtest())
