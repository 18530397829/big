from typing import Protocol

from trading_assistant.alerts.models import Alert, AlertLevel


class TextSender(Protocol):
    def send_text(self, text: str) -> None:
        raise NotImplementedError


class AlertDispatcher:
    def __init__(self, sender: TextSender) -> None:
        self.sender = sender

    def dispatch(self, alerts: list[Alert]) -> None:
        for alert in alerts:
            if alert.level in {AlertLevel.P0, AlertLevel.P1}:
                self.sender.send_text(f"[{alert.level}] {alert.symbol} {alert.message}")
