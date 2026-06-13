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
