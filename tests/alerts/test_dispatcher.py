from trading_assistant.alerts.dispatcher import AlertDispatcher
from trading_assistant.alerts.models import Alert, AlertLevel


class FakeSender:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send_text(self, text: str) -> None:
        self.messages.append(text)


def test_dispatcher_sends_only_p0_p1_by_default() -> None:
    sender = FakeSender()
    dispatcher = AlertDispatcher(sender)
    alerts = [
        Alert(AlertLevel.P0, "000001", "跌破硬止损位"),
        Alert(AlertLevel.P1, "000002", "触发减仓提醒"),
        Alert(AlertLevel.P2, "000003", "接近触发价"),
        Alert(AlertLevel.P3, "000004", "观察中"),
    ]

    dispatcher.dispatch(alerts)

    assert sender.messages == [
        "[P0] 000001 跌破硬止损位",
        "[P1] 000002 触发减仓提醒",
    ]
