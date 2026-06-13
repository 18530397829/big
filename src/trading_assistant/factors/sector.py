import pandas as pd


def compute_sector_strength(sectors: pd.DataFrame) -> list[dict[str, float | str]]:
    ranked = sectors.sort_values(["pct_chg", "turnover", "limit_up_count"], ascending=False)
    result: list[dict[str, float | str]] = []
    for row in ranked.to_dict(orient="records"):
        result.append(
            {
                "sector_name": str(row["sector_name"]),
                "sector_type": str(row["sector_type"]),
                "strength_score": round(
                    float(row["pct_chg"]) * 8 + float(row["limit_up_count"]) * 5, 2
                ),
                "leader_symbol": str(row["leader_symbol"]),
            }
        )
    return result
