from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, field_validator

from trading_assistant.agents.llm_client import LLMClient
from trading_assistant.agents.prompts import EVENT_EXTRACTION_SYSTEM_PROMPT


class _EventExtraction(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_type: StrictStr
    sentiment: Literal["positive", "negative", "neutral", "uncertain"]
    confidence: float = Field(ge=0, le=1)
    summary: StrictStr
    risk_flags: list[StrictStr]
    source_required: StrictBool

    @field_validator("confidence", mode="before")
    @classmethod
    def _confidence_must_be_number(cls, value: object) -> object:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("confidence must be a number")
        return value

    @field_validator("risk_flags", mode="before")
    @classmethod
    def _risk_flags_must_be_list(cls, value: object) -> object:
        if not isinstance(value, list):
            raise ValueError("risk_flags must be a list")
        return value


class EventAgent:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def extract(self, *, symbol: str, text: str, source: str) -> dict[str, object]:
        user_prompt = f"symbol={symbol}\nsource={source}\ntext={text}"
        result = self.client.complete_json(
            system_prompt=EVENT_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        result = _EventExtraction.model_validate(result).model_dump()
        result["symbol"] = symbol
        result["source"] = source
        return result
