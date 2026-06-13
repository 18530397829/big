import pandas as pd


class SignalLedger:
    def __init__(self) -> None:
        self._rows: list[dict[str, object]] = []

    def record_signal(
        self,
        *,
        trade_date: str,
        symbol: str,
        signal_type: str,
        score: float,
        action: str,
    ) -> None:
        self._rows.append(
            {
                "trade_date": trade_date,
                "symbol": symbol,
                "signal_type": signal_type,
                "score": score,
                "action": action,
            }
        )

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self._rows)
