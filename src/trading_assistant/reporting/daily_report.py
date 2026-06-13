from trading_assistant.reporting.markdown import bullet_list


def build_daily_report(
    *,
    trade_date: str,
    market_summary: str,
    holdings: list[str],
    candidates: list[str],
    risks: list[str],
) -> str:
    return "\n".join(
        [
            f"# A 股短线交易辅助日报 {trade_date}",
            "",
            "## 今日市场总结",
            market_summary,
            "",
            "## 当前持仓风险",
            bullet_list(holdings),
            "",
            "## 明日是否适合开新仓",
            "由市场环境分、持仓风险分和总仓位共同决定。",
            "",
            "## 强势板块与退潮板块",
            "由板块强度因子和智能体题材摘要生成。",
            "",
            "## 重点候选股交易计划",
            bullet_list(candidates),
            "",
            "## 禁入和风险股票",
            bullet_list(risks),
            "",
            "## 次日盘中提醒清单",
            "P0/P1 通过消息推送，P2/P3 进入仪表盘汇总。",
            "",
            "## 今日系统信号复盘",
            "由回测模块在收盘后更新。",
        ]
    )
