import json
from typing import Protocol


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
