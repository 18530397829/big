from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from trading_assistant.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class HoldingORM(Base):
    __tablename__ = "holdings"

    symbol: Mapped[str] = mapped_column(String(12), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    buy_date: Mapped[date] = mapped_column(Date, nullable=False)
    theme: Mapped[str] = mapped_column(String(64), nullable=False)
    buy_reason: Mapped[str] = mapped_column(String(256), nullable=False)


class FocusStockORM(Base):
    __tablename__ = "focus_stocks"

    symbol: Mapped[str] = mapped_column(String(6), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    focus_reason: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    tags: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )
