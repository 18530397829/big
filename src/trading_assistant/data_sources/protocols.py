from datetime import date
from typing import Protocol

import pandas as pd


class MarketDataProvider(Protocol):
    def get_daily_bars(self, start: date, end: date) -> pd.DataFrame:
        raise NotImplementedError

    def get_minute_bars(self, trade_date: date) -> pd.DataFrame:
        raise NotImplementedError

    def get_sector_snapshot(self, trade_date: date) -> pd.DataFrame:
        raise NotImplementedError
