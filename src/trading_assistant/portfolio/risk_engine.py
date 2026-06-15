from dataclasses import dataclass

from trading_assistant.domain.enums import ActionAdvice, RiskLevel
from trading_assistant.domain.models import Holding


@dataclass(frozen=True)
class PortfolioRiskDecision:
    symbol: str
    risk_score: float
    risk_level: RiskLevel
    action_advice: ActionAdvice
    reasons: list[str]


class PortfolioRiskEngine:
    def __init__(self, default_stop_loss_pct: float, hard_stop_loss_pct: float) -> None:
        self.default_stop_loss_pct = default_stop_loss_pct
        self.hard_stop_loss_pct = hard_stop_loss_pct

    def evaluate(
        self,
        *,
        holding: Holding,
        technical_broken: bool,
        sector_cooling: bool,
        negative_event: bool,
        fund_outflow: bool,
        market_score: float,
    ) -> PortfolioRiskDecision:
        reasons: list[str] = []
        score = 0.0
        loss_pct = -holding.unrealized_return_pct
        if loss_pct >= self.hard_stop_loss_pct:
            score += 45
            reasons.append("触发硬止损")
        elif loss_pct >= self.default_stop_loss_pct:
            score += 30
            reasons.append("接近默认止损")
        if technical_broken:
            score += 25
            reasons.append("技术位破位")
        if fund_outflow:
            score += 10
            reasons.append("资金流出")
        if sector_cooling:
            score += 10
            reasons.append("板块退潮")
        if negative_event:
            score += 10
            reasons.append("负面事件")
        if market_score < 40:
            score += 15
            reasons.append("市场环境禁止新冒险")
        score = min(100.0, round(score, 2))
        if score >= 71:
            return PortfolioRiskDecision(
                holding.symbol,
                score,
                RiskLevel.CRITICAL,
                ActionAdvice.CLEAR_OR_STOP,
                reasons,
            )
        if score >= 51:
            return PortfolioRiskDecision(
                holding.symbol,
                score,
                RiskLevel.HIGH,
                ActionAdvice.REDUCE,
                reasons,
            )
        if score >= 31:
            return PortfolioRiskDecision(
                holding.symbol,
                score,
                RiskLevel.MEDIUM,
                ActionAdvice.TIGHTEN_STOP,
                reasons,
            )
        return PortfolioRiskDecision(
            holding.symbol,
            score,
            RiskLevel.LOW,
            ActionAdvice.HOLD,
            reasons or ["风险较低"],
        )
