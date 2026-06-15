import pandas as pd


def select_candidates(
    scored_stocks: pd.DataFrame,
    *,
    min_opportunity_score: float,
    min_plan_confidence_score: float,
    limit: int,
) -> pd.DataFrame:
    filtered = scored_stocks[
        (scored_stocks["pool_type"] == "tradable")
        & (scored_stocks["opportunity_score"] >= min_opportunity_score)
        & (scored_stocks["plan_confidence_score"] >= min_plan_confidence_score)
    ]
    return (
        filtered.sort_values(["opportunity_score", "plan_confidence_score"], ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )
