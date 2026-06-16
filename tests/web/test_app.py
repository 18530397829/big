from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from trading_assistant.domain.enums import ActionAdvice, RiskLevel
from trading_assistant.domain.models import Holding
from trading_assistant.portfolio.risk_engine import PortfolioRiskDecision
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
        "盘中提醒",
        "P1 提醒",
    ]
    missing_labels = [label for label in expected_labels if label not in response.text]
    assert missing_labels == []
    assert "平安银行" in response.text
    assert "25480.00" in response.text
    assert "等待后续任务填充实时数据" not in response.text
    assert "data-freshness" in response.text
    assert "metric-card--quiet" in response.text
    assert "metric-card--critical" not in response.text
    assert 'class="risk-badge risk-badge--low"' in response.text
    assert 'class="workspace-card"' in response.text
    assert 'href="/holdings"' in response.text
    assert "P0/P1" not in response.text
    assert '<a class="card-link" href="/">查看概览</a>' not in response.text
    assert '<a class="card-link" href="/">查看提醒</a>' not in response.text
    assert 'risk-badge--negative' not in response.text
    assert 'class="risk-badge risk-badge--danger">52</span>' in response.text


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
            "data_freshness": "样例数据 / 最近更新 2026-06-12 09:40",
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


def test_navigation_marks_current_page():
    client = TestClient(create_app())

    response = client.get("/candidates")

    assert response.status_code == 200
    assert '<a href="/candidates" aria-current="page">重点候选</a>' in response.text
    assert '<a href="/focus-pool">关注股票池</a>' in response.text
    assert '<a href="/holdings" aria-current="page">' not in response.text


@pytest.mark.parametrize(
    ("path", "expected_nav", "expected_text"),
    [
        ("/market", "市场环境", "银行"),
        ("/intraday", "盘中提醒", "000001 平安银行"),
    ],
)
def test_core_readonly_pages_render_from_navigation(
    path: str,
    expected_nav: str,
    expected_text: str,
):
    client = TestClient(create_app())

    response = client.get(path)

    assert response.status_code == 200
    assert f'<a href="{path}" aria-current="page">{expected_nav}</a>' in response.text
    assert expected_text in response.text
    assert "页面占位" not in response.text


def test_dashboard_uses_module_freshness_and_single_workspace_cta():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "页面生成时间" in response.text
    assert "暂无详情" not in response.text
    assert response.text.count('<a class="card-link" href="/holdings">查看持仓</a>') == 1
    assert response.text.count('<a class="card-link" href="/candidates">查看候选</a>') == 1
    assert '<a class="card-link" href="/market">查看市场</a>' in response.text
    assert '<a class="card-link" href="/intraday">查看提醒</a>' in response.text
    assert "样例数据 / 最近更新 2026-06-12 09:40" in response.text
    assert "样例数据 / 最近板块交易日 2026-06-12" in response.text
    assert "样例数据 / 最近交易日 2026-06-11" in response.text
    assert "样例数据 / 最近信号 2026-06-11" in response.text


@pytest.mark.parametrize(
    ("template_name", "expected_heading"),
    [
        ("holdings.html", "持仓风险"),
        ("candidates.html", "重点候选"),
        ("backtest.html", "回测复盘"),
        ("market.html", "市场环境"),
        ("intraday.html", "盘中提醒"),
        ("focus_pool.html", "关注股票池"),
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
    assert "暂无可用数据。请检查样例数据或任务日志后刷新。" in response.text


def test_dashboard_view_is_built_from_sample_data():
    view = view_models.build_dashboard_view()

    assert view["market_score"] == 52
    assert view["portfolio_risk"] == "低"
    assert view["holding_count"] == 2
    assert view["total_market_value"] == "25480.00"
    assert view["candidate_count"] == 1
    assert view["critical_alerts"] == 0
    assert view["top_candidate"] == "000001 平安银行"
    assert "页面生成时间" in view["page_generated_at"]
    assert view["sections"][1] == {
        "title": "市场环境",
        "summary": "样例板块平均涨幅 0.35%，环境分 52",
        "href": "/market",
        "status": "52",
        "status_key": "danger",
        "action": "查看市场",
        "is_available": True,
        "data_freshness": "样例数据 / 最近板块交易日 2026-06-12",
    }
    assert view["sections"][3] == {
        "title": "盘中提醒",
        "summary": "3 个监控项，P1 0 条",
        "href": "/intraday",
        "status": "0 条",
        "status_key": "low",
        "action": "查看提醒",
        "is_available": True,
        "data_freshness": "样例数据 / 最近更新 2026-06-12 09:40",
    }
    assert view["sections"][0] == {
        "title": "持仓风险",
        "summary": "2 只持仓，总市值 25480.00，最高风险 低",
        "href": "/holdings",
        "status": "低",
        "status_key": "low",
        "action": "查看持仓",
        "is_available": True,
        "data_freshness": "样例数据 / 最近更新 2026-06-12 09:40",
    }


def test_market_view_contains_sector_rows_and_freshness():
    view = view_models.build_market_view()

    assert view["summary"] == {
        "market_score": 52,
        "market_score_key": "danger",
        "average_sector_pct": "0.35%",
        "sector_count": 2,
        "data_freshness": "样例数据 / 最近板块交易日 2026-06-12",
    }
    assert view["sectors"][0] == {
        "sector_name": "银行",
        "sector_type": "industry",
        "pct_chg": "1.50%",
        "pct_tone": "positive",
        "turnover": "9000000000.00",
        "limit_up_count": 2,
        "leader_symbol": "000001",
    }


def test_holdings_view_contains_sample_positions_and_risk_decisions():
    assert hasattr(view_models, "build_holdings_view")

    view = view_models.build_holdings_view()

    assert view["summary"] == {
        "holding_count": 2,
        "total_market_value": "25480.00",
        "max_risk_level": "低",
        "max_risk_level_key": "low",
        "data_freshness": "样例数据 / 最近更新 2026-06-12 09:40",
    }
    assert view["holdings"][0] == {
        "symbol": "000001",
        "name": "平安银行",
        "identity": "000001 平安银行",
        "quantity": 1000,
        "market_value": "10300.00",
        "unrealized_return_pct": "3.00%",
        "return_tone": "positive",
        "risk_level": "低",
        "risk_level_key": "low",
        "risk_sort_key": 0,
        "action_advice": "持有",
        "reasons": "风险较低",
        "row_id": "holding-000001",
    }
    assert view["holdings"][1]["symbol"] == "600519"
    assert view["holdings"][1]["name"] == "贵州茅台"


def test_holdings_view_sorts_highest_risk_first(monkeypatch: pytest.MonkeyPatch):
    holdings = [
        Holding(
            symbol="000001",
            name="低风险",
            quantity=100,
            cost_price=10,
            current_price=10.1,
            buy_date=date(2026, 6, 1),
            theme="银行",
            buy_reason="sample",
        ),
        Holding(
            symbol="600000",
            name="严重风险",
            quantity=100,
            cost_price=10,
            current_price=9.0,
            buy_date=date(2026, 6, 1),
            theme="银行",
            buy_reason="sample",
        ),
    ]
    decisions = [
        PortfolioRiskDecision("000001", 0, RiskLevel.LOW, ActionAdvice.HOLD, ["风险较低"]),
        PortfolioRiskDecision(
            "600000",
            80,
            RiskLevel.CRITICAL,
            ActionAdvice.CLEAR_OR_STOP,
            ["触发硬止损"],
        ),
    ]
    monkeypatch.setattr(view_models, "load_holdings_csv", lambda _: holdings)
    monkeypatch.setattr(view_models, "_risk_decisions", lambda *_: decisions)

    view = view_models.build_holdings_view()

    assert [row["symbol"] for row in view["holdings"]] == ["600000", "000001"]
    assert [row["risk_sort_key"] for row in view["holdings"]] == [3, 0]


def test_candidates_view_uses_sample_market_data_and_selector():
    assert hasattr(view_models, "build_candidates_view")

    view = view_models.build_candidates_view()

    assert view["candidate_count"] == 1
    assert view["outside_observation_count"] == 1
    assert view["candidates"][0]["symbol"] == "000001"
    assert view["candidates"][0]["name"] == "平安银行"
    assert view["candidates"][0]["opportunity_score"] == "85.50"
    assert view["candidates"][0]["score_tone"] == "positive"
    assert view["candidates"][0]["confidence_tone"] == "positive"
    assert view["candidates"][0]["event_label"] == "正面事件"
    assert view["candidates"][0]["summary_reason"] == "银行板块涨幅 1.50%"
    assert view["candidates"][0]["detail_id"] == "candidate-000001"
    assert view["candidates"][0]["holding_href"] == "/holdings#holding-000001"
    assert view["candidates"][0]["backtest_href"] == "/backtest#signal-000001"
    assert view["candidates"][0]["reason_items"] == [
        "银行板块涨幅 1.50%",
        "日线涨幅 3.00%",
        "正面事件",
    ]
    assert "银行板块涨幅 1.50%" in view["candidates"][0]["reasons"]
    assert view["outside_observations"][0]["symbol"] == "300001"
    assert view["outside_observations"][0]["pool_scope_label"] == "池外观察"
    assert "2026-06-11" in view["data_freshness"]


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
        "data_freshness": "样例数据 / 最近信号 2026-06-11",
        "has_enough_metrics": False,
        "insufficient_metrics_message": (
            "当前 1 条信号，1 日后续收益可用 0 条；"
            "至少需要 1 条带后续收益的信号完成基础胜率统计。"
            "正式复盘建议覆盖 60 个交易日历史样本。"
        ),
    }
    assert view["signals"][0]["symbol"] == "000001"
    assert view["signals"][0]["identity"] == "000001 平安银行"
    assert view["signals"][0]["return_1d"] == "N/A"
    assert view["signals"][0]["return_1d_tone"] == "neutral"
    assert view["signals"][0]["max_return_5d_tone"] == "neutral"
    assert view["signals"][0]["row_id"] == "signal-000001"


@pytest.mark.parametrize(
    ("path", "expected_text"),
    [
        ("/holdings", "持仓风险"),
        ("/candidates", "重点候选"),
        ("/backtest", "回测复盘"),
        ("/market", "市场环境"),
        ("/intraday", "盘中提醒"),
        ("/focus-pool", "关注股票池"),
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
    assert 'class="data-table-shell"' in response.text
    assert 'tabindex="0"' in response.text
    assert 'aria-label="持仓明细横向滚动表格"' in response.text
    assert 'class="data-table"' in response.text
    assert '<th scope="col" class="identity-cell">标的</th>' in response.text
    assert '<td class="identity-cell">000001 平安银行</td>' in response.text
    assert 'id="holding-000001"' in response.text
    assert 'class="numeric tone-positive"' in response.text
    assert 'class="risk-badge risk-badge--low"' in response.text


def test_candidates_page_renders_sample_candidate_list():
    client = TestClient(create_app())

    response = client.get("/candidates")

    assert response.status_code == 200
    assert "000001" in response.text
    assert "平安银行" in response.text
    assert "85.50" in response.text
    assert "银行板块涨幅 1.50%" in response.text
    assert "正面事件" in response.text
    assert "事件 positive" not in response.text
    assert "页面占位" not in response.text
    assert 'id="candidate-000001"' in response.text
    assert 'class="candidate-card"' in response.text
    assert "池外观察" in response.text
    assert "300001" in response.text
    assert "<summary>查看触发条件</summary>" in response.text
    assert 'href="/holdings#holding-000001"' in response.text
    assert 'href="/backtest#signal-000001"' in response.text


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
    assert "样本不足" in response.text
    assert "当前 1 条信号" in response.text
    assert "1 日后续收益可用 0 条" in response.text
    assert "至少需要 1 条带后续收益" in response.text
    assert "60 个交易日" in response.text
    assert '<a class="card-link" href="/candidates">查看候选</a>' in response.text
    assert response.text.count("N/A") < 9
    assert "页面占位" not in response.text
    assert 'class="metric-card metric-card--muted"' in response.text
    assert 'class="data-table-shell"' in response.text
    assert 'aria-label="样例信号回测横向滚动表格"' in response.text
    assert 'class="data-table"' in response.text
    assert '<th scope="col" class="identity-cell">标的</th>' in response.text
    assert '<td class="identity-cell">000001 平安银行</td>' in response.text
    assert 'id="signal-000001"' in response.text
    assert 'class="numeric tone-neutral"' in response.text


def test_intraday_view_contains_watch_items_and_priority_keys():
    view = view_models.build_intraday_monitor_view()

    assert view["data_freshness"] == "样例数据 / 最近更新 2026-06-12 09:40"
    assert view["items"][0] == {
        "symbol": "000001",
        "name": "平安银行",
        "identity": "000001 平安银行",
        "latest_price": "10.36",
        "change_pct": "0.58%",
        "change_tone": "positive",
        "priority": "P2",
        "priority_key": "medium",
    }


def test_intraday_page_renders_sample_watch_table():
    client = TestClient(create_app())

    response = client.get("/intraday")

    assert response.status_code == 200
    assert "P1 0 条" in response.text
    assert "000001 平安银行" in response.text
    assert "10.36" in response.text
    assert '<th scope="col" class="identity-cell">标的</th>' in response.text
    assert '<td class="identity-cell">000001 平安银行</td>' in response.text
    assert 'class="risk-badge risk-badge--medium">P2</span>' in response.text


def test_focus_pool_view_contains_sample_rows_and_summary():
    view = view_models.build_focus_pool_view()

    assert view["summary"] == {
        "total_count": 3,
        "active_count": 2,
        "paused_count": 0,
        "archived_count": 1,
    }
    assert view["focus_stocks"][0] == {
        "symbol": "000001",
        "name": "平安银行",
        "display_name": "平安银行",
        "focus_reason": "银行主线仍强",
        "tags": ["银行", "低估"],
        "tags_label": "银行、低估",
        "priority": 5,
        "status": "active",
        "status_label": "启用",
        "status_key": "positive",
    }


def test_focus_pool_page_renders_sample_rows():
    client = TestClient(create_app())

    response = client.get("/focus-pool")

    assert response.status_code == 200
    assert '<a href="/focus-pool" aria-current="page">关注股票池</a>' in response.text
    assert "平安银行" in response.text
    assert "银行主线仍强" in response.text
    assert "批量导入" in response.text
    assert 'name="mode"' in response.text


def test_focus_pool_import_uploads_csv_to_temp_database(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    database_path = tmp_path / "focus.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    client = TestClient(create_app())

    response = client.post(
        "/focus-pool/import",
        data={"mode": "merge"},
        files={
            "file": (
                "focus_pool.csv",
                "symbol,name,focus_reason,tags,priority,status\n"
                "SZ000002,万科A,地产修复,地产|低位,4,active\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    assert "已导入 1 只关注股票" in response.text
    assert "000002" in response.text
    assert "万科A" in response.text


def test_focus_pool_import_validation_error_does_not_write_rows(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    database_path = tmp_path / "focus.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    client = TestClient(create_app())

    response = client.post(
        "/focus-pool/import",
        data={"mode": "merge"},
        files={"file": ("focus_pool.csv", "symbol,priority\n000001,9\n", "text/csv")},
    )

    assert response.status_code == 400
    assert "priority must be between 1 and 5" in response.text
    follow_up = client.get("/focus-pool")
    assert "000001" not in follow_up.text


def test_css_keeps_product_ui_and_mobile_identity_column_rules():
    css = Path("src/trading_assistant/web/static/app.css").read_text(encoding="utf-8")

    assert "clamp(" not in css
    assert "--shadow-raised" not in css
    assert "min-height: 44px;" in css
    assert ".identity-cell" in css
    assert "position: sticky;" in css
    assert "left: 0;" in css


def test_product_and_design_docs_capture_project_context():
    product = Path("PRODUCT.md").read_text(encoding="utf-8")
    design = Path("DESIGN.md").read_text(encoding="utf-8")

    assert "## Register" in product
    assert "product" in product
    assert "有一定技术和交易经验" in product
    assert "克制" in product
    assert "## Design Principles" in product
    assert "## Accessibility & Inclusion" in product
    assert "## Color" in design
    assert "## Typography" in design
    assert "数据新鲜度" in design


@pytest.mark.parametrize(
    ("path", "builder_name", "empty_view", "expected_text"),
    [
        (
            "/holdings",
            "build_holdings_view",
            {
                "summary": {
                    "holding_count": 0,
                    "total_market_value": "0.00",
                    "max_risk_level": "低",
                    "max_risk_level_key": "low",
                    "data_freshness": "样例数据 / 暂无持仓",
                },
                "holdings": [],
            },
            "暂无持仓数据。请先导入持仓后再查看风险。",
        ),
        (
            "/candidates",
            "build_candidates_view",
            {
                "candidate_count": 0,
                "data_freshness": "样例数据 / 暂无候选",
                "candidates": [],
            },
            "暂无候选标的。请先运行盘后选股任务。",
        ),
        (
            "/backtest",
            "build_backtest_view",
            {
                "summary": {
                    "signal_count": 0,
                    "win_rate_1d": "N/A",
                    "avg_return_1d": "N/A",
                    "net_win_rate_1d": "N/A",
                    "net_avg_return_1d": "N/A",
                    "profit_loss_ratio_1d": "N/A",
                    "max_drawdown_1d": "N/A",
                    "false_sell_rate_5d": "N/A",
                    "missed_rebound_rate_5d": "N/A",
                    "transaction_cost_rate": "0.00%",
                    "data_freshness": "样例数据 / 暂无信号",
                    "has_enough_metrics": False,
                    "insufficient_metrics_message": (
                        "当前 0 条信号，1 日后续收益可用 0 条；"
                        "至少需要 1 条带后续收益的信号完成基础胜率统计。"
                        "正式复盘建议覆盖 60 个交易日历史样本。"
                    ),
                },
                "signals": [],
            },
            "暂无回测信号。请先生成候选信号后再查看复盘。",
        ),
        (
            "/market",
            "build_market_view",
            {
                "summary": {
                    "market_score": 50,
                    "market_score_key": "neutral",
                    "average_sector_pct": "0.00%",
                    "sector_count": 0,
                    "data_freshness": "样例数据 / 暂无板块交易日",
                },
                "sectors": [],
            },
            "暂无板块数据。请先运行盘后任务或检查样例数据。",
        ),
        (
            "/intraday",
            "build_intraday_monitor_view",
            {
                "watch_items": 0,
                "critical_alerts": 0,
                "priority_label": "P1 提醒",
                "critical_label": "P1 0 条",
                "data_freshness": "样例数据 / 暂无分钟数据",
                "items": [],
            },
            "暂无盘中监控项。请先导入持仓后再查看提醒。",
        ),
    ],
)
def test_detail_pages_render_empty_states(
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    builder_name: str,
    empty_view: dict[str, object],
    expected_text: str,
):
    from trading_assistant.web import routes

    monkeypatch.setattr(routes, builder_name, lambda: empty_view)
    client = TestClient(create_app())

    response = client.get(path)

    assert response.status_code == 200
    assert 'class="empty-state"' in response.text
    assert expected_text in response.text
