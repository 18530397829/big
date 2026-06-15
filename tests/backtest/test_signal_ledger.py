import pandas as pd

from trading_assistant.backtest.signal_ledger import SignalLedger


def test_signal_ledger_records_signal():
    ledger = SignalLedger()

    ledger.record_signal(
        trade_date="2026-06-12",
        symbol="000001",
        signal_type="candidate",
        score=82,
        action="watch_for_trigger",
    )

    rows = ledger.to_frame()
    assert len(rows) == 1
    assert rows.iloc[0]["symbol"] == "000001"


def test_signal_ledger_exports_signals_to_csv(tmp_path):
    ledger = SignalLedger()
    ledger.record_signal(
        trade_date="2026-06-12",
        symbol="000001",
        signal_type="candidate",
        score=82,
        action="watch_for_trigger",
    )
    export_path = tmp_path / "signals.csv"

    written_path = ledger.export_csv(export_path)

    exported = pd.read_csv(written_path, dtype={"symbol": str})
    assert written_path == export_path
    assert list(exported.columns) == [
        "trade_date",
        "symbol",
        "signal_type",
        "score",
        "action",
    ]
    assert exported.iloc[0].to_dict() == {
        "trade_date": "2026-06-12",
        "symbol": "000001",
        "signal_type": "candidate",
        "score": 82,
        "action": "watch_for_trigger",
    }
