from trading_assistant.domain.models import ScoreBreakdown


class ScoreEngine:
    def __init__(self, weights: dict[str, float]) -> None:
        self.weights = weights

    def score(self, normalized_factors: dict[str, float]) -> ScoreBreakdown:
        components: dict[str, float] = {}
        reasons: list[str] = []
        for factor_name, weight in self.weights.items():
            value = max(0.0, min(100.0, float(normalized_factors.get(factor_name, 0.0))))
            components[factor_name] = round(value * weight, 4)
            reasons.append(f"{factor_name}={normalized_factors.get(factor_name, 0)} weight={weight}")
        total_score = round(sum(components.values()), 2)
        return ScoreBreakdown(total_score=total_score, components=components, reasons=reasons)
