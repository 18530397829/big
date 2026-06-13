from trading_assistant.domain.enums import ActionAdvice, PoolType, RiskLevel
from trading_assistant.domain.models import TradePlan
from trading_assistant.planning.position_sizing import compute_position_pct


def build_trade_plan(
    *,
    symbol: str,
    name: str,
    current_price: float,
    opportunity_score: float,
    plan_confidence_score: float,
    market_score: float,
    portfolio_risk_score: float,
    atr_pct: float,
    theme: str,
) -> TradePlan:
    entry_low = round(current_price * 1.005, 2)
    entry_high = round(current_price * 1.03, 2)
    stop_loss = round(current_price * (1 - max(0.03, atr_pct)), 2)
    first_take_profit = round(entry_high * 1.06, 2)
    second_take_profit = round(entry_high * 1.10, 2)
    stop_distance_pct = (entry_low - stop_loss) / entry_low
    position_pct = compute_position_pct(
        opportunity_score=opportunity_score,
        plan_confidence_score=plan_confidence_score,
        market_score=market_score,
        portfolio_risk_score=portfolio_risk_score,
        stop_loss_distance_pct=stop_distance_pct,
    )
    risk_level = RiskLevel.MEDIUM if market_score < 60 else RiskLevel.LOW

    return TradePlan(
        symbol=symbol,
        name=name,
        pool_type=PoolType.TRADABLE,
        opportunity_score=opportunity_score,
        plan_confidence_score=plan_confidence_score,
        entry_trigger=f"{theme} 板块继续强于大盘，且 {symbol} 放量突破 {entry_low:.2f}",
        entry_price_low=entry_low,
        entry_price_high=entry_high,
        stop_loss_price=stop_loss,
        first_take_profit_price=first_take_profit,
        second_take_profit_price=second_take_profit,
        position_pct=position_pct,
        invalidation_condition=f"跌破 {stop_loss:.2f}、高开超过 3% 后回落、或 {theme} 板块退潮",
        risk_level=risk_level,
        action_advice=(
            ActionAdvice.WATCH_FOR_TRIGGER if position_pct > 0 else ActionAdvice.NO_ACTION
        ),
    )
