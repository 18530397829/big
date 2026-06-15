from datetime import date
from typing import Any

import pandas as pd


class TushareMarketDataProvider:
    def __init__(self, token: str, client: Any | None = None) -> None:
        self.token = token
        self.client = client

    def get_daily_bars(self, start: date, end: date) -> pd.DataFrame:
        if self.client is None:
            return pd.DataFrame(
                columns=["trade_date", "symbol", "open", "high", "low", "close", "volume", "turnover"]
            )
        raw = self.client.daily(start_date=start.strftime("%Y%m%d"), end_date=end.strftime("%Y%m%d"))
        return raw.rename(columns={"ts_code": "symbol", "vol": "volume", "amount": "turnover"})

    def get_minute_bars(self, trade_date: date) -> pd.DataFrame:
        return pd.DataFrame(
            columns=["datetime", "symbol", "open", "high", "low", "close", "volume", "turnover"]
        )

    def get_sector_snapshot(self, trade_date: date) -> pd.DataFrame:
        return pd.DataFrame(
            columns=[
                "trade_date",
                "sector_name",
                "sector_type",
                "pct_chg",
                "turnover",
                "limit_up_count",
                "leader_symbol",
            ]
        )
