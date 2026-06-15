from trading_assistant.reporting import build_daily_report as public_build_daily_report
from trading_assistant.reporting.daily_report import build_daily_report
from trading_assistant.reporting.markdown import bullet_list


def test_public_package_api_exports_build_daily_report():
    assert public_build_daily_report is build_daily_report


def test_bullet_list_renders_empty_list_as_none():
    assert bullet_list([]) == "- 无"


def test_bullet_list_renders_each_item_on_its_own_line():
    assert bullet_list(["000001 继续持有。", "600519 观察。"]) == (
        "- 000001 继续持有。\n"
        "- 600519 观察。"
    )


def test_build_daily_report_contains_required_sections():
    report = build_daily_report(
        trade_date="2026-06-12",
        market_summary="市场成交额放大，涨多跌少。",
        holdings=["000001 风险低，继续持有。"],
        candidates=["000001 触发价 10.60，止损 10.20。"],
        risks=["600519 板块退潮，观察。"],
    )

    assert "## 今日市场总结" in report
    assert "## 当前持仓风险" in report
    assert "## 重点候选股交易计划" in report


def test_build_daily_report_renders_holdings_candidates_and_risks_as_bullets():
    report = build_daily_report(
        trade_date="2026-06-12",
        market_summary="市场成交额放大，涨多跌少。",
        holdings=["000001 风险低，继续持有。", "000002 仓位过高，降仓。"],
        candidates=["300001 触发价 12.30，止损 11.80。"],
        risks=["600519 板块退潮，观察。"],
    )

    assert (
        "## 当前持仓风险\n"
        "- 000001 风险低，继续持有。\n"
        "- 000002 仓位过高，降仓。\n"
        "\n"
        "## 明日是否适合开新仓"
    ) in report
    assert (
        "## 重点候选股交易计划\n"
        "- 300001 触发价 12.30，止损 11.80。\n"
        "\n"
        "## 禁入和风险股票"
    ) in report
    assert (
        "## 禁入和风险股票\n"
        "- 600519 板块退潮，观察。\n"
        "\n"
        "## 次日盘中提醒清单"
    ) in report


def test_build_daily_report_contains_all_fixed_sections_in_order():
    report = build_daily_report(
        trade_date="2026-06-12",
        market_summary="市场成交额放大，涨多跌少。",
        holdings=[],
        candidates=[],
        risks=[],
    )

    expected_sections = [
        "# A 股短线交易辅助日报 2026-06-12",
        "## 今日市场总结",
        "## 当前持仓风险",
        "## 明日是否适合开新仓",
        "## 强势板块与退潮板块",
        "## 重点候选股交易计划",
        "## 禁入和风险股票",
        "## 次日盘中提醒清单",
        "## 今日系统信号复盘",
    ]

    positions = [report.index(section) for section in expected_sections]
    assert positions == sorted(positions)
