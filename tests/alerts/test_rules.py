import pytest

from trading_assistant.alerts.models import AlertLevel
from trading_assistant.alerts.rules import evaluate_price_alerts


def test_evaluate_price_alerts_emits_p0_when_stop_loss_breaks() -> None:
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


def test_evaluate_price_alerts_emits_p0_at_stop_loss() -> None:
    alerts = evaluate_price_alerts(
        symbol="000001",
        current_price=10.0,
        stop_loss_price=10.0,
        take_profit_price=11.0,
        entry_trigger_price=10.6,
    )

    assert [alert.level for alert in alerts] == [AlertLevel.P0]
    assert "跌破硬止损位" in alerts[0].message


def test_evaluate_price_alerts_emits_p1_near_stop_within_one_percent() -> None:
    alerts = evaluate_price_alerts(
        symbol="000001",
        current_price=10.05,
        stop_loss_price=10.0,
        take_profit_price=11.0,
        entry_trigger_price=10.6,
    )

    assert [alert.level for alert in alerts] == [AlertLevel.P1]
    assert "接近止损位" in alerts[0].message


@pytest.mark.parametrize("current_price", [11.0, 11.2])
def test_evaluate_price_alerts_emits_p1_at_or_above_take_profit(
    current_price: float,
) -> None:
    alerts = evaluate_price_alerts(
        symbol="000001",
        current_price=current_price,
        stop_loss_price=10.0,
        take_profit_price=11.0,
        entry_trigger_price=10.6,
    )

    assert [alert.level for alert in alerts] == [AlertLevel.P1]
    assert "到达第一止盈位" in alerts[0].message


@pytest.mark.parametrize("current_price", [10.6, 10.8])
def test_evaluate_price_alerts_emits_p2_at_or_above_entry_trigger(
    current_price: float,
) -> None:
    alerts = evaluate_price_alerts(
        symbol="000001",
        current_price=current_price,
        stop_loss_price=10.0,
        take_profit_price=11.0,
        entry_trigger_price=10.6,
    )

    assert [alert.level for alert in alerts] == [AlertLevel.P2]
    assert "触发买入观察价" in alerts[0].message


def test_evaluate_price_alerts_emits_no_alerts_below_active_thresholds() -> None:
    alerts = evaluate_price_alerts(
        symbol="000001",
        current_price=10.2,
        stop_loss_price=10.0,
        take_profit_price=11.0,
        entry_trigger_price=10.6,
    )

    assert alerts == []


def test_evaluate_price_alerts_orders_stop_loss_before_take_profit_when_both_trigger() -> None:
    alerts = evaluate_price_alerts(
        symbol="000001",
        current_price=9.8,
        stop_loss_price=10.0,
        take_profit_price=9.5,
        entry_trigger_price=9.0,
    )

    assert [alert.level for alert in alerts] == [AlertLevel.P0, AlertLevel.P1]
    assert "跌破硬止损位" in alerts[0].message
    assert "到达第一止盈位" in alerts[1].message
