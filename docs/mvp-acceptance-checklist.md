# MVP 验收清单

验收证据见 [docs/mvp-acceptance-evidence.md](mvp-acceptance-evidence.md)。真实 AKShare/Tushare、真实 LLM 和真实飞书 Webhook 的端到端稳定性验收按 [docs/integration-acceptance-runbook.md](integration-acceptance-runbook.md) 单独执行。

## M1 数据与持仓底座

- [x] 能读取示例持仓。
- [x] 能读取示例日线、分钟线和板块数据。
- [x] 能区分可交易池、观察池、禁入池和持仓池。

## M2 因子与评分引擎

- [x] 能计算技术、量价、市场和板块因子。
- [x] 能加载权重。
- [x] 能输出可追溯评分。

## M3 持仓风控与卖出规则

- [x] 能识别硬止损。
- [x] 能输出继续持有、收紧止损、减仓、清仓建议。
- [x] 能生成 P0/P1 持仓提醒。

## M4 盘后选股与交易计划

- [x] 能筛选重点候选。
- [x] 能生成买入触发、止损、止盈、仓位和失效条件。
- [x] 能拦截市场环境差、持仓风险高、盈亏比不足的交易计划。

## M5 智能体与报告

- [x] 能用 Mock LLM 结构化公告事件。
- [x] 能用 Mock LLM 结构化新闻题材。
- [x] 能生成固定结构的盘后报告。

## M6 仪表盘与提醒

- [x] 能打开 Web 仪表盘。
- [x] 能展示市场、持仓、候选和提醒摘要。
- [x] 能通过 Webhook 分发 P0/P1 提醒。

## M7 回测与复盘

- [x] 能记录信号。
- [x] 能统计 1/3/5 日收益。
- [x] 能输出胜率和平均收益。

## 风险与技术债

详见 [docs/risk-and-debt-register.md](risk-and-debt-register.md)。

- [x] 所有 P0/P1 风险都有缓解措施。
- [x] 所有外部数据源都有 Mock 或样例数据回退。
- [x] 所有已知技术债都有负责人和复查日期。
- [x] 下一阶段前必须偿还的技术债没有遗漏。
