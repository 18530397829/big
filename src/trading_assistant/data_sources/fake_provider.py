from datetime import date
from pathlib import Path

import pandas as pd


class FakeMarketDataProvider:
    def __init__(self, sample_dir: Path) -> None:
        self.sample_dir = sample_dir

    def get_daily_bars(self, start: date, end: date) -> pd.DataFrame:
        frame = pd.read_csv(self.sample_dir / "daily_bars.csv", dtype={"symbol": str})
        frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
        return frame[(frame["trade_date"] >= start) & (frame["trade_date"] <= end)].reset_index(
            drop=True
        )

    def get_minute_bars(self, trade_date: date) -> pd.DataFrame:
        frame = pd.read_csv(self.sample_dir / "minute_bars.csv", dtype={"symbol": str})
        frame["datetime"] = pd.to_datetime(frame["datetime"])
        return frame[frame["datetime"].dt.date == trade_date].reset_index(drop=True)

    def get_sector_snapshot(self, trade_date: date) -> pd.DataFrame:
        frame = pd.read_csv(self.sample_dir / "sectors.csv", dtype={"leader_symbol": str})
        frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
        return frame[frame["trade_date"] == trade_date].reset_index(drop=True)
