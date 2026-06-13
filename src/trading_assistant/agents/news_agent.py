from trading_assistant.agents.llm_client import LLMClient


NEWS_THEME_SYSTEM_PROMPT = """
你是 A 股题材新闻结构化助手。你只输出 JSON 对象。
字段必须包含 theme、sentiment、confidence、summary、related_symbols。
sentiment 只能是 positive、negative、neutral、uncertain。
"""


class NewsAgent:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def extract_theme(self, *, text: str, source: str) -> dict[str, object]:
        result = self.client.complete_json(
            system_prompt=NEWS_THEME_SYSTEM_PROMPT,
            user_prompt=f"source={source}\ntext={text}",
        )
        result["source"] = source
        return result
