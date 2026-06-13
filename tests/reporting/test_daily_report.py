from trading_assistant.reporting.daily_report import build_daily_report


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
