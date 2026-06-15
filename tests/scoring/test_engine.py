from pathlib import Path

import pytest

from trading_assistant.scoring.engine import ScoreEngine
from trading_assistant.scoring.weights import load_weight_config

ROOT = Path(__file__).resolve().parents[2]


def test_score_engine_computes_weighted_score():
    weights = load_weight_config(ROOT / "config/scoring.yml")
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
    assert score.components == {
        "sector_strength": 20.0,
        "volume_price_structure": 22.5,
        "technical_pattern": 14.0,
        "market_environment": 6.0,
        "event_catalyst": 5.0,
        "fund_behavior": 2.0,
        "sentiment_heat": 1.5,
    }


def test_score_engine_clamps_values_and_defaults_missing_factors_to_zero():
    engine = ScoreEngine({"over": 0.5, "under": 0.25, "missing": 0.25})

    score = engine.score({"over": 120, "under": -20})

    assert score.total_score == 50.0
    assert score.components == {
        "over": 50.0,
        "under": 0.0,
        "missing": 0.0,
    }


def test_load_weight_config_rejects_weights_that_do_not_sum_to_one(tmp_path: Path):
    config = tmp_path / "bad.yml"
    config.write_text("bad_score:\n  one: 0.4\n  two: 0.4\n", encoding="utf-8")

    with pytest.raises(ValueError, match="weights sum"):
        load_weight_config(config)


@pytest.mark.parametrize("content", ["", "- item\n"])
def test_load_weight_config_rejects_non_mapping_config(tmp_path: Path, content: str):
    config = tmp_path / "bad.yml"
    config.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="Weight config must be a mapping"):
        load_weight_config(config)


def test_load_weight_config_rejects_non_mapping_weights(tmp_path: Path):
    config = tmp_path / "bad.yml"
    config.write_text("bad_score: []\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Weights for bad_score must be a mapping"):
        load_weight_config(config)
