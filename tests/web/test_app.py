from fastapi.testclient import TestClient
import pytest

from trading_assistant.web.app import create_app
from trading_assistant.web import view_models


def test_dashboard_home_renders():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    expected_labels = [
        "A 股短线交易辅助系统",
        "市场环境分",
        "持仓风险",
        "重点候选",
        "P0/P1 提醒",
    ]
    missing_labels = [label for label in expected_labels if label not in response.text]
    assert missing_labels == []
    assert "平安银行" in response.text
    assert "25480.00" in response.text
    assert "等待后续任务填充实时数据" not in response.text


def test_dashboard_sections_render_section_titles_and_summaries():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "built-in method" not in response.text
    assert "2 只持仓，总市值 25480.00，最高风险 低" in response.text


def test_dashboard_sections_support_legacy_title_strings(monkeypatch: pytest.MonkeyPatch):
    from trading_assistant.web import routes

    monkeypatch.setattr(
        routes,
        "build_dashboard_view",
        lambda: {
            "market_score": 58,
            "portfolio_risk": "中等",
            "candidate_count": 3,
            "critical_alerts": 0,
            "sections": ["持仓风险", "市场环境", "重点候选", "盘中提醒", "回测复盘"],
        },
    )
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "built-in method" not in response.text
    assert "持仓风险" in response.text
    assert "回测复盘" in response.text
    assert "当前等级" in response.text
    assert "待观察标的" in response.text


@pytest.mark.parametrize(
    ("template_name", "expected_heading"),
    [
        ("holdings.html", "持仓风险"),
        ("candidates.html", "重点候选"),
        ("backtest.html", "回测复盘"),
    ],
)
def test_detail_templates_render_fallback_without_view_context(
    template_name: str,
    expected_heading: str,
):
    from fastapi import FastAPI, Request
    from fastapi.staticfiles import StaticFiles
    from trading_assistant.web.app import STATIC_DIR
    from trading_assistant.web.routes import templates

    application = FastAPI()
    application.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @application.get("/")
    def legacy_page(request: Request):
        return templates.TemplateResponse(
            request=request,
            name=template_name,
            context={"request": request},
        )

    client = TestClient(application, raise_server_exceptions=False)

    response = client.get("/")

    assert response.status_code == 200
    assert expected_heading in response.text
    assert "页面数据加载中，请重启服务后刷新。" in response.text


def test_dashboard_view_is_built_from_sample_data():
    view = view_models.build_dashboard_view()

    assert view["market_score"] == 52
    assert view["portfolio_risk"] == "低"
    assert view["holding_count"] == 2
    assert view["total_market_value"] == "25480.00"
    assert view["candidate_count"] == 1
    assert view["critical_alerts"] == 0
    assert view["top_candidate"] == "000001 平安银行"
    assert view["sections"][0] == {
        "title": "持仓风险",
        "summary": "2 只持仓，总市值 25480.00，最高风险 低",
    }


def test_holdings_view_contains_sample_positions_and_risk_decisions():
    assert hasattr(view_models, "build_holdings_view")

    view = view_models.build_holdings_view()

    assert view["summary"] == {
        "holding_count": 2,
        "total_market_value": "25480.00",
        "max_risk_level": "低",
    }
    assert view["holdings"][0] == {
        "symbol": "000001",
        "name": "平安银行",
        "quantity": 1000,
        "market_value": "10300.00",
        "unrealized_return_pct": "3.00%",
        "risk_level": "低",
        "action_advice": "持有",
        "reasons": "风险较低",
    }
    assert view["holdings"][1]["symbol"] == "600519"
    assert view["holdings"][1]["name"] == "贵州茅台"


def test_candidates_view_uses_sample_market_data_and_selector():
    assert hasattr(view_models, "build_candidates_view")

    view = view_models.build_candidates_view()

    assert view["candidate_count"] == 1
    assert view["candidates"][0]["symbol"] == "000001"
    assert view["candidates"][0]["name"] == "平安银行"
    assert view["candidates"][0]["opportunity_score"] == "85.50"
    assert "银行板块涨幅 1.50%" in view["candidates"][0]["reasons"]


def test_backtest_view_summarizes_sample_candidate_forward_return():
    assert hasattr(view_models, "build_backtest_view")

    view = view_models.build_backtest_view()

    assert view["summary"] == {
        "signal_count": 1,
        "win_rate_1d": "N/A",
        "avg_return_1d": "N/A",
        "net_win_rate_1d": "N/A",
        "net_avg_return_1d": "N/A",
        "profit_loss_ratio_1d": "N/A",
        "max_drawdown_1d": "N/A",
        "false_sell_rate_5d": "N/A",
        "missed_rebound_rate_5d": "N/A",
        "transaction_cost_rate": "0.00%",
    }
    assert view["signals"][0]["symbol"] == "000001"
    assert view["signals"][0]["return_1d"] == "N/A"


@pytest.mark.parametrize(
    ("path", "expected_text"),
    [
        ("/holdings", "持仓风险"),
        ("/candidates", "重点候选"),
        ("/backtest", "回测复盘"),
    ],
)
def test_placeholder_pages_render_from_navigation(path: str, expected_text: str):
    client = TestClient(create_app())

    response = client.get(path)

    assert response.status_code == 200
    assert expected_text in response.text


def test_holdings_page_renders_sample_risk_table():
    client = TestClient(create_app())

    response = client.get("/holdings")

    assert response.status_code == 200
    assert "平安银行" in response.text
    assert "贵州茅台" in response.text
    assert "10300.00" in response.text
    assert "持有" in response.text
    assert "页面占位" not in response.text


def test_candidates_page_renders_sample_candidate_list():
    client = TestClient(create_app())

    response = client.get("/candidates")

    assert response.status_code == 200
    assert "000001" in response.text
    assert "平安银行" in response.text
    assert "85.50" in response.text
    assert "银行板块涨幅 1.50%" in response.text
    assert "页面占位" not in response.text


def test_backtest_page_renders_sample_backtest_summary():
    client = TestClient(create_app())

    response = client.get("/backtest")

    assert response.status_code == 200
    assert "1日胜率" in response.text
    assert "最大回撤" in response.text
    assert "盈亏比" in response.text
    assert "交易成本" in response.text
    assert "错误卖出率" in response.text
    assert "错过反弹率" in response.text
    assert "N/A" in response.text
    assert "页面占位" not in response.text
