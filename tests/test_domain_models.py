from datetime import date

import pytest

from trading_assistant.domain.enums import ActionAdvice, PoolType, RiskLevel
from trading_assistant.domain.models import Holding, TradePlan


def test_holding_unrealized_return_pct():
    holding = Holding(
        symbol="000001",
        name="平安银行",
        quantity=1000,
        cost_price=10.0,
        current_price=10.5,
        buy_date=date(2026, 6, 10),
        theme="银行",
        buy_reason="放量突破平台",
    )

    assert holding.market_value == 10500.0
    assert holding.unrealized_return_pct == 0.05


def test_trade_plan_requires_risk_controls():
    plan = TradePlan(
        symbol="000001",
        name="平安银行",
        pool_type=PoolType.TRADABLE,
        opportunity_score=78,
        plan_confidence_score=82,
        entry_trigger="放量突破 10.60",
        entry_price_low=10.50,
        entry_price_high=10.65,
        stop_loss_price=10.20,
        first_take_profit_price=11.10,
        second_take_profit_price=11.50,
        position_pct=0.08,
        invalidation_condition="跌破 10.20 或板块退潮",
        risk_level=RiskLevel.MEDIUM,
        action_advice=ActionAdvice.WATCH_FOR_TRIGGER,
    )

    assert plan.reward_risk_ratio > 1.5


def _trade_plan_params(**overrides: object) -> dict[str, object]:
    params: dict[str, object] = {
        "symbol": "000001",
        "name": "平安银行",
        "pool_type": PoolType.TRADABLE,
        "opportunity_score": 78,
        "plan_confidence_score": 82,
        "entry_trigger": "放量突破 10.60",
        "entry_price_low": 10.50,
        "entry_price_high": 10.65,
        "stop_loss_price": 10.20,
        "first_take_profit_price": 11.10,
        "second_take_profit_price": 11.50,
        "position_pct": 0.08,
        "invalidation_condition": "跌破 10.20 或板块退潮",
        "risk_level": RiskLevel.MEDIUM,
        "action_advice": ActionAdvice.WATCH_FOR_TRIGGER,
    }
    params.update(overrides)
    return params


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"entry_price_high": 10.40}, "entry_price_high"),
        ({"stop_loss_price": 10.50}, "stop_loss_price"),
        ({"first_take_profit_price": 10.60}, "first_take_profit_price"),
        ({"second_take_profit_price": 11.00}, "second_take_profit_price"),
    ],
)
def test_trade_plan_rejects_invalid_price_relationships(
    overrides: dict[str, float], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        TradePlan(**_trade_plan_params(**overrides))
