def compute_position_pct(
    *,
    opportunity_score: float,
    plan_confidence_score: float,
    market_score: float,
    portfolio_risk_score: float,
    stop_loss_distance_pct: float,
) -> float:
    if market_score < 40 or portfolio_risk_score >= 70:
        return 0.0

    base = 0.05
    if opportunity_score >= 86 and plan_confidence_score >= 80:
        base = 0.10
    elif opportunity_score >= 76 and plan_confidence_score >= 70:
        base = 0.08

    if market_score < 60:
        base = min(base, 0.05)
    if stop_loss_distance_pct > 0.04:
        base *= 0.5

    return round(base, 4)
