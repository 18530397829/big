import pytest

from trading_assistant.domain.enums import ActionAdvice, RiskLevel
from trading_assistant.planning.position_sizing import compute_position_pct
from trading_assistant.planning.trade_plan import build_trade_plan


def _build_trade_plan(**overrides: object):
    params = {
        "symbol": "000001",
        "name": "Ping An Bank",
        "current_price": 10.0,
        "opportunity_score": 88,
        "plan_confidence_score": 82,
        "market_score": 80,
        "portfolio_risk_score": 20,
        "atr_pct": 0.03,
        "theme": "bank",
    }
    params.update(overrides)
    return build_trade_plan(**params)


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        (
            {
                "opportunity_score": 90,
                "plan_confidence_score": 90,
                "market_score": 39,
                "portfolio_risk_score": 20,
                "stop_loss_distance_pct": 0.02,
            },
            0.0,
        ),
        (
            {
                "opportunity_score": 90,
                "plan_confidence_score": 90,
                "market_score": 80,
                "portfolio_risk_score": 70,
                "stop_loss_distance_pct": 0.02,
            },
            0.0,
        ),
        (
            {
                "opportunity_score": 86,
                "plan_confidence_score": 80,
                "market_score": 80,
                "portfolio_risk_score": 20,
                "stop_loss_distance_pct": 0.02,
            },
            0.10,
        ),
        (
            {
                "opportunity_score": 76,
                "plan_confidence_score": 70,
                "market_score": 80,
                "portfolio_risk_score": 20,
                "stop_loss_distance_pct": 0.02,
            },
            0.08,
        ),
        (
            {
                "opportunity_score": 90,
                "plan_confidence_score": 90,
                "market_score": 59,
                "portfolio_risk_score": 20,
                "stop_loss_distance_pct": 0.02,
            },
            0.05,
        ),
        (
            {
                "opportunity_score": 76,
                "plan_confidence_score": 70,
                "market_score": 80,
                "portfolio_risk_score": 20,
                "stop_loss_distance_pct": 0.05,
            },
            0.04,
        ),
    ],
)
def test_compute_position_pct_applies_conservative_rules(
    kwargs: dict[str, float], expected: float
) -> None:
    assert compute_position_pct(**kwargs) == expected


def test_build_trade_plan_marks_high_portfolio_risk_as_high_no_action() -> None:
    plan = _build_trade_plan(portfolio_risk_score=70)

    assert plan.position_pct == 0.0
    assert plan.risk_level == RiskLevel.HIGH
    assert plan.action_advice == ActionAdvice.NO_ACTION


@pytest.mark.parametrize("current_price", [0.0, -1.0])
def test_build_trade_plan_rejects_non_positive_current_price(current_price: float) -> None:
    with pytest.raises(ValueError, match="current_price"):
        _build_trade_plan(current_price=current_price)


@pytest.mark.parametrize("atr_pct", [-0.01, 1.0])
def test_build_trade_plan_rejects_out_of_range_atr_pct(atr_pct: float) -> None:
    with pytest.raises(ValueError, match="atr_pct"):
        _build_trade_plan(atr_pct=atr_pct)


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

    assert plan.position_pct == 0.05
    assert plan.action_advice == ActionAdvice.WATCH_FOR_TRIGGER
    assert plan.stop_loss_price < plan.entry_price_low
    assert plan.first_take_profit_price > plan.entry_price_high
