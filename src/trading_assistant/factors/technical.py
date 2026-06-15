import pandas as pd


def compute_technical_factors(bars: pd.DataFrame) -> dict[str, float | bool]:
    ordered = bars.reset_index(drop=True)
    close = ordered["close"]
    high = ordered["high"]
    low = ordered["low"]
    ma5 = close.tail(5).mean()
    momentum_5d = round((close.iloc[-1] - close.iloc[0]) / close.iloc[0], 4)
    atr_5d = round(((high - low).tail(5).mean() / close.iloc[-1]), 4)
    return {
        "momentum_5d": momentum_5d,
        "above_ma5": bool(close.iloc[-1] >= ma5),
        "atr_5d": atr_5d,
    }
