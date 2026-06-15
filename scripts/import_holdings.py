from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from trading_assistant.portfolio.importer import load_holdings_csv

    holdings = load_holdings_csv(Path("data/samples/holdings.csv"))
    for holding in holdings:
        print(f"{holding.symbol} {holding.name} {holding.market_value:.2f}")


if __name__ == "__main__":
    main()
