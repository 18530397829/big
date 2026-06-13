import pandas as pd

from trading_assistant.factors.market import compute_market_environment_factors
from trading_assistant.factors.technical import compute_technical_factors
from trading_assistant.factors.volume_price import compute_volume_price_factors


def test_compute_technical_and_volume_factors():
    bars = pd.DataFrame(
        {
            "symbol": ["000001"] * 5,
            "close": [10.0, 10.2, 10.3, 10.5, 10.8],
            "high": [10.1, 10.3, 10.4, 10.6, 10.9],
            "low": [9.9, 10.0, 10.1, 10.2, 10.5],
            "turnover": [100, 120, 130, 180, 220],
        }
    )

    technical = compute_technical_factors(bars)
    volume_price = compute_volume_price_factors(bars)

    assert technical["momentum_5d"] == 0.08
    assert technical["above_ma5"] is True
    assert volume_price["turnover_expansion"] > 1.5


def test_compute_market_environment_factors():
    market = pd.DataFrame(
        {
            "symbol": ["000001", "600519", "300001"],
            "pct_chg": [2.0, -1.0, 3.0],
            "turnover": [100, 200, 300],
            "is_limit_up": [True, False, False],
            "is_limit_down": [False, False, False],
        }
    )

    factors = compute_market_environment_factors(market)

    assert factors["advance_ratio"] == 0.67
    assert factors["limit_up_count"] == 1
