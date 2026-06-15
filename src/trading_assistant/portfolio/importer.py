from pathlib import Path

import pandas as pd

from trading_assistant.domain.models import Holding


REQUIRED_COLUMNS = {
    "symbol",
    "name",
    "quantity",
    "cost_price",
    "current_price",
    "buy_date",
    "theme",
    "buy_reason",
}


def load_holdings_csv(path: Path) -> list[Holding]:
    frame = pd.read_csv(path, dtype={"symbol": str})
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"holdings csv missing columns: {sorted(missing)}")

    holdings: list[Holding] = []
    for row in frame.to_dict(orient="records"):
        holdings.append(
            Holding(
                symbol=row["symbol"],
                name=row["name"],
                quantity=int(row["quantity"]),
                cost_price=float(row["cost_price"]),
                current_price=float(row["current_price"]),
                buy_date=pd.to_datetime(row["buy_date"]).date(),
                theme=row["theme"],
                buy_reason=row["buy_reason"],
            )
        )
    return holdings
