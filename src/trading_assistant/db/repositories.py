from datetime import date
from typing import Literal

from sqlalchemy.orm import Session

from trading_assistant.db.models import FocusStockORM, HoldingORM
from trading_assistant.pools.focus_pool import FocusStockImportRow, FocusStockStatus


class HoldingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_holding(
        self,
        *,
        symbol: str,
        name: str,
        quantity: int,
        cost_price: float,
        current_price: float,
        buy_date: date,
        theme: str,
        buy_reason: str,
    ) -> None:
        existing = self.session.get(HoldingORM, symbol)
        if existing is None:
            existing = HoldingORM(symbol=symbol)
            self.session.add(existing)
        existing.name = name
        existing.quantity = quantity
        existing.cost_price = cost_price
        existing.current_price = current_price
        existing.buy_date = buy_date
        existing.theme = theme
        existing.buy_reason = buy_reason
        self.session.commit()

    def list_holdings(self) -> list[HoldingORM]:
        return list(self.session.query(HoldingORM).order_by(HoldingORM.symbol).all())


FocusImportMode = Literal["merge", "replace"]


class FocusStockRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_many(
        self,
        items: list[FocusStockImportRow],
        *,
        mode: FocusImportMode = "merge",
    ) -> int:
        if mode not in ("merge", "replace"):
            raise ValueError("focus pool import mode must be merge or replace")

        uploaded_symbols = {item.symbol for item in items}
        if mode == "replace":
            stale_rows = (
                self.session.query(FocusStockORM)
                .filter(FocusStockORM.status.in_(["active", "paused"]))
                .filter(~FocusStockORM.symbol.in_(uploaded_symbols))
                .all()
            )
            for stale_row in stale_rows:
                stale_row.status = FocusStockStatus.ARCHIVED.value

        for item in items:
            existing = self.session.get(FocusStockORM, item.symbol)
            if existing is None:
                existing = FocusStockORM(symbol=item.symbol)
                self.session.add(existing)
            if item.name is not None or existing.name is None:
                existing.name = item.name
            existing.focus_reason = item.focus_reason
            existing.tags = "|".join(item.tags)
            existing.priority = item.priority
            existing.status = item.status.value
        self.session.commit()
        return len(items)

    def list_focus_stocks(
        self,
        statuses: set[FocusStockStatus | str] | None = None,
    ) -> list[FocusStockORM]:
        query = self.session.query(FocusStockORM)
        if statuses is not None:
            status_values = [status.value if isinstance(status, FocusStockStatus) else status for status in statuses]
            query = query.filter(FocusStockORM.status.in_(status_values))
        return list(query.order_by(FocusStockORM.symbol).all())

    def active_symbol_map(self) -> dict[str, int]:
        rows = self.list_focus_stocks(statuses={FocusStockStatus.ACTIVE})
        return {row.symbol: row.priority for row in rows}
