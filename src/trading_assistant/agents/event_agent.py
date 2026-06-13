from trading_assistant.agents.llm_client import LLMClient
from trading_assistant.agents.prompts import EVENT_EXTRACTION_SYSTEM_PROMPT


class EventAgent:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def extract(self, *, symbol: str, text: str, source: str) -> dict[str, object]:
        user_prompt = f"symbol={symbol}\nsource={source}\ntext={text}"
        result = self.client.complete_json(
            system_prompt=EVENT_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        result["symbol"] = symbol
        result["source"] = source
        return result
