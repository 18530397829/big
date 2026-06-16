from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from trading_assistant.db.base import Base
    from trading_assistant.db.repositories import FocusStockRepository, HoldingRepository
    from trading_assistant.db.session import build_engine, build_session_factory
    from trading_assistant.pools.focus_pool import load_focus_pool_csv
    from trading_assistant.portfolio.importer import load_holdings_csv
    from trading_assistant.settings import Settings

    holdings = load_holdings_csv(Path("data/samples/holdings.csv"))
    focus_stocks = load_focus_pool_csv(Path("data/samples/focus_pool.csv"))
    settings = Settings()
    engine = build_engine(settings.database_url)
    try:
        Base.metadata.create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            holding_repo = HoldingRepository(session)
            for holding in holdings:
                holding_repo.upsert_holding(
                    symbol=holding.symbol,
                    name=holding.name,
                    quantity=holding.quantity,
                    cost_price=holding.cost_price,
                    current_price=holding.current_price,
                    buy_date=holding.buy_date,
                    theme=holding.theme,
                    buy_reason=holding.buy_reason,
                )
            focus_repo = FocusStockRepository(session)
            focus_repo.upsert_many(focus_stocks, mode="merge")
    finally:
        engine.dispose()

    print(f"seeded {len(holdings)} sample holdings into {settings.database_url}")
    print(f"seeded {len(focus_stocks)} sample focus stocks into {settings.database_url}")
    for holding in holdings:
        print(
            f"{holding.symbol} {holding.name} "
            f"market_value={holding.market_value:.2f} "
            f"return={holding.unrealized_return_pct * 100:.2f}%"
        )


if __name__ == "__main__":
    main()
