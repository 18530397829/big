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
