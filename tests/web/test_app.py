from fastapi.testclient import TestClient

from trading_assistant.web.app import create_app
from trading_assistant.web.view_models import build_dashboard_view


def test_dashboard_home_renders():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "A 股短线交易辅助系统" in response.text
    assert "持仓风险" in response.text


def test_dashboard_view_contains_shell_metrics():
    assert build_dashboard_view() == {
        "market_score": 58,
        "portfolio_risk": "中等",
        "candidate_count": 3,
        "critical_alerts": 0,
        "sections": ["持仓风险", "市场环境", "重点候选", "盘中提醒", "回测复盘"],
    }
