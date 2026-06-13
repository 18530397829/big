from datetime import date

import akshare as ak
import pandas as pd


class AkshareMarketDataProvider:
    def __init__(self, symbols: list[str]) -> None:
        self.symbols = symbols

    def get_daily_bars(self, start: date, end: date) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for symbol in self.symbols:
            raw = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust="qfq",
            )
            if raw.empty:
                continue
            frame = raw.rename(
                columns={
                    "日期": "trade_date",
                    "股票代码": "symbol",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "turnover",
                }
            )
            frame["symbol"] = symbol
            frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
            frames.append(
                frame[
                    ["trade_date", "symbol", "open", "high", "low", "close", "volume", "turnover"]
                ]
            )
        if not frames:
            return pd.DataFrame(
                columns=["trade_date", "symbol", "open", "high", "low", "close", "volume", "turnover"]
            )
        return pd.concat(frames, ignore_index=True)

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
