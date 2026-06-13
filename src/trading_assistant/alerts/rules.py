from trading_assistant.alerts.models import Alert, AlertLevel


def evaluate_price_alerts(
    *,
    symbol: str,
    current_price: float,
    stop_loss_price: float,
    take_profit_price: float,
    entry_trigger_price: float,
) -> list[Alert]:
    alerts: list[Alert] = []
    if current_price <= stop_loss_price:
        alerts.append(Alert(AlertLevel.P0, symbol, f"{symbol} 跌破硬止损位 {stop_loss_price:.2f}"))
    elif current_price <= stop_loss_price * 1.01:
        alerts.append(Alert(AlertLevel.P1, symbol, f"{symbol} 接近止损位 {stop_loss_price:.2f}"))
    if current_price >= take_profit_price:
        alerts.append(Alert(AlertLevel.P1, symbol, f"{symbol} 到达第一止盈位 {take_profit_price:.2f}"))
    elif current_price >= entry_trigger_price:
        alerts.append(Alert(AlertLevel.P2, symbol, f"{symbol} 触发买入观察价 {entry_trigger_price:.2f}"))
    return alerts
