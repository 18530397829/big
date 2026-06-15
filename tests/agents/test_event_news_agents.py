from trading_assistant.agents.event_agent import EventAgent
from trading_assistant.agents.llm_client import MockLLMClient
from trading_assistant.agents.news_agent import NewsAgent


def test_event_agent_extracts_negative_event():
    client = MockLLMClient(
        response='{"event_type":"reduction","sentiment":"negative","confidence":0.9,"summary":"股东拟减持","risk_flags":["减持"],"source_required":true}'
    )
    agent = EventAgent(client)

    event = agent.extract(symbol="000001", text="股东计划减持不超过 2% 股份", source="sample")

    assert event["sentiment"] == "negative"
    assert "减持" in event["risk_flags"]


def test_news_agent_extracts_theme():
    client = MockLLMClient(
        response='{"theme":"银行","sentiment":"positive","confidence":0.8,"summary":"银行板块成交额放大","related_symbols":["000001"]}'
    )
    agent = NewsAgent(client)

    result = agent.extract_theme(text="银行板块成交额明显放大", source="sample")

    assert result["theme"] == "银行"
