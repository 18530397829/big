from collections.abc import Mapping

from trading_assistant.domain.enums import ActionAdvice, PoolType, RiskLevel
from trading_assistant.domain.models import TradePlan
from trading_assistant.planning.position_sizing import compute_position_pct, resolve_risk_config


LEGACY_DEFAULT_STOP_LOSS_PCT = 0.03


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
    risk_config: Mapping[str, object] | None = None,
) -> TradePlan:
    if current_price <= 0:
        msg = "current_price must be greater than 0"
        raise ValueError(msg)
    if atr_pct < 0 or atr_pct >= 1:
        msg = "atr_pct must be greater than or equal to 0 and less than 1"
        raise ValueError(msg)

    rules = resolve_risk_config(risk_config)
    no_new_market_score = rules["market_score_no_new_position"]
    high_portfolio_risk = rules["high_portfolio_risk_no_new_position"]
    if market_score < no_new_market_score:
        msg = (
            f"market_score {market_score} is below no-new-position threshold "
            f"{no_new_market_score}"
        )
        raise ValueError(msg)
    if portfolio_risk_score >= high_portfolio_risk:
        msg = (
            f"portfolio_risk_score {portfolio_risk_score} is at or above no-new-position "
            f"threshold {high_portfolio_risk}"
        )
        raise ValueError(msg)

    stop_loss_floor = (
        rules["default_stop_loss_pct"] if risk_config is not None else LEGACY_DEFAULT_STOP_LOSS_PCT
    )
    entry_low = round(current_price * 1.005, 2)
    entry_high = round(current_price * (1 + rules["max_gap_up_for_entry_pct"]), 2)
    stop_loss = round(current_price * (1 - max(stop_loss_floor, atr_pct)), 2)
    first_take_profit = round(entry_high * (1 + rules["first_take_profit_pct"]), 2)
    second_take_profit = round(entry_high * (1 + rules["second_take_profit_pct"]), 2)
    risk = entry_low - stop_loss
    reward = first_take_profit - entry_low
    reward_risk_ratio = 0.0 if risk <= 0 else round(reward / risk, 2)
    min_reward_risk_ratio = rules["min_reward_risk_ratio"]
    if reward_risk_ratio < min_reward_risk_ratio:
        msg = (
            f"reward/risk ratio {reward_risk_ratio:.2f} is below minimum "
            f"{min_reward_risk_ratio:.2f}"
        )
        raise ValueError(msg)

    stop_distance_pct = (entry_low - stop_loss) / entry_low
    position_pct = compute_position_pct(
        opportunity_score=opportunity_score,
        plan_confidence_score=plan_confidence_score,
        market_score=market_score,
        portfolio_risk_score=portfolio_risk_score,
        stop_loss_distance_pct=stop_distance_pct,
        risk_config=risk_config,
    )
    if portfolio_risk_score >= high_portfolio_risk:
        risk_level = RiskLevel.HIGH
    elif market_score < rules["market_score_light_position"]:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.LOW

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
