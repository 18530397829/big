from datetime import date
from pathlib import Path

from trading_assistant.data_sources.fake_provider import FakeMarketDataProvider


def test_fake_provider_loads_daily_bars_and_sectors():
    provider = FakeMarketDataProvider(Path("data/samples"))

    daily = provider.get_daily_bars(date(2026, 6, 10), date(2026, 6, 11))
    sectors = provider.get_sector_snapshot(date(2026, 6, 12))

    assert set(daily["symbol"]) == {"000001", "600519"}
    assert sectors.iloc[0]["sector_name"] == "银行"
