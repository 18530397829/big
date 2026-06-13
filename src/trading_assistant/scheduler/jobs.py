def build_job_plan() -> dict[str, str]:
    return {
        "daily_after_close": "15:30 拉取行情、计算因子、生成评分、生成交易计划和日报",
        "evening_agent_report": "20:30 处理公告新闻、补充智能体解释",
        "intraday_monitor": "交易时段每 5 分钟检查持仓和候选股关键价位",
        "weekly_review": "周末统计信号表现、回撤、胜率和误判案例",
    }
