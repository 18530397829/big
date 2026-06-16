# MVP 验收证据

验收日期：2026-06-15

## 本轮自动化验证

在 Windows PowerShell 中必须使用项目虚拟环境执行命令；当前系统 `python` 指向 Windows Store 占位程序。

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
```

最近一次执行结果：

- `pytest`：156 passed，1 warning。
- `ruff`：All checks passed。
- `mypy`：Success，60 个源文件无类型错误。

## 验收项与证据

| 模块 | 验收项 | 证据 |
| --- | --- | --- |
| M1 数据与持仓底座 | 能读取示例持仓 | `tests/portfolio/test_importer.py`、`tests/db/test_repositories.py`、`tests/scripts/test_entrypoints.py` |
| M1 数据与持仓底座 | 能读取示例日线、分钟线和板块数据 | `tests/web/test_app.py`、`tests/factors/test_core_factors.py`、`data/samples/daily_bars.csv`、`data/samples/minute_bars.csv`、`data/samples/sectors.csv` |
| M1 数据与持仓底座 | 能使用 AKShare 历史数据支撑本地验收样本 | `data/samples/akshare_acceptance_daily_bars.csv`、`tests/data_sources/test_acceptance_samples.py` |
| M1 数据与持仓底座 | 能区分可交易池、观察池、禁入池和持仓池 | `tests/pools/test_classifier.py`、`tests/test_domain_models.py` |
| M2 因子与评分引擎 | 能计算技术、量价、市场和板块因子 | `tests/factors/test_core_factors.py`、`tests/scoring/test_engine.py` |
| M2 因子与评分引擎 | 能加载权重 | `tests/scoring/test_engine.py`、`config/scoring_weights.yaml` |
| M2 因子与评分引擎 | 能输出可追溯评分 | `tests/scoring/test_engine.py` |
| M3 持仓风控与卖出规则 | 能识别硬止损 | `tests/portfolio/test_risk_engine.py` |
| M3 持仓风控与卖出规则 | 能输出继续持有、收紧止损、减仓、清仓建议 | `tests/portfolio/test_risk_engine.py`、`tests/web/test_app.py` |
| M3 持仓风控与卖出规则 | 能生成 P0/P1 持仓提醒 | `tests/alerts/test_rules.py`、`tests/scheduler/test_jobs.py` |
| M4 盘后选股与交易计划 | 能筛选重点候选 | `tests/planning/test_candidate_selector.py`、`tests/web/test_app.py` |
| M4 盘后选股与交易计划 | 能生成买入触发、止损、止盈、仓位和失效条件 | `tests/planning/test_trade_plan.py` |
| M4 盘后选股与交易计划 | 能拦截市场环境差、持仓风险高、盈亏比不足的交易计划 | `tests/planning/test_trade_plan.py` |
| M5 智能体与报告 | 能用 Mock LLM 结构化公告事件 | `tests/agents/test_event_news_agents.py` |
| M5 智能体与报告 | 能用 Mock LLM 结构化新闻题材 | `tests/agents/test_event_news_agents.py` |
| M5 智能体与报告 | 能生成固定结构的盘后报告 | `tests/reporting/test_daily_report.py`、`tests/scripts/test_entrypoints.py` |
| M6 仪表盘与提醒 | 能打开 Web 仪表盘 | `tests/web/test_app.py` |
| M6 仪表盘与提醒 | 能展示市场、持仓、候选和提醒摘要 | `tests/web/test_app.py` |
| M6 仪表盘与提醒 | 能通过 Webhook 分发 P0/P1 提醒 | `tests/alerts/test_feishu.py`、`tests/alerts/test_dispatcher.py` |
| M7 回测与复盘 | 能记录信号 | `tests/backtest/test_signal_ledger.py` |
| M7 回测与复盘 | 能统计 1/3/5 日收益 | `tests/backtest/test_engine_metrics.py` |
| M7 回测与复盘 | 能输出胜率和平均收益 | `tests/backtest/test_engine_metrics.py`、`tests/web/test_app.py` |
| 风险与技术债 | 所有 P0/P1 风险都有缓解措施 | `docs/risk-and-debt-register.md` |
| 风险与技术债 | 所有外部数据源都有 Mock 或样例数据回退 | `tests/data_sources/test_fake_provider.py`、`tests/data_sources/test_provider_contracts.py`、`data/samples/` |
| 风险与技术债 | 所有已知技术债都有负责人和复查日期 | `docs/risk-and-debt-register.md` |
| 风险与技术债 | 下一阶段前必须偿还的技术债没有遗漏 | `docs/risk-and-debt-register.md`、`tests/backtest/test_engine_metrics.py` |

## 真实外部链路状态

核心真实外部链路已按 [docs/integration-acceptance-runbook.md](integration-acceptance-runbook.md) 执行并归档。当前第一阶段核心准入口径为 `AKShare + 本地 LLM + 飞书`，Tushare 为可选增强项，不阻断核心业务闭环。

最新核心真实验收报告：

- 报告文件：`data/reports/integration-core-akshare-llm-feishu-retry-local/integration-acceptance-report.json`
- `AKShare`：passed，样本标的 `000001`、`600519`，返回 58 行真实日线数据。
- `LLM`：passed，本地 OpenAI 兼容接口 `http://127.0.0.1:8317/v1`，模型 `gpt-5.4-mini`，完成 3 条结构化样本和 1 条低信息量样本降级检查。
- `飞书`：passed，测试群收到 P0、P1 和 SUMMARY 共 3 条消息。
- `Tushare`：skipped，`required=false`，当前不参与核心准入；如后续开通 `daily` 权限，可作为增强数据源单独验收。

AKShare 本地历史验收样本：

- 文件：`data/samples/akshare_acceptance_daily_bars.csv`
- 来源：真实 AKShare 日线接口。
- 区间：2024-01-02 至 2024-06-14。
- 标的：`000001`、`600519`。
- 规模：214 行，每个标的 107 个交易日。
- 字段：`trade_date`、`symbol`、`open`、`high`、`low`、`close`、`volume`、`turnover`。
