from trading_assistant.domain.models import ScoreBreakdown

_CONSERVATIVE_CONFIRMATION_FACTORS = {"fund_behavior", "sentiment_heat"}
_CONFIRMATION_BASELINE = 60.0


class ScoreEngine:
    def __init__(self, weights: dict[str, float]) -> None:
        self.weights = weights

    def score(self, normalized_factors: dict[str, float]) -> ScoreBreakdown:
        components: dict[str, float] = {}
        reasons: list[str] = []
        for factor_name, weight in self.weights.items():
            value = max(0.0, min(100.0, float(normalized_factors.get(factor_name, 0.0))))
            adjusted_value = self._adjust_factor_value(factor_name, value)
            components[factor_name] = round(adjusted_value * weight, 4)
            reasons.append(f"{factor_name}={value:g} adjusted={adjusted_value:g} weight={weight}")
        total_score = round(sum(components.values()), 2)
        return ScoreBreakdown(total_score=total_score, components=components, reasons=reasons)

    def _adjust_factor_value(self, factor_name: str, value: float) -> float:
        if factor_name not in _CONSERVATIVE_CONFIRMATION_FACTORS:
            return value
        shortfall = max(0.0, _CONFIRMATION_BASELINE - value)
        return max(0.0, value - shortfall)
