from pathlib import Path

from trading_assistant.scoring.engine import ScoreEngine
from trading_assistant.scoring.weights import load_weight_config


def test_score_engine_computes_weighted_score():
    weights = load_weight_config(Path("config/scoring.yml"))
    engine = ScoreEngine(weights["short_term_opportunity"])

    score = engine.score(
        {
            "sector_strength": 80,
            "volume_price_structure": 90,
            "technical_pattern": 70,
            "market_environment": 60,
            "event_catalyst": 50,
            "fund_behavior": 40,
            "sentiment_heat": 30,
        }
    )

    assert score.total_score == 71.0
    assert "sector_strength" in score.components
