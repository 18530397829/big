import pandas as pd

from trading_assistant.backtest.engine import evaluate_forward_returns
from trading_assistant.backtest.metrics import summarize_returns


def test_forward_returns_and_summary():
    signals = pd.DataFrame(
        [
            {
                "trade_date": "2026-06-10",
                "symbol": "000001",
                "signal_type": "candidate",
                "score": 82,
                "action": "watch",
            }
        ]
    )
    prices = pd.DataFrame(
        [
            {"trade_date": "2026-06-10", "symbol": "000001", "close": 10.0},
            {"trade_date": "2026-06-11", "symbol": "000001", "close": 10.3},
            {"trade_date": "2026-06-13", "symbol": "000001", "close": 10.5},
            {"trade_date": "2026-06-15", "symbol": "000001", "close": 10.8},
        ]
    )

    evaluated = evaluate_forward_returns(signals, prices)
    summary = summarize_returns(evaluated)

    assert evaluated.iloc[0]["return_1d"] == 0.03
    assert summary["win_rate_1d"] == 1.0


def test_forward_returns_marks_unavailable_horizons_as_missing():
    signals = pd.DataFrame(
        [
            {
                "trade_date": "2026-06-10",
                "symbol": "000001",
                "signal_type": "candidate",
                "score": 82,
                "action": "watch",
            }
        ]
    )
    prices = pd.DataFrame(
        [
            {"trade_date": "2026-06-10", "symbol": "000001", "close": 10.0},
            {"trade_date": "2026-06-11", "symbol": "000001", "close": 11.0},
            {"trade_date": "2026-06-12", "symbol": "000001", "close": 12.0},
        ]
    )

    evaluated = evaluate_forward_returns(signals, prices)

    assert evaluated.iloc[0]["return_1d"] == 0.1
    assert pd.isna(evaluated.iloc[0]["return_3d"])
    assert pd.isna(evaluated.iloc[0]["return_5d"])


def test_forward_returns_tracks_max_rebound_within_five_sessions():
    signals = pd.DataFrame(
        [
            {
                "trade_date": "2026-06-10",
                "symbol": "000001",
                "signal_type": "exit",
                "score": 50,
                "action": "clear",
            }
        ]
    )
    prices = pd.DataFrame(
        [
            {"trade_date": "2026-06-10", "symbol": "000001", "close": 10.0},
            {"trade_date": "2026-06-11", "symbol": "000001", "close": 9.8},
            {"trade_date": "2026-06-12", "symbol": "000001", "close": 10.2},
            {"trade_date": "2026-06-13", "symbol": "000001", "close": 10.4},
            {"trade_date": "2026-06-14", "symbol": "000001", "close": 10.1},
            {"trade_date": "2026-06-15", "symbol": "000001", "close": 10.3},
        ]
    )

    evaluated = evaluate_forward_returns(signals, prices)

    assert evaluated.iloc[0]["max_return_5d"] == 0.04


def test_summary_ignores_missing_horizons():
    evaluated = pd.DataFrame(
        [
            {"return_1d": 0.01, "return_3d": pd.NA, "return_5d": pd.NA},
            {"return_1d": pd.NA, "return_3d": 0.05, "return_5d": pd.NA},
        ]
    )

    summary = summarize_returns(evaluated)

    assert summary["win_rate_1d"] == 1.0
    assert summary["avg_return_1d"] == 0.01
    assert summary["avg_return_3d"] == 0.05
    assert summary["avg_return_5d"] is None


def test_summary_returns_none_for_empty_samples():
    assert summarize_returns(pd.DataFrame()) == {
        "win_rate_1d": None,
        "avg_return_1d": None,
        "avg_return_3d": None,
        "avg_return_5d": None,
        "net_win_rate_1d": None,
        "net_avg_return_1d": None,
        "profit_loss_ratio_1d": None,
        "max_drawdown_1d": None,
        "false_sell_rate_5d": None,
        "missed_rebound_rate_5d": None,
        "transaction_cost_rate": 0.0,
    }


def test_summary_includes_profit_loss_ratio_and_max_drawdown():
    evaluated = pd.DataFrame(
        [
            {"trade_date": "2026-06-10", "return_1d": 0.1},
            {"trade_date": "2026-06-11", "return_1d": -0.05},
            {"trade_date": "2026-06-12", "return_1d": -0.05},
        ]
    )

    summary = summarize_returns(evaluated)

    assert summary["profit_loss_ratio_1d"] == 2.0
    assert summary["max_drawdown_1d"] == -0.0975


def test_summary_applies_transaction_cost_to_net_return_metrics():
    evaluated = pd.DataFrame(
        [
            {"return_1d": 0.01},
            {"return_1d": -0.01},
        ]
    )

    summary = summarize_returns(evaluated, transaction_cost_rate=0.002)

    assert summary["transaction_cost_rate"] == 0.002
    assert summary["net_win_rate_1d"] == 0.5
    assert summary["net_avg_return_1d"] == -0.002


def test_summary_counts_false_sells_and_missed_rebounds():
    evaluated = pd.DataFrame(
        [
            {"action": "clear", "return_5d": 0.04, "max_return_5d": 0.08},
            {"action": "reduce", "return_5d": -0.01, "max_return_5d": 0.05},
            {"action": "watch", "return_5d": 0.1, "max_return_5d": 0.1},
        ]
    )

    summary = summarize_returns(evaluated)

    assert summary["false_sell_rate_5d"] == 0.5
    assert summary["missed_rebound_rate_5d"] == 1.0
