from pathlib import Path
import argparse
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    parser = argparse.ArgumentParser(description="Import focus stock pool CSV")
    parser.add_argument(
        "--path",
        default=os.getenv("FOCUS_POOL_CSV", "data/samples/focus_pool.csv"),
        help="CSV path to import",
    )
    parser.add_argument(
        "--mode",
        choices=["merge", "replace"],
        default="merge",
        help="merge updates rows; replace archives rows missing from the CSV",
    )
    args = parser.parse_args()

    from trading_assistant.db.base import Base
    from trading_assistant.db.repositories import FocusStockRepository
    from trading_assistant.db.session import build_engine, build_session_factory
    from trading_assistant.pools.focus_pool import load_focus_pool_csv
    from trading_assistant.settings import Settings

    rows = load_focus_pool_csv(Path(args.path))
    settings = Settings()
    engine = build_engine(settings.database_url)
    try:
        Base.metadata.create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            repo = FocusStockRepository(session)
            imported_count = repo.upsert_many(rows, mode=args.mode)
            stored_rows = repo.list_focus_stocks()
    finally:
        engine.dispose()

    print(f"imported {imported_count} focus stocks in {args.mode} mode")
    for row in stored_rows:
        display_name = row.name or row.symbol
        print(f"{row.symbol} {display_name} priority={row.priority} status={row.status}")


if __name__ == "__main__":
    main()
