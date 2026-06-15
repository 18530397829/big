from datetime import date

import pandas as pd

from trading_assistant.data_sources.protocols import MarketDataProvider


def load_market_snapshot(provider: MarketDataProvider, trade_date: date) -> dict[str, pd.DataFrame]:
    return {
        "daily": provider.get_daily_bars(trade_date, trade_date),
        "minute": provider.get_minute_bars(trade_date),
        "sectors": provider.get_sector_snapshot(trade_date),
    }
