from datetime import date

from sqlalchemy.orm import Session

from trading_assistant.db.models import HoldingORM


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
