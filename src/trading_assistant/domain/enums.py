from enum import StrEnum


class PoolType(StrEnum):
    TRADABLE = "tradable"
    WATCH = "watch"
    BLOCKED = "blocked"
    HOLDING = "holding"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionAdvice(StrEnum):
    HOLD = "hold"
    TIGHTEN_STOP = "tighten_stop"
    REDUCE = "reduce"
    SELL_ON_REBOUND = "sell_on_rebound"
    CLEAR_OR_STOP = "clear_or_stop"
    WATCH_FOR_TRIGGER = "watch_for_trigger"
    NO_ACTION = "no_action"
