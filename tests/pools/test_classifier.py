import pandas as pd

from trading_assistant.domain.enums import PoolType
from trading_assistant.pools.classifier import classify_stock_pool


def test_classify_blocks_st_and_low_turnover():
    stock = pd.Series(
        {
            "symbol": "000001",
            "name": "平安银行",
            "board": "沪市主板",
            "is_st": False,
            "has_delisting_risk": False,
            "daily_turnover": 120_000_000,
            "listing_days": 300,
            "one_word_limit_up": False,
            "limit_down_days": 0,
        }
    )

    assert classify_stock_pool(stock).pool_type == PoolType.TRADABLE

    stock["is_st"] = True
    blocked = classify_stock_pool(stock)
    assert blocked.pool_type == PoolType.BLOCKED
    assert "ST" in blocked.reason
