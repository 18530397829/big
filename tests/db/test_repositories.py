from datetime import date

from trading_assistant.db.base import Base
from trading_assistant.db.repositories import HoldingRepository
from trading_assistant.db import session as db_session
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


def test_build_engine_adds_sqlite_threading_connect_args(monkeypatch):
    captured: dict[str, object] = {}
    sentinel = object()

    def fake_create_engine(database_url: str, **kwargs: object) -> object:
        captured["database_url"] = database_url
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(db_session, "create_engine", fake_create_engine)

    engine = db_session.build_engine("sqlite:///./trading_assistant.db")

    assert engine is sentinel
    assert captured == {
        "database_url": "sqlite:///./trading_assistant.db",
        "future": True,
        "connect_args": {"check_same_thread": False},
    }


def test_build_engine_does_not_add_sqlite_connect_args_to_other_databases(monkeypatch):
    captured: dict[str, object] = {}
    sentinel = object()

    def fake_create_engine(database_url: str, **kwargs: object) -> object:
        captured["database_url"] = database_url
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(db_session, "create_engine", fake_create_engine)

    engine = db_session.build_engine("postgresql://user:pass@localhost:5432/app")

    assert engine is sentinel
    assert captured == {
        "database_url": "postgresql://user:pass@localhost:5432/app",
        "future": True,
    }
