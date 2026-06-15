from pathlib import Path

import yaml


def test_config_files_exist_and_have_required_sections():
    root = Path(__file__).resolve().parents[1]

    scoring = yaml.safe_load((root / "config/scoring.yml").read_text(encoding="utf-8"))
    risk = yaml.safe_load((root / "config/risk.yml").read_text(encoding="utf-8"))
    pools = yaml.safe_load((root / "config/pools.yml").read_text(encoding="utf-8"))

    assert set(scoring) == {
        "portfolio_risk",
        "market_environment",
        "short_term_opportunity",
        "plan_confidence",
    }
    assert risk["max_single_position_pct"] == 0.10
    assert pools["exclude_st"] is True
