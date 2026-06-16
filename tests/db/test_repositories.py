from datetime import date

from trading_assistant.db.base import Base
from trading_assistant.db.repositories import FocusStockRepository, HoldingRepository
from trading_assistant.db import session as db_session
from trading_assistant.db.session import build_engine, build_session_factory
from trading_assistant.pools.focus_pool import FocusStockImportRow, FocusStockStatus


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


def test_focus_stock_repository_merge_adds_updates_and_keeps_existing() -> None:
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)

    with session_factory() as session:
        repo = FocusStockRepository(session)
        repo.upsert_many(
            [
                FocusStockImportRow(
                    symbol="000001",
                    name="平安银行",
                    focus_reason="银行主线",
                    tags=("银行", "低估"),
                    priority=5,
                    status=FocusStockStatus.ACTIVE,
                ),
                FocusStockImportRow(
                    symbol="600519",
                    name="贵州茅台",
                    focus_reason="白酒观察",
                    tags=("白酒",),
                    priority=2,
                    status=FocusStockStatus.PAUSED,
                ),
            ],
            mode="merge",
        )
        repo.upsert_many(
            [
                FocusStockImportRow(
                    symbol="000001",
                    name=None,
                    focus_reason="继续观察银行",
                    tags=("金融",),
                    priority=4,
                    status=FocusStockStatus.ACTIVE,
                )
            ],
            mode="merge",
        )
        rows = repo.list_focus_stocks()

    assert [row.symbol for row in rows] == ["000001", "600519"]
    assert rows[0].name == "平安银行"
    assert rows[0].focus_reason == "继续观察银行"
    assert rows[0].tags == "金融"
    assert rows[0].priority == 4
    assert rows[0].status == "active"
    assert rows[1].status == "paused"


def test_focus_stock_repository_replace_archives_missing_active_and_paused_rows() -> None:
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)

    with session_factory() as session:
        repo = FocusStockRepository(session)
        repo.upsert_many(
            [
                FocusStockImportRow("000001", "平安银行", "", (), 5, FocusStockStatus.ACTIVE),
                FocusStockImportRow("600519", "贵州茅台", "", (), 3, FocusStockStatus.PAUSED),
                FocusStockImportRow("300001", "样例科技", "", (), 1, FocusStockStatus.ARCHIVED),
            ],
            mode="merge",
        )
        repo.upsert_many(
            [FocusStockImportRow("000001", "平安银行", "保留", (), 4, FocusStockStatus.ACTIVE)],
            mode="replace",
        )
        rows = {row.symbol: row for row in repo.list_focus_stocks()}
        active_map = repo.active_symbol_map()

    assert rows["000001"].status == "active"
    assert rows["600519"].status == "archived"
    assert rows["300001"].status == "archived"
    assert active_map == {"000001": 4}


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
