import pandas as pd

from trading_assistant.planning.candidate_selector import select_candidate_groups, select_candidates


def test_select_candidates_filters_by_score_and_pool() -> None:
    frame = pd.DataFrame(
        [
            {
                "symbol": "000001",
                "name": "平安银行",
                "pool_type": "tradable",
                "opportunity_score": 82,
                "plan_confidence_score": 75,
            },
            {
                "symbol": "600519",
                "name": "贵州茅台",
                "pool_type": "watch",
                "opportunity_score": 90,
                "plan_confidence_score": 80,
            },
            {
                "symbol": "300001",
                "name": "样例科技",
                "pool_type": "tradable",
                "opportunity_score": 55,
                "plan_confidence_score": 90,
            },
        ]
    )

    selected = select_candidates(
        frame,
        min_opportunity_score=76,
        min_plan_confidence_score=70,
        limit=8,
    )

    assert list(selected["symbol"]) == ["000001"]


def test_select_candidates_orders_by_scores_and_applies_limit() -> None:
    frame = pd.DataFrame(
        [
            {
                "symbol": "000001",
                "name": "Alpha",
                "pool_type": "tradable",
                "opportunity_score": 80,
                "plan_confidence_score": 99,
            },
            {
                "symbol": "000002",
                "name": "Beta",
                "pool_type": "tradable",
                "opportunity_score": 90,
                "plan_confidence_score": 70,
            },
            {
                "symbol": "000003",
                "name": "Gamma",
                "pool_type": "tradable",
                "opportunity_score": 90,
                "plan_confidence_score": 85,
            },
            {
                "symbol": "000004",
                "name": "Delta",
                "pool_type": "tradable",
                "opportunity_score": 78,
                "plan_confidence_score": 100,
            },
        ]
    )

    selected = select_candidates(
        frame,
        min_opportunity_score=76,
        min_plan_confidence_score=70,
        limit=2,
    )

    assert list(selected["symbol"]) == ["000003", "000002"]


def test_select_candidate_groups_separates_focus_primary_and_outside_observation() -> None:
    frame = pd.DataFrame(
        [
            {
                "symbol": "000001",
                "name": "平安银行",
                "pool_type": "tradable",
                "opportunity_score": 82,
                "plan_confidence_score": 75,
            },
            {
                "symbol": "600519",
                "name": "贵州茅台",
                "pool_type": "tradable",
                "opportunity_score": 90,
                "plan_confidence_score": 80,
            },
            {
                "symbol": "300001",
                "name": "已停看",
                "pool_type": "tradable",
                "opportunity_score": 95,
                "plan_confidence_score": 80,
            },
            {
                "symbol": "000002",
                "name": "持仓但未关注",
                "pool_type": "tradable",
                "opportunity_score": 78,
                "plan_confidence_score": 72,
            },
        ]
    )

    groups = select_candidate_groups(
        frame,
        active_focus_priorities={"000001": 3},
        holding_symbols={"000002"},
        inactive_focus_symbols={"300001"},
        min_opportunity_score=76,
        min_plan_confidence_score=70,
        limit=8,
        outside_limit=8,
    )

    assert list(groups.primary["symbol"]) == ["000001", "000002"]
    assert list(groups.outside_observation["symbol"]) == ["600519"]


def test_select_candidate_groups_uses_focus_priority_inside_same_score_band() -> None:
    frame = pd.DataFrame(
        [
            {
                "symbol": "000001",
                "name": "Alpha",
                "pool_type": "tradable",
                "opportunity_score": 88,
                "plan_confidence_score": 95,
            },
            {
                "symbol": "000002",
                "name": "Beta",
                "pool_type": "tradable",
                "opportunity_score": 86,
                "plan_confidence_score": 75,
            },
            {
                "symbol": "000003",
                "name": "Gamma",
                "pool_type": "tradable",
                "opportunity_score": 91,
                "plan_confidence_score": 70,
            },
        ]
    )

    groups = select_candidate_groups(
        frame,
        active_focus_priorities={"000001": 1, "000002": 5, "000003": 1},
        holding_symbols=set(),
        inactive_focus_symbols=set(),
        min_opportunity_score=76,
        min_plan_confidence_score=70,
        limit=8,
        outside_limit=8,
    )

    assert list(groups.primary["symbol"]) == ["000003", "000002", "000001"]
