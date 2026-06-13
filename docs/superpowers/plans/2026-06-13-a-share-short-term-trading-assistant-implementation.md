# A 股保守型短线交易辅助系统实施计划

日期：2026-06-13

## 1. 实施目标

建设第一阶段 MVP：一个可每日运行的 A 股保守型短线交易辅助系统，覆盖持仓风控、市场环境评分、盘后候选股、完整交易计划、盘中分级提醒、智能体解释、仪表盘和回测复盘。

第一阶段不实现自动下单、券商接口、Level-2、逐笔成交、委托队列和自动交易合规报备。

## 2. 技术路线

采用 Python 单仓库，核心交易逻辑全部放在可测试的纯 Python 模块中，Web、定时任务、消息推送和智能体作为外层适配器。

建议技术栈：

- Python 3.11+；
- FastAPI；
- Jinja2；
- SQLAlchemy；
- PostgreSQL；
- Redis；
- pandas；
- numpy；
- AKShare；
- Tushare Pro；
- APScheduler；
- httpx；
- pytest；
- ruff；
- mypy；
- Docker Compose。

## 3. 建议仓库结构

```text
.
├── .env.example
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
├── README.md
├── config/
│   ├── scoring.yml
│   ├── risk.yml
│   └── pools.yml
├── data/
│   ├── samples/
│   └── reports/
├── docs/
│   └── superpowers/
│       ├── specs/
│       └── plans/
├── scripts/
│   ├── run_daily_after_close.py
│   ├── run_intraday_monitor.py
│   ├── import_holdings.py
│   └── seed_sample_data.py
├── src/
│   └── trading_assistant/
│       ├── settings.py
│       ├── logging_config.py
│       ├── domain/
│       ├── db/
│       ├── data_sources/
│       ├── pools/
│       ├── factors/
│       ├── scoring/
│       ├── portfolio/
│       ├── planning/
│       ├── agents/
│       ├── reporting/
│       ├── alerts/
│       ├── backtest/
│       ├── scheduler/
│       └── web/
└── tests/
    ├── data_sources/
    ├── pools/
    ├── factors/
    ├── scoring/
    ├── portfolio/
    ├── planning/
    ├── agents/
    ├── reporting/
    ├── alerts/
    ├── backtest/
    └── web/
```

## 4. 代码边界

- `domain/`：枚举和领域数据模型，不访问数据库、网络或大模型。
- `data_sources/`：拉取并标准化外部数据，不计算交易分数。
- `pools/`：可交易池、观察池、禁入池、持仓池分层。
- `factors/`：把行情、板块、事件、持仓转换成因子。
- `scoring/`：根据权重输出四类评分。
- `portfolio/`：持仓导入、风险判断和卖出动作建议。
- `planning/`：候选股筛选、仓位计算和交易计划。
- `agents/`：文本理解、结构化摘要和自然语言解释。
- `alerts/`：提醒分级、去重和发送。
- `backtest/`：信号记录、回测和指标统计。
- `web/`：展示，不写交易决策逻辑。

## 5. 阶段 0：项目骨架与配置

### 任务 0.1：创建 Python 项目基础

创建文件：

- `pyproject.toml`；
- `.gitignore`；
- `.env.example`；
- `README.md`；
- `src/trading_assistant/__init__.py`；
- `src/trading_assistant/settings.py`；
- `tests/test_settings.py`。

开发内容：

- 配置 Python 版本和依赖；
- 配置 pytest、ruff、mypy；
- 定义 `Settings`；
- 提供本地默认配置。

测试要求：

- `Settings()` 能读取默认值；
- `database_url` 默认为 SQLite；
- `redis_url` 默认为本地 Redis；
- `python -m pytest tests/test_settings.py -v` 通过。

### 任务 0.2：创建配置文件和样例数据

创建文件：

- `config/scoring.yml`；
- `config/risk.yml`；
- `config/pools.yml`；
- `data/samples/holdings.csv`；
- `data/samples/daily_bars.csv`；
- `data/samples/minute_bars.csv`；
- `data/samples/sectors.csv`；
- `data/samples/events.jsonl`；
- `tests/test_config_files.py`。

开发内容：

- 定义四类评分权重；
- 定义仓位、止损、止盈和市场阈值；
- 定义股票池过滤条件；
- 准备最小可运行样例数据。

测试要求：

- 评分配置包含 `portfolio_risk`、`market_environment`、`short_term_opportunity`、`plan_confidence`；
- 每组权重和为 1；
- 风控配置包含单票仓位上限、总仓位上限和硬止损阈值；
- 样例数据可被 pandas 正常读取。

## 6. 阶段 1：M1 数据与持仓底座

### 任务 1.1：领域模型

创建文件：

- `src/trading_assistant/domain/enums.py`；
- `src/trading_assistant/domain/models.py`；
- `tests/test_domain_models.py`。

开发内容：

- 定义 `PoolType`：`TRADABLE`、`WATCH`、`BLOCKED`、`HOLDING`；
- 定义 `RiskLevel`：`LOW`、`MEDIUM`、`HIGH`、`CRITICAL`；
- 定义 `ActionAdvice`：`HOLD`、`TIGHTEN_STOP`、`REDUCE`、`SELL_ON_REBOUND`、`CLEAR_OR_STOP`、`WATCH_FOR_TRIGGER`、`NO_ACTION`；
- 定义 `Holding`；
- 定义 `ScoreBreakdown`；
- 定义 `TradePlan`。

测试要求：

- `Holding.market_value` 正确；
- `Holding.unrealized_return_pct` 正确；
- `TradePlan.reward_risk_ratio` 正确；
- 交易计划必须包含买点、止损、止盈、仓位和失效条件。

### 任务 1.2：数据库会话和仓储

创建文件：

- `src/trading_assistant/db/base.py`；
- `src/trading_assistant/db/models.py`；
- `src/trading_assistant/db/session.py`；
- `src/trading_assistant/db/repositories.py`；
- `tests/db/test_repositories.py`。

开发内容：

- 建立 SQLAlchemy Base；
- 建立 Engine 和 SessionFactory；
- 建立 `HoldingORM`；
- 实现 `HoldingRepository.upsert_holding()`；
- 实现 `HoldingRepository.list_holdings()`。

测试要求：

- 使用 SQLite 内存数据库；
- 能保存持仓；
- 能更新持仓；
- 能按代码排序读取持仓。

### 任务 1.3：持仓 CSV 导入

创建文件：

- `src/trading_assistant/portfolio/importer.py`；
- `scripts/import_holdings.py`；
- `tests/portfolio/test_importer.py`。

开发内容：

- 从 CSV 读取持仓；
- 校验字段：`symbol`、`name`、`quantity`、`cost_price`、`current_price`、`buy_date`、`theme`、`buy_reason`；
- 转成 `Holding` 领域模型；
- 提供 CLI 脚本。

测试要求：

- 能读取 `data/samples/holdings.csv`；
- 能正确解析股票代码为字符串；
- 能正确计算浮盈浮亏。

### 任务 1.4：数据源协议和样例 Provider

创建文件：

- `src/trading_assistant/data_sources/protocols.py`；
- `src/trading_assistant/data_sources/fake_provider.py`；
- `src/trading_assistant/data_sources/ingestion.py`；
- `tests/data_sources/test_fake_provider.py`。

开发内容：

- 定义 `MarketDataProvider` 协议；
- 实现 `get_daily_bars()`；
- 实现 `get_minute_bars()`；
- 实现 `get_sector_snapshot()`；
- 实现样例数据 Provider；
- 实现 `load_market_snapshot()`。

测试要求：

- 能读取日线；
- 能读取分钟线；
- 能读取板块快照；
- 输出字段统一。

### 任务 1.5：AKShare 和 Tushare Provider 外壳

创建文件：

- `src/trading_assistant/data_sources/akshare_provider.py`；
- `src/trading_assistant/data_sources/tushare_provider.py`；
- `tests/data_sources/test_provider_contracts.py`。

开发内容：

- 封装 AKShare 日线数据；
- 封装 Tushare 基础日线接口；
- 真实网络请求不进入单元测试；
- 测试中使用 mock 数据。

测试要求：

- AKShare 字段能标准化为 `trade_date`、`symbol`、`open`、`high`、`low`、`close`、`volume`、`turnover`；
- Tushare Provider 可用 mock client 初始化；
- 无 token 时不影响单元测试。

## 7. 阶段 2：M2 因子与评分引擎

### 任务 2.1：股票池分层

创建文件：

- `src/trading_assistant/pools/classifier.py`；
- `tests/pools/test_classifier.py`。

开发内容：

- ST 股票进入禁入池；
- 退市风险进入禁入池；
- 成交额低于阈值进入禁入池；
- 上市时间不足进入观察池；
- 连续一字板进入观察池；
- 连续跌停进入禁入池；
- 北交所默认观察。

测试要求：

- 正常主板高流动性股票进入可交易池；
- ST 股票进入禁入池；
- 低成交额股票进入禁入池；
- 次新股进入观察池。

### 任务 2.2：核心因子计算

创建文件：

- `src/trading_assistant/factors/technical.py`；
- `src/trading_assistant/factors/volume_price.py`；
- `src/trading_assistant/factors/market.py`；
- `src/trading_assistant/factors/sector.py`；
- `tests/factors/test_core_factors.py`。

开发内容：

- 技术因子：5 日动量、是否站上 5 日均线、ATR；
- 量价因子：成交额放大倍数、上涨是否带量；
- 市场因子：涨跌家数比例、全市场成交额、涨停数、跌停数；
- 板块因子：板块涨幅、成交额、涨停数和龙头股综合排序。

测试要求：

- 用固定样例数据计算确定性结果；
- 动量、成交额放大倍数和涨跌家数比例必须可复现；
- 因子输出使用标准字段名。

### 任务 2.3：权重加载和评分引擎

创建文件：

- `src/trading_assistant/scoring/weights.py`；
- `src/trading_assistant/scoring/engine.py`；
- `tests/scoring/test_engine.py`。

开发内容：

- 从 YAML 加载四套权重；
- 校验每套权重和为 1；
- 实现加权评分；
- 输出总分、组件分和原因列表。

测试要求：

- 权重和不为 1 时抛出错误；
- 输入标准化因子后输出确定性总分；
- 每个组件分可追溯。

## 8. 阶段 3：M3 持仓风控与卖出规则

### 任务 3.1：持仓风险引擎

创建文件：

- `src/trading_assistant/factors/portfolio.py`；
- `src/trading_assistant/portfolio/risk_engine.py`；
- `tests/portfolio/test_risk_engine.py`。

开发内容：

- 计算持仓浮亏/回撤风险因子；
- 根据硬止损、技术破位、资金流出、板块退潮、负面事件、市场环境生成风险分；
- 输出风险等级；
- 输出动作建议。

测试要求：

- 触发硬止损时风险等级为 CRITICAL；
- 技术破位和资金流出会提高风险分；
- 风险分 71 以上输出 `CLEAR_OR_STOP`；
- 风险分 51 到 70 输出 `REDUCE`；
- 风险分 31 到 50 输出 `TIGHTEN_STOP`。

### 任务 3.2：盘中提醒规则

创建文件：

- `src/trading_assistant/alerts/models.py`；
- `src/trading_assistant/alerts/rules.py`；
- `tests/alerts/test_rules.py`。

开发内容：

- 定义 `AlertLevel`：P0、P1、P2、P3；
- 定义 `Alert`；
- 跌破硬止损位触发 P0；
- 接近止损位触发 P1；
- 到达第一止盈位触发 P1；
- 接近买入触发价触发 P2。

测试要求：

- 跌破止损位输出 P0；
- 接近止损位输出 P1；
- 到达止盈位输出 P1；
- 接近买点输出 P2。

## 9. 阶段 4：M4 盘后选股与完整交易计划

### 任务 4.1：候选股筛选

创建文件：

- `src/trading_assistant/planning/candidate_selector.py`；
- `tests/planning/test_candidate_selector.py`。

开发内容：

- 只从可交易池产生候选；
- 短线机会分达到阈值；
- 交易计划可信分达到阈值；
- 按机会分和计划可信分排序；
- 输出重点候选 3 到 8 只。

测试要求：

- 观察池股票不进入可执行候选；
- 禁入池股票不进入候选；
- 低分股票不进入候选；
- 高分可交易股票进入候选。

### 任务 4.2：仓位计算和交易计划生成

创建文件：

- `src/trading_assistant/planning/position_sizing.py`；
- `src/trading_assistant/planning/trade_plan.py`；
- `tests/planning/test_trade_plan.py`。

开发内容：

- 根据机会分、计划可信分、市场分、持仓风险分、止损距离计算仓位；
- 市场环境低于 40 时仓位为 0；
- 持仓风险高于 70 时禁止新增；
- 市场环境 40 到 60 时最多轻仓；
- 止损距离过大时自动降仓；
- 生成买入触发、买入区间、止损、止盈、仓位、失效条件。

测试要求：

- 市场弱时仓位不超过 5%；
- 持仓风险高时仓位为 0；
- 止损位低于买入区间；
- 第一止盈位高于买入区间；
- 盈亏比不达标时计划不可执行。

## 10. 阶段 5：M5 智能体与报告

### 任务 5.1：LLM 客户端抽象和 Mock 客户端

创建文件：

- `src/trading_assistant/agents/llm_client.py`；
- `src/trading_assistant/agents/prompts.py`；
- `tests/agents/test_llm_client.py`。

开发内容：

- 定义 `LLMClient` 协议；
- 实现 `complete_json()`；
- 实现 `MockLLMClient`；
- 所有智能体测试使用 Mock，不依赖外部 API。

测试要求：

- Mock 客户端能返回 JSON 对象；
- 非 JSON 响应抛出错误；
- 智能体不直接访问外部模型。

### 任务 5.2：公告事件和新闻题材智能体

创建文件：

- `src/trading_assistant/agents/event_agent.py`；
- `src/trading_assistant/agents/news_agent.py`；
- `tests/agents/test_event_news_agents.py`。

开发内容：

- 公告事件智能体提取事件类型、情绪、置信度、摘要、风险标签和来源；
- 新闻题材智能体提取题材、情绪、置信度、摘要和相关股票；
- 输出必须结构化；
- 输出必须保留来源字段。

测试要求：

- 减持公告输出负面事件；
- 板块新闻输出题材标签；
- 智能体不能覆盖规则引擎输出。

### 任务 5.3：盘后报告生成

创建文件：

- `src/trading_assistant/reporting/markdown.py`；
- `src/trading_assistant/reporting/daily_report.py`；
- `tests/reporting/test_daily_report.py`。

开发内容：

日报固定包含九段：

1. 今日市场总结；
2. 当前持仓风险；
3. 明日是否适合开新仓；
4. 强势板块与退潮板块；
5. 重点候选股交易计划；
6. 观察候选；
7. 禁入和风险股票；
8. 次日盘中提醒清单；
9. 今日系统信号复盘。

测试要求：

- 报告包含固定标题；
- 空列表输出“无”；
- 报告可写入 `data/reports/`。

## 11. 阶段 6：M6 仪表盘与提醒

### 任务 6.1：消息推送和提醒分发

创建文件：

- `src/trading_assistant/alerts/feishu.py`；
- `src/trading_assistant/alerts/dispatcher.py`；
- `tests/alerts/test_dispatcher.py`。

开发内容：

- 实现飞书 Webhook 发送器；
- 实现提醒分发器；
- 默认只推送 P0 和 P1；
- P2 和 P3 进入仪表盘或汇总推送。

测试要求：

- P0 被推送；
- P1 被推送；
- P2 默认不推送；
- 空 Webhook 不报错。

### 任务 6.2：FastAPI 仪表盘

创建文件：

- `src/trading_assistant/web/app.py`；
- `src/trading_assistant/web/routes.py`；
- `src/trading_assistant/web/view_models.py`；
- `src/trading_assistant/web/templates/base.html`；
- `src/trading_assistant/web/templates/dashboard.html`；
- `src/trading_assistant/web/templates/holdings.html`；
- `src/trading_assistant/web/templates/candidates.html`；
- `src/trading_assistant/web/templates/backtest.html`；
- `src/trading_assistant/web/static/app.css`；
- `tests/web/test_app.py`。

开发内容：

- 建立 FastAPI 应用；
- 建立仪表盘首页；
- 展示市场环境分；
- 展示持仓风险；
- 展示重点候选数量；
- 展示 P0/P1 提醒数量；
- 建立持仓、候选、回测页面骨架。

测试要求：

- `GET /` 返回 200；
- 页面包含 “A 股短线交易辅助系统”；
- 页面包含 “持仓风险”；
- 页面包含 “重点候选”。

### 任务 6.3：定时任务入口

创建文件：

- `src/trading_assistant/scheduler/jobs.py`；
- `scripts/run_daily_after_close.py`；
- `scripts/run_intraday_monitor.py`；
- `tests/scheduler/test_jobs.py`。

开发内容：

- 定义盘后任务；
- 定义晚间智能体报告任务；
- 定义盘中监控任务；
- 定义周末复盘任务；
- 提供 CLI 入口。

测试要求：

- 任务计划包含 `daily_after_close`；
- 任务计划包含 `intraday_monitor`；
- CLI 能输出任务说明。

## 12. 阶段 7：M7 回测与复盘

### 任务 7.1：信号台账

创建文件：

- `src/trading_assistant/backtest/signal_ledger.py`；
- `tests/backtest/test_signal_ledger.py`。

开发内容：

- 记录信号日期；
- 记录股票代码；
- 记录信号类型；
- 记录评分；
- 记录动作建议；
- 输出 DataFrame。

测试要求：

- 能记录候选信号；
- 能记录持仓风控信号；
- 能转成 DataFrame；
- 字段完整。

### 任务 7.2：1/3/5 日收益回测指标

创建文件：

- `src/trading_assistant/backtest/engine.py`；
- `src/trading_assistant/backtest/metrics.py`；
- `tests/backtest/test_engine_metrics.py`。

开发内容：

- 计算信号后 1 日收益；
- 计算信号后 3 日收益；
- 计算信号后 5 日收益；
- 统计 1 日胜率；
- 统计 1/3/5 日平均收益。

测试要求：

- 固定价格序列输出确定性收益；
- 缺失价格数据时跳过该信号；
- 空结果返回 0 指标。

## 13. 阶段 8：部署、运行手册和验收

### 任务 8.1：Docker Compose 和本地启动脚本

创建文件：

- `docker-compose.yml`；
- `scripts/seed_sample_data.py`；
- `tests/test_docker_compose_exists.py`。

开发内容：

- 定义 PostgreSQL 服务；
- 定义 Redis 服务；
- 提供样例数据初始化脚本；
- README 增加本地启动说明。

测试要求：

- Docker Compose 包含 `postgres`；
- Docker Compose 包含 `redis`；
- 样例数据脚本可运行。

### 任务 8.2：MVP 验收清单

创建文件：

- `docs/mvp-acceptance-checklist.md`。

验收清单必须覆盖：

- M1 数据与持仓底座；
- M2 因子与评分引擎；
- M3 持仓风控与卖出规则；
- M4 盘后选股与交易计划；
- M5 智能体与报告；
- M6 仪表盘与提醒；
- M7 回测与复盘。

## 14. 全量验证命令

每个阶段完成后运行：

```powershell
python -m pytest -v
python -m ruff check .
python -m mypy src
```

仪表盘验收：

```powershell
python -m uvicorn trading_assistant.web.app:app --reload --port 8000
```

访问：

```text
http://127.0.0.1:8000
```

页面应显示：

- A 股短线交易辅助系统；
- 市场环境分；
- 持仓风险；
- 重点候选；
- P0/P1 提醒。

## 15. 执行策略

建议使用子代理驱动开发：

1. 每个任务派一个新子代理执行；
2. 子代理只完成一个任务；
3. 主代理在每个任务后 review；
4. 每个任务单独运行测试；
5. 每个任务单独提交；
6. 出现测试失败时先系统化调试，不跳过失败。

如果当前环境没有 `git`，执行者仍按任务边界工作，并记录修改文件和测试结果；安装或恢复 `git` 后再补提交。

## 16. 第一阶段之外的独立计划

以下内容不进入 MVP：

- Level-2 和逐笔成交接入；
- 委托队列和盘口模型；
- 券商接口；
- 自动下单；
- 程序化交易合规报备自动化；
- 本地深度学习预测模型训练；
- 多账户和多策略组合管理。

这些能力需要在 MVP 稳定运行、回测数据积累后分别创建独立设计文档和实施计划。