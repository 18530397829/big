from trading_assistant.agents.llm_client import MockLLMClient


def test_mock_llm_client_returns_structured_json():
    client = MockLLMClient(response='{"sentiment":"positive","event_type":"news","confidence":0.8}')

    result = client.complete_json(system_prompt="system", user_prompt="user")

    assert result["sentiment"] == "positive"
    assert result["confidence"] == 0.8
