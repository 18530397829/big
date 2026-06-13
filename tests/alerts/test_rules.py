from trading_assistant.alerts.models import AlertLevel
from trading_assistant.alerts.rules import evaluate_price_alerts


def test_evaluate_price_alerts_emits_p0_when_stop_loss_breaks():
    alerts = evaluate_price_alerts(
        symbol="000001",
        current_price=9.8,
        stop_loss_price=10.0,
        take_profit_price=11.0,
        entry_trigger_price=10.6,
    )

    assert alerts[0].level == AlertLevel.P0
    assert alerts[0].symbol == "000001"
    assert "跌破硬止损位" in alerts[0].message
