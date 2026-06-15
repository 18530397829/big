from pathlib import Path

import pandas as pd


class SignalLedger:
    COLUMNS = ["trade_date", "symbol", "signal_type", "score", "action"]

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
        return pd.DataFrame(self._rows, columns=self.COLUMNS)

    def export_csv(self, path: str | Path) -> Path:
        csv_path = Path(path)
        self.to_frame().to_csv(csv_path, index=False)
        return csv_path
