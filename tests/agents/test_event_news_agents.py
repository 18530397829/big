import json

import pytest
from pydantic import ValidationError

from trading_assistant.agents.event_agent import EventAgent
from trading_assistant.agents.llm_client import MockLLMClient
from trading_assistant.agents.news_agent import NewsAgent
from trading_assistant.agents.prompts import EVENT_EXTRACTION_SYSTEM_PROMPT


def _json_response(payload: dict[str, object]) -> str:
    return json.dumps(payload)


def test_event_prompt_requires_source_required_boolean():
    assert "source_required must be a JSON boolean true or false" in EVENT_EXTRACTION_SYSTEM_PROMPT


def test_event_agent_extracts_negative_event():
    client = MockLLMClient(
        response=_json_response(
            {
                "event_type": "reduction",
                "sentiment": "negative",
                "confidence": 0.9,
                "summary": "major holder reduction",
                "risk_flags": ["reduction"],
                "source_required": True,
            }
        )
    )
    agent = EventAgent(client)

    event = agent.extract(
        symbol="000001",
        text="holder plans to reduce no more than 2%",
        source="sample",
    )

    assert event["sentiment"] == "negative"
    assert "reduction" in event["risk_flags"]
    assert event["symbol"] == "000001"
    assert event["source"] == "sample"


def test_news_agent_extracts_theme():
    client = MockLLMClient(
        response=_json_response(
            {
                "theme": "bank",
                "sentiment": "positive",
                "confidence": 0.8,
                "summary": "bank turnover expanded",
                "related_symbols": ["000001"],
            }
        )
    )
    agent = NewsAgent(client)

    result = agent.extract_theme(text="bank turnover expanded", source="sample")

    assert result["theme"] == "bank"
    assert result["source"] == "sample"


@pytest.mark.parametrize(
    "response",
    [
        _json_response(
            {
                "event_type": "reduction",
                "sentiment": "bad",
                "confidence": 0.9,
                "summary": "x",
                "risk_flags": ["x"],
                "source_required": True,
            }
        ),
        _json_response(
            {
                "event_type": "reduction",
                "sentiment": "negative",
                "confidence": 1.2,
                "summary": "x",
                "risk_flags": ["x"],
                "source_required": True,
            }
        ),
        _json_response(
            {
                "event_type": "reduction",
                "sentiment": "negative",
                "confidence": 0.9,
                "risk_flags": ["x"],
                "source_required": True,
            }
        ),
        _json_response(
            {
                "event_type": "reduction",
                "sentiment": "negative",
                "confidence": 0.9,
                "summary": "x",
                "risk_flags": "x",
                "source_required": True,
            }
        ),
        _json_response(
            {
                "event_type": "reduction",
                "sentiment": "negative",
                "confidence": 0.9,
                "summary": "x",
                "risk_flags": ["x"],
                "source_required": "yes",
            }
        ),
    ],
)
def test_event_agent_rejects_invalid_llm_schema(response: str):
    agent = EventAgent(MockLLMClient(response=response))

    with pytest.raises(ValidationError):
        agent.extract(symbol="000001", text="sample", source="sample")


@pytest.mark.parametrize(
    "response",
    [
        _json_response(
            {
                "theme": "bank",
                "sentiment": "bad",
                "confidence": 0.8,
                "summary": "x",
                "related_symbols": ["000001"],
            }
        ),
        _json_response(
            {
                "theme": "bank",
                "sentiment": "positive",
                "confidence": -0.1,
                "summary": "x",
                "related_symbols": ["000001"],
            }
        ),
        _json_response(
            {
                "theme": "bank",
                "sentiment": "positive",
                "confidence": 0.8,
                "related_symbols": ["000001"],
            }
        ),
        _json_response(
            {
                "theme": "bank",
                "sentiment": "positive",
                "confidence": 0.8,
                "summary": "x",
                "related_symbols": "000001",
            }
        ),
        _json_response(
            {
                "theme": "bank",
                "sentiment": "positive",
                "confidence": "0.8",
                "summary": "x",
                "related_symbols": ["000001"],
            }
        ),
    ],
)
def test_news_agent_rejects_invalid_llm_schema(response: str):
    agent = NewsAgent(MockLLMClient(response=response))

    with pytest.raises(ValidationError):
        agent.extract_theme(text="sample", source="sample")
