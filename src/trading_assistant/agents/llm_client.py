import json
from typing import Protocol, cast

import httpx


class LLMClient(Protocol):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        raise NotImplementedError


class MockLLMClient:
    def __init__(self, response: str) -> None:
        self.response = response

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        parsed = json.loads(self.response)
        if not isinstance(parsed, dict):
            raise ValueError("LLM response must be a JSON object")
        return parsed


class OpenAICompatibleLLMClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 30.0,
        temperature: float = 0,
        max_retries: int = 2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.max_retries = max_retries

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        for attempt in range(self.max_retries + 1):
            try:
                return self._complete_json_once(system_prompt=system_prompt, user_prompt=user_prompt)
            except httpx.HTTPError:
                if attempt >= self.max_retries:
                    raise
        raise RuntimeError("unreachable LLM retry state")

    def _complete_json_once(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": self.temperature,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        parsed = json.loads(_strip_json_fence(_extract_chat_content(response.json())))
        if not isinstance(parsed, dict):
            raise ValueError("LLM response must be a JSON object")
        return cast(dict[str, object], parsed)


def _extract_chat_content(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ValueError("LLM response body must be a JSON object")
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("LLM response must include at least one choice")
    choice = choices[0]
    if not isinstance(choice, dict):
        raise ValueError("LLM response choice must be an object")
    message = choice.get("message")
    if not isinstance(message, dict):
        raise ValueError("LLM response choice must include a message object")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("LLM response message content must be non-empty text")
    return content


def _strip_json_fence(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if len(lines) >= 3 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped
