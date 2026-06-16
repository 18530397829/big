import json

import httpx


class FeishuWebhookError(RuntimeError):
    pass


class FeishuWebhookSender:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def send_text(self, text: str) -> None:
        if not self.webhook_url:
            return

        payload = {
            "msg_type": "text",
            "content": {"text": text},
            "text": text,
            "message": text,
            "content_text": text,
            "title": "A-share trading assistant acceptance",
            "source": "trading-assistant-acceptance",
        }
        response = httpx.post(
            self.webhook_url,
            content=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=10,
        )
        response.raise_for_status()
        _raise_for_feishu_error(response.json())


def _raise_for_feishu_error(payload: object) -> None:
    if not isinstance(payload, dict):
        raise FeishuWebhookError("Feishu webhook response must be a JSON object")

    code = payload.get("code", payload.get("StatusCode", 0))
    if code == 0:
        return

    msg = payload.get("msg", payload.get("StatusMessage", "unknown error"))
    raise FeishuWebhookError(f"Feishu webhook rejected message: code={code} msg={msg}")
