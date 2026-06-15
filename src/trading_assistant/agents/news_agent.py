from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

from trading_assistant.agents.llm_client import LLMClient


NEWS_THEME_SYSTEM_PROMPT = """
你是 A 股题材新闻结构化助手。你只输出 JSON 对象。
字段必须包含 theme、sentiment、confidence、summary、related_symbols。
sentiment 只能是 positive、negative、neutral、uncertain。
"""


class _NewsThemeExtraction(BaseModel):
    model_config = ConfigDict(extra="allow")

    theme: StrictStr
    sentiment: Literal["positive", "negative", "neutral", "uncertain"]
    confidence: float = Field(ge=0, le=1)
    summary: StrictStr
    related_symbols: list[StrictStr]

    @field_validator("confidence", mode="before")
    @classmethod
    def _confidence_must_be_number(cls, value: object) -> object:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("confidence must be a number")
        return value

    @field_validator("related_symbols", mode="before")
    @classmethod
    def _related_symbols_must_be_list(cls, value: object) -> object:
        if not isinstance(value, list):
            raise ValueError("related_symbols must be a list")
        return value


class NewsAgent:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def extract_theme(self, *, text: str, source: str) -> dict[str, object]:
        result = self.client.complete_json(
            system_prompt=NEWS_THEME_SYSTEM_PROMPT,
            user_prompt=f"source={source}\ntext={text}",
        )
        result = _NewsThemeExtraction.model_validate(result).model_dump()
        result["source"] = source
        return result
