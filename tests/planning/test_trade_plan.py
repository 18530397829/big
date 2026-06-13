from trading_assistant.domain.enums import ActionAdvice
from trading_assistant.planning.trade_plan import build_trade_plan


def test_build_trade_plan_caps_position_when_market_is_weak() -> None:
    plan = build_trade_plan(
        symbol="000001",
        name="平安银行",
        current_price=10.0,
        opportunity_score=82,
        plan_confidence_score=80,
        market_score=45,
        portfolio_risk_score=20,
        atr_pct=0.03,
        theme="银行",
    )

    assert plan.position_pct <= 0.05
    assert plan.action_advice == ActionAdvice.WATCH_FOR_TRIGGER
    assert plan.stop_loss_price < plan.entry_price_low
    assert plan.first_take_profit_price > plan.entry_price_high
