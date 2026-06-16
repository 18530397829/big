import json

import pytest

from trading_assistant.alerts.feishu import FeishuWebhookError, FeishuWebhookSender


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

        def json(self) -> dict[str, object]:
            return {"code": 0, "msg": "success"}

    calls: list[dict[str, object]] = []
    response = FakeResponse()

    def fake_post(url: str, **kwargs: object) -> FakeResponse:
        calls.append({"url": url, **kwargs})
        return response

    monkeypatch.setattr("trading_assistant.alerts.feishu.httpx.post", fake_post)

    FeishuWebhookSender("https://example.test/webhook").send_text(
        "\u7aef\u5230\u7aef Flow text"
    )

    expected_payload = {
        "msg_type": "text",
        "content": {"text": "\u7aef\u5230\u7aef Flow text"},
        "text": "\u7aef\u5230\u7aef Flow text",
        "message": "\u7aef\u5230\u7aef Flow text",
        "content_text": "\u7aef\u5230\u7aef Flow text",
        "title": "A-share trading assistant acceptance",
        "source": "trading-assistant-acceptance",
    }

    assert len(calls) == 1
    call = calls[0]
    assert call["url"] == "https://example.test/webhook"
    assert call["headers"] == {"Content-Type": "application/json; charset=utf-8"}
    assert call["timeout"] == 10
    body = call["content"]
    assert isinstance(body, bytes)
    assert json.loads(body.decode("utf-8")) == expected_payload
    assert "\u7aef\u5230\u7aef".encode("utf-8") in body
    assert b"\\u7aef" not in body
    assert response.raise_for_status_called is True


def test_webhook_sender_rejects_feishu_error_response_without_leaking_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return

        def json(self) -> dict[str, object]:
            return {"code": 19021, "msg": "invalid webhook token"}

    def fake_post(
        url: str,
        *,
        content: bytes,
        headers: dict[str, str],
        timeout: int,
    ) -> FakeResponse:
        assert url == "https://example.test/secret-webhook"
        assert json.loads(content.decode("utf-8"))["msg_type"] == "text"
        assert headers == {"Content-Type": "application/json; charset=utf-8"}
        assert timeout == 10
        return FakeResponse()

    monkeypatch.setattr("trading_assistant.alerts.feishu.httpx.post", fake_post)

    with pytest.raises(FeishuWebhookError) as exc_info:
        FeishuWebhookSender("https://example.test/secret-webhook").send_text("alert text")

    message = str(exc_info.value)
    assert "code=19021" in message
    assert "invalid webhook token" in message
    assert "secret-webhook" not in message
