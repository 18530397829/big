import pandas as pd
import pytest

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


def test_compute_technical_factors_uses_latest_five_rows_for_momentum():
    bars = pd.DataFrame(
        {
            "close": [1.0, 10.0, 11.0, 12.0, 13.0, 15.0],
            "high": [1.1, 10.5, 11.5, 12.5, 13.5, 15.5],
            "low": [0.9, 9.5, 10.5, 11.5, 12.5, 14.5],
        }
    )

    technical = compute_technical_factors(bars)

    assert technical["momentum_5d"] == 0.5


def test_factor_inputs_sort_by_trade_date_when_available():
    bars = pd.DataFrame(
        {
            "trade_date": [
                "2024-01-05",
                "2024-01-01",
                "2024-01-04",
                "2024-01-03",
                "2024-01-02",
            ],
            "close": [16.0, 10.0, 13.0, 12.0, 11.0],
            "high": [16.5, 10.5, 13.5, 12.5, 11.5],
            "low": [15.5, 9.5, 12.5, 11.5, 10.5],
            "turnover": [200.0, 100.0, 100.0, 100.0, 100.0],
        }
    )

    technical = compute_technical_factors(bars)
    volume_price = compute_volume_price_factors(bars)

    assert technical["momentum_5d"] == 0.6
    assert volume_price["turnover_expansion"] == 2.0
    assert volume_price["price_up_with_volume"] is True


def test_compute_volume_price_factors_supports_single_row():
    bars = pd.DataFrame({"close": [10.0], "turnover": [120.0]})

    volume_price = compute_volume_price_factors(bars)

    assert volume_price["turnover_expansion"] == 1.0
    assert volume_price["price_up_with_volume"] is False


@pytest.mark.parametrize(
    "factor_func,bars",
    [
        (compute_technical_factors, pd.DataFrame(columns=["close", "high", "low"])),
        (compute_volume_price_factors, pd.DataFrame(columns=["close", "turnover"])),
    ],
)
def test_factor_inputs_reject_empty_data(factor_func, bars):
    with pytest.raises(ValueError, match="empty"):
        factor_func(bars)


@pytest.mark.parametrize(
    "factor_func,bars",
    [
        (compute_technical_factors, pd.DataFrame({"close": [10.0], "high": [10.5]})),
        (compute_volume_price_factors, pd.DataFrame({"close": [10.0]})),
    ],
)
def test_factor_inputs_reject_missing_required_columns(factor_func, bars):
    with pytest.raises(ValueError, match="missing required columns"):
        factor_func(bars)


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
