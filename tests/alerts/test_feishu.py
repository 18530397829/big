import pytest

from trading_assistant.alerts.feishu import FeishuWebhookSender


def test_empty_webhook_url_does_not_call_httpx_post(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fake_post(*_args: object, **_kwargs: object) -> object:
        nonlocal called
        called = True
        raise AssertionError("httpx.post should not be called")

    monkeypatch.setattr("trading_assistant.alerts.feishu.httpx.post", fake_post)

    FeishuWebhookSender("").send_text("alert")

    assert called is False


def test_non_empty_webhook_posts_text_payload_and_checks_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def __init__(self) -> None:
            self.raise_for_status_called = False

        def raise_for_status(self) -> None:
            self.raise_for_status_called = True

    calls: list[dict[str, object]] = []
    response = FakeResponse()

    def fake_post(url: str, *, json: dict[str, object], timeout: int) -> FakeResponse:
        calls.append({"url": url, "json": json, "timeout": timeout})
        return response

    monkeypatch.setattr("trading_assistant.alerts.feishu.httpx.post", fake_post)

    FeishuWebhookSender("https://example.test/webhook").send_text("alert text")

    assert calls == [
        {
            "url": "https://example.test/webhook",
            "json": {"msg_type": "text", "content": {"text": "alert text"}},
            "timeout": 10,
        }
    ]
    assert response.raise_for_status_called is True
