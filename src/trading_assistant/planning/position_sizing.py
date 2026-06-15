from collections.abc import Mapping


DEFAULT_RISK_CONFIG: dict[str, float] = {
    "max_single_position_pct": 0.10,
    "default_stop_loss_pct": 0.04,
    "hard_stop_loss_pct": 0.05,
    "first_take_profit_pct": 0.06,
    "second_take_profit_pct": 0.10,
    "max_gap_up_for_entry_pct": 0.03,
    "min_reward_risk_ratio": 1.5,
    "market_score_no_new_position": 40,
    "market_score_light_position": 60,
    "high_portfolio_risk_no_new_position": 70,
}


def _float_config_value(value: object) -> float:
    if isinstance(value, str | int | float):
        return float(value)
    msg = f"risk config value must be numeric, got {type(value).__name__}"
    raise TypeError(msg)


def resolve_risk_config(risk_config: Mapping[str, object] | None = None) -> dict[str, float]:
    resolved = DEFAULT_RISK_CONFIG.copy()
    if risk_config is None:
        return resolved
    for key, value in risk_config.items():
        if key in resolved:
            resolved[key] = _float_config_value(value)
    return resolved


def compute_position_pct(
    *,
    opportunity_score: float,
    plan_confidence_score: float,
    market_score: float,
    portfolio_risk_score: float,
    stop_loss_distance_pct: float,
    risk_config: Mapping[str, object] | None = None,
) -> float:
    rules = resolve_risk_config(risk_config)
    no_new_market_score = rules["market_score_no_new_position"]
    high_portfolio_risk = rules["high_portfolio_risk_no_new_position"]
    max_single_position_pct = rules["max_single_position_pct"]

    if market_score < no_new_market_score or portfolio_risk_score >= high_portfolio_risk:
        return 0.0

    base = max_single_position_pct * 0.5
    if opportunity_score >= 86 and plan_confidence_score >= 80:
        base = max_single_position_pct
    elif opportunity_score >= 76 and plan_confidence_score >= 70:
        base = max_single_position_pct * 0.8

    if market_score < rules["market_score_light_position"]:
        base = min(base, max_single_position_pct * 0.5)
    if stop_loss_distance_pct > rules["default_stop_loss_pct"]:
        base *= 0.5

    return round(base, 4)
