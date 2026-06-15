from datetime import date

from trading_assistant.db.base import Base
from trading_assistant.db.repositories import HoldingRepository
from trading_assistant.db.session import build_engine, build_session_factory


def test_holding_repository_upsert_and_list():
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)

    with session_factory() as session:
        repo = HoldingRepository(session)
        repo.upsert_holding(
            symbol="000001",
            name="平安银行",
            quantity=1000,
            cost_price=10.0,
            current_price=10.3,
            buy_date=date(2026, 6, 10),
            theme="银行",
            buy_reason="放量突破平台",
        )
        rows = repo.list_holdings()

    assert len(rows) == 1
    assert rows[0].symbol == "000001"
    assert rows[0].current_price == 10.3


def test_build_engine_supports_documented_postgresql_url():
    engine = build_engine(
        "postgresql://trading_assistant:trading_assistant@localhost:5432/trading_assistant"
    )
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.driver == "psycopg2"
    finally:
        engine.dispose()
