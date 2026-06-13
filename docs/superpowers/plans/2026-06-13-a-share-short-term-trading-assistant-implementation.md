# A 股保守型短线交易辅助系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建设第一阶段 MVP：一个可每日运行的 A 股保守型短线交易辅助系统，覆盖持仓风控、市场环境评分、盘后候选股、完整交易计划、盘中分级提醒、智能体解释、仪表盘和回测复盘。

**Architecture:** 采用 Python 单仓库，核心交易逻辑全部放在可测试的纯 Python 模块中，Web、定时任务、消息推送和智能体只是外层适配器。第一阶段以规则因子和回测闭环为核心，大模型只做公告、新闻、题材、风险和报告解释，不直接决定买卖。

**Tech Stack:** Python 3.11+、FastAPI、Jinja2、SQLAlchemy、PostgreSQL、Redis、pandas、numpy、AKShare、Tushare Pro、APScheduler、httpx、pytest、ruff、mypy、Docker Compose。

---

## 1. 计划范围

本计划只覆盖第一阶段 MVP，不实现自动下单、券商接口、Level-2、逐笔成交、委托队列和自动交易合规报备。

第一阶段必须交付：

- M1：数据与持仓底座；
- M2：因子与评分引擎；
- M3：持仓风控与卖出规则；
- M4：盘后选股与交易计划；
- M5：智能体与报告；
- M6：仪表盘与提醒；
- M7：回测与复盘。

后续专业行情、半自动交易和本地深度学习模型单独开计划。

### 1.1 MVP 最小闭环

虽然完整第一阶段包含 M1 到 M7，但开发执行必须先打通一条最小闭环，避免先做大量外围能力却无法验证交易辅助价值。

最小闭环顺序：

1. 样例持仓和样例行情可导入；
2. 可生成持仓风险分和市场环境分；
3. 可从样例股票池生成 3 到 8 只重点候选；
4. 每只重点候选都有买入触发、止损、止盈、仓位和失效条件；
5. 可生成一份盘后 Markdown 报告；
6. 可触发至少一种 P0/P1 风险提醒；
7. 可把信号写入信号台账；
8. 可统计信号后 1、3、5 日表现。

最小闭环完成前，不接入真实券商、不接入 Level-2、不训练本地预测模型、不做多账户权限系统。

### 1.2 迭代时间表

建议按 5 个迭代推进，每个迭代结束都要能演示和验收。

| 迭代 | 建议周期 | 目标 | 对应任务 |
| --- | --- | --- | --- |
| Sprint 0 | 2 到 3 天 | 项目骨架、配置、样例数据、CI 检查 | Task 0.1、0.2 |
| Sprint 1 | 1 周 | 数据、持仓、股票池和基础因子闭环 | Task 1.1 到 2.2 |
| Sprint 2 | 1 周 | 四类评分、持仓风控、盘中提醒规则 | Task 2.3、3.1、3.2 |
| Sprint 3 | 1 周 | 候选股、交易计划、盘后报告和 Mock 智能体 | Task 4.1 到 5.3 |
| Sprint 4 | 1 周 | 仪表盘、推送、调度、信号台账、回测和运行手册 | Task 6.1 到 8.2 |

如果实际人力不足，优先压缩智能体解释和仪表盘美化，不压缩持仓风控、信号台账和回测。

### 1.3 分层交付口径

每个迭代按后端、前端、测试、DevOps 四条线验收：

- 后端：领域模型、规则引擎、数据源适配、报告生成、API 和调度入口；
- 前端：仪表盘信息架构、持仓页、候选股页、交易计划页、回测页；
- 测试：单元测试、样例数据集成测试、盘后流程测试、提醒规则测试、回测指标测试；
- DevOps：环境变量、Docker Compose、日志、CI、备份、运行手册和故障排查清单。

核心交易逻辑必须先有测试再有实现；外部数据源、LLM 和推送服务必须有 Mock，确保本地和 CI 不依赖外部服务。

### 1.4 非功能落地要求

第一阶段的非功能要求不单独做成“大平台工程”，而是分散落实到每个里程碑中。

- 性能：盘后最小闭环目标 10 分钟内完成，完整盘后流程目标 30 分钟内完成；盘中 P0/P1 提醒从数据刷新到生成提醒目标不超过 60 秒。
- 安全：真实 Token、Webhook 和账户数据只能来自 `.env` 或本地受控配置，不进入 Git；局域网以外访问前必须增加认证和 HTTPS。
- 可扩展：数据源、LLM、推送渠道都通过接口抽象接入，新增实现不得改动核心规则。
- 可维护：交易规则、阈值、权重和提示词都必须版本化；新增因子必须同时有测试、解释和回测记录。
- 可观测：盘后任务、盘中任务、智能体任务和回测任务都必须记录结构化任务日志。
- 审计：所有信号、提醒、人工处理结果和规则版本必须可追溯，后续半自动交易前再扩展为完整合规审计。

### 1.5 共享对话要求覆盖矩阵

本计划对共享对话中提到的 8 类优化要求做如下覆盖，后续审阅时按本表检查是否遗漏。

| 共享对话要求 | 已补充位置 | 覆盖说明 |
| --- | --- | --- |
| 审查并完善需求设计文档，覆盖完整业务逻辑、边界条件、非功能需求 | 需求设计 7.6、7.7、7.8，实施计划 1.4 | 盘后、盘中、复盘主流程构成完整业务逻辑；数据、标的、持仓、智能体边界单列；性能、安全、可扩展性、可维护性、可观测性和审计进入非功能落地要求。 |
| 优化并拆分第一阶段 MVP 目标，确保可落地、可验证、最小闭环 | 需求设计 11，实施计划 1.1 | 将第一阶段拆成“导入数据 -> 风险评分 -> 市场评分 -> 候选与交易计划 -> 报告 -> 提醒 -> 信号台账 -> 1/3/5 日回测”的最小闭环。 |
| 将整体系统拆分为模块架构 | 需求设计 7.2、实施计划 3 和 3.1 | 明确 data_sources、factors、scoring、portfolio、planning、agents、alerts、backtest、web 等模块边界。 |
| 输出详细分层架构设计，覆盖前端、后端、数据、基础设施 | 需求设计 7.5，实施计划 3.1 | 将前端展示层、后端应用层、领域规则层、数据访问层、智能体解释层、基础设施层映射到目录和禁止事项。 |
| 将 MVP 拆分为可执行的开发里程碑与迭代计划 | 实施计划 1.2、4 | 增加 Sprint 0 到 Sprint 4 的开发里程碑和迭代计划，并保留阶段 0 到阶段 8 的执行顺序。 |
| 为每个阶段提供具体开发任务清单，按后端、前端、测试、DevOps 拆分 | 实施计划 1.3、阶段 0 到阶段 8 | 每个 Task 保留文件、测试、实现、验证和提交步骤；1.3 单列后端、前端、测试、DevOps 的分层交付口径。 |
| 识别潜在风险与技术债务 | 需求设计 13.1、实施计划 8.5 | 补充数据风险、策略风险、工程风险、合规风险和技术债治理原则，并新增风险与技术债登记表任务。 |
| 提出优化建议与最佳实践 | 需求设计 7.8、13.1，实施计划 1.4、3.2、8.3 到 8.5 | 明确 Mock 外部依赖、配置化阈值、结构化日志、信号可追溯、规则版本化、运行手册、数据质量检查和风险债务登记等最佳实践。 |

## 2. 仓库结构

执行计划前，仓库从空目录开始。建议创建以下结构。

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
│   │   ├── holdings.csv
│   │   ├── daily_bars.csv
│   │   ├── minute_bars.csv
│   │   ├── sectors.csv
│   │   └── events.jsonl
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
│       ├── __init__.py
│       ├── settings.py
│       ├── logging_config.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── enums.py
│       │   └── models.py
│       ├── db/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── models.py
│       │   ├── repositories.py
│       │   └── session.py
│       ├── data_sources/
│       │   ├── __init__.py
│       │   ├── protocols.py
│       │   ├── fake_provider.py
│       │   ├── akshare_provider.py
│       │   ├── tushare_provider.py
│       │   └── ingestion.py
│       ├── pools/
│       │   ├── __init__.py
│       │   └── classifier.py
│       ├── factors/
│       │   ├── __init__.py
│       │   ├── market.py
│       │   ├── sector.py
│       │   ├── technical.py
│       │   ├── volume_price.py
│       │   ├── event.py
│       │   └── portfolio.py
│       ├── scoring/
│       │   ├── __init__.py
│       │   ├── weights.py
│       │   └── engine.py
│       ├── portfolio/
│       │   ├── __init__.py
│       │   ├── importer.py
│       │   └── risk_engine.py
│       ├── planning/
│       │   ├── __init__.py
│       │   ├── candidate_selector.py
│       │   ├── position_sizing.py
│       │   └── trade_plan.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── llm_client.py
│       │   ├── prompts.py
│       │   ├── event_agent.py
│       │   ├── news_agent.py
│       │   ├── portfolio_agent.py
│       │   ├── trade_plan_agent.py
│       │   └── review_agent.py
│       ├── reporting/
│       │   ├── __init__.py
│       │   ├── daily_report.py
│       │   └── markdown.py
│       ├── alerts/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── rules.py
│       │   ├── feishu.py
│       │   └── dispatcher.py
│       ├── backtest/
│       │   ├── __init__.py
│       │   ├── signal_ledger.py
│       │   ├── engine.py
│       │   └── metrics.py
│       ├── scheduler/
│       │   ├── __init__.py
│       │   └── jobs.py
│       └── web/
│           ├── __init__.py
│           ├── app.py
│           ├── routes.py
│           ├── view_models.py
│           ├── static/
│           │   └── app.css
│           └── templates/
│               ├── base.html
│               ├── dashboard.html
│               ├── holdings.html
│               ├── candidates.html
│               └── backtest.html
└── tests/
    ├── conftest.py
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

## 3. 代码边界

核心规则必须保持可测试：

- `domain/`：只放枚举和数据模型，不访问数据库、网络和大模型。
- `data_sources/`：只负责拉取和标准化外部数据，不计算交易分数。
- `factors/`：只负责把行情、板块、事件、持仓转换成因子。
- `scoring/`：只负责根据权重打分。
- `portfolio/`：只负责持仓导入、风险判断和卖出动作建议。
- `planning/`：只负责候选股筛选、仓位和交易计划。
- `agents/`：只负责文本理解、结构化摘要和自然语言解释。
- `alerts/`：只负责提醒分级、去重和发送。
- `backtest/`：只负责信号记录、回测和指标。
- `web/`：只负责展示，不写交易决策逻辑。

### 3.1 分层架构到目录映射

| 层级 | 目录或组件 | 主要职责 | 禁止事项 |
| --- | --- | --- | --- |
| 前端展示层 | `web/templates`、`web/static`、`web/view_models.py` | 展示持仓、候选股、交易计划、提醒、回测摘要 | 不计算评分，不修改风控阈值 |
| 后端应用层 | `web/app.py`、`web/routes.py`、`scheduler/jobs.py`、`scripts/` | API、页面路由、任务编排、命令入口 | 不写具体交易规则 |
| 领域规则层 | `factors/`、`scoring/`、`portfolio/`、`planning/`、`alerts/rules.py` | 因子、评分、风控、候选、仓位、提醒规则 | 不直接访问外部网络和 LLM |
| 数据访问层 | `data_sources/`、`db/`、`backtest/signal_ledger.py` | 数据源协议、数据清洗、持久化、信号台账 | 不决定买卖动作 |
| 智能体解释层 | `agents/`、`reporting/` | 结构化公告新闻、解释评分、生成报告 | 不覆盖硬风控，不生成新的买卖规则 |
| 基础设施层 | `docker-compose.yml`、`.env.example`、`config/`、`docs/ops-runbook.md` | 本地依赖、配置、运行手册、运维约束 | 不保存真实密钥 |

### 3.2 跨层接口约定

- 领域层输入和输出优先使用 dataclass 或 Pydantic 模型，避免裸 dict 在多层传递；
- 数据源输出必须带 `source`、`as_of`、`trade_date` 和质量状态；
- 评分输出必须带总分、组件分、触发因子和解释原因；
- 交易计划输出必须带买入触发、止损、止盈、仓位、失效条件和风险等级；
- 智能体输出必须是结构化 JSON 或固定 Markdown 模板，不返回不可解析的自由文本给核心流程；
- Web 层只读取 view model，不直接调用外部数据源和 LLM。

## 4. 执行顺序总览

1. 阶段 0：项目骨架与配置。
2. 阶段 1：M1 数据与持仓底座。
3. 阶段 2：M2 因子与评分引擎。
4. 阶段 3：M3 持仓风控与卖出规则。
5. 阶段 4：M4 盘后选股与完整交易计划。
6. 阶段 5：M5 智能体与报告。
7. 阶段 6：M6 仪表盘与提醒。
8. 阶段 7：M7 回测与复盘。
9. 阶段 8：部署、运行手册和验收。

每个任务按 TDD 执行：先写失败测试，再写最小实现，再运行测试，再提交。

---

## 阶段 0：项目骨架与配置

### Task 0.1: 创建 Python 项目基础

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Create: `src/trading_assistant/__init__.py`
- Create: `src/trading_assistant/settings.py`
- Create: `tests/test_settings.py`

- [ ] **Step 1: 写配置测试**

创建 `tests/test_settings.py`：

```python
from trading_assistant.settings import Settings


def test_default_settings_use_local_values():
    settings = Settings()

    assert settings.app_name == "a-share-short-term-trading-assistant"
    assert settings.environment == "local"
    assert settings.database_url.startswith("sqlite")
    assert settings.redis_url == "redis://localhost:6379/0"
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/test_settings.py -v
```

Expected:

```text
ModuleNotFoundError: No module named 'trading_assistant'
```

- [ ] **Step 3: 创建项目配置文件**

创建 `pyproject.toml`：

```toml
[project]
name = "a-share-short-term-trading-assistant"
version = "0.1.0"
description = "Conservative A-share short-term trading assistant"
requires-python = ">=3.11"
dependencies = [
  "akshare>=1.14.0",
  "apscheduler>=3.10.4",
  "fastapi>=0.115.0",
  "httpx>=0.27.0",
  "jinja2>=3.1.4",
  "numpy>=1.26.0",
  "pandas>=2.2.0",
  "pydantic>=2.8.0",
  "pydantic-settings>=2.4.0",
  "python-multipart>=0.0.9",
  "pyyaml>=6.0.2",
  "redis>=5.0.8",
  "sqlalchemy>=2.0.32",
  "tushare>=1.4.12",
  "uvicorn>=0.30.0"
]

[project.optional-dependencies]
dev = [
  "mypy>=1.11.0",
  "pytest>=8.3.0",
  "pytest-cov>=5.0.0",
  "ruff>=0.6.0"
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
```

创建 `.gitignore`：

```gitignore
.env
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
.mypy_cache/
data/reports/*.md
data/reports/*.html
*.db
*.sqlite
```

创建 `.env.example`：

```dotenv
APP_NAME=a-share-short-term-trading-assistant
ENVIRONMENT=local
DATABASE_URL=sqlite:///./trading_assistant.db
REDIS_URL=redis://localhost:6379/0
TUSHARE_TOKEN=
OPENAI_API_KEY=
FEISHU_WEBHOOK_URL=
```

创建 `README.md`：

```markdown
# A 股保守型短线交易辅助系统

第一阶段目标：盘后选股、持仓风控、完整交易计划、盘中分级提醒、智能体解释和回测复盘。

## 本地测试

```powershell
python -m pytest -v
python -m ruff check .
python -m mypy src
```
```

- [ ] **Step 4: 创建设置模块**

创建 `src/trading_assistant/__init__.py`：

```python
__all__ = ["__version__"]

__version__ = "0.1.0"
```

创建 `src/trading_assistant/settings.py`：

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "a-share-short-term-trading-assistant"
    environment: str = "local"
    database_url: str = "sqlite:///./trading_assistant.db"
    redis_url: str = "redis://localhost:6379/0"
    tushare_token: str = ""
    openai_api_key: str = ""
    feishu_webhook_url: str = ""
```

- [ ] **Step 5: 运行测试并确认通过**

Run:

```powershell
python -m pytest tests/test_settings.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 6: 运行质量检查**

Run:

```powershell
python -m ruff check .
python -m mypy src
```

Expected:

```text
All checks passed!
Success: no issues found
```

- [ ] **Step 7: 提交**

```powershell
git add pyproject.toml .gitignore .env.example README.md src tests
git commit -m "chore: scaffold trading assistant project"
```

### Task 0.2: 创建配置文件和示例数据目录

**Files:**
- Create: `config/scoring.yml`
- Create: `config/risk.yml`
- Create: `config/pools.yml`
- Create: `data/samples/holdings.csv`
- Create: `data/samples/daily_bars.csv`
- Create: `data/samples/minute_bars.csv`
- Create: `data/samples/sectors.csv`
- Create: `data/samples/events.jsonl`
- Create: `tests/test_config_files.py`

- [ ] **Step 1: 写配置文件测试**

创建 `tests/test_config_files.py`：

```python
from pathlib import Path

import yaml


def test_config_files_exist_and_have_required_sections():
    root = Path(__file__).resolve().parents[1]

    scoring = yaml.safe_load((root / "config/scoring.yml").read_text(encoding="utf-8"))
    risk = yaml.safe_load((root / "config/risk.yml").read_text(encoding="utf-8"))
    pools = yaml.safe_load((root / "config/pools.yml").read_text(encoding="utf-8"))

    assert set(scoring) == {"portfolio_risk", "market_environment", "short_term_opportunity", "plan_confidence"}
    assert risk["max_single_position_pct"] == 0.10
    assert pools["exclude_st"] is True
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/test_config_files.py -v
```

Expected:

```text
FileNotFoundError
```

- [ ] **Step 3: 创建评分配置**

创建 `config/scoring.yml`：

```yaml
portfolio_risk:
  technical_breakdown: 0.25
  volume_price_deterioration: 0.20
  sector_cooling: 0.15
  market_environment: 0.15
  fund_outflow: 0.10
  negative_event: 0.10
  holding_drawdown: 0.05
market_environment:
  index_trend: 0.25
  market_turnover: 0.20
  advance_decline: 0.20
  limit_up_down_structure: 0.15
  sector_persistence: 0.15
  external_risk: 0.05
short_term_opportunity:
  sector_strength: 0.25
  volume_price_structure: 0.25
  technical_pattern: 0.20
  market_environment: 0.10
  event_catalyst: 0.10
  fund_behavior: 0.05
  sentiment_heat: 0.05
plan_confidence:
  stop_loss_clarity: 0.25
  entry_clarity: 0.20
  reward_risk_ratio: 0.20
  liquidity: 0.15
  gap_up_chase_risk: 0.10
  invalidation_clarity: 0.10
```

创建 `config/risk.yml`：

```yaml
max_single_position_pct: 0.10
max_total_position_pct: 0.50
max_theme_position_pct: 0.20
default_stop_loss_pct: 0.04
hard_stop_loss_pct: 0.05
first_take_profit_pct: 0.06
second_take_profit_pct: 0.10
max_gap_up_for_entry_pct: 0.03
min_reward_risk_ratio: 1.5
market_score_no_new_position: 40
market_score_light_position: 60
high_portfolio_risk_no_new_position: 70
```

创建 `config/pools.yml`：

```yaml
exclude_st: true
exclude_delisting_risk: true
min_daily_turnover_cny: 100000000
min_listing_days: 60
exclude_limit_down_days: 2
exclude_one_word_limit_up: true
watch_boards:
  - 创业板
  - 科创板
  - 北交所
tradable_boards:
  - 沪市主板
  - 深市主板
  - 创业板
```

- [ ] **Step 4: 创建示例数据**

创建 `data/samples/holdings.csv`：

```csv
symbol,name,quantity,cost_price,current_price,buy_date,theme,buy_reason
000001,平安银行,1000,10.00,10.30,2026-06-10,银行,放量突破平台
600519,贵州茅台,10,1500.00,1518.00,2026-06-11,白酒,缩量回踩支撑
```

创建 `data/samples/daily_bars.csv`：

```csv
trade_date,symbol,open,high,low,close,volume,turnover,pre_close
2026-06-10,000001,9.80,10.20,9.70,10.00,120000000,1200000000,9.70
2026-06-11,000001,10.02,10.50,9.95,10.30,150000000,1545000000,10.00
2026-06-10,600519,1490.00,1510.00,1480.00,1500.00,2000000,3000000000,1488.00
2026-06-11,600519,1505.00,1528.00,1498.00,1518.00,2200000,3339600000,1500.00
```

创建 `data/samples/minute_bars.csv`：

```csv
datetime,symbol,open,high,low,close,volume,turnover
2026-06-12 09:35:00,000001,10.30,10.35,10.25,10.32,2000000,20640000
2026-06-12 09:40:00,000001,10.32,10.38,10.30,10.36,2500000,25900000
2026-06-12 09:35:00,600519,1518.00,1522.00,1512.00,1516.00,30000,45480000
2026-06-12 09:40:00,600519,1516.00,1520.00,1510.00,1512.00,35000,52920000
```

创建 `data/samples/sectors.csv`：

```csv
trade_date,sector_name,sector_type,pct_chg,turnover,limit_up_count,leader_symbol
2026-06-12,银行,industry,1.50,9000000000,2,000001
2026-06-12,白酒,industry,-0.80,7000000000,0,600519
```

创建 `data/samples/events.jsonl`：

```jsonl
{"trade_date":"2026-06-12","symbol":"000001","event_type":"news","sentiment":"positive","title":"银行板块成交额放大","source":"sample"}
{"trade_date":"2026-06-12","symbol":"600519","event_type":"announcement","sentiment":"neutral","title":"年度权益分派进展","source":"sample"}
```

- [ ] **Step 5: 运行测试**

Run:

```powershell
python -m pytest tests/test_config_files.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 6: 提交**

```powershell
git add config data/samples tests/test_config_files.py
git commit -m "chore: add MVP config and sample data"
```

---

## 阶段 1：M1 数据与持仓底座

### Task 1.1: 定义领域模型

**Files:**
- Create: `src/trading_assistant/domain/enums.py`
- Create: `src/trading_assistant/domain/models.py`
- Create: `tests/test_domain_models.py`

- [ ] **Step 1: 写领域模型测试**

创建 `tests/test_domain_models.py`：

```python
from datetime import date

from trading_assistant.domain.enums import ActionAdvice, PoolType, RiskLevel
from trading_assistant.domain.models import Holding, TradePlan


def test_holding_unrealized_return_pct():
    holding = Holding(
        symbol="000001",
        name="平安银行",
        quantity=1000,
        cost_price=10.0,
        current_price=10.5,
        buy_date=date(2026, 6, 10),
        theme="银行",
        buy_reason="放量突破平台",
    )

    assert holding.market_value == 10500.0
    assert holding.unrealized_return_pct == 0.05


def test_trade_plan_requires_risk_controls():
    plan = TradePlan(
        symbol="000001",
        name="平安银行",
        pool_type=PoolType.TRADABLE,
        opportunity_score=78,
        plan_confidence_score=82,
        entry_trigger="放量突破 10.60",
        entry_price_low=10.50,
        entry_price_high=10.65,
        stop_loss_price=10.20,
        first_take_profit_price=11.10,
        second_take_profit_price=11.50,
        position_pct=0.08,
        invalidation_condition="跌破 10.20 或板块退潮",
        risk_level=RiskLevel.MEDIUM,
        action_advice=ActionAdvice.WATCH_FOR_TRIGGER,
    )

    assert plan.reward_risk_ratio > 1.5
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/test_domain_models.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 创建枚举**

创建 `src/trading_assistant/domain/enums.py`：

```python
from enum import StrEnum


class PoolType(StrEnum):
    TRADABLE = "tradable"
    WATCH = "watch"
    BLOCKED = "blocked"
    HOLDING = "holding"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionAdvice(StrEnum):
    HOLD = "hold"
    TIGHTEN_STOP = "tighten_stop"
    REDUCE = "reduce"
    SELL_ON_REBOUND = "sell_on_rebound"
    CLEAR_OR_STOP = "clear_or_stop"
    WATCH_FOR_TRIGGER = "watch_for_trigger"
    NO_ACTION = "no_action"
```

- [ ] **Step 4: 创建数据模型**

创建 `src/trading_assistant/domain/models.py`：

```python
from datetime import date, datetime

from pydantic import BaseModel, Field

from trading_assistant.domain.enums import ActionAdvice, PoolType, RiskLevel


class Holding(BaseModel):
    symbol: str
    name: str
    quantity: int = Field(gt=0)
    cost_price: float = Field(gt=0)
    current_price: float = Field(gt=0)
    buy_date: date
    theme: str
    buy_reason: str

    @property
    def market_value(self) -> float:
        return round(self.quantity * self.current_price, 2)

    @property
    def unrealized_return_pct(self) -> float:
        return round((self.current_price - self.cost_price) / self.cost_price, 4)


class ScoreBreakdown(BaseModel):
    total_score: float = Field(ge=0, le=100)
    components: dict[str, float]
    reasons: list[str]


class TradePlan(BaseModel):
    symbol: str
    name: str
    pool_type: PoolType
    opportunity_score: float = Field(ge=0, le=100)
    plan_confidence_score: float = Field(ge=0, le=100)
    entry_trigger: str
    entry_price_low: float = Field(gt=0)
    entry_price_high: float = Field(gt=0)
    stop_loss_price: float = Field(gt=0)
    first_take_profit_price: float = Field(gt=0)
    second_take_profit_price: float = Field(gt=0)
    position_pct: float = Field(ge=0, le=1)
    invalidation_condition: str
    risk_level: RiskLevel
    action_advice: ActionAdvice
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def reward_risk_ratio(self) -> float:
        planned_entry = (self.entry_price_low + self.entry_price_high) / 2
        risk = planned_entry - self.stop_loss_price
        reward = self.first_take_profit_price - planned_entry
        if risk <= 0:
            return 0.0
        return round(reward / risk, 2)
```

- [ ] **Step 5: 创建包初始化文件**

创建 `src/trading_assistant/domain/__init__.py`：

```python
from trading_assistant.domain.enums import ActionAdvice, PoolType, RiskLevel
from trading_assistant.domain.models import Holding, ScoreBreakdown, TradePlan

__all__ = [
    "ActionAdvice",
    "Holding",
    "PoolType",
    "RiskLevel",
    "ScoreBreakdown",
    "TradePlan",
]
```

- [ ] **Step 6: 运行测试**

Run:

```powershell
python -m pytest tests/test_domain_models.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 7: 提交**

```powershell
git add src/trading_assistant/domain tests/test_domain_models.py
git commit -m "feat: add trading domain models"
```

### Task 1.2: 建立数据库会话和仓储接口

**Files:**
- Create: `src/trading_assistant/db/base.py`
- Create: `src/trading_assistant/db/models.py`
- Create: `src/trading_assistant/db/session.py`
- Create: `src/trading_assistant/db/repositories.py`
- Create: `tests/db/test_repositories.py`

- [ ] **Step 1: 写仓储测试**

创建 `tests/db/test_repositories.py`：

```python
from datetime import date

from trading_assistant.db.base import Base
from trading_assistant.db.repositories import HoldingRepository
from trading_assistant.db.session import build_engine, build_session_factory


def test_holding_repository_upsert_and_list():
    engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)

    with session_factory() as session:
        repo = HoldingRepository(session)
        repo.upsert_holding(
            symbol="000001",
            name="平安银行",
            quantity=1000,
            cost_price=10.0,
            current_price=10.3,
            buy_date=date(2026, 6, 10),
            theme="银行",
            buy_reason="放量突破平台",
        )
        rows = repo.list_holdings()

    assert len(rows) == 1
    assert rows[0].symbol == "000001"
    assert rows[0].current_price == 10.3
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/db/test_repositories.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 创建数据库基础对象**

创建 `src/trading_assistant/db/base.py`：

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

创建 `src/trading_assistant/db/session.py`：

```python
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def build_engine(database_url: str) -> Engine:
    return create_engine(database_url, future=True)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
```

- [ ] **Step 4: 创建数据库模型和仓储**

创建 `src/trading_assistant/db/models.py`：

```python
from datetime import date

from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from trading_assistant.db.base import Base


class HoldingORM(Base):
    __tablename__ = "holdings"

    symbol: Mapped[str] = mapped_column(String(12), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    buy_date: Mapped[date] = mapped_column(Date, nullable=False)
    theme: Mapped[str] = mapped_column(String(64), nullable=False)
    buy_reason: Mapped[str] = mapped_column(String(256), nullable=False)
```

创建 `src/trading_assistant/db/repositories.py`：

```python
from datetime import date

from sqlalchemy.orm import Session

from trading_assistant.db.models import HoldingORM


class HoldingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_holding(
        self,
        *,
        symbol: str,
        name: str,
        quantity: int,
        cost_price: float,
        current_price: float,
        buy_date: date,
        theme: str,
        buy_reason: str,
    ) -> None:
        existing = self.session.get(HoldingORM, symbol)
        if existing is None:
            existing = HoldingORM(symbol=symbol)
            self.session.add(existing)
        existing.name = name
        existing.quantity = quantity
        existing.cost_price = cost_price
        existing.current_price = current_price
        existing.buy_date = buy_date
        existing.theme = theme
        existing.buy_reason = buy_reason
        self.session.commit()

    def list_holdings(self) -> list[HoldingORM]:
        return list(self.session.query(HoldingORM).order_by(HoldingORM.symbol).all())
```

创建 `src/trading_assistant/db/__init__.py`：

```python
from trading_assistant.db.base import Base

__all__ = ["Base"]
```

- [ ] **Step 5: 运行测试**

Run:

```powershell
python -m pytest tests/db/test_repositories.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 6: 提交**

```powershell
git add src/trading_assistant/db tests/db
git commit -m "feat: add database session and holding repository"
```

### Task 1.3: 实现持仓 CSV 导入

**Files:**
- Create: `src/trading_assistant/portfolio/importer.py`
- Create: `scripts/import_holdings.py`
- Create: `tests/portfolio/test_importer.py`

- [ ] **Step 1: 写导入测试**

创建 `tests/portfolio/test_importer.py`：

```python
from pathlib import Path

from trading_assistant.portfolio.importer import load_holdings_csv


def test_load_holdings_csv_parses_holdings():
    path = Path("data/samples/holdings.csv")

    holdings = load_holdings_csv(path)

    assert len(holdings) == 2
    assert holdings[0].symbol == "000001"
    assert holdings[0].unrealized_return_pct == 0.03
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/portfolio/test_importer.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 实现导入器**

创建 `src/trading_assistant/portfolio/importer.py`：

```python
from pathlib import Path

import pandas as pd

from trading_assistant.domain.models import Holding


REQUIRED_COLUMNS = {
    "symbol",
    "name",
    "quantity",
    "cost_price",
    "current_price",
    "buy_date",
    "theme",
    "buy_reason",
}


def load_holdings_csv(path: Path) -> list[Holding]:
    frame = pd.read_csv(path, dtype={"symbol": str})
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"holdings csv missing columns: {sorted(missing)}")

    holdings: list[Holding] = []
    for row in frame.to_dict(orient="records"):
        holdings.append(
            Holding(
                symbol=row["symbol"],
                name=row["name"],
                quantity=int(row["quantity"]),
                cost_price=float(row["cost_price"]),
                current_price=float(row["current_price"]),
                buy_date=pd.to_datetime(row["buy_date"]).date(),
                theme=row["theme"],
                buy_reason=row["buy_reason"],
            )
        )
    return holdings
```

创建 `src/trading_assistant/portfolio/__init__.py`：

```python
from trading_assistant.portfolio.importer import load_holdings_csv

__all__ = ["load_holdings_csv"]
```

创建 `scripts/import_holdings.py`：

```python
from pathlib import Path

from trading_assistant.portfolio.importer import load_holdings_csv


def main() -> None:
    holdings = load_holdings_csv(Path("data/samples/holdings.csv"))
    for holding in holdings:
        print(f"{holding.symbol} {holding.name} {holding.market_value:.2f}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 运行测试和脚本**

Run:

```powershell
python -m pytest tests/portfolio/test_importer.py -v
python scripts/import_holdings.py
```

Expected:

```text
1 passed
000001 平安银行 10300.00
600519 贵州茅台 15180.00
```

- [ ] **Step 5: 提交**

```powershell
git add src/trading_assistant/portfolio scripts/import_holdings.py tests/portfolio
git commit -m "feat: import portfolio holdings from csv"
```

### Task 1.4: 实现数据源协议和样例数据 Provider

**Files:**
- Create: `src/trading_assistant/data_sources/protocols.py`
- Create: `src/trading_assistant/data_sources/fake_provider.py`
- Create: `src/trading_assistant/data_sources/ingestion.py`
- Create: `tests/data_sources/test_fake_provider.py`

- [ ] **Step 1: 写 Provider 测试**

创建 `tests/data_sources/test_fake_provider.py`：

```python
from datetime import date
from pathlib import Path

from trading_assistant.data_sources.fake_provider import FakeMarketDataProvider


def test_fake_provider_loads_daily_bars_and_sectors():
    provider = FakeMarketDataProvider(Path("data/samples"))

    daily = provider.get_daily_bars(date(2026, 6, 10), date(2026, 6, 11))
    sectors = provider.get_sector_snapshot(date(2026, 6, 12))

    assert set(daily["symbol"]) == {"000001", "600519"}
    assert sectors.iloc[0]["sector_name"] == "银行"
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/data_sources/test_fake_provider.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 创建协议和样例 Provider**

创建 `src/trading_assistant/data_sources/protocols.py`：

```python
from datetime import date
from typing import Protocol

import pandas as pd


class MarketDataProvider(Protocol):
    def get_daily_bars(self, start: date, end: date) -> pd.DataFrame:
        raise NotImplementedError

    def get_minute_bars(self, trade_date: date) -> pd.DataFrame:
        raise NotImplementedError

    def get_sector_snapshot(self, trade_date: date) -> pd.DataFrame:
        raise NotImplementedError
```

创建 `src/trading_assistant/data_sources/fake_provider.py`：

```python
from datetime import date
from pathlib import Path

import pandas as pd


class FakeMarketDataProvider:
    def __init__(self, sample_dir: Path) -> None:
        self.sample_dir = sample_dir

    def get_daily_bars(self, start: date, end: date) -> pd.DataFrame:
        frame = pd.read_csv(self.sample_dir / "daily_bars.csv", dtype={"symbol": str})
        frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
        return frame[(frame["trade_date"] >= start) & (frame["trade_date"] <= end)].reset_index(drop=True)

    def get_minute_bars(self, trade_date: date) -> pd.DataFrame:
        frame = pd.read_csv(self.sample_dir / "minute_bars.csv", dtype={"symbol": str})
        frame["datetime"] = pd.to_datetime(frame["datetime"])
        return frame[frame["datetime"].dt.date == trade_date].reset_index(drop=True)

    def get_sector_snapshot(self, trade_date: date) -> pd.DataFrame:
        frame = pd.read_csv(self.sample_dir / "sectors.csv", dtype={"leader_symbol": str})
        frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
        return frame[frame["trade_date"] == trade_date].reset_index(drop=True)
```

创建 `src/trading_assistant/data_sources/ingestion.py`：

```python
from datetime import date

import pandas as pd

from trading_assistant.data_sources.protocols import MarketDataProvider


def load_market_snapshot(provider: MarketDataProvider, trade_date: date) -> dict[str, pd.DataFrame]:
    return {
        "daily": provider.get_daily_bars(trade_date, trade_date),
        "minute": provider.get_minute_bars(trade_date),
        "sectors": provider.get_sector_snapshot(trade_date),
    }
```

创建 `src/trading_assistant/data_sources/__init__.py`：

```python
from trading_assistant.data_sources.fake_provider import FakeMarketDataProvider

__all__ = ["FakeMarketDataProvider"]
```

- [ ] **Step 4: 运行测试**

Run:

```powershell
python -m pytest tests/data_sources/test_fake_provider.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交**

```powershell
git add src/trading_assistant/data_sources tests/data_sources
git commit -m "feat: add market data provider interface"
```

### Task 1.5: 实现 AKShare 和 Tushare Provider 外壳

**Files:**
- Create: `src/trading_assistant/data_sources/akshare_provider.py`
- Create: `src/trading_assistant/data_sources/tushare_provider.py`
- Create: `tests/data_sources/test_provider_contracts.py`

- [ ] **Step 1: 写 Provider 契约测试**

创建 `tests/data_sources/test_provider_contracts.py`：

```python
from datetime import date
from unittest.mock import Mock, patch

import pandas as pd

from trading_assistant.data_sources.akshare_provider import AkshareMarketDataProvider
from trading_assistant.data_sources.tushare_provider import TushareMarketDataProvider


def test_akshare_provider_normalizes_symbol_column():
    raw = pd.DataFrame(
        {
            "日期": ["2026-06-12"],
            "股票代码": ["000001"],
            "开盘": [10.0],
            "收盘": [10.3],
            "最高": [10.4],
            "最低": [9.9],
            "成交量": [1000],
            "成交额": [10300],
        }
    )

    with patch("trading_assistant.data_sources.akshare_provider.ak.stock_zh_a_hist", return_value=raw):
        provider = AkshareMarketDataProvider(symbols=["000001"])
        frame = provider.get_daily_bars(date(2026, 6, 12), date(2026, 6, 12))

    assert frame.iloc[0]["symbol"] == "000001"
    assert frame.iloc[0]["close"] == 10.3


def test_tushare_provider_requires_token():
    client = Mock()
    provider = TushareMarketDataProvider(token="token", client=client)

    assert provider.token == "token"
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/data_sources/test_provider_contracts.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 实现 AKShare Provider**

创建 `src/trading_assistant/data_sources/akshare_provider.py`：

```python
from datetime import date

import akshare as ak
import pandas as pd


class AkshareMarketDataProvider:
    def __init__(self, symbols: list[str]) -> None:
        self.symbols = symbols

    def get_daily_bars(self, start: date, end: date) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for symbol in self.symbols:
            raw = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust="qfq",
            )
            if raw.empty:
                continue
            frame = raw.rename(
                columns={
                    "日期": "trade_date",
                    "股票代码": "symbol",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "turnover",
                }
            )
            frame["symbol"] = symbol
            frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
            frames.append(frame[["trade_date", "symbol", "open", "high", "low", "close", "volume", "turnover"]])
        if not frames:
            return pd.DataFrame(columns=["trade_date", "symbol", "open", "high", "low", "close", "volume", "turnover"])
        return pd.concat(frames, ignore_index=True)

    def get_minute_bars(self, trade_date: date) -> pd.DataFrame:
        return pd.DataFrame(columns=["datetime", "symbol", "open", "high", "low", "close", "volume", "turnover"])

    def get_sector_snapshot(self, trade_date: date) -> pd.DataFrame:
        return pd.DataFrame(columns=["trade_date", "sector_name", "sector_type", "pct_chg", "turnover", "limit_up_count", "leader_symbol"])
```

- [ ] **Step 4: 实现 Tushare Provider 外壳**

创建 `src/trading_assistant/data_sources/tushare_provider.py`：

```python
from datetime import date
from typing import Any

import pandas as pd


class TushareMarketDataProvider:
    def __init__(self, token: str, client: Any | None = None) -> None:
        self.token = token
        self.client = client

    def get_daily_bars(self, start: date, end: date) -> pd.DataFrame:
        if self.client is None:
            return pd.DataFrame(columns=["trade_date", "symbol", "open", "high", "low", "close", "volume", "turnover"])
        raw = self.client.daily(start_date=start.strftime("%Y%m%d"), end_date=end.strftime("%Y%m%d"))
        return raw.rename(columns={"ts_code": "symbol", "vol": "volume", "amount": "turnover"})

    def get_minute_bars(self, trade_date: date) -> pd.DataFrame:
        return pd.DataFrame(columns=["datetime", "symbol", "open", "high", "low", "close", "volume", "turnover"])

    def get_sector_snapshot(self, trade_date: date) -> pd.DataFrame:
        return pd.DataFrame(columns=["trade_date", "sector_name", "sector_type", "pct_chg", "turnover", "limit_up_count", "leader_symbol"])
```

- [ ] **Step 5: 运行测试**

Run:

```powershell
python -m pytest tests/data_sources/test_provider_contracts.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 6: 提交**

```powershell
git add src/trading_assistant/data_sources/akshare_provider.py src/trading_assistant/data_sources/tushare_provider.py tests/data_sources/test_provider_contracts.py
git commit -m "feat: add low-cost data provider adapters"
```

---

## 阶段 2：M2 因子与评分引擎

### Task 2.1: 实现股票池分层和禁入过滤

**Files:**
- Create: `src/trading_assistant/pools/classifier.py`
- Create: `tests/pools/test_classifier.py`

- [ ] **Step 1: 写分层测试**

创建 `tests/pools/test_classifier.py`：

```python
import pandas as pd

from trading_assistant.domain.enums import PoolType
from trading_assistant.pools.classifier import classify_stock_pool


def test_classify_blocks_st_and_low_turnover():
    stock = pd.Series(
        {
            "symbol": "000001",
            "name": "平安银行",
            "board": "沪市主板",
            "is_st": False,
            "has_delisting_risk": False,
            "daily_turnover": 120_000_000,
            "listing_days": 300,
            "one_word_limit_up": False,
            "limit_down_days": 0,
        }
    )

    assert classify_stock_pool(stock).pool_type == PoolType.TRADABLE

    stock["is_st"] = True
    blocked = classify_stock_pool(stock)
    assert blocked.pool_type == PoolType.BLOCKED
    assert "ST" in blocked.reason
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/pools/test_classifier.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 实现分层器**

创建 `src/trading_assistant/pools/classifier.py`：

```python
from dataclasses import dataclass

import pandas as pd

from trading_assistant.domain.enums import PoolType


@dataclass(frozen=True)
class PoolClassification:
    symbol: str
    pool_type: PoolType
    reason: str


def classify_stock_pool(stock: pd.Series) -> PoolClassification:
    symbol = str(stock["symbol"])
    if bool(stock.get("is_st", False)):
        return PoolClassification(symbol, PoolType.BLOCKED, "ST 股票禁入")
    if bool(stock.get("has_delisting_risk", False)):
        return PoolClassification(symbol, PoolType.BLOCKED, "存在退市风险")
    if float(stock.get("daily_turnover", 0)) < 100_000_000:
        return PoolClassification(symbol, PoolType.BLOCKED, "成交额低于 1 亿元")
    if int(stock.get("listing_days", 0)) < 60:
        return PoolClassification(symbol, PoolType.WATCH, "上市不足 60 天")
    if bool(stock.get("one_word_limit_up", False)):
        return PoolClassification(symbol, PoolType.WATCH, "连续一字板不追")
    if int(stock.get("limit_down_days", 0)) >= 2:
        return PoolClassification(symbol, PoolType.BLOCKED, "连续跌停风险")
    if stock.get("board") in {"北交所"}:
        return PoolClassification(symbol, PoolType.WATCH, "高波动板块先观察")
    return PoolClassification(symbol, PoolType.TRADABLE, "满足可交易池基础条件")
```

创建 `src/trading_assistant/pools/__init__.py`：

```python
from trading_assistant.pools.classifier import PoolClassification, classify_stock_pool

__all__ = ["PoolClassification", "classify_stock_pool"]
```

- [ ] **Step 4: 运行测试**

Run:

```powershell
python -m pytest tests/pools/test_classifier.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交**

```powershell
git add src/trading_assistant/pools tests/pools
git commit -m "feat: classify tradable watch and blocked pools"
```

### Task 2.2: 实现核心因子计算

**Files:**
- Create: `src/trading_assistant/factors/technical.py`
- Create: `src/trading_assistant/factors/volume_price.py`
- Create: `src/trading_assistant/factors/market.py`
- Create: `src/trading_assistant/factors/sector.py`
- Create: `tests/factors/test_core_factors.py`

- [ ] **Step 1: 写因子测试**

创建 `tests/factors/test_core_factors.py`：

```python
import pandas as pd

from trading_assistant.factors.market import compute_market_environment_factors
from trading_assistant.factors.technical import compute_technical_factors
from trading_assistant.factors.volume_price import compute_volume_price_factors


def test_compute_technical_and_volume_factors():
    bars = pd.DataFrame(
        {
            "symbol": ["000001"] * 5,
            "close": [10.0, 10.2, 10.3, 10.5, 10.8],
            "high": [10.1, 10.3, 10.4, 10.6, 10.9],
            "low": [9.9, 10.0, 10.1, 10.2, 10.5],
            "turnover": [100, 120, 130, 180, 220],
        }
    )

    technical = compute_technical_factors(bars)
    volume_price = compute_volume_price_factors(bars)

    assert technical["momentum_5d"] == 0.08
    assert technical["above_ma5"] is True
    assert volume_price["turnover_expansion"] > 1.5


def test_compute_market_environment_factors():
    market = pd.DataFrame(
        {
            "symbol": ["000001", "600519", "300001"],
            "pct_chg": [2.0, -1.0, 3.0],
            "turnover": [100, 200, 300],
            "is_limit_up": [True, False, False],
            "is_limit_down": [False, False, False],
        }
    )

    factors = compute_market_environment_factors(market)

    assert factors["advance_ratio"] == 0.67
    assert factors["limit_up_count"] == 1
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/factors/test_core_factors.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 实现技术和量价因子**

创建 `src/trading_assistant/factors/technical.py`：

```python
import pandas as pd


def compute_technical_factors(bars: pd.DataFrame) -> dict[str, float | bool]:
    ordered = bars.reset_index(drop=True)
    close = ordered["close"]
    high = ordered["high"]
    low = ordered["low"]
    ma5 = close.tail(5).mean()
    momentum_5d = round((close.iloc[-1] - close.iloc[0]) / close.iloc[0], 4)
    atr_5d = round(((high - low).tail(5).mean() / close.iloc[-1]), 4)
    return {
        "momentum_5d": momentum_5d,
        "above_ma5": bool(close.iloc[-1] >= ma5),
        "atr_5d": atr_5d,
    }
```

创建 `src/trading_assistant/factors/volume_price.py`：

```python
import pandas as pd


def compute_volume_price_factors(bars: pd.DataFrame) -> dict[str, float | bool]:
    ordered = bars.reset_index(drop=True)
    recent_turnover = float(ordered["turnover"].iloc[-1])
    base_turnover = float(ordered["turnover"].head(max(len(ordered) - 1, 1)).mean())
    turnover_expansion = recent_turnover / base_turnover if base_turnover > 0 else 0.0
    close_up = float(ordered["close"].iloc[-1]) > float(ordered["close"].iloc[-2])
    return {
        "turnover_expansion": round(turnover_expansion, 2),
        "price_up_with_volume": bool(close_up and turnover_expansion >= 1.2),
    }
```

- [ ] **Step 4: 实现市场和板块因子**

创建 `src/trading_assistant/factors/market.py`：

```python
import pandas as pd


def compute_market_environment_factors(market: pd.DataFrame) -> dict[str, float | int]:
    total = len(market)
    advance_count = int((market["pct_chg"] > 0).sum())
    decline_count = int((market["pct_chg"] < 0).sum())
    return {
        "advance_ratio": round(advance_count / total, 2) if total else 0.0,
        "decline_ratio": round(decline_count / total, 2) if total else 0.0,
        "total_turnover": float(market["turnover"].sum()),
        "limit_up_count": int(market["is_limit_up"].sum()),
        "limit_down_count": int(market["is_limit_down"].sum()),
    }
```

创建 `src/trading_assistant/factors/sector.py`：

```python
import pandas as pd


def compute_sector_strength(sectors: pd.DataFrame) -> list[dict[str, float | str]]:
    ranked = sectors.sort_values(["pct_chg", "turnover", "limit_up_count"], ascending=False)
    result: list[dict[str, float | str]] = []
    for row in ranked.to_dict(orient="records"):
        result.append(
            {
                "sector_name": str(row["sector_name"]),
                "sector_type": str(row["sector_type"]),
                "strength_score": round(float(row["pct_chg"]) * 8 + float(row["limit_up_count"]) * 5, 2),
                "leader_symbol": str(row["leader_symbol"]),
            }
        )
    return result
```

创建 `src/trading_assistant/factors/__init__.py`：

```python
from trading_assistant.factors.market import compute_market_environment_factors
from trading_assistant.factors.sector import compute_sector_strength
from trading_assistant.factors.technical import compute_technical_factors
from trading_assistant.factors.volume_price import compute_volume_price_factors

__all__ = [
    "compute_market_environment_factors",
    "compute_sector_strength",
    "compute_technical_factors",
    "compute_volume_price_factors",
]
```

- [ ] **Step 5: 运行测试**

Run:

```powershell
python -m pytest tests/factors/test_core_factors.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 6: 提交**

```powershell
git add src/trading_assistant/factors tests/factors
git commit -m "feat: compute core market technical and volume factors"
```

### Task 2.3: 实现权重加载和评分引擎

**Files:**
- Create: `src/trading_assistant/scoring/weights.py`
- Create: `src/trading_assistant/scoring/engine.py`
- Create: `tests/scoring/test_engine.py`

- [ ] **Step 1: 写评分测试**

创建 `tests/scoring/test_engine.py`：

```python
from pathlib import Path

from trading_assistant.scoring.engine import ScoreEngine
from trading_assistant.scoring.weights import load_weight_config


def test_score_engine_computes_weighted_score():
    weights = load_weight_config(Path("config/scoring.yml"))
    engine = ScoreEngine(weights["short_term_opportunity"])

    score = engine.score(
        {
            "sector_strength": 80,
            "volume_price_structure": 90,
            "technical_pattern": 70,
            "market_environment": 60,
            "event_catalyst": 50,
            "fund_behavior": 40,
            "sentiment_heat": 30,
        }
    )

    assert score.total_score == 68.5
    assert "sector_strength" in score.components
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/scoring/test_engine.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 实现权重加载**

创建 `src/trading_assistant/scoring/weights.py`：

```python
from pathlib import Path

import yaml


def load_weight_config(path: Path) -> dict[str, dict[str, float]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    for score_name, weights in raw.items():
        total = round(sum(float(value) for value in weights.values()), 4)
        if total != 1.0:
            raise ValueError(f"{score_name} weights sum to {total}, expected 1.0")
    return {name: {key: float(value) for key, value in weights.items()} for name, weights in raw.items()}
```

创建 `src/trading_assistant/scoring/engine.py`：

```python
from trading_assistant.domain.models import ScoreBreakdown


class ScoreEngine:
    def __init__(self, weights: dict[str, float]) -> None:
        self.weights = weights

    def score(self, normalized_factors: dict[str, float]) -> ScoreBreakdown:
        components: dict[str, float] = {}
        for factor_name, weight in self.weights.items():
            value = max(0.0, min(100.0, float(normalized_factors.get(factor_name, 0.0))))
            components[factor_name] = round(value * weight, 4)
        total_score = round(sum(components.values()), 2)
        reasons = [f"{name}={normalized_factors.get(name, 0)} weight={weight}" for name, weight in self.weights.items()]
        return ScoreBreakdown(total_score=total_score, components=components, reasons=reasons)
```

创建 `src/trading_assistant/scoring/__init__.py`：

```python
from trading_assistant.scoring.engine import ScoreEngine
from trading_assistant.scoring.weights import load_weight_config

__all__ = ["ScoreEngine", "load_weight_config"]
```

- [ ] **Step 4: 运行测试**

Run:

```powershell
python -m pytest tests/scoring/test_engine.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交**

```powershell
git add src/trading_assistant/scoring tests/scoring
git commit -m "feat: add weighted scoring engine"
```

---

## 阶段 3：M3 持仓风控与卖出规则

### Task 3.1: 实现持仓风险引擎

**Files:**
- Create: `src/trading_assistant/factors/portfolio.py`
- Create: `src/trading_assistant/portfolio/risk_engine.py`
- Create: `tests/portfolio/test_risk_engine.py`

- [ ] **Step 1: 写持仓风险测试**

创建 `tests/portfolio/test_risk_engine.py`：

```python
from datetime import date

from trading_assistant.domain.enums import ActionAdvice, RiskLevel
from trading_assistant.domain.models import Holding
from trading_assistant.portfolio.risk_engine import PortfolioRiskEngine


def test_portfolio_risk_engine_flags_hard_stop():
    holding = Holding(
        symbol="000001",
        name="平安银行",
        quantity=1000,
        cost_price=10.0,
        current_price=9.45,
        buy_date=date(2026, 6, 10),
        theme="银行",
        buy_reason="放量突破平台",
    )
    engine = PortfolioRiskEngine(default_stop_loss_pct=0.04, hard_stop_loss_pct=0.05)

    decision = engine.evaluate(
        holding=holding,
        technical_broken=True,
        sector_cooling=False,
        negative_event=False,
        fund_outflow=True,
        market_score=55,
    )

    assert decision.risk_level == RiskLevel.CRITICAL
    assert decision.action_advice == ActionAdvice.CLEAR_OR_STOP
    assert decision.risk_score >= 71
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/portfolio/test_risk_engine.py -v
```

Expected:

```text
ImportError
```

- [ ] **Step 3: 实现持仓因子和风险决策**

创建 `src/trading_assistant/factors/portfolio.py`：

```python
from trading_assistant.domain.models import Holding


def compute_holding_drawdown_factor(holding: Holding) -> float:
    if holding.unrealized_return_pct <= -0.05:
        return 100.0
    if holding.unrealized_return_pct <= -0.03:
        return 75.0
    if holding.unrealized_return_pct <= 0:
        return 50.0
    return 10.0
```

创建 `src/trading_assistant/portfolio/risk_engine.py`：

```python
from dataclasses import dataclass

from trading_assistant.domain.enums import ActionAdvice, RiskLevel
from trading_assistant.domain.models import Holding


@dataclass(frozen=True)
class PortfolioRiskDecision:
    symbol: str
    risk_score: float
    risk_level: RiskLevel
    action_advice: ActionAdvice
    reasons: list[str]


class PortfolioRiskEngine:
    def __init__(self, default_stop_loss_pct: float, hard_stop_loss_pct: float) -> None:
        self.default_stop_loss_pct = default_stop_loss_pct
        self.hard_stop_loss_pct = hard_stop_loss_pct

    def evaluate(
        self,
        *,
        holding: Holding,
        technical_broken: bool,
        sector_cooling: bool,
        negative_event: bool,
        fund_outflow: bool,
        market_score: float,
    ) -> PortfolioRiskDecision:
        reasons: list[str] = []
        score = 0.0
        loss_pct = -holding.unrealized_return_pct
        if loss_pct >= self.hard_stop_loss_pct:
            score += 45
            reasons.append("触发硬止损")
        elif loss_pct >= self.default_stop_loss_pct:
            score += 30
            reasons.append("接近默认止损")
        if technical_broken:
            score += 25
            reasons.append("技术位破位")
        if fund_outflow:
            score += 10
            reasons.append("资金流出")
        if sector_cooling:
            score += 10
            reasons.append("板块退潮")
        if negative_event:
            score += 10
            reasons.append("负面事件")
        if market_score < 40:
            score += 15
            reasons.append("市场环境禁止新冒险")
        score = min(100.0, round(score, 2))
        if score >= 71:
            return PortfolioRiskDecision(holding.symbol, score, RiskLevel.CRITICAL, ActionAdvice.CLEAR_OR_STOP, reasons)
        if score >= 51:
            return PortfolioRiskDecision(holding.symbol, score, RiskLevel.HIGH, ActionAdvice.REDUCE, reasons)
        if score >= 31:
            return PortfolioRiskDecision(holding.symbol, score, RiskLevel.MEDIUM, ActionAdvice.TIGHTEN_STOP, reasons)
        return PortfolioRiskDecision(holding.symbol, score, RiskLevel.LOW, ActionAdvice.HOLD, reasons or ["风险较低"])
```

- [ ] **Step 4: 运行测试**

Run:

```powershell
python -m pytest tests/portfolio/test_risk_engine.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交**

```powershell
git add src/trading_assistant/factors/portfolio.py src/trading_assistant/portfolio/risk_engine.py tests/portfolio/test_risk_engine.py
git commit -m "feat: evaluate portfolio risk and sell advice"
```

### Task 3.2: 实现盘中提醒规则

**Files:**
- Create: `src/trading_assistant/alerts/models.py`
- Create: `src/trading_assistant/alerts/rules.py`
- Create: `tests/alerts/test_rules.py`

- [ ] **Step 1: 写提醒规则测试**

创建 `tests/alerts/test_rules.py`：

```python
from trading_assistant.alerts.models import AlertLevel
from trading_assistant.alerts.rules import evaluate_price_alerts


def test_evaluate_price_alerts_emits_p0_when_stop_loss_breaks():
    alerts = evaluate_price_alerts(
        symbol="000001",
        current_price=9.8,
        stop_loss_price=10.0,
        take_profit_price=11.0,
        entry_trigger_price=10.6,
    )

    assert alerts[0].level == AlertLevel.P0
    assert alerts[0].symbol == "000001"
    assert "跌破硬止损位" in alerts[0].message
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/alerts/test_rules.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 实现提醒模型和规则**

创建 `src/trading_assistant/alerts/models.py`：

```python
from dataclasses import dataclass
from enum import StrEnum


class AlertLevel(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


@dataclass(frozen=True)
class Alert:
    level: AlertLevel
    symbol: str
    message: str
```

创建 `src/trading_assistant/alerts/rules.py`：

```python
from trading_assistant.alerts.models import Alert, AlertLevel


def evaluate_price_alerts(
    *,
    symbol: str,
    current_price: float,
    stop_loss_price: float,
    take_profit_price: float,
    entry_trigger_price: float,
) -> list[Alert]:
    alerts: list[Alert] = []
    if current_price <= stop_loss_price:
        alerts.append(Alert(AlertLevel.P0, symbol, f"{symbol} 跌破硬止损位 {stop_loss_price:.2f}"))
    elif current_price <= stop_loss_price * 1.01:
        alerts.append(Alert(AlertLevel.P1, symbol, f"{symbol} 接近止损位 {stop_loss_price:.2f}"))
    if current_price >= take_profit_price:
        alerts.append(Alert(AlertLevel.P1, symbol, f"{symbol} 到达第一止盈位 {take_profit_price:.2f}"))
    elif current_price >= entry_trigger_price:
        alerts.append(Alert(AlertLevel.P2, symbol, f"{symbol} 触发买入观察价 {entry_trigger_price:.2f}"))
    return alerts
```

创建 `src/trading_assistant/alerts/__init__.py`：

```python
from trading_assistant.alerts.models import Alert, AlertLevel
from trading_assistant.alerts.rules import evaluate_price_alerts

__all__ = ["Alert", "AlertLevel", "evaluate_price_alerts"]
```

- [ ] **Step 4: 运行测试**

Run:

```powershell
python -m pytest tests/alerts/test_rules.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交**

```powershell
git add src/trading_assistant/alerts tests/alerts
git commit -m "feat: add intraday alert levels and price rules"
```

---

## 阶段 4：M4 盘后选股与完整交易计划

### Task 4.1: 实现候选股筛选

**Files:**
- Create: `src/trading_assistant/planning/candidate_selector.py`
- Create: `tests/planning/test_candidate_selector.py`

- [ ] **Step 1: 写候选股筛选测试**

创建 `tests/planning/test_candidate_selector.py`：

```python
import pandas as pd

from trading_assistant.planning.candidate_selector import select_candidates


def test_select_candidates_filters_by_score_and_pool():
    frame = pd.DataFrame(
        [
            {"symbol": "000001", "name": "平安银行", "pool_type": "tradable", "opportunity_score": 82, "plan_confidence_score": 75},
            {"symbol": "600519", "name": "贵州茅台", "pool_type": "watch", "opportunity_score": 90, "plan_confidence_score": 80},
            {"symbol": "300001", "name": "样例科技", "pool_type": "tradable", "opportunity_score": 55, "plan_confidence_score": 90},
        ]
    )

    selected = select_candidates(frame, min_opportunity_score=76, min_plan_confidence_score=70, limit=8)

    assert list(selected["symbol"]) == ["000001"]
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/planning/test_candidate_selector.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 实现候选股筛选**

创建 `src/trading_assistant/planning/candidate_selector.py`：

```python
import pandas as pd


def select_candidates(
    scored_stocks: pd.DataFrame,
    *,
    min_opportunity_score: float,
    min_plan_confidence_score: float,
    limit: int,
) -> pd.DataFrame:
    filtered = scored_stocks[
        (scored_stocks["pool_type"] == "tradable")
        & (scored_stocks["opportunity_score"] >= min_opportunity_score)
        & (scored_stocks["plan_confidence_score"] >= min_plan_confidence_score)
    ]
    return filtered.sort_values(["opportunity_score", "plan_confidence_score"], ascending=False).head(limit).reset_index(drop=True)
```

创建 `src/trading_assistant/planning/__init__.py`：

```python
from trading_assistant.planning.candidate_selector import select_candidates

__all__ = ["select_candidates"]
```

- [ ] **Step 4: 运行测试**

Run:

```powershell
python -m pytest tests/planning/test_candidate_selector.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交**

```powershell
git add src/trading_assistant/planning tests/planning
git commit -m "feat: select conservative short-term candidates"
```

### Task 4.2: 实现仓位计算和交易计划生成

**Files:**
- Create: `src/trading_assistant/planning/position_sizing.py`
- Create: `src/trading_assistant/planning/trade_plan.py`
- Create: `tests/planning/test_trade_plan.py`

- [ ] **Step 1: 写交易计划测试**

创建 `tests/planning/test_trade_plan.py`：

```python
from trading_assistant.domain.enums import ActionAdvice
from trading_assistant.planning.trade_plan import build_trade_plan


def test_build_trade_plan_caps_position_when_market_is_weak():
    plan = build_trade_plan(
        symbol="000001",
        name="平安银行",
        current_price=10.0,
        opportunity_score=82,
        plan_confidence_score=80,
        market_score=45,
        portfolio_risk_score=20,
        atr_pct=0.03,
        theme="银行",
    )

    assert plan.position_pct <= 0.05
    assert plan.action_advice == ActionAdvice.WATCH_FOR_TRIGGER
    assert plan.stop_loss_price < plan.entry_price_low
    assert plan.first_take_profit_price > plan.entry_price_high
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/planning/test_trade_plan.py -v
```

Expected:

```text
ImportError
```

- [ ] **Step 3: 实现仓位计算**

创建 `src/trading_assistant/planning/position_sizing.py`：

```python
def compute_position_pct(
    *,
    opportunity_score: float,
    plan_confidence_score: float,
    market_score: float,
    portfolio_risk_score: float,
    stop_loss_distance_pct: float,
) -> float:
    if market_score < 40 or portfolio_risk_score >= 70:
        return 0.0
    base = 0.05
    if opportunity_score >= 86 and plan_confidence_score >= 80:
        base = 0.10
    elif opportunity_score >= 76 and plan_confidence_score >= 70:
        base = 0.08
    if market_score < 60:
        base = min(base, 0.05)
    if stop_loss_distance_pct > 0.04:
        base *= 0.5
    return round(base, 4)
```

- [ ] **Step 4: 实现交易计划生成**

创建 `src/trading_assistant/planning/trade_plan.py`：

```python
from trading_assistant.domain.enums import ActionAdvice, PoolType, RiskLevel
from trading_assistant.domain.models import TradePlan
from trading_assistant.planning.position_sizing import compute_position_pct


def build_trade_plan(
    *,
    symbol: str,
    name: str,
    current_price: float,
    opportunity_score: float,
    plan_confidence_score: float,
    market_score: float,
    portfolio_risk_score: float,
    atr_pct: float,
    theme: str,
) -> TradePlan:
    entry_low = round(current_price * 1.005, 2)
    entry_high = round(current_price * 1.03, 2)
    stop_loss = round(current_price * (1 - max(0.03, atr_pct)), 2)
    first_take_profit = round(entry_high * 1.06, 2)
    second_take_profit = round(entry_high * 1.10, 2)
    stop_distance_pct = (entry_low - stop_loss) / entry_low
    position_pct = compute_position_pct(
        opportunity_score=opportunity_score,
        plan_confidence_score=plan_confidence_score,
        market_score=market_score,
        portfolio_risk_score=portfolio_risk_score,
        stop_loss_distance_pct=stop_distance_pct,
    )
    risk_level = RiskLevel.MEDIUM if market_score < 60 else RiskLevel.LOW
    return TradePlan(
        symbol=symbol,
        name=name,
        pool_type=PoolType.TRADABLE,
        opportunity_score=opportunity_score,
        plan_confidence_score=plan_confidence_score,
        entry_trigger=f"{theme} 板块继续强于大盘，且 {symbol} 放量突破 {entry_low:.2f}",
        entry_price_low=entry_low,
        entry_price_high=entry_high,
        stop_loss_price=stop_loss,
        first_take_profit_price=first_take_profit,
        second_take_profit_price=second_take_profit,
        position_pct=position_pct,
        invalidation_condition=f"跌破 {stop_loss:.2f}、高开超过 3% 后回落、或 {theme} 板块退潮",
        risk_level=risk_level,
        action_advice=ActionAdvice.WATCH_FOR_TRIGGER if position_pct > 0 else ActionAdvice.NO_ACTION,
    )
```

- [ ] **Step 5: 运行测试**

Run:

```powershell
python -m pytest tests/planning/test_trade_plan.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 6: 提交**

```powershell
git add src/trading_assistant/planning tests/planning/test_trade_plan.py
git commit -m "feat: build conservative trade plans"
```

---

## 阶段 5：M5 智能体与报告

### Task 5.1: 实现 LLM 客户端抽象和 Mock 客户端

**Files:**
- Create: `src/trading_assistant/agents/llm_client.py`
- Create: `src/trading_assistant/agents/prompts.py`
- Create: `tests/agents/test_llm_client.py`

- [ ] **Step 1: 写 LLM 客户端测试**

创建 `tests/agents/test_llm_client.py`：

```python
from trading_assistant.agents.llm_client import MockLLMClient


def test_mock_llm_client_returns_structured_json():
    client = MockLLMClient(response='{"sentiment":"positive","event_type":"news","confidence":0.8}')

    result = client.complete_json(system_prompt="system", user_prompt="user")

    assert result["sentiment"] == "positive"
    assert result["confidence"] == 0.8
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/agents/test_llm_client.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 实现客户端抽象**

创建 `src/trading_assistant/agents/llm_client.py`：

```python
import json
from typing import Protocol


class LLMClient(Protocol):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        raise NotImplementedError


class MockLLMClient:
    def __init__(self, response: str) -> None:
        self.response = response

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        parsed = json.loads(self.response)
        if not isinstance(parsed, dict):
            raise ValueError("LLM response must be a JSON object")
        return parsed
```

创建 `src/trading_assistant/agents/prompts.py`：

```python
EVENT_EXTRACTION_SYSTEM_PROMPT = """
你是 A 股公告和新闻结构化助手。你只输出 JSON 对象，不输出自然语言解释。
字段必须包含 event_type、sentiment、confidence、summary、risk_flags、source_required。
sentiment 只能是 positive、negative、neutral、uncertain。
"""
```

- [ ] **Step 4: 运行测试**

Run:

```powershell
python -m pytest tests/agents/test_llm_client.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交**

```powershell
git add src/trading_assistant/agents tests/agents
git commit -m "feat: add llm client abstraction for agents"
```

### Task 5.2: 实现公告事件和新闻题材智能体

**Files:**
- Create: `src/trading_assistant/agents/event_agent.py`
- Create: `src/trading_assistant/agents/news_agent.py`
- Create: `tests/agents/test_event_news_agents.py`

- [ ] **Step 1: 写智能体测试**

创建 `tests/agents/test_event_news_agents.py`：

```python
from trading_assistant.agents.event_agent import EventAgent
from trading_assistant.agents.llm_client import MockLLMClient
from trading_assistant.agents.news_agent import NewsAgent


def test_event_agent_extracts_negative_event():
    client = MockLLMClient(
        response='{"event_type":"reduction","sentiment":"negative","confidence":0.9,"summary":"股东拟减持","risk_flags":["减持"],"source_required":true}'
    )
    agent = EventAgent(client)

    event = agent.extract(symbol="000001", text="股东计划减持不超过 2% 股份", source="sample")

    assert event["sentiment"] == "negative"
    assert "减持" in event["risk_flags"]


def test_news_agent_extracts_theme():
    client = MockLLMClient(
        response='{"theme":"银行","sentiment":"positive","confidence":0.8,"summary":"银行板块成交额放大","related_symbols":["000001"]}'
    )
    agent = NewsAgent(client)

    result = agent.extract_theme(text="银行板块成交额明显放大", source="sample")

    assert result["theme"] == "银行"
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/agents/test_event_news_agents.py -v
```

Expected:

```text
ImportError
```

- [ ] **Step 3: 实现智能体**

创建 `src/trading_assistant/agents/event_agent.py`：

```python
from trading_assistant.agents.llm_client import LLMClient
from trading_assistant.agents.prompts import EVENT_EXTRACTION_SYSTEM_PROMPT


class EventAgent:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def extract(self, *, symbol: str, text: str, source: str) -> dict[str, object]:
        user_prompt = f"symbol={symbol}\nsource={source}\ntext={text}"
        result = self.client.complete_json(
            system_prompt=EVENT_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        result["symbol"] = symbol
        result["source"] = source
        return result
```

创建 `src/trading_assistant/agents/news_agent.py`：

```python
from trading_assistant.agents.llm_client import LLMClient


NEWS_THEME_SYSTEM_PROMPT = """
你是 A 股题材新闻结构化助手。你只输出 JSON 对象。
字段必须包含 theme、sentiment、confidence、summary、related_symbols。
sentiment 只能是 positive、negative、neutral、uncertain。
"""


class NewsAgent:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def extract_theme(self, *, text: str, source: str) -> dict[str, object]:
        result = self.client.complete_json(
            system_prompt=NEWS_THEME_SYSTEM_PROMPT,
            user_prompt=f"source={source}\ntext={text}",
        )
        result["source"] = source
        return result
```

创建 `src/trading_assistant/agents/__init__.py`：

```python
from trading_assistant.agents.event_agent import EventAgent
from trading_assistant.agents.llm_client import LLMClient, MockLLMClient
from trading_assistant.agents.news_agent import NewsAgent

__all__ = ["EventAgent", "LLMClient", "MockLLMClient", "NewsAgent"]
```

- [ ] **Step 4: 运行测试**

Run:

```powershell
python -m pytest tests/agents/test_event_news_agents.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: 提交**

```powershell
git add src/trading_assistant/agents tests/agents/test_event_news_agents.py
git commit -m "feat: extract announcement events and news themes"
```

### Task 5.3: 实现盘后报告生成

**Files:**
- Create: `src/trading_assistant/reporting/markdown.py`
- Create: `src/trading_assistant/reporting/daily_report.py`
- Create: `tests/reporting/test_daily_report.py`

- [ ] **Step 1: 写报告测试**

创建 `tests/reporting/test_daily_report.py`：

```python
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
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/reporting/test_daily_report.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 实现报告生成**

创建 `src/trading_assistant/reporting/markdown.py`：

```python
def bullet_list(items: list[str]) -> str:
    if not items:
        return "- 无"
    return "\n".join(f"- {item}" for item in items)
```

创建 `src/trading_assistant/reporting/daily_report.py`：

```python
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
```

创建 `src/trading_assistant/reporting/__init__.py`：

```python
from trading_assistant.reporting.daily_report import build_daily_report

__all__ = ["build_daily_report"]
```

- [ ] **Step 4: 运行测试**

Run:

```powershell
python -m pytest tests/reporting/test_daily_report.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交**

```powershell
git add src/trading_assistant/reporting tests/reporting
git commit -m "feat: generate daily markdown trading report"
```

---

## 阶段 6：M6 仪表盘与提醒

### Task 6.1: 实现飞书 Webhook 推送和提醒分发

**Files:**
- Create: `src/trading_assistant/alerts/feishu.py`
- Create: `src/trading_assistant/alerts/dispatcher.py`
- Create: `tests/alerts/test_dispatcher.py`

- [ ] **Step 1: 写分发测试**

创建 `tests/alerts/test_dispatcher.py`：

```python
from trading_assistant.alerts.dispatcher import AlertDispatcher
from trading_assistant.alerts.models import Alert, AlertLevel


class FakeSender:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send_text(self, text: str) -> None:
        self.messages.append(text)


def test_dispatcher_sends_only_p0_p1_by_default():
    sender = FakeSender()
    dispatcher = AlertDispatcher(sender)
    alerts = [
        Alert(AlertLevel.P0, "000001", "跌破硬止损位"),
        Alert(AlertLevel.P2, "000001", "接近触发价"),
    ]

    dispatcher.dispatch(alerts)

    assert sender.messages == ["[P0] 000001 跌破硬止损位"]
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/alerts/test_dispatcher.py -v
```

Expected:

```text
ImportError
```

- [ ] **Step 3: 实现飞书发送器和分发器**

创建 `src/trading_assistant/alerts/feishu.py`：

```python
import httpx


class FeishuWebhookSender:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def send_text(self, text: str) -> None:
        if not self.webhook_url:
            return
        response = httpx.post(self.webhook_url, json={"msg_type": "text", "content": {"text": text}}, timeout=10)
        response.raise_for_status()
```

创建 `src/trading_assistant/alerts/dispatcher.py`：

```python
from typing import Protocol

from trading_assistant.alerts.models import Alert, AlertLevel


class TextSender(Protocol):
    def send_text(self, text: str) -> None:
        raise NotImplementedError


class AlertDispatcher:
    def __init__(self, sender: TextSender) -> None:
        self.sender = sender

    def dispatch(self, alerts: list[Alert]) -> None:
        for alert in alerts:
            if alert.level in {AlertLevel.P0, AlertLevel.P1}:
                self.sender.send_text(f"[{alert.level}] {alert.symbol} {alert.message}")
```

- [ ] **Step 4: 运行测试**

Run:

```powershell
python -m pytest tests/alerts/test_dispatcher.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交**

```powershell
git add src/trading_assistant/alerts tests/alerts/test_dispatcher.py
git commit -m "feat: dispatch critical alerts to webhook"
```

### Task 6.2: 实现 FastAPI 仪表盘

**Files:**
- Create: `src/trading_assistant/web/app.py`
- Create: `src/trading_assistant/web/routes.py`
- Create: `src/trading_assistant/web/view_models.py`
- Create: `src/trading_assistant/web/templates/base.html`
- Create: `src/trading_assistant/web/templates/dashboard.html`
- Create: `src/trading_assistant/web/templates/holdings.html`
- Create: `src/trading_assistant/web/templates/candidates.html`
- Create: `src/trading_assistant/web/templates/backtest.html`
- Create: `src/trading_assistant/web/static/app.css`
- Create: `tests/web/test_app.py`

- [ ] **Step 1: 写 Web 测试**

创建 `tests/web/test_app.py`：

```python
from fastapi.testclient import TestClient

from trading_assistant.web.app import create_app


def test_dashboard_home_renders():
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "A 股短线交易辅助系统" in response.text
    assert "持仓风险" in response.text
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/web/test_app.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 实现 Web 应用**

创建 `src/trading_assistant/web/app.py`：

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from trading_assistant.web.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="A 股短线交易辅助系统")
    app.include_router(router)
    app.mount("/static", StaticFiles(directory="src/trading_assistant/web/static"), name="static")
    return app


app = create_app()
```

创建 `src/trading_assistant/web/routes.py`：

```python
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from trading_assistant.web.view_models import build_dashboard_view

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "view": build_dashboard_view()},
    )
```

创建 `src/trading_assistant/web/view_models.py`：

```python
def build_dashboard_view() -> dict[str, object]:
    return {
        "market_score": 58,
        "portfolio_risk": "中等",
        "candidate_count": 3,
        "critical_alerts": 0,
        "sections": ["持仓风险", "市场环境", "重点候选", "盘中提醒", "回测复盘"],
    }
```

- [ ] **Step 4: 创建模板和样式**

创建 `src/trading_assistant/web/templates/base.html`：

```html
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>A 股短线交易辅助系统</title>
  <link rel="stylesheet" href="/static/app.css">
</head>
<body>
  <header class="topbar">
    <h1>A 股短线交易辅助系统</h1>
    <nav>
      <a href="/">总览</a>
    </nav>
  </header>
  <main class="layout">
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

创建 `src/trading_assistant/web/templates/dashboard.html`：

```html
{% extends "base.html" %}
{% block content %}
<section class="summary-grid">
  <article><span>市场环境分</span><strong>{{ view.market_score }}</strong></article>
  <article><span>持仓风险</span><strong>{{ view.portfolio_risk }}</strong></article>
  <article><span>重点候选</span><strong>{{ view.candidate_count }}</strong></article>
  <article><span>P0/P1 提醒</span><strong>{{ view.critical_alerts }}</strong></article>
</section>
<section class="panel">
  <h2>工作台</h2>
  <ul>
    {% for section in view.sections %}
    <li>{{ section }}</li>
    {% endfor %}
  </ul>
</section>
{% endblock %}
```

创建空模板文件：

```powershell
New-Item -ItemType File -Force -Path src/trading_assistant/web/templates/holdings.html
New-Item -ItemType File -Force -Path src/trading_assistant/web/templates/candidates.html
New-Item -ItemType File -Force -Path src/trading_assistant/web/templates/backtest.html
```

创建 `src/trading_assistant/web/static/app.css`：

```css
body {
  margin: 0;
  font-family: Arial, "Microsoft YaHei", sans-serif;
  background: #f6f7f9;
  color: #1f2933;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: #ffffff;
  border-bottom: 1px solid #d8dee6;
}
.topbar h1 {
  margin: 0;
  font-size: 20px;
}
.layout {
  max-width: 1180px;
  margin: 0 auto;
  padding: 24px;
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.summary-grid article,
.panel {
  background: #ffffff;
  border: 1px solid #d8dee6;
  border-radius: 8px;
  padding: 16px;
}
.summary-grid span {
  display: block;
  color: #52616f;
  font-size: 13px;
}
.summary-grid strong {
  display: block;
  margin-top: 8px;
  font-size: 24px;
}
@media (max-width: 760px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
```

- [ ] **Step 5: 运行测试和本地服务**

Run:

```powershell
python -m pytest tests/web/test_app.py -v
python -m uvicorn trading_assistant.web.app:app --reload --port 8000
```

Expected:

```text
1 passed
Uvicorn running on http://127.0.0.1:8000
```

- [ ] **Step 6: 提交**

```powershell
git add src/trading_assistant/web tests/web
git commit -m "feat: add web dashboard shell"
```

### Task 6.3: 实现定时任务入口

**Files:**
- Create: `src/trading_assistant/scheduler/jobs.py`
- Create: `scripts/run_daily_after_close.py`
- Create: `scripts/run_intraday_monitor.py`
- Create: `tests/scheduler/test_jobs.py`

- [ ] **Step 1: 写任务编排测试**

创建 `tests/scheduler/test_jobs.py`：

```python
from trading_assistant.scheduler.jobs import build_job_plan


def test_build_job_plan_contains_daily_and_intraday_jobs():
    jobs = build_job_plan()

    assert "daily_after_close" in jobs
    assert "intraday_monitor" in jobs
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/scheduler/test_jobs.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 实现任务计划**

创建 `src/trading_assistant/scheduler/jobs.py`：

```python
def build_job_plan() -> dict[str, str]:
    return {
        "daily_after_close": "15:30 拉取行情、计算因子、生成评分、生成交易计划和日报",
        "evening_agent_report": "20:30 处理公告新闻、补充智能体解释",
        "intraday_monitor": "交易时段每 5 分钟检查持仓和候选股关键价位",
        "weekly_review": "周末统计信号表现、回撤、胜率和误判案例",
    }
```

创建 `scripts/run_daily_after_close.py`：

```python
from trading_assistant.scheduler.jobs import build_job_plan


def main() -> None:
    print(build_job_plan()["daily_after_close"])


if __name__ == "__main__":
    main()
```

创建 `scripts/run_intraday_monitor.py`：

```python
from trading_assistant.scheduler.jobs import build_job_plan


def main() -> None:
    print(build_job_plan()["intraday_monitor"])


if __name__ == "__main__":
    main()
```

创建 `src/trading_assistant/scheduler/__init__.py`：

```python
from trading_assistant.scheduler.jobs import build_job_plan

__all__ = ["build_job_plan"]
```

- [ ] **Step 4: 运行测试和脚本**

Run:

```powershell
python -m pytest tests/scheduler/test_jobs.py -v
python scripts/run_daily_after_close.py
python scripts/run_intraday_monitor.py
```

Expected:

```text
1 passed
15:30 拉取行情、计算因子、生成评分、生成交易计划和日报
交易时段每 5 分钟检查持仓和候选股关键价位
```

- [ ] **Step 5: 提交**

```powershell
git add src/trading_assistant/scheduler scripts/run_daily_after_close.py scripts/run_intraday_monitor.py tests/scheduler
git commit -m "feat: add scheduled workflow entrypoints"
```

---

## 阶段 7：M7 回测与复盘

### Task 7.1: 实现信号台账

**Files:**
- Create: `src/trading_assistant/backtest/signal_ledger.py`
- Create: `tests/backtest/test_signal_ledger.py`

- [ ] **Step 1: 写信号台账测试**

创建 `tests/backtest/test_signal_ledger.py`：

```python
from trading_assistant.backtest.signal_ledger import SignalLedger


def test_signal_ledger_records_signal():
    ledger = SignalLedger()

    ledger.record_signal(
        trade_date="2026-06-12",
        symbol="000001",
        signal_type="candidate",
        score=82,
        action="watch_for_trigger",
    )

    rows = ledger.to_frame()
    assert len(rows) == 1
    assert rows.iloc[0]["symbol"] == "000001"
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/backtest/test_signal_ledger.py -v
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 实现信号台账**

创建 `src/trading_assistant/backtest/signal_ledger.py`：

```python
import pandas as pd


class SignalLedger:
    def __init__(self) -> None:
        self._rows: list[dict[str, object]] = []

    def record_signal(
        self,
        *,
        trade_date: str,
        symbol: str,
        signal_type: str,
        score: float,
        action: str,
    ) -> None:
        self._rows.append(
            {
                "trade_date": trade_date,
                "symbol": symbol,
                "signal_type": signal_type,
                "score": score,
                "action": action,
            }
        )

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self._rows)
```

创建 `src/trading_assistant/backtest/__init__.py`：

```python
from trading_assistant.backtest.signal_ledger import SignalLedger

__all__ = ["SignalLedger"]
```

- [ ] **Step 4: 运行测试**

Run:

```powershell
python -m pytest tests/backtest/test_signal_ledger.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交**

```powershell
git add src/trading_assistant/backtest tests/backtest
git commit -m "feat: record strategy signals for backtest"
```

### Task 7.2: 实现 1/3/5 日收益回测指标

**Files:**
- Create: `src/trading_assistant/backtest/engine.py`
- Create: `src/trading_assistant/backtest/metrics.py`
- Create: `tests/backtest/test_engine_metrics.py`

- [ ] **Step 1: 写回测指标测试**

创建 `tests/backtest/test_engine_metrics.py`：

```python
import pandas as pd

from trading_assistant.backtest.engine import evaluate_forward_returns
from trading_assistant.backtest.metrics import summarize_returns


def test_forward_returns_and_summary():
    signals = pd.DataFrame(
        [{"trade_date": "2026-06-10", "symbol": "000001", "signal_type": "candidate", "score": 82, "action": "watch"}]
    )
    prices = pd.DataFrame(
        [
            {"trade_date": "2026-06-10", "symbol": "000001", "close": 10.0},
            {"trade_date": "2026-06-11", "symbol": "000001", "close": 10.3},
            {"trade_date": "2026-06-13", "symbol": "000001", "close": 10.5},
            {"trade_date": "2026-06-15", "symbol": "000001", "close": 10.8},
        ]
    )

    evaluated = evaluate_forward_returns(signals, prices)
    summary = summarize_returns(evaluated)

    assert evaluated.iloc[0]["return_1d"] == 0.03
    assert summary["win_rate_1d"] == 1.0
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/backtest/test_engine_metrics.py -v
```

Expected:

```text
ImportError
```

- [ ] **Step 3: 实现回测引擎和指标**

创建 `src/trading_assistant/backtest/engine.py`：

```python
import pandas as pd


def evaluate_forward_returns(signals: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    prices = prices.copy()
    prices["trade_date"] = pd.to_datetime(prices["trade_date"])
    rows: list[dict[str, object]] = []
    for signal in signals.to_dict(orient="records"):
        symbol_prices = prices[prices["symbol"] == signal["symbol"]].sort_values("trade_date").reset_index(drop=True)
        start_date = pd.to_datetime(signal["trade_date"])
        start_row = symbol_prices[symbol_prices["trade_date"] == start_date]
        if start_row.empty:
            continue
        start_index = int(start_row.index[0])
        start_close = float(start_row.iloc[0]["close"])
        row = dict(signal)
        for horizon in [1, 3, 5]:
            target_index = min(start_index + horizon, len(symbol_prices) - 1)
            target_close = float(symbol_prices.iloc[target_index]["close"])
            row[f"return_{horizon}d"] = round((target_close - start_close) / start_close, 4)
        rows.append(row)
    return pd.DataFrame(rows)
```

创建 `src/trading_assistant/backtest/metrics.py`：

```python
import pandas as pd


def summarize_returns(evaluated: pd.DataFrame) -> dict[str, float]:
    if evaluated.empty:
        return {"win_rate_1d": 0.0, "avg_return_1d": 0.0, "avg_return_3d": 0.0, "avg_return_5d": 0.0}
    return {
        "win_rate_1d": round(float((evaluated["return_1d"] > 0).mean()), 4),
        "avg_return_1d": round(float(evaluated["return_1d"].mean()), 4),
        "avg_return_3d": round(float(evaluated["return_3d"].mean()), 4),
        "avg_return_5d": round(float(evaluated["return_5d"].mean()), 4),
    }
```

- [ ] **Step 4: 运行测试**

Run:

```powershell
python -m pytest tests/backtest/test_engine_metrics.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交**

```powershell
git add src/trading_assistant/backtest tests/backtest/test_engine_metrics.py
git commit -m "feat: evaluate forward returns for signals"
```

---

## 阶段 8：部署、运行手册和验收

### Task 8.1: 创建 Docker Compose 和本地启动脚本

**Files:**
- Create: `docker-compose.yml`
- Create: `scripts/seed_sample_data.py`
- Modify: `README.md`
- Create: `tests/test_docker_compose_exists.py`

- [ ] **Step 1: 写部署文件测试**

创建 `tests/test_docker_compose_exists.py`：

```python
from pathlib import Path

import yaml


def test_docker_compose_defines_postgres_and_redis():
    compose = yaml.safe_load(Path("docker-compose.yml").read_text(encoding="utf-8"))

    assert "postgres" in compose["services"]
    assert "redis" in compose["services"]
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```powershell
python -m pytest tests/test_docker_compose_exists.py -v
```

Expected:

```text
FileNotFoundError
```

- [ ] **Step 3: 创建 Docker Compose**

创建 `docker-compose.yml`：

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: trading_assistant
      POSTGRES_USER: trading_assistant
      POSTGRES_PASSWORD: trading_assistant
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  redis:
    image: redis:7
    ports:
      - "6379:6379"
volumes:
  postgres_data:
```

创建 `scripts/seed_sample_data.py`：

```python
from pathlib import Path

from trading_assistant.portfolio.importer import load_holdings_csv


def main() -> None:
    holdings = load_holdings_csv(Path("data/samples/holdings.csv"))
    print(f"loaded {len(holdings)} sample holdings")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 更新 README 运行说明**

在 `README.md` 增加：

````markdown
## 本地启动

```powershell
docker compose up -d postgres redis
python scripts/seed_sample_data.py
python -m uvicorn trading_assistant.web.app:app --reload --port 8000
```

访问 http://127.0.0.1:8000 查看仪表盘。
````

- [ ] **Step 5: 运行测试**

Run:

```powershell
python -m pytest tests/test_docker_compose_exists.py -v
```

Expected:

```text
1 passed
```

- [ ] **Step 6: 提交**

```powershell
git add docker-compose.yml scripts/seed_sample_data.py README.md tests/test_docker_compose_exists.py
git commit -m "chore: add local infrastructure setup"
```

### Task 8.2: 全量质量检查和 MVP 验收

**Files:**
- Modify: `README.md`
- Create: `docs/mvp-acceptance-checklist.md`

- [ ] **Step 1: 创建验收清单**

创建 `docs/mvp-acceptance-checklist.md`：

```markdown
# MVP 验收清单

## M1 数据与持仓底座

- [ ] 能读取示例持仓。
- [ ] 能读取示例日线、分钟线和板块数据。
- [ ] 能区分可交易池、观察池、禁入池和持仓池。

## M2 因子与评分引擎

- [ ] 能计算技术、量价、市场和板块因子。
- [ ] 能加载权重。
- [ ] 能输出可追溯评分。

## M3 持仓风控与卖出规则

- [ ] 能识别硬止损。
- [ ] 能输出继续持有、收紧止损、减仓、清仓建议。
- [ ] 能生成 P0/P1 持仓提醒。

## M4 盘后选股与交易计划

- [ ] 能筛选重点候选。
- [ ] 能生成买入触发、止损、止盈、仓位和失效条件。
- [ ] 能拦截市场环境差、持仓风险高、盈亏比不足的交易计划。

## M5 智能体与报告

- [ ] 能用 Mock LLM 结构化公告事件。
- [ ] 能用 Mock LLM 结构化新闻题材。
- [ ] 能生成固定结构的盘后报告。

## M6 仪表盘与提醒

- [ ] 能打开 Web 仪表盘。
- [ ] 能展示市场、持仓、候选和提醒摘要。
- [ ] 能通过 Webhook 分发 P0/P1 提醒。

## M7 回测与复盘

- [ ] 能记录信号。
- [ ] 能统计 1/3/5 日收益。
- [ ] 能输出胜率和平均收益。
```

- [ ] **Step 2: 运行全量测试**

Run:

```powershell
python -m pytest -v
```

Expected:

```text
所有测试通过
```

- [ ] **Step 3: 运行静态检查**

Run:

```powershell
python -m ruff check .
python -m mypy src
```

Expected:

```text
All checks passed!
Success: no issues found
```

- [ ] **Step 4: 启动服务并人工验收**

Run:

```powershell
python -m uvicorn trading_assistant.web.app:app --reload --port 8000
```

Expected:

```text
Uvicorn running on http://127.0.0.1:8000
```

浏览器打开：

```text
http://127.0.0.1:8000
```

页面应显示：

- A 股短线交易辅助系统；
- 市场环境分；
- 持仓风险；
- 重点候选；
- P0/P1 提醒。

- [ ] **Step 5: 提交**

```powershell
git add README.md docs/mvp-acceptance-checklist.md
git commit -m "docs: add MVP acceptance checklist"
```

### Task 8.3: 创建运行手册和故障处理清单

**Files:**
- Create: `docs/ops-runbook.md`
- Modify: `README.md`
- Create: `tests/test_ops_docs_exist.py`

- [ ] **Step 1: 写运行文档存在性测试**

创建 `tests/test_ops_docs_exist.py`：

```python
from pathlib import Path


def test_ops_runbook_exists_and_mentions_core_workflows():
    text = Path("docs/ops-runbook.md").read_text(encoding="utf-8")

    assert "盘后任务" in text
    assert "盘中提醒" in text
    assert "数据源失败" in text
    assert "备份" in text
```

- [ ] **Step 2: 创建运行手册**

创建 `docs/ops-runbook.md`，至少包含：

- 本地启动和停止；
- 环境变量说明；
- 盘后任务执行步骤；
- 盘中提醒执行步骤；
- 样例数据重置步骤；
- 数据源失败时的降级策略；
- LLM 或 Webhook 不可用时的处理方式；
- PostgreSQL 和本地报告备份方式；
- 常见错误排查；
- 每日运维检查清单。

- [ ] **Step 3: 更新 README 入口**

在 `README.md` 增加运行手册链接和最小闭环执行命令。

- [ ] **Step 4: 运行测试并提交**

Run:

```powershell
python -m pytest tests/test_ops_docs_exist.py -v
```

Expected:

```text
1 passed
```

提交：

```powershell
git add README.md docs/ops-runbook.md tests/test_ops_docs_exist.py
git commit -m "docs: add operations runbook"
```

### Task 8.4: 增加数据质量和可观测性要求

**Files:**
- Create: `src/trading_assistant/observability/__init__.py`
- Create: `src/trading_assistant/observability/task_log.py`
- Create: `src/trading_assistant/data_sources/quality.py`
- Create: `tests/observability/test_task_log.py`
- Create: `tests/data_sources/test_quality.py`

- [ ] **Step 1: 写任务日志和数据质量测试**

测试应覆盖：

- 任务日志包含任务名、交易日、开始时间、结束时间、输入数量、输出数量、状态和错误原因；
- 行情数据缺失关键列时返回失败；
- 行情数据存在重复股票和交易日时返回警告；
- 数据质量失败时，上层流程可以把标的降级为观察或禁入，而不是继续生成交易计划。

- [ ] **Step 2: 实现最小可观测性工具**

实现 `TaskRunLog` 和 `DataQualityResult` 等轻量对象，不急着接入完整 OpenTelemetry。第一阶段先确保日志结构稳定，后续再扩展到 Prometheus 或 OpenTelemetry。

- [ ] **Step 3: 把任务日志接入关键入口**

至少接入：

- 盘后任务；
- 盘中监控任务；
- 智能体报告任务；
- 回测任务。

- [ ] **Step 4: 运行测试并提交**

Run:

```powershell
python -m pytest tests/observability tests/data_sources -v
```

Expected:

```text
所有相关测试通过
```

提交：

```powershell
git add src/trading_assistant/observability src/trading_assistant/data_sources/quality.py tests/observability tests/data_sources
git commit -m "feat: add data quality and task observability"
```

### Task 8.5: 创建风险与技术债登记表

**Files:**
- Create: `docs/risk-and-debt-register.md`
- Modify: `docs/mvp-acceptance-checklist.md`

- [ ] **Step 1: 创建风险与技术债登记表**

创建 `docs/risk-and-debt-register.md`，按以下分类维护：

- 数据源风险；
- 策略和回测风险；
- 工程稳定性风险；
- 安全与权限风险；
- 合规边界风险；
- 已接受的技术债；
- 必须在进入下一阶段前偿还的技术债。

每条记录至少包含：

- 描述；
- 影响；
- 触发条件；
- 缓解措施；
- 负责人；
- 状态；
- 复查日期。

- [ ] **Step 2: 把登记表纳入 MVP 验收**

在 `docs/mvp-acceptance-checklist.md` 增加：

- [ ] 所有 P0/P1 风险都有缓解措施；
- [ ] 所有外部数据源都有 Mock 或样例数据回退；
- [ ] 所有已知技术债都有负责人和复查日期；
- [ ] 下一阶段前必须偿还的技术债没有遗漏。

- [ ] **Step 3: 提交**

```powershell
git add docs/risk-and-debt-register.md docs/mvp-acceptance-checklist.md
git commit -m "docs: track MVP risks and technical debt"
```

---

## 5. 阶段验收标准

### 阶段 0 验收

- `python -m pytest tests/test_settings.py tests/test_config_files.py -v` 通过；
- 配置文件存在且权重和为 1；
- 示例数据可读取。

### M1 验收

- 持仓 CSV 能导入为领域模型；
- 样例行情 Provider 可读取日线、分钟线和板块；
- 数据库仓储可以保存和读取持仓；
- AKShare 和 Tushare Provider 有可测试外壳，真实数据接入不影响单元测试稳定性。

### M2 验收

- 可交易池、观察池、禁入池能按规则分层；
- 技术、量价、市场、板块因子能用样例数据计算；
- 四类评分引擎可以输出总分、组件分和原因。

### M3 验收

- 持仓硬止损能输出 P0 或清仓优先；
- 技术破位、资金流出、板块退潮、负面事件能抬高风险分；
- P0/P1/P2/P3 提醒规则可测试。

### M4 验收

- 候选股只从可交易池中产生；
- 重点候选要求短线机会分和交易计划可信分同时达标；
- 交易计划包含买入触发、买入区间、止损、止盈、仓位和失效条件；
- 市场弱或持仓风险高时，仓位会自动降低或归零。

### M5 验收

- 智能体通过 LLMClient 接口接入；
- 测试使用 MockLLMClient，不依赖外部 API；
- 公告和新闻输出结构化 JSON；
- 盘后报告包含固定九段结构。

### M6 验收

- Web 首页可以访问；
- 仪表盘显示市场、持仓、候选、提醒摘要；
- P0/P1 会进入推送；
- P2/P3 默认只展示或汇总。

### M7 验收

- 信号能记录成台账；
- 能计算 1/3/5 日收益；
- 能统计 1 日胜率和平均收益；
- 后续可以扩展最大回撤、错误卖出率和错过反弹率。

---

## 6. 执行策略

建议使用子代理驱动开发：

1. 每个 Task 派一个新子代理执行；
2. 子代理只完成一个 Task；
3. 主代理在每个 Task 后 review；
4. 每个 Task 单独运行测试；
5. 每个 Task 单独提交；
6. 出现测试失败时先使用系统化调试流程，不跳过失败。

如果当前环境没有 `git`，执行者仍按任务边界工作，并在每个任务结束时记录修改文件和测试结果；安装或恢复 `git` 后再补提交。

## 7. 第一阶段之外的独立计划

以下内容不进入本 MVP 开发计划：

- Level-2 和逐笔成交接入；
- 委托队列和盘口模型；
- 券商接口；
- 自动下单；
- 程序化交易合规报备自动化；
- 本地深度学习预测模型训练；
- 多账户和多策略组合管理。

这些能力需要在 MVP 稳定运行、回测数据积累后分别创建独立设计文档和实施计划。
