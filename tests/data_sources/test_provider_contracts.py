from datetime import date
from unittest.mock import Mock, patch

import pandas as pd

from trading_assistant.data_sources.akshare_provider import AkshareMarketDataProvider
from trading_assistant.data_sources.tushare_provider import TushareMarketDataProvider


def test_akshare_provider_normalizes_symbol_column():
    raw = pd.DataFrame(
        {
            "日期": ["2026-06-12"],
            "股票代码": ["000001"],
            "开盘": [10.0],
            "收盘": [10.3],
            "最高": [10.4],
            "最低": [9.9],
            "成交量": [1000],
            "成交额": [10300],
        }
    )

    with patch("trading_assistant.data_sources.akshare_provider.ak.stock_zh_a_hist", return_value=raw):
        provider = AkshareMarketDataProvider(symbols=["000001"])
        frame = provider.get_daily_bars(date(2026, 6, 12), date(2026, 6, 12))

    assert frame.iloc[0]["symbol"] == "000001"
    assert frame.iloc[0]["close"] == 10.3


def test_tushare_provider_requires_token():
    client = Mock()
    provider = TushareMarketDataProvider(token="token", client=client)

    assert provider.token == "token"
