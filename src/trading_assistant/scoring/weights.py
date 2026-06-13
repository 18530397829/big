from collections.abc import Mapping
from pathlib import Path

import yaml


def load_weight_config(path: Path) -> dict[str, dict[str, float]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError("Weight config must be a mapping")

    result: dict[str, dict[str, float]] = {}
    for score_name, weights in raw.items():
        if not isinstance(weights, Mapping):
            raise ValueError(f"Weights for {score_name} must be a mapping")
        total = round(sum(float(value) for value in weights.values()), 4)
        if total != 1.0:
            raise ValueError(f"{score_name} weights sum to {total}, expected 1.0")
        result[str(score_name)] = {str(key): float(value) for key, value in weights.items()}
    return result
