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


def test_classify_stock_pool_uses_configured_turnover_threshold() -> None:
    stock = pd.Series(
        {
            "symbol": "688001",
            "name": "华兴源创",
            "board": "科创板",
            "is_st": False,
            "has_delisting_risk": False,
            "daily_turnover": 80_000_000,
            "listing_days": 300,
            "one_word_limit_up": False,
            "limit_down_days": 0,
        }
    )
    config = {
        "min_daily_turnover_cny": 50_000_000,
        "min_listing_days": 60,
        "exclude_limit_down_days": 2,
        "watch_boards": [],
    }

    classification = classify_stock_pool(stock, config=config)

    assert classification.pool_type == PoolType.TRADABLE


def test_classify_stock_pool_uses_configured_watch_boards() -> None:
    stock = pd.Series(
        {
            "symbol": "688001",
            "name": "华兴源创",
            "board": "科创板",
            "is_st": False,
            "has_delisting_risk": False,
            "daily_turnover": 120_000_000,
            "listing_days": 300,
            "one_word_limit_up": False,
            "limit_down_days": 0,
        }
    )
    config = {
        "min_daily_turnover_cny": 100_000_000,
        "min_listing_days": 60,
        "exclude_limit_down_days": 2,
        "watch_boards": ["科创板"],
    }

    classification = classify_stock_pool(stock, config=config)

    assert classification.pool_type == PoolType.WATCH


def test_classify_stock_pool_keeps_current_holdings_first() -> None:
    stock = pd.Series(
        {
            "symbol": "000001",
            "name": "平安银行",
            "board": "沪市主板",
            "is_st": True,
            "has_delisting_risk": False,
            "daily_turnover": 1,
            "listing_days": 1,
            "one_word_limit_up": True,
            "limit_down_days": 3,
        }
    )

    classification = classify_stock_pool(stock, holding_symbols={"000001"})

    assert classification.pool_type == PoolType.HOLDING
