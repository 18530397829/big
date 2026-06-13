import pandas as pd


def compute_market_environment_factors(market: pd.DataFrame) -> dict[str, float | int]:
    total = len(market)
    advance_count = int((market["pct_chg"] > 0).sum())
    decline_count = int((market["pct_chg"] < 0).sum())
    return {
        "advance_ratio": round(advance_count / total, 2) if total else 0.0,
        "decline_ratio": round(decline_count / total, 2) if total else 0.0,
        "total_turnover": float(market["turnover"].sum()),
        "limit_up_count": int(market["is_limit_up"].sum()),
        "limit_down_count": int(market["is_limit_down"].sum()),
    }
