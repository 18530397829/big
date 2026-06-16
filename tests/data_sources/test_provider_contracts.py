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


def test_akshare_provider_falls_back_to_daily_endpoint_when_hist_fails():
    raw = pd.DataFrame(
        {
            "date": ["2024-06-14"],
            "open": [10.0],
            "high": [10.4],
            "low": [9.9],
            "close": [10.3],
            "volume": [1000],
            "amount": [10300],
        }
    )

    with (
        patch(
            "trading_assistant.data_sources.akshare_provider.ak.stock_zh_a_hist",
            side_effect=ConnectionError("primary endpoint disconnected"),
        ),
        patch(
            "trading_assistant.data_sources.akshare_provider.ak.stock_zh_a_daily",
            return_value=raw,
        ) as fallback,
    ):
        provider = AkshareMarketDataProvider(symbols=["000001"])
        frame = provider.get_daily_bars(date(2024, 6, 14), date(2024, 6, 14))

    fallback.assert_called_once_with(
        symbol="sz000001",
        start_date="20240614",
        end_date="20240614",
        adjust="qfq",
    )
    assert frame.iloc[0]["symbol"] == "000001"
    assert frame.iloc[0]["trade_date"] == date(2024, 6, 14)
    assert frame.iloc[0]["turnover"] == 10300


def test_akshare_provider_fallback_prefers_amount_when_daily_has_turnover_rate():
    raw = pd.DataFrame(
        {
            "date": ["2024-06-14"],
            "open": [10.0],
            "high": [10.4],
            "low": [9.9],
            "close": [10.3],
            "volume": [1000],
            "amount": [10300],
            "turnover": [1.23],
        }
    )

    with (
        patch(
            "trading_assistant.data_sources.akshare_provider.ak.stock_zh_a_hist",
            side_effect=ConnectionError("primary endpoint disconnected"),
        ),
        patch(
            "trading_assistant.data_sources.akshare_provider.ak.stock_zh_a_daily",
            return_value=raw,
        ),
    ):
        provider = AkshareMarketDataProvider(symbols=["000001"])
        frame = provider.get_daily_bars(date(2024, 6, 14), date(2024, 6, 14))

    assert list(frame.columns) == [
        "trade_date",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "turnover",
    ]
    assert frame.iloc[0]["turnover"] == 10300


def test_akshare_provider_exposes_sector_snapshot_method():
    provider = AkshareMarketDataProvider(symbols=["000001"])

    frame = provider.get_sector_snapshot(date(2024, 6, 14))

    assert "sector_name" in frame.columns


def test_tushare_provider_requires_token():
    client = Mock()
    provider = TushareMarketDataProvider(token="token", client=client)

    assert provider.token == "token"
