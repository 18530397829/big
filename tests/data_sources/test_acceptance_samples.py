from pathlib import Path

import pandas as pd


def test_akshare_acceptance_daily_sample_has_sixty_trading_days_per_symbol():
    sample_path = (
        Path(__file__).resolve().parents[2] / "data/samples/akshare_acceptance_daily_bars.csv"
    )

    frame = pd.read_csv(sample_path, parse_dates=["trade_date"])

    assert set(frame.columns) == {
        "trade_date",
        "symbol",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "turnover",
    }
    assert sorted(frame["symbol"].astype(str).str.zfill(6).unique().tolist()) == [
        "000001",
        "600519",
    ]
    assert frame.duplicated(["trade_date", "symbol"]).sum() == 0
    assert (frame.groupby("symbol")["trade_date"].nunique() >= 60).all()
    assert frame[["open", "high", "low", "close", "volume", "turnover"]].notna().all().all()
