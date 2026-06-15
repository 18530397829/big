import httpx


class FeishuWebhookSender:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def send_text(self, text: str) -> None:
        if not self.webhook_url:
            return

        response = httpx.post(
            self.webhook_url,
            json={"msg_type": "text", "content": {"text": text}},
            timeout=10,
        )
        response.raise_for_status()
