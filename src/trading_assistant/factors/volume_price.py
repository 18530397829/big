import pandas as pd


REQUIRED_COLUMNS = frozenset({"close", "turnover"})


def _prepare_bars(bars: pd.DataFrame) -> pd.DataFrame:
    missing_columns = REQUIRED_COLUMNS - set(bars.columns)
    if missing_columns:
        raise ValueError(
            f"volume price factors missing required columns: {', '.join(sorted(missing_columns))}"
        )
    if bars.empty:
        raise ValueError("volume price factors input is empty")
    if "trade_date" in bars.columns:
        return bars.sort_values("trade_date", kind="mergesort").reset_index(drop=True)
    return bars.reset_index(drop=True)


def compute_volume_price_factors(bars: pd.DataFrame) -> dict[str, float | bool]:
    ordered = _prepare_bars(bars)
    recent_turnover = float(ordered["turnover"].iloc[-1])
    if len(ordered) == 1:
        base_turnover = recent_turnover
        close_up = False
    else:
        base_turnover = float(ordered["turnover"].iloc[:-1].mean())
        close_up = float(ordered["close"].iloc[-1]) > float(ordered["close"].iloc[-2])
    turnover_expansion = recent_turnover / base_turnover if base_turnover > 0 else 0.0
    return {
        "turnover_expansion": round(turnover_expansion, 2),
        "price_up_with_volume": bool(close_up and turnover_expansion >= 1.2),
    }
