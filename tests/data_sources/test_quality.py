import pandas as pd

from trading_assistant.data_sources.quality import validate_market_data


def test_missing_required_market_data_columns_fail_and_block_trade_plans():
    frame = pd.DataFrame(
        {
            "trade_date": ["2026-06-12"],
            "symbol": ["000001"],
        }
    )

    result = validate_market_data(frame)

    assert result.passed is False
    assert result.recommended_pool in {"blocked", "watch"}
    assert result.recommended_pool == "blocked"
    assert any("close" in error for error in result.errors)


def test_duplicate_symbol_trade_date_warns_but_remains_tradable():
    frame = pd.DataFrame(
        {
            "trade_date": ["2026-06-12", "2026-06-12"],
            "symbol": ["000001", "000001"],
            "close": [10.0, 10.1],
        }
    )

    result = validate_market_data(frame)

    assert result.passed is True
    assert result.recommended_pool == "tradable"
    assert result.errors == ()
    assert any("duplicate" in warning.lower() for warning in result.warnings)


def test_clean_market_data_passes_without_warnings_or_errors():
    frame = pd.DataFrame(
        {
            "trade_date": ["2026-06-12", "2026-06-12"],
            "symbol": ["000001", "600519"],
            "close": [10.0, 1580.0],
        }
    )

    result = validate_market_data(frame)

    assert result.passed is True
    assert result.recommended_pool == "tradable"
    assert result.warnings == ()
    assert result.errors == ()


def test_failed_quality_result_maps_candidate_to_non_tradable_pool():
    frame = pd.DataFrame(
        {
            "trade_date": ["2026-06-12"],
            "symbol": ["000001"],
        }
    )

    result = validate_market_data(frame)
    should_generate_trade_plan = result.recommended_pool == "tradable"

    assert result.passed is False
    assert should_generate_trade_plan is False
