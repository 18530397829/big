import pandas as pd


def compute_volume_price_factors(bars: pd.DataFrame) -> dict[str, float | bool]:
    ordered = bars.reset_index(drop=True)
    recent_turnover = float(ordered["turnover"].iloc[-1])
    base_turnover = float(ordered["turnover"].head(max(len(ordered) - 1, 1)).mean())
    turnover_expansion = recent_turnover / base_turnover if base_turnover > 0 else 0.0
    close_up = float(ordered["close"].iloc[-1]) > float(ordered["close"].iloc[-2])
    return {
        "turnover_expansion": round(turnover_expansion, 2),
        "price_up_with_volume": bool(close_up and turnover_expansion >= 1.2),
    }
