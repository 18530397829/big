import pandas as pd


def summarize_returns(evaluated: pd.DataFrame) -> dict[str, float]:
    if evaluated.empty:
        return {
            "win_rate_1d": 0.0,
            "avg_return_1d": 0.0,
            "avg_return_3d": 0.0,
            "avg_return_5d": 0.0,
        }
    return {
        "win_rate_1d": round(float((evaluated["return_1d"] > 0).mean()), 4),
        "avg_return_1d": round(float(evaluated["return_1d"].mean()), 4),
        "avg_return_3d": round(float(evaluated["return_3d"].mean()), 4),
        "avg_return_5d": round(float(evaluated["return_5d"].mean()), 4),
    }
