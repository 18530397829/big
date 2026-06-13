from pathlib import Path

import yaml


def load_weight_config(path: Path) -> dict[str, dict[str, float]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    for score_name, weights in raw.items():
        total = round(sum(float(value) for value in weights.values()), 4)
        if total != 1.0:
            raise ValueError(f"{score_name} weights sum to {total}, expected 1.0")
    return {
        name: {key: float(value) for key, value in weights.items()} for name, weights in raw.items()
    }
