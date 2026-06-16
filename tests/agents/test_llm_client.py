import pytest
import httpx

from trading_assistant.agents.llm_client import MockLLMClient, OpenAICompatibleLLMClient


def test_mock_llm_client_returns_structured_json():
    client = MockLLMClient(response='{"sentiment":"positive","event_type":"news","confidence":0.8}')

    result = client.complete_json(system_prompt="system", user_prompt="user")

    assert result["sentiment"] == "positive"
    assert result["confidence"] == 0.8


def test_openai_compatible_llm_client_posts_chat_completion_and_parses_json(monkeypatch):
    class FakeResponse:
        def __init__(self) -> None:
            self.raise_for_status_called = False

        def raise_for_status(self) -> None:
            self.raise_for_status_called = True

        def json(self) -> dict[str, object]:
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"event_type":"announcement","sentiment":"positive",'
                                '"confidence":0.82,"summary":"订单增长","risk_flags":[],'
                                '"source_required":true}'
                            )
                        }
                    }
                ]
            }

    calls: list[dict[str, object]] = []
    response = FakeResponse()

    def fake_post(
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, object],
        timeout: float,
    ) -> FakeResponse:
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return response

    monkeypatch.setattr("trading_assistant.agents.llm_client.httpx.post", fake_post)

    client = OpenAICompatibleLLMClient(
        base_url="http://127.0.0.1:8317/v1",
        api_key="test-key",
        model="gpt-5.4-mini",
        timeout=3.5,
    )
    result = client.complete_json(system_prompt="system prompt", user_prompt="user prompt")

    assert result["event_type"] == "announcement"
    assert result["confidence"] == 0.82
    assert response.raise_for_status_called is True
    assert calls == [
        {
            "url": "http://127.0.0.1:8317/v1/chat/completions",
            "headers": {"Authorization": "Bearer test-key", "Content-Type": "application/json"},
            "json": {
                "model": "gpt-5.4-mini",
                "messages": [
                    {"role": "system", "content": "system prompt"},
                    {"role": "user", "content": "user prompt"},
                ],
                "temperature": 0,
            },
            "timeout": 3.5,
        }
    ]


def test_openai_compatible_llm_client_requires_json_object(monkeypatch):
    class FakeResponse:
        def raise_for_status(self) -> None:
            return

        def json(self) -> dict[str, object]:
            return {"choices": [{"message": {"content": '["not", "an", "object"]'}}]}

    monkeypatch.setattr(
        "trading_assistant.agents.llm_client.httpx.post",
        lambda *_args, **_kwargs: FakeResponse(),
    )

    client = OpenAICompatibleLLMClient(
        base_url="http://127.0.0.1:8317/v1",
        api_key="test-key",
        model="gpt-5.4-mini",
    )

    with pytest.raises(ValueError, match="LLM response must be a JSON object"):
        client.complete_json(system_prompt="system", user_prompt="user")


def test_openai_compatible_llm_client_retries_transient_http_errors(monkeypatch):
    class FakeResponse:
        def __init__(self, *, fail: bool) -> None:
            self.fail = fail
            self.request = httpx.Request("POST", "http://127.0.0.1:8317/v1/chat/completions")

        def raise_for_status(self) -> None:
            if self.fail:
                raise httpx.HTTPStatusError(
                    "server error",
                    request=self.request,
                    response=httpx.Response(500, request=self.request),
                )

        def json(self) -> dict[str, object]:
            return {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"event_type":"announcement","sentiment":"positive",'
                                '"confidence":0.82,"summary":"订单增长","risk_flags":[],'
                                '"source_required":true}'
                            )
                        }
                    }
                ]
            }

    responses = [FakeResponse(fail=True), FakeResponse(fail=True), FakeResponse(fail=False)]
    calls = 0

    def fake_post(*_args: object, **_kwargs: object) -> FakeResponse:
        nonlocal calls
        response = responses[calls]
        calls += 1
        return response

    monkeypatch.setattr("trading_assistant.agents.llm_client.httpx.post", fake_post)

    client = OpenAICompatibleLLMClient(
        base_url="http://127.0.0.1:8317/v1",
        api_key="test-key",
        model="gpt-5.4-mini",
        max_retries=2,
    )

    result = client.complete_json(system_prompt="system", user_prompt="user")

    assert result["event_type"] == "announcement"
    assert calls == 3
