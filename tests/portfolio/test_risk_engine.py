from datetime import date

import pytest

from trading_assistant.domain.enums import ActionAdvice, RiskLevel
from trading_assistant.domain.models import Holding
from trading_assistant.factors import compute_holding_drawdown_factor
from trading_assistant.portfolio import PortfolioRiskDecision, PortfolioRiskEngine


def make_holding(*, current_price: float = 10.0) -> Holding:
    return Holding(
        symbol="000001",
        name="平安银行",
        quantity=1000,
        cost_price=10.0,
        current_price=current_price,
        buy_date=date(2026, 6, 10),
        theme="银行",
        buy_reason="放量突破平台",
    )


def test_package_barrels_export_portfolio_risk_public_api():
    assert compute_holding_drawdown_factor is not None
    assert PortfolioRiskDecision is not None
    assert PortfolioRiskEngine is not None


def test_portfolio_risk_engine_flags_hard_stop():
    holding = make_holding(current_price=9.45)
    engine = PortfolioRiskEngine(default_stop_loss_pct=0.04, hard_stop_loss_pct=0.05)

    decision = engine.evaluate(
        holding=holding,
        technical_broken=True,
        sector_cooling=False,
        negative_event=False,
        fund_outflow=True,
        market_score=55,
    )

    assert decision.risk_level == RiskLevel.CRITICAL
    assert decision.action_advice == ActionAdvice.CLEAR_OR_STOP
    assert decision.risk_score == 80.0
    assert decision.reasons == ["触发硬止损", "技术位破位", "资金流出"]


@pytest.mark.parametrize(
    ("current_price", "expected"),
    [
        (9.50, 100.0),
        (9.51, 75.0),
        (9.70, 75.0),
        (9.71, 50.0),
        (10.00, 50.0),
        (10.01, 10.0),
    ],
)
def test_compute_holding_drawdown_factor_thresholds(
    current_price: float, expected: float
):
    assert compute_holding_drawdown_factor(make_holding(current_price=current_price)) == expected


@pytest.mark.parametrize(
    (
        "current_price",
        "technical_broken",
        "sector_cooling",
        "negative_event",
        "fund_outflow",
        "market_score",
        "expected_score",
        "expected_risk_level",
        "expected_action",
    ),
    [
        (10.10, False, False, False, False, 55, 0.0, RiskLevel.LOW, ActionAdvice.HOLD),
        (9.60, False, False, False, True, 55, 40.0, RiskLevel.MEDIUM, ActionAdvice.TIGHTEN_STOP),
        (9.60, True, False, False, False, 55, 55.0, RiskLevel.HIGH, ActionAdvice.REDUCE),
        (9.50, True, False, False, True, 55, 80.0, RiskLevel.CRITICAL, ActionAdvice.CLEAR_OR_STOP),
    ],
)
def test_portfolio_risk_engine_maps_score_thresholds_to_actions(
    current_price: float,
    technical_broken: bool,
    sector_cooling: bool,
    negative_event: bool,
    fund_outflow: bool,
    market_score: float,
    expected_score: float,
    expected_risk_level: RiskLevel,
    expected_action: ActionAdvice,
):
    engine = PortfolioRiskEngine(default_stop_loss_pct=0.04, hard_stop_loss_pct=0.05)

    decision = engine.evaluate(
        holding=make_holding(current_price=current_price),
        technical_broken=technical_broken,
        sector_cooling=sector_cooling,
        negative_event=negative_event,
        fund_outflow=fund_outflow,
        market_score=market_score,
    )

    assert decision.risk_score == expected_score
    assert decision.risk_level == expected_risk_level
    assert decision.action_advice == expected_action


def test_portfolio_risk_engine_returns_default_low_risk_reason():
    engine = PortfolioRiskEngine(default_stop_loss_pct=0.04, hard_stop_loss_pct=0.05)

    decision = engine.evaluate(
        holding=make_holding(current_price=10.10),
        technical_broken=False,
        sector_cooling=False,
        negative_event=False,
        fund_outflow=False,
        market_score=55,
    )

    assert decision.risk_score == 0.0
    assert decision.reasons == ["风险较低"]


def test_portfolio_risk_engine_caps_score_at_100():
    engine = PortfolioRiskEngine(default_stop_loss_pct=0.04, hard_stop_loss_pct=0.05)

    decision = engine.evaluate(
        holding=make_holding(current_price=9.00),
        technical_broken=True,
        sector_cooling=True,
        negative_event=True,
        fund_outflow=True,
        market_score=20,
    )

    assert decision.risk_score == 100.0
    assert decision.risk_level == RiskLevel.CRITICAL
    assert decision.action_advice == ActionAdvice.CLEAR_OR_STOP
    assert decision.reasons == [
        "触发硬止损",
        "技术位破位",
        "资金流出",
        "板块退潮",
        "负面事件",
        "市场环境禁止新冒险",
    ]
