from trading_assistant.domain.models import Holding


def compute_holding_drawdown_factor(holding: Holding) -> float:
    if holding.unrealized_return_pct <= -0.05:
        return 100.0
    if holding.unrealized_return_pct <= -0.03:
        return 75.0
    if holding.unrealized_return_pct <= 0:
        return 50.0
    return 10.0
