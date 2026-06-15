DashboardView = dict[str, int | str | list[str]]


def build_dashboard_view() -> DashboardView:
    return {
        "market_score": 58,
        "portfolio_risk": "中等",
        "candidate_count": 3,
        "critical_alerts": 0,
        "sections": ["持仓风险", "市场环境", "重点候选", "盘中提醒", "回测复盘"],
    }
