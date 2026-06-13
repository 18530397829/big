from datetime import date

from trading_assistant.domain.enums import ActionAdvice, RiskLevel
from trading_assistant.domain.models import Holding
from trading_assistant.portfolio.risk_engine import PortfolioRiskEngine


def test_portfolio_risk_engine_flags_hard_stop():
    holding = Holding(
        symbol="000001",
        name="平安银行",
        quantity=1000,
        cost_price=10.0,
        current_price=9.45,
        buy_date=date(2026, 6, 10),
        theme="银行",
        buy_reason="放量突破平台",
    )
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
    assert decision.risk_score >= 71
