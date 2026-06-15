import pandas as pd


REQUIRED_COLUMNS = frozenset({"close", "high", "low"})


def _prepare_bars(bars: pd.DataFrame) -> pd.DataFrame:
    missing_columns = REQUIRED_COLUMNS - set(bars.columns)
    if missing_columns:
        raise ValueError(
            f"technical factors missing required columns: {', '.join(sorted(missing_columns))}"
        )
    if bars.empty:
        raise ValueError("technical factors input is empty")
    if "trade_date" in bars.columns:
        return bars.sort_values("trade_date", kind="mergesort").reset_index(drop=True)
    return bars.reset_index(drop=True)


def compute_technical_factors(bars: pd.DataFrame) -> dict[str, float | bool]:
    ordered = _prepare_bars(bars)
    close = ordered["close"]
    high = ordered["high"]
    low = ordered["low"]
    ma5 = close.tail(5).mean()
    momentum_window = close.tail(5)
    momentum_5d = round(
        (momentum_window.iloc[-1] - momentum_window.iloc[0]) / momentum_window.iloc[0], 4
    )
    atr_5d = round(((high - low).tail(5).mean() / close.iloc[-1]), 4)
    return {
        "momentum_5d": momentum_5d,
        "above_ma5": bool(close.iloc[-1] >= ma5),
        "atr_5d": atr_5d,
    }
