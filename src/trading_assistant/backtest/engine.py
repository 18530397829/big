import pandas as pd


def evaluate_forward_returns(signals: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.copy()
    prices["trade_date"] = pd.to_datetime(prices["trade_date"])
    rows: list[dict[str, object]] = []
    for signal in signals.to_dict(orient="records"):
        symbol_prices = (
            prices[prices["symbol"] == signal["symbol"]]
            .sort_values("trade_date")
            .reset_index(drop=True)
        )
        start_date = pd.to_datetime(signal["trade_date"])
        start_row = symbol_prices[symbol_prices["trade_date"] == start_date]
        if start_row.empty:
            continue
        start_index = int(start_row.index[0])
        start_close = float(start_row.iloc[0]["close"])
        row = dict(signal)
        for horizon in [1, 3, 5]:
            target_index = start_index + horizon
            if target_index >= len(symbol_prices):
                row[f"return_{horizon}d"] = pd.NA
                continue
            target_close = float(symbol_prices.iloc[target_index]["close"])
            row[f"return_{horizon}d"] = round(
                (target_close - start_close) / start_close,
                4,
            )
        future_5d = symbol_prices.iloc[start_index + 1 : start_index + 6]
        if future_5d.empty:
            row["max_return_5d"] = pd.NA
        else:
            max_close = float(future_5d["close"].max())
            row["max_return_5d"] = round((max_close - start_close) / start_close, 4)
        rows.append(row)
    return pd.DataFrame(rows)
