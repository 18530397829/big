import pandas as pd

SELL_ACTIONS = {
    "clear",
    "clear_or_stop",
    "reduce",
    "sell",
    "sell_on_rebound",
    "stop",
    "清仓",
    "清仓/止损",
    "减仓",
    "反弹卖出",
}


def _available_returns(evaluated: pd.DataFrame, column: str) -> pd.Series:
    if column not in evaluated:
        return pd.Series(dtype="float64")
    return pd.to_numeric(evaluated[column], errors="coerce").dropna()


def _average_return(evaluated: pd.DataFrame, column: str) -> float | None:
    returns = _available_returns(evaluated, column)
    if returns.empty:
        return None
    return round(float(returns.mean()), 4)


def _win_rate(evaluated: pd.DataFrame, column: str) -> float | None:
    returns = _available_returns(evaluated, column)
    if returns.empty:
        return None
    return round(float((returns > 0).mean()), 4)


def _net_returns(evaluated: pd.DataFrame, column: str, transaction_cost_rate: float) -> pd.Series:
    returns = _available_returns(evaluated, column)
    if returns.empty:
        return returns
    return returns - transaction_cost_rate


def _net_average_return(
    evaluated: pd.DataFrame,
    column: str,
    transaction_cost_rate: float,
) -> float | None:
    returns = _net_returns(evaluated, column, transaction_cost_rate)
    if returns.empty:
        return None
    return round(float(returns.mean()), 4)


def _net_win_rate(
    evaluated: pd.DataFrame,
    column: str,
    transaction_cost_rate: float,
) -> float | None:
    returns = _net_returns(evaluated, column, transaction_cost_rate)
    if returns.empty:
        return None
    return round(float((returns > 0).mean()), 4)


def _profit_loss_ratio(evaluated: pd.DataFrame, column: str) -> float | None:
    returns = _available_returns(evaluated, column)
    if returns.empty:
        return None
    gains = returns[returns > 0]
    losses = returns[returns < 0]
    if gains.empty or losses.empty:
        return None
    return round(float(gains.mean() / abs(losses.mean())), 4)


def _returns_in_trade_order(
    evaluated: pd.DataFrame,
    column: str,
    transaction_cost_rate: float,
) -> pd.Series:
    if column not in evaluated:
        return pd.Series(dtype="float64")
    ordered = evaluated.copy()
    if "trade_date" in ordered:
        ordered["_trade_date_sort"] = pd.to_datetime(ordered["trade_date"], errors="coerce")
        ordered = ordered.sort_values("_trade_date_sort", kind="stable")
    returns = pd.to_numeric(ordered[column], errors="coerce").dropna()
    if returns.empty:
        return pd.Series(dtype="float64")
    return returns - transaction_cost_rate


def _max_drawdown(
    evaluated: pd.DataFrame,
    column: str,
    transaction_cost_rate: float,
) -> float | None:
    returns = _returns_in_trade_order(evaluated, column, transaction_cost_rate)
    if returns.empty:
        return None
    equity = pd.concat(
        [pd.Series([1.0], dtype="float64"), (1 + returns).cumprod()],
        ignore_index=True,
    )
    peaks = equity.cummax()
    drawdowns = equity / peaks - 1
    return round(float(drawdowns.min()), 4)


def _sell_mask(evaluated: pd.DataFrame) -> pd.Series:
    if "action" not in evaluated:
        return pd.Series(False, index=evaluated.index, dtype="bool")
    normalized = evaluated["action"].astype(str).str.lower()
    return normalized.isin(SELL_ACTIONS)


def _sell_signal_rate(evaluated: pd.DataFrame, column: str, threshold: float) -> float | None:
    if column not in evaluated:
        return None
    sell_mask = _sell_mask(evaluated)
    sell_values = pd.to_numeric(evaluated.loc[sell_mask, column], errors="coerce").dropna()
    if sell_values.empty:
        return None
    return round(float((sell_values > threshold).mean()), 4)


def summarize_returns(
    evaluated: pd.DataFrame,
    *,
    transaction_cost_rate: float = 0.0,
) -> dict[str, float | None]:
    return {
        "win_rate_1d": _win_rate(evaluated, "return_1d"),
        "avg_return_1d": _average_return(evaluated, "return_1d"),
        "avg_return_3d": _average_return(evaluated, "return_3d"),
        "avg_return_5d": _average_return(evaluated, "return_5d"),
        "net_win_rate_1d": _net_win_rate(evaluated, "return_1d", transaction_cost_rate),
        "net_avg_return_1d": _net_average_return(
            evaluated,
            "return_1d",
            transaction_cost_rate,
        ),
        "profit_loss_ratio_1d": _profit_loss_ratio(evaluated, "return_1d"),
        "max_drawdown_1d": _max_drawdown(evaluated, "return_1d", transaction_cost_rate),
        "false_sell_rate_5d": _sell_signal_rate(evaluated, "return_5d", 0.0),
        "missed_rebound_rate_5d": _sell_signal_rate(evaluated, "max_return_5d", 0.03),
        "transaction_cost_rate": round(float(transaction_cost_rate), 4),
    }
