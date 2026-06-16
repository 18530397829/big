from dataclasses import dataclass
from math import floor

import pandas as pd


@dataclass(frozen=True)
class CandidateGroups:
    primary: pd.DataFrame
    outside_observation: pd.DataFrame


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


def select_candidate_groups(
    scored_stocks: pd.DataFrame,
    *,
    active_focus_priorities: dict[str, int],
    holding_symbols: set[str],
    inactive_focus_symbols: set[str],
    min_opportunity_score: float,
    min_plan_confidence_score: float,
    limit: int,
    outside_limit: int,
) -> CandidateGroups:
    filtered = scored_stocks[
        (scored_stocks["pool_type"] == "tradable")
        & (scored_stocks["opportunity_score"] >= min_opportunity_score)
        & (scored_stocks["plan_confidence_score"] >= min_plan_confidence_score)
    ].copy()
    if filtered.empty:
        return CandidateGroups(
            primary=filtered.reset_index(drop=True),
            outside_observation=filtered.reset_index(drop=True),
        )

    filtered["symbol"] = filtered["symbol"].astype(str)
    filtered["_score_band"] = filtered["opportunity_score"].map(_score_band)
    filtered["_focus_priority"] = filtered["symbol"].map(active_focus_priorities).fillna(0)

    active_focus_symbols = set(active_focus_priorities)
    primary_mask = filtered["symbol"].isin(active_focus_symbols | holding_symbols)
    outside_mask = (
        ~filtered["symbol"].isin(active_focus_symbols)
        & ~filtered["symbol"].isin(holding_symbols)
        & ~filtered["symbol"].isin(inactive_focus_symbols)
    )

    primary = (
        filtered[primary_mask]
        .sort_values(
            ["_score_band", "_focus_priority", "opportunity_score", "plan_confidence_score"],
            ascending=False,
        )
        .head(limit)
        .drop(columns=["_score_band", "_focus_priority"])
        .reset_index(drop=True)
    )
    outside_observation = (
        filtered[outside_mask]
        .sort_values(["opportunity_score", "plan_confidence_score"], ascending=False)
        .head(outside_limit)
        .drop(columns=["_score_band", "_focus_priority"])
        .reset_index(drop=True)
    )
    return CandidateGroups(primary=primary, outside_observation=outside_observation)


def _score_band(value: float) -> int:
    return floor(float(value) / 5) * 5
