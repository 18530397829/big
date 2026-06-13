# A Share Trading Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a conservative A-share short-term trading assistant that prioritizes existing-position risk control, then market regime checks, then 1-5 trading-day candidate selection with explainable trade plans, alerts, reports, and backtests.

**Architecture:** Use a single repository MVP with clear module boundaries: Python/FastAPI backend, PostgreSQL persistence, Redis-backed job state, scheduled ingestion/scoring jobs, source-grounded LLM agents, and a React dashboard. The MVP keeps trading decisions inside deterministic rule engines; agents explain, classify, and summarize, but cannot override hard risk rules.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic, Pandas/Polars, AKShare/Tushare adapters, PostgreSQL, Redis, Pytest, React + TypeScript + Vite, TanStack Query, ECharts, Docker Compose.

---

## 0. Scope And Delivery Strategy

The confirmed design covers multiple subsystems: market data, holdings, factors, scoring, trade plans, agents, alerts, dashboard, backtesting, and operations. This document is a master implementation plan for an MVP that delivers a working vertical slice across all required subsystems. Each phase below produces testable software on its own and can be executed by a fresh worker.

Fixed MVP assumptions:

- Market scope: A-share equities only.
- Holding import: CSV upload and CLI import first.
- Alerts: Feishu webhook first, with a provider interface for enterprise WeChat, email, and Telegram.
- Dashboard access: private LAN deployment first.
- Deployment target: Docker Compose on DGX Spark/Linux or a Linux host connected to DGX Spark.
- Automation: scheduled jobs only; no automatic order placement.
- Data source priority: provider interface + mock fixtures + AKShare/Tushare adapters.
- Model use: commercial or local LLMs only for structured text analysis and report generation. Final scores come from deterministic rules.

MVP non-goals:

- No automatic trading.
- No Level-2 or tick-by-tick dependency.
- No high-frequency trading loop.
- No claim of deterministic price prediction.
- No deep learning model as the first-stage decision core.

## 1. Repository File Structure

Create this structure before implementation begins:

```text
backend/
  app/
    __init__.py
    main.py
    api/
      __init__.py
      deps.py
      routes/
        __init__.py
        health.py
        holdings.py
        market.py
        scores.py
        candidates.py
        plans.py
        reports.py
        alerts.py
        backtests.py
    core/
      __init__.py
      config.py
      logging.py
      time.py
      enums.py
      errors.py
    db/
      __init__.py
      base.py
      session.py
      migrations/
    models/
      __init__.py
      security.py
      market_data.py
      holding.py
      factor.py
      score.py
      trade_plan.py
      event.py
      alert.py
      backtest.py
      report.py
    schemas/
      __init__.py
      security.py
      market_data.py
      holding.py
      factor.py
      score.py
      trade_plan.py
      event.py
      alert.py
      backtest.py
      report.py
    repositories/
      __init__.py
      securities.py
      market_data.py
      holdings.py
      factors.py
      scores.py
      trade_plans.py
      events.py
      alerts.py
      backtests.py
      reports.py
    data_sources/
      __init__.py
      base.py
      mock_provider.py
      akshare_provider.py
      tushare_provider.py
      normalizers.py
    services/
      __init__.py
      trading_calendar.py
      stock_pool.py
      data_quality.py
      factors/
        __init__.py
        technical.py
        market_environment.py
        sector_strength.py
        liquidity.py
        event_risk.py
      scoring/
        __init__.py
        config.py
        trace.py
        market_score.py
        holding_risk_score.py
        opportunity_score.py
        plan_confidence_score.py
        orchestrator.py
      portfolio/
        __init__.py
        importer.py
        risk_rules.py
        position_sizing.py
      plans/
        __init__.py
        generator.py
        risk_gates.py
      agents/
        __init__.py
        llm_gateway.py
        schemas.py
        announcement_agent.py
        news_theme_agent.py
        holding_review_agent.py
        trade_plan_agent.py
        daily_review_agent.py
      reports/
        __init__.py
        daily_report.py
        markdown_renderer.py
      alerts/
        __init__.py
        base.py
        feishu.py
        router.py
      backtest/
        __init__.py
        signal_ledger.py
        simulator.py
        metrics.py
      scheduler/
        __init__.py
        jobs.py
        runner.py
  tests/
    conftest.py
    fixtures/
      holdings_sample.csv
      securities_sample.json
      daily_bars_sample.csv
      intraday_bars_sample.csv
      announcements_sample.json
      news_sample.json
    unit/
      test_config.py
      test_stock_pool.py
      test_data_quality.py
      test_technical_factors.py
      test_market_score.py
      test_holding_risk_score.py
      test_opportunity_score.py
      test_plan_confidence_score.py
      test_position_sizing.py
      test_trade_plan_generator.py
      test_agents_schema.py
      test_alert_router.py
      test_backtest_metrics.py
    integration/
      test_ingestion_pipeline.py
      test_daily_scoring_pipeline.py
      test_daily_report_pipeline.py
      test_api_routes.py
  alembic.ini
  pyproject.toml
  Dockerfile
frontend/
  index.html
  package.json
  tsconfig.json
  vite.config.ts
  src/
    main.tsx
    app/App.tsx
    api/client.ts
    api/types.ts
    pages/Dashboard.tsx
    pages/Holdings.tsx
    pages/Candidates.tsx
    pages/TradePlans.tsx
    pages/Backtests.tsx
    components/Layout.tsx
    components/ScoreBadge.tsx
    components/RiskTable.tsx
    components/CandidateTable.tsx
    components/PlanDetail.tsx
    components/AlertList.tsx
    components/MarketRegimePanel.tsx
    components/BacktestSummary.tsx
  tests/
    dashboard.spec.ts
infra/
  docker-compose.yml
  postgres/init.sql
  redis/redis.conf
  env.example
scripts/
  dev.ps1
  dev.sh
  import_holdings.py
  run_daily_pipeline.py
  run_backtest.py
docs/
  operations/
    data_sources.md
    deployment.md
    daily_runbook.md
```

## 2. Phase Overview

| Phase | Name | Primary Outcome | Exit Gate |
|---|---|---|---|
| P0 | Foundation | Repo, backend app, DB, test harness, Docker Compose | Health API and tests pass |
| P1 | Data And Holdings | Securities, bars, sectors, holdings, data quality | Daily data and holding import work with fixtures |
| P2 | Factors And Scores | Market, holding risk, opportunity, plan confidence scores | Scores are traceable to factor inputs |
| P3 | Portfolio Risk | Sell states, hard stops, take-profit, sizing, risk gates | Existing holdings get clear daily actions |
| P4 | Candidate And Plan Pipeline | After-close stock pool, candidates, complete trade plans | 3-8重点候选 and plans generated from fixtures |
| P5 | Agents And Reports | Event/news agents, report generator, source-grounded summaries | Daily markdown report includes sources |
| P6 | Dashboard And Alerts | LAN dashboard, Feishu alerts, API routes | Human can review holdings, candidates, plans, alerts |
| P7 | Backtest And Review | Signal ledger, 1/3/5-day metrics, sell-rule evaluation | Signals produce repeatable backtest metrics |
| P8 | Deployment And Ops | Scheduler, logs, runbooks, backup, DGX deployment path | One-command daily pipeline on target host |
| P9 | Post-MVP Expansion | Data upgrades, local model experiments, compliance path | Research backlog and model dataset contracts ready |

## 3. Phase P0: Foundation

### Task 1: Backend Project Bootstrap

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/main.py`
- Create: `backend/app/api/routes/health.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/logging.py`
- Create: `backend/tests/unit/test_config.py`
- Create: `backend/tests/integration/test_api_routes.py`

- [ ] **Step 1: Write failing configuration and health tests**

```python
# backend/tests/unit/test_config.py
from app.core.config import Settings

def test_settings_defaults_are_conservative():
    settings = Settings()
    assert settings.app_name == "a-share-trading-assistant"
    assert settings.environment == "local"
    assert settings.allow_auto_trade is False
```

```python
# backend/tests/integration/test_api_routes.py
from fastapi.testclient import TestClient
from app.main import app

def test_health_route_returns_ok():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "auto_trade": False}
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_config.py tests/integration/test_api_routes.py -v`  
Expected: tests fail because the app modules do not exist.

- [ ] **Step 3: Implement minimal FastAPI app and settings**

Create `Settings` with Pydantic settings, `allow_auto_trade=False`, and a `/health` route that returns the exact JSON in the test.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_config.py tests/integration/test_api_routes.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/pyproject.toml backend/app backend/tests
git commit -m "feat: bootstrap backend health service"
```

### Task 2: Database Models And Migrations

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/models/security.py`
- Create: `backend/app/models/market_data.py`
- Create: `backend/app/models/holding.py`
- Create: `backend/app/models/factor.py`
- Create: `backend/app/models/score.py`
- Create: `backend/app/models/trade_plan.py`
- Create: `backend/app/models/event.py`
- Create: `backend/app/models/alert.py`
- Create: `backend/app/models/backtest.py`
- Create: `backend/app/models/report.py`
- Create: `backend/tests/unit/test_model_contracts.py`

- [ ] **Step 1: Write model contract tests**

```python
# backend/tests/unit/test_model_contracts.py
from app.models.security import Security
from app.models.holding import Holding
from app.models.score import ScoreType

def test_security_identity_fields():
    security = Security(symbol="000001.SZ", name="平安银行", exchange="SZSE", is_st=False)
    assert security.symbol == "000001.SZ"
    assert security.is_st is False

def test_holding_auto_trade_is_not_required():
    holding = Holding(symbol="000001.SZ", quantity=1000, cost_price=10.0)
    assert holding.symbol == "000001.SZ"
    assert holding.quantity == 1000

def test_score_type_values_are_stable():
    assert ScoreType.HOLDING_RISK.value == "holding_risk"
    assert ScoreType.MARKET_ENVIRONMENT.value == "market_environment"
    assert ScoreType.OPPORTUNITY.value == "opportunity"
    assert ScoreType.PLAN_CONFIDENCE.value == "plan_confidence"
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_model_contracts.py -v`  
Expected: fail because models are missing.

- [ ] **Step 3: Implement SQLAlchemy models**

Define tables for securities, daily bars, intraday bars, holdings, factor snapshots, scores, trade plans, events, alerts, backtest runs, backtest metrics, and reports. Every table needs `created_at` and `updated_at` where mutable.

- [ ] **Step 4: Add first Alembic migration**

Run: `cd backend && alembic revision --autogenerate -m "create core tables"`  
Expected: migration file contains all core tables.

- [ ] **Step 5: Run tests and migration**

Run: `cd backend && pytest tests/unit/test_model_contracts.py -v`  
Expected: all tests pass.  
Run: `cd backend && alembic upgrade head`  
Expected: migration applies against local PostgreSQL.

- [ ] **Step 6: Commit**

```bash
git add backend/alembic.ini backend/app/db backend/app/models backend/tests/unit/test_model_contracts.py backend/app/db/migrations
git commit -m "feat: add core database models"
```

### Task 3: Local Infrastructure

**Files:**
- Create: `infra/docker-compose.yml`
- Create: `infra/env.example`
- Create: `infra/postgres/init.sql`
- Create: `infra/redis/redis.conf`
- Create: `scripts/dev.ps1`
- Create: `scripts/dev.sh`
- Create: `docs/operations/deployment.md`

- [ ] **Step 1: Add Docker Compose services**

Services: `postgres`, `redis`, `backend`, and `frontend`. The backend depends on PostgreSQL and Redis. PostgreSQL exposes `5432`, Redis exposes `6379`, backend exposes `8000`, frontend exposes `5173`.

- [ ] **Step 2: Add environment example**

`infra/env.example` must include conservative defaults: `ALLOW_AUTO_TRADE=false`, `DATABASE_URL`, `REDIS_URL`, `FEISHU_WEBHOOK_URL`, `TUSHARE_TOKEN`, `LLM_PROVIDER`, `LLM_API_KEY`.

- [ ] **Step 3: Add dev scripts**

`scripts/dev.ps1` and `scripts/dev.sh` start Docker Compose using the env file and print the backend and frontend URLs.

- [ ] **Step 4: Verify infrastructure**

Run: `docker compose -f infra/docker-compose.yml --env-file infra/env.example config`  
Expected: Compose configuration renders successfully.

- [ ] **Step 5: Commit**

```bash
git add infra scripts docs/operations/deployment.md
git commit -m "chore: add local infrastructure"
```

## 4. Phase P1: Data And Holdings

### Task 4: Trading Calendar And Security Master

**Files:**
- Create: `backend/app/services/trading_calendar.py`
- Create: `backend/app/repositories/securities.py`
- Create: `backend/app/schemas/security.py`
- Create: `backend/tests/fixtures/securities_sample.json`
- Create: `backend/tests/unit/test_trading_calendar.py`
- Create: `backend/tests/unit/test_stock_pool.py`

- [ ] **Step 1: Write tests**

```python
# backend/tests/unit/test_trading_calendar.py
from datetime import date
from app.services.trading_calendar import TradingCalendar

def test_weekend_is_not_trading_day():
    calendar = TradingCalendar(extra_holidays=set())
    assert calendar.is_trading_day(date(2026, 6, 13)) is False

def test_weekday_without_holiday_is_trading_day():
    calendar = TradingCalendar(extra_holidays=set())
    assert calendar.is_trading_day(date(2026, 6, 15)) is True
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_trading_calendar.py -v`  
Expected: fail because service is missing.

- [ ] **Step 3: Implement calendar and security repository**

Implement weekday trading-day logic with an injected holiday set. Implement repository methods `upsert_many`, `get_by_symbol`, and `list_active`.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_trading_calendar.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/trading_calendar.py backend/app/repositories/securities.py backend/app/schemas/security.py backend/tests
git commit -m "feat: add trading calendar and security master"
```

### Task 5: Market Data Provider Interface

**Files:**
- Create: `backend/app/data_sources/base.py`
- Create: `backend/app/data_sources/mock_provider.py`
- Create: `backend/app/data_sources/akshare_provider.py`
- Create: `backend/app/data_sources/tushare_provider.py`
- Create: `backend/app/data_sources/normalizers.py`
- Create: `backend/tests/fixtures/daily_bars_sample.csv`
- Create: `backend/tests/fixtures/intraday_bars_sample.csv`
- Create: `backend/tests/unit/test_market_data_provider.py`

- [ ] **Step 1: Write provider interface tests**

```python
# backend/tests/unit/test_market_data_provider.py
from datetime import date
from app.data_sources.mock_provider import MockMarketDataProvider

def test_mock_provider_returns_normalized_daily_bars():
    provider = MockMarketDataProvider()
    bars = provider.get_daily_bars("000001.SZ", date(2026, 6, 1), date(2026, 6, 5))
    assert len(bars) > 0
    first = bars[0]
    assert first.symbol == "000001.SZ"
    assert first.close > 0
    assert first.amount >= 0
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_market_data_provider.py -v`  
Expected: fail because provider modules are missing.

- [ ] **Step 3: Implement provider contracts**

Create dataclasses or Pydantic schemas for daily bars and intraday bars. `MockMarketDataProvider` reads fixtures. AKShare and Tushare providers implement the same methods and return normalized records.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_market_data_provider.py -v`  
Expected: all tests pass with fixture data.

- [ ] **Step 5: Commit**

```bash
git add backend/app/data_sources backend/tests/fixtures backend/tests/unit/test_market_data_provider.py
git commit -m "feat: add market data provider interface"
```

### Task 6: Data Ingestion And Quality Checks

**Files:**
- Create: `backend/app/repositories/market_data.py`
- Create: `backend/app/services/data_quality.py`
- Create: `backend/app/scheduler/jobs.py`
- Create: `backend/tests/unit/test_data_quality.py`
- Create: `backend/tests/integration/test_ingestion_pipeline.py`

- [ ] **Step 1: Write data quality tests**

```python
# backend/tests/unit/test_data_quality.py
from app.services.data_quality import validate_daily_bar

def test_daily_bar_rejects_negative_close():
    errors = validate_daily_bar({"symbol": "000001.SZ", "close": -1, "volume": 100, "amount": 1000})
    assert "close_must_be_positive" in errors

def test_daily_bar_accepts_positive_prices():
    errors = validate_daily_bar({"symbol": "000001.SZ", "close": 10.5, "volume": 100, "amount": 1000})
    assert errors == []
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_data_quality.py -v`  
Expected: fail because validator is missing.

- [ ] **Step 3: Implement validators and ingestion job**

Validate positive prices, non-negative volume, non-negative amount, valid symbol, and date presence. The ingestion job writes valid rows and stores rejected rows with error codes.

- [ ] **Step 4: Run unit and integration tests**

Run: `cd backend && pytest tests/unit/test_data_quality.py tests/integration/test_ingestion_pipeline.py -v`  
Expected: all tests pass with mock provider fixtures.

- [ ] **Step 5: Commit**

```bash
git add backend/app/repositories/market_data.py backend/app/services/data_quality.py backend/app/scheduler/jobs.py backend/tests
git commit -m "feat: add market data ingestion pipeline"
```

### Task 7: Holdings Import

**Files:**
- Create: `backend/app/services/portfolio/importer.py`
- Create: `backend/app/repositories/holdings.py`
- Create: `backend/app/schemas/holding.py`
- Create: `backend/tests/fixtures/holdings_sample.csv`
- Create: `backend/tests/unit/test_holdings_importer.py`
- Create: `scripts/import_holdings.py`

- [ ] **Step 1: Write importer tests**

```python
# backend/tests/unit/test_holdings_importer.py
from pathlib import Path
from app.services.portfolio.importer import parse_holdings_csv

def test_parse_holdings_csv_maps_required_fields():
    rows = parse_holdings_csv(Path("tests/fixtures/holdings_sample.csv"))
    assert rows[0].symbol == "000001.SZ"
    assert rows[0].quantity > 0
    assert rows[0].cost_price > 0
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_holdings_importer.py -v`  
Expected: fail because importer is missing.

- [ ] **Step 3: Implement CSV parser**

Required CSV columns: `symbol`, `name`, `quantity`, `cost_price`, `current_price`, `buy_date`, `strategy_note`. Reject rows with invalid symbol, non-positive quantity, or non-positive cost price.

- [ ] **Step 4: Add CLI import script**

`scripts/import_holdings.py` loads the CSV, writes holdings, and prints inserted and rejected counts.

- [ ] **Step 5: Run tests**

Run: `cd backend && pytest tests/unit/test_holdings_importer.py -v`  
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/portfolio/importer.py backend/app/repositories/holdings.py backend/app/schemas/holding.py backend/tests/fixtures/holdings_sample.csv backend/tests/unit/test_holdings_importer.py scripts/import_holdings.py
git commit -m "feat: add holdings csv import"
```

### Task 8: Stock Pool Classification

**Files:**
- Create: `backend/app/services/stock_pool.py`
- Create: `backend/tests/unit/test_stock_pool.py`

- [ ] **Step 1: Write classification tests**

```python
# backend/tests/unit/test_stock_pool.py
from app.services.stock_pool import classify_security

def test_st_stock_goes_to_forbidden_pool():
    result = classify_security(is_st=True, turnover_amount=100000000, days_since_listing=500, has_major_negative_event=False)
    assert result.pool == "forbidden"
    assert "st_stock" in result.reasons

def test_liquid_non_st_stock_goes_to_tradable_pool():
    result = classify_security(is_st=False, turnover_amount=300000000, days_since_listing=500, has_major_negative_event=False)
    assert result.pool == "tradable"
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_stock_pool.py -v`  
Expected: fail because classifier is missing.

- [ ] **Step 3: Implement classifier**

Rules: ST, major negative event, turnover below threshold, or very recent listing goes to forbidden or watch pool. Liquid non-ST stocks with no major negative event go to tradable pool.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_stock_pool.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/stock_pool.py backend/tests/unit/test_stock_pool.py
git commit -m "feat: classify stock pools"
```

## 5. Phase P2: Factors And Scores

### Task 9: Technical And Liquidity Factors

**Files:**
- Create: `backend/app/services/factors/technical.py`
- Create: `backend/app/services/factors/liquidity.py`
- Create: `backend/tests/unit/test_technical_factors.py`

- [ ] **Step 1: Write factor tests**

```python
# backend/tests/unit/test_technical_factors.py
from app.services.factors.technical import moving_average, momentum_pct, atr

def test_moving_average_uses_last_n_values():
    assert moving_average([1, 2, 3, 4, 5], 3) == 4.0

def test_momentum_pct_compares_first_and_last():
    assert round(momentum_pct([10, 11]), 4) == 0.1

def test_atr_is_positive_for_volatile_bars():
    bars = [
        {"high": 11, "low": 9, "close": 10},
        {"high": 12, "low": 10, "close": 11},
        {"high": 13, "low": 10, "close": 12},
    ]
    assert atr(bars, 3) > 0
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_technical_factors.py -v`  
Expected: fail because factor functions are missing.

- [ ] **Step 3: Implement factor functions**

Implement moving averages, 1/3/5-day momentum, ATR, volume ratio, turnover rank, close-to-high drawdown, and breakout distance.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_technical_factors.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/factors backend/tests/unit/test_technical_factors.py
git commit -m "feat: add technical and liquidity factors"
```

### Task 10: Market Environment And Sector Factors

**Files:**
- Create: `backend/app/services/factors/market_environment.py`
- Create: `backend/app/services/factors/sector_strength.py`
- Create: `backend/tests/unit/test_market_environment_factors.py`

- [ ] **Step 1: Write factor tests**

```python
# backend/tests/unit/test_market_environment_factors.py
from app.services.factors.market_environment import market_breadth
from app.services.factors.sector_strength import sector_strength_score

def test_market_breadth_counts_advancers():
    result = market_breadth([1.0, -0.5, 2.0, 0.0])
    assert result.advancers == 2
    assert result.decliners == 1

def test_sector_strength_rewards_positive_return_and_turnover():
    score = sector_strength_score(return_pct=0.03, turnover_change=0.4, limit_up_count=5)
    assert score > 60
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_market_environment_factors.py -v`  
Expected: fail because factor functions are missing.

- [ ] **Step 3: Implement functions**

Compute index trend, market turnover change, advancer/decliner counts, limit-up/limit-down structure, sector return, sector turnover expansion, sector limit-up count, and sector continuation days.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_market_environment_factors.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/factors/market_environment.py backend/app/services/factors/sector_strength.py backend/tests/unit/test_market_environment_factors.py
git commit -m "feat: add market and sector factors"
```

### Task 11: Score Trace Infrastructure

**Files:**
- Create: `backend/app/services/scoring/config.py`
- Create: `backend/app/services/scoring/trace.py`
- Create: `backend/tests/unit/test_score_trace.py`

- [ ] **Step 1: Write trace tests**

```python
# backend/tests/unit/test_score_trace.py
from app.services.scoring.trace import ScoreTrace, FactorContribution

def test_score_trace_records_contributions():
    trace = ScoreTrace(score_type="holding_risk")
    trace.add(FactorContribution(name="technical_breakdown", value=80, weight=0.25, reason="跌破平台"))
    assert trace.total_weight == 0.25
    assert trace.contributions[0].reason == "跌破平台"
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_score_trace.py -v`  
Expected: fail because trace classes are missing.

- [ ] **Step 3: Implement trace classes**

Each score returns `score`, `score_type`, `contributions`, `raw_inputs`, and `decision_reason`. Store contribution names and reasons in Chinese for dashboard readability.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_score_trace.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scoring/config.py backend/app/services/scoring/trace.py backend/tests/unit/test_score_trace.py
git commit -m "feat: add score trace infrastructure"
```

### Task 12: Four Score Engines

**Files:**
- Create: `backend/app/services/scoring/market_score.py`
- Create: `backend/app/services/scoring/holding_risk_score.py`
- Create: `backend/app/services/scoring/opportunity_score.py`
- Create: `backend/app/services/scoring/plan_confidence_score.py`
- Create: `backend/app/services/scoring/orchestrator.py`
- Create: `backend/tests/unit/test_market_score.py`
- Create: `backend/tests/unit/test_holding_risk_score.py`
- Create: `backend/tests/unit/test_opportunity_score.py`
- Create: `backend/tests/unit/test_plan_confidence_score.py`

- [ ] **Step 1: Write score tests**

```python
# backend/tests/unit/test_holding_risk_score.py
from app.services.scoring.holding_risk_score import score_holding_risk

def test_holding_risk_is_high_when_stop_and_breakdown_trigger():
    result = score_holding_risk({
        "price_below_stop": True,
        "technical_breakdown": True,
        "volume_selloff": True,
        "sector_retreat": False,
        "market_weak": False,
        "negative_event": False,
        "profit_drawdown": 0.0,
    })
    assert result.score >= 71
    assert "止损" in result.decision_reason
```

```python
# backend/tests/unit/test_market_score.py
from app.services.scoring.market_score import score_market_environment

def test_market_score_blocks_new_positions_in_weak_market():
    result = score_market_environment({
        "index_trend": 20,
        "turnover": 30,
        "breadth": 20,
        "limit_structure": 20,
        "sector_continuity": 20,
        "external_risk": 40,
    })
    assert result.score < 40
    assert result.allow_new_positions is False
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_*score.py -v`  
Expected: fail because score engines are missing.

- [ ] **Step 3: Implement scoring engines**

Implement fixed MVP weights from the design:

- Holding risk: technical breakdown 25%, volume/price deterioration 20%, sector retreat 15%, market environment 15%, capital outflow 10%, negative event/sentiment 10%, holding PnL drawdown 5%.
- Market environment: index trend 25%, market turnover 20%, breadth 20%, limit-up/limit-down structure 15%, sector continuity 15%, external risk 5%.
- Opportunity: sector/theme 25%, individual volume/price 25%, technical pattern 20%, market environment 10%, event catalyst 10%, capital behavior 5%, sentiment 5%.
- Plan confidence: stop clarity 25%, entry clarity 20%, reward/risk 20%, liquidity 15%, gap-up risk 10%, invalidation clarity 10%.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_*score.py -v`  
Expected: all score tests pass and every score has a trace.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scoring backend/tests/unit/test_*score.py
git commit -m "feat: add four rule-based score engines"
```

## 6. Phase P3: Portfolio Risk

### Task 13: Sell State And Hard Stop Rules

**Files:**
- Create: `backend/app/services/portfolio/risk_rules.py`
- Create: `backend/tests/unit/test_portfolio_risk_rules.py`

- [ ] **Step 1: Write sell-rule tests**

```python
# backend/tests/unit/test_portfolio_risk_rules.py
from app.services.portfolio.risk_rules import evaluate_holding_action

def test_hard_stop_plus_breakdown_returns_clear_exit():
    action = evaluate_holding_action(
        risk_score=82,
        price_below_stop=True,
        technical_breakdown=True,
        profit_drawdown_pct=0.0,
    )
    assert action.state == "clear_exit"
    assert action.priority == "P0"

def test_medium_risk_returns_reduce_or_watch():
    action = evaluate_holding_action(
        risk_score=58,
        price_below_stop=False,
        technical_breakdown=True,
        profit_drawdown_pct=0.04,
    )
    assert action.state == "reduce_watch"
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_portfolio_risk_rules.py -v`  
Expected: fail because rules are missing.

- [ ] **Step 3: Implement sell states**

States: `hold`, `tighten_stop`, `reduce_watch`, `sell_on_rebound`, `clear_exit`. P0 is reserved for hard stop, major negative event, market crash, or fast volume selloff.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_portfolio_risk_rules.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/portfolio/risk_rules.py backend/tests/unit/test_portfolio_risk_rules.py
git commit -m "feat: add holding sell rules"
```

### Task 14: Position Sizing And Risk Gates

**Files:**
- Create: `backend/app/services/portfolio/position_sizing.py`
- Create: `backend/app/services/plans/risk_gates.py`
- Create: `backend/tests/unit/test_position_sizing.py`
- Create: `backend/tests/unit/test_trade_risk_gates.py`

- [ ] **Step 1: Write sizing and gate tests**

```python
# backend/tests/unit/test_position_sizing.py
from app.services.portfolio.position_sizing import recommend_position_pct

def test_position_size_decreases_when_stop_distance_is_large():
    small_stop = recommend_position_pct(market_score=70, plan_score=85, holding_risk_score=20, stop_distance_pct=0.03)
    large_stop = recommend_position_pct(market_score=70, plan_score=85, holding_risk_score=20, stop_distance_pct=0.08)
    assert large_stop < small_stop

def test_position_size_is_zero_when_holding_risk_is_high():
    assert recommend_position_pct(market_score=80, plan_score=90, holding_risk_score=80, stop_distance_pct=0.03) == 0
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_position_sizing.py tests/unit/test_trade_risk_gates.py -v`  
Expected: fail because services are missing.

- [ ] **Step 3: Implement sizing and gates**

Default rules: base 5-10%, zero new exposure when market score < 40, cap at 5% when market score 40-60, zero when holding risk >= 71, reduce size when stop distance is above 5%, and block if reward/risk < 1.5.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_position_sizing.py tests/unit/test_trade_risk_gates.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/portfolio/position_sizing.py backend/app/services/plans/risk_gates.py backend/tests/unit/test_position_sizing.py backend/tests/unit/test_trade_risk_gates.py
git commit -m "feat: add conservative position sizing"
```

## 7. Phase P4: Candidate And Trade Plan Pipeline

### Task 15: Candidate Selection Pipeline

**Files:**
- Create: `backend/app/services/plans/generator.py`
- Create: `backend/app/repositories/scores.py`
- Create: `backend/app/repositories/trade_plans.py`
- Create: `backend/tests/integration/test_daily_scoring_pipeline.py`

- [ ] **Step 1: Write integration test**

```python
# backend/tests/integration/test_daily_scoring_pipeline.py
from app.services.scoring.orchestrator import run_daily_scoring

def test_daily_scoring_returns_candidates_after_forbidden_filter():
    result = run_daily_scoring(trading_date="2026-06-12", data_mode="fixture")
    assert len(result.focus_candidates) <= 8
    assert all(item.pool == "tradable" for item in result.focus_candidates)
    assert all(item.opportunity_score >= 76 for item in result.focus_candidates)
```

- [ ] **Step 2: Run failing integration test**

Run: `cd backend && pytest tests/integration/test_daily_scoring_pipeline.py -v`  
Expected: fail because orchestration is incomplete.

- [ ] **Step 3: Implement orchestration**

Pipeline order: classify pool, compute market score, compute sector strength, compute opportunity scores, compute plan confidence, apply risk gates, rank candidates, return focus candidates and watch candidates.

- [ ] **Step 4: Run integration test**

Run: `cd backend && pytest tests/integration/test_daily_scoring_pipeline.py -v`  
Expected: test passes with fixture data.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/plans/generator.py backend/app/repositories/scores.py backend/app/repositories/trade_plans.py backend/tests/integration/test_daily_scoring_pipeline.py
git commit -m "feat: add daily candidate selection pipeline"
```

### Task 16: Complete Trade Plan Generator

**Files:**
- Create: `backend/app/schemas/trade_plan.py`
- Modify: `backend/app/services/plans/generator.py`
- Create: `backend/tests/unit/test_trade_plan_generator.py`

- [ ] **Step 1: Write plan generator tests**

```python
# backend/tests/unit/test_trade_plan_generator.py
from app.services.plans.generator import generate_trade_plan

def test_trade_plan_contains_required_execution_fields():
    plan = generate_trade_plan(
        symbol="000001.SZ",
        latest_close=10.0,
        support_price=9.7,
        resistance_price=10.8,
        opportunity_score=82,
        plan_confidence_score=78,
        market_score=68,
        holding_risk_score=20,
    )
    assert plan.entry_trigger
    assert plan.buy_range_low <= plan.buy_range_high
    assert plan.stop_loss < plan.buy_range_low
    assert plan.first_take_profit > plan.buy_range_high
    assert plan.position_pct > 0
    assert plan.invalidation_conditions
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_trade_plan_generator.py -v`  
Expected: fail because generator fields are incomplete.

- [ ] **Step 3: Implement plan generator**

Generate entry trigger, buy range, stop loss, first take-profit, second take-profit or trailing stop rule, position percentage, invalidation conditions, risk summary, and factor trace references.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_trade_plan_generator.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/trade_plan.py backend/app/services/plans/generator.py backend/tests/unit/test_trade_plan_generator.py
git commit -m "feat: generate complete trade plans"
```

### Task 17: Daily Report Data Contract

**Files:**
- Create: `backend/app/services/reports/daily_report.py`
- Create: `backend/app/services/reports/markdown_renderer.py`
- Create: `backend/app/repositories/reports.py`
- Create: `backend/tests/unit/test_daily_report.py`

- [ ] **Step 1: Write report tests**

```python
# backend/tests/unit/test_daily_report.py
from app.services.reports.markdown_renderer import render_daily_report

def test_daily_report_contains_required_sections():
    markdown = render_daily_report({
        "market_summary": "市场环境偏谨慎",
        "holding_risks": [],
        "focus_candidates": [],
        "watch_candidates": [],
        "forbidden_summary": [],
        "alerts_for_next_day": [],
        "signal_review": "无历史信号",
    })
    assert "今日市场总结" in markdown
    assert "当前持仓风险" in markdown
    assert "重点候选股交易计划" in markdown
    assert "次日盘中提醒清单" in markdown
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_daily_report.py -v`  
Expected: fail because report renderer is missing.

- [ ] **Step 3: Implement report renderer**

Render the nine confirmed sections: market summary, holding risk, new-position decision, strong/weak sectors, focus candidates, watch candidates, forbidden/risk stocks, next-day alerts, and signal review.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_daily_report.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/reports backend/app/repositories/reports.py backend/tests/unit/test_daily_report.py
git commit -m "feat: render daily trading report"
```

## 8. Phase P5: Agents And Source-Grounded Reports

### Task 18: LLM Gateway And Agent Schemas

**Files:**
- Create: `backend/app/services/agents/llm_gateway.py`
- Create: `backend/app/services/agents/schemas.py`
- Create: `backend/tests/unit/test_agents_schema.py`

- [ ] **Step 1: Write schema tests**

```python
# backend/tests/unit/test_agents_schema.py
from app.services.agents.schemas import EventClassification

def test_event_classification_requires_source_and_uncertainty():
    result = EventClassification(
        symbol="000001.SZ",
        event_type="buyback",
        direction="positive",
        confidence=0.82,
        source_url="https://example.com/a",
        source_time="2026-06-12T20:00:00+08:00",
        summary="公司发布回购公告",
    )
    assert result.confidence <= 1
    assert result.source_url.startswith("https://")
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_agents_schema.py -v`  
Expected: fail because schemas are missing.

- [ ] **Step 3: Implement gateway and schemas**

Create typed outputs for event classification, theme extraction, holding review, trade plan explanation, and daily review. The gateway must support a mock provider for tests and configured external provider for runtime.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_agents_schema.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/agents backend/tests/unit/test_agents_schema.py
git commit -m "feat: add llm gateway and agent schemas"
```

### Task 19: Five Agent Workflows

**Files:**
- Create: `backend/app/services/agents/announcement_agent.py`
- Create: `backend/app/services/agents/news_theme_agent.py`
- Create: `backend/app/services/agents/holding_review_agent.py`
- Create: `backend/app/services/agents/trade_plan_agent.py`
- Create: `backend/app/services/agents/daily_review_agent.py`
- Create: `backend/tests/unit/test_agent_workflows.py`

- [ ] **Step 1: Write workflow tests**

```python
# backend/tests/unit/test_agent_workflows.py
from app.services.agents.announcement_agent import classify_announcement

def test_announcement_agent_preserves_source():
    result = classify_announcement(
        text="公司公告拟回购股份。",
        source_url="https://example.com/announcement",
        source_time="2026-06-12T19:30:00+08:00",
        llm_mode="mock",
    )
    assert result.source_url == "https://example.com/announcement"
    assert result.direction in {"positive", "negative", "neutral", "uncertain"}
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_agent_workflows.py -v`  
Expected: fail because workflows are missing.

- [ ] **Step 3: Implement workflows**

Each workflow must accept source text and source metadata, call the LLM gateway, validate typed output, and return source-grounded structured data. Trade plan and holding review agents must not change risk score, stop loss, or risk gate output.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_agent_workflows.py -v`  
Expected: all tests pass with mock LLM provider.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/agents backend/tests/unit/test_agent_workflows.py
git commit -m "feat: add source-grounded agent workflows"
```

## 9. Phase P6: Dashboard And Alerts

### Task 20: Backend API Routes

**Files:**
- Create: `backend/app/api/routes/holdings.py`
- Create: `backend/app/api/routes/market.py`
- Create: `backend/app/api/routes/scores.py`
- Create: `backend/app/api/routes/candidates.py`
- Create: `backend/app/api/routes/plans.py`
- Create: `backend/app/api/routes/reports.py`
- Create: `backend/app/api/routes/alerts.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/integration/test_api_routes.py`

- [ ] **Step 1: Write API tests**

```python
# backend/tests/integration/test_api_routes.py
from fastapi.testclient import TestClient
from app.main import app

def test_dashboard_routes_exist():
    client = TestClient(app)
    for path in ["/holdings", "/market/summary", "/candidates", "/plans", "/alerts", "/reports/latest"]:
        response = client.get(path)
        assert response.status_code in {200, 204}
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/integration/test_api_routes.py -v`  
Expected: fail until routes are registered.

- [ ] **Step 3: Implement routes**

Expose read APIs for holdings, market summary, score traces, candidates, plans, latest report, alerts, and backtest summary. Keep write APIs limited to holding import and manual operation notes.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/integration/test_api_routes.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api backend/app/main.py backend/tests/integration/test_api_routes.py
git commit -m "feat: expose dashboard api routes"
```

### Task 21: Alert Router And Feishu Provider

**Files:**
- Create: `backend/app/services/alerts/base.py`
- Create: `backend/app/services/alerts/feishu.py`
- Create: `backend/app/services/alerts/router.py`
- Create: `backend/app/repositories/alerts.py`
- Create: `backend/tests/unit/test_alert_router.py`

- [ ] **Step 1: Write alert routing tests**

```python
# backend/tests/unit/test_alert_router.py
from app.services.alerts.router import should_push_alert

def test_p0_and_p1_alerts_are_pushed():
    assert should_push_alert("P0") is True
    assert should_push_alert("P1") is True

def test_p2_and_p3_alerts_are_not_immediate_by_default():
    assert should_push_alert("P2") is False
    assert should_push_alert("P3") is False
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_alert_router.py -v`  
Expected: fail because alert router is missing.

- [ ] **Step 3: Implement router and Feishu provider**

Route P0/P1 to webhook immediately. Store all P0-P3 alerts in the database. P2/P3 are dashboard-visible and included in grouped summaries.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_alert_router.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/alerts backend/app/repositories/alerts.py backend/tests/unit/test_alert_router.py
git commit -m "feat: add alert routing and feishu provider"
```

### Task 22: React Dashboard

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/app/App.tsx`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/types.ts`
- Create: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/pages/Holdings.tsx`
- Create: `frontend/src/pages/Candidates.tsx`
- Create: `frontend/src/pages/TradePlans.tsx`
- Create: `frontend/src/pages/Backtests.tsx`
- Create: all components listed in the file structure
- Create: `frontend/tests/dashboard.spec.ts`

- [ ] **Step 1: Write dashboard smoke test**

```ts
// frontend/tests/dashboard.spec.ts
import { test, expect } from "@playwright/test";

test("dashboard shows core sections", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("持仓风险")).toBeVisible();
  await expect(page.getByText("市场环境")).toBeVisible();
  await expect(page.getByText("重点候选")).toBeVisible();
  await expect(page.getByText("盘中提醒")).toBeVisible();
});
```

- [ ] **Step 2: Run failing frontend test**

Run: `cd frontend && npm test`  
Expected: fail because the app is not built.

- [ ] **Step 3: Implement dashboard**

Create a dense operational dashboard, not a landing page. First screen must show market environment, holding risk table, focus candidates, and P0/P1 alerts. Use compact tables, status badges, tabs, and detail drawers for trade plans.

- [ ] **Step 4: Run tests**

Run: `cd frontend && npm test`  
Expected: dashboard smoke test passes.

- [ ] **Step 5: Visual verification**

Run local app and inspect desktop and mobile widths. Confirm no text overlaps, tables are scrollable, and critical risk actions remain visible.

- [ ] **Step 6: Commit**

```bash
git add frontend
git commit -m "feat: add trading dashboard"
```

## 10. Phase P7: Backtest And Review

### Task 23: Signal Ledger

**Files:**
- Create: `backend/app/services/backtest/signal_ledger.py`
- Create: `backend/app/repositories/backtests.py`
- Create: `backend/tests/unit/test_signal_ledger.py`

- [ ] **Step 1: Write ledger tests**

```python
# backend/tests/unit/test_signal_ledger.py
from app.services.backtest.signal_ledger import SignalRecord

def test_signal_record_contains_required_evaluation_windows():
    record = SignalRecord(symbol="000001.SZ", signal_date="2026-06-12", signal_type="focus_candidate")
    assert record.evaluation_windows == [1, 3, 5]
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_signal_ledger.py -v`  
Expected: fail because signal ledger is missing.

- [ ] **Step 3: Implement ledger**

Record every candidate, sell signal, stop signal, take-profit signal, forbidden filter, and actual manual operation note with timestamp and source score trace IDs.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_signal_ledger.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/backtest/signal_ledger.py backend/app/repositories/backtests.py backend/tests/unit/test_signal_ledger.py
git commit -m "feat: record trading signals for backtests"
```

### Task 24: Backtest Metrics

**Files:**
- Create: `backend/app/services/backtest/simulator.py`
- Create: `backend/app/services/backtest/metrics.py`
- Create: `backend/tests/unit/test_backtest_metrics.py`
- Create: `scripts/run_backtest.py`

- [ ] **Step 1: Write metric tests**

```python
# backend/tests/unit/test_backtest_metrics.py
from app.services.backtest.metrics import max_drawdown, win_rate

def test_max_drawdown_computes_largest_peak_to_trough_loss():
    assert round(max_drawdown([100, 110, 105, 90, 95]), 4) == -0.1818

def test_win_rate_counts_positive_returns():
    assert win_rate([0.01, -0.02, 0.03]) == 2 / 3
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_backtest_metrics.py -v`  
Expected: fail because metrics are missing.

- [ ] **Step 3: Implement simulator and metrics**

Metrics: 1/3/5-day forward return, win rate, average return, reward/risk, maximum drawdown, stop-loss effectiveness, take-profit effectiveness, false sell rate, missed rebound rate.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_backtest_metrics.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Add CLI**

`scripts/run_backtest.py` accepts start date, end date, signal type, and outputs a markdown summary.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/backtest scripts/run_backtest.py backend/tests/unit/test_backtest_metrics.py
git commit -m "feat: add backtest metrics"
```

### Task 25: Review Loop And Weight Adjustment Inputs

**Files:**
- Create: `backend/app/services/backtest/review.py`
- Create: `backend/tests/unit/test_review_outputs.py`
- Modify: `backend/app/services/reports/daily_report.py`

- [ ] **Step 1: Write review output tests**

```python
# backend/tests/unit/test_review_outputs.py
from app.services.backtest.review import summarize_weight_inputs

def test_review_summary_surfaces_underperforming_factor():
    summary = summarize_weight_inputs([
        {"factor": "sentiment", "ic": -0.05, "sample_size": 100},
        {"factor": "sector_strength", "ic": 0.12, "sample_size": 100},
    ])
    assert "sentiment" in summary.factors_to_review
    assert "sector_strength" in summary.factors_to_keep
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_review_outputs.py -v`  
Expected: fail because review service is missing.

- [ ] **Step 3: Implement review summary**

Summarize factor effectiveness, sell-rule effectiveness, candidate quality, alert noise, and drawdown improvement. Output is advisory and never mutates production weights automatically.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_review_outputs.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/backtest/review.py backend/app/services/reports/daily_report.py backend/tests/unit/test_review_outputs.py
git commit -m "feat: summarize factor review inputs"
```

## 11. Phase P8: Scheduler, Deployment, And Operations

### Task 26: Scheduled Jobs

**Files:**
- Create: `backend/app/scheduler/runner.py`
- Modify: `backend/app/scheduler/jobs.py`
- Create: `scripts/run_daily_pipeline.py`
- Create: `backend/tests/unit/test_scheduler_jobs.py`

- [ ] **Step 1: Write scheduler tests**

```python
# backend/tests/unit/test_scheduler_jobs.py
from app.scheduler.jobs import daily_job_sequence

def test_daily_job_sequence_keeps_risk_before_new_candidates():
    names = [job.name for job in daily_job_sequence()]
    assert names.index("score_holdings") < names.index("select_candidates")
    assert names.index("score_market") < names.index("select_candidates")
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_scheduler_jobs.py -v`  
Expected: fail because sequence is missing.

- [ ] **Step 3: Implement scheduler**

Job sequence: ingest market data, import holdings, classify pools, score holdings, score market, compute candidate scores, generate plans, run agents, render report, route alerts, record signals.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_scheduler_jobs.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Add CLI**

`scripts/run_daily_pipeline.py --date YYYY-MM-DD --mode fixture|live` runs the full pipeline and prints report path, alert counts, and candidate counts.

- [ ] **Step 6: Commit**

```bash
git add backend/app/scheduler scripts/run_daily_pipeline.py backend/tests/unit/test_scheduler_jobs.py
git commit -m "feat: add daily scheduler sequence"
```

### Task 27: Operations Runbooks

**Files:**
- Create: `docs/operations/data_sources.md`
- Create: `docs/operations/daily_runbook.md`
- Modify: `docs/operations/deployment.md`

- [ ] **Step 1: Document daily operations**

Include commands for starting services, importing holdings, running fixture pipeline, running live pipeline, viewing reports, and running backtests.

- [ ] **Step 2: Document data source fallback**

Order: fixture for tests, AKShare for low-cost live data, Tushare when token exists, professional provider interface for future upgrades.

- [ ] **Step 3: Document safety boundaries**

State that the system does not place orders, does not bypass hard stop rules, and does not treat agent output as final trading authority.

- [ ] **Step 4: Verify commands from docs**

Run documented fixture commands on a clean checkout. Expected: health route passes, fixture daily pipeline produces report, and fixture backtest produces metrics.

- [ ] **Step 5: Commit**

```bash
git add docs/operations
git commit -m "docs: add operations runbooks"
```

### Task 28: Backup, Audit, And Compliance Logs

**Files:**
- Create: `backend/app/core/audit.py`
- Create: `backend/app/services/compliance/logging.py`
- Create: `backend/tests/unit/test_audit_logging.py`
- Modify: `docs/operations/daily_runbook.md`

- [ ] **Step 1: Write audit tests**

```python
# backend/tests/unit/test_audit_logging.py
from app.core.audit import AuditEvent

def test_audit_event_records_actor_and_action():
    event = AuditEvent(actor="system", action="generated_trade_plan", entity_id="000001.SZ")
    assert event.actor == "system"
    assert event.action == "generated_trade_plan"
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_audit_logging.py -v`  
Expected: fail because audit module is missing.

- [ ] **Step 3: Implement audit events**

Log data imports, score generation, trade plan creation, agent summaries, alert pushes, report generation, backtest runs, and manual notes. Keep order-placement audit fields in the model for future extension, but never call any broker API in MVP.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_audit_logging.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/audit.py backend/app/services/compliance backend/tests/unit/test_audit_logging.py docs/operations/daily_runbook.md
git commit -m "feat: add audit logging"
```

## 12. Phase P9: Post-MVP Expansion Backlog

### Task 29: Model Experiment Dataset Contract

**Files:**
- Create: `backend/app/services/modeling/datasets.py`
- Create: `docs/operations/model_experiments.md`
- Create: `backend/tests/unit/test_model_dataset_contract.py`

- [ ] **Step 1: Write dataset contract tests**

```python
# backend/tests/unit/test_model_dataset_contract.py
from app.services.modeling.datasets import TrainingExample

def test_training_example_contains_features_and_forward_returns():
    example = TrainingExample(
        symbol="000001.SZ",
        trade_date="2026-06-12",
        features={"opportunity_score": 82.0},
        forward_returns={"d1": 0.01, "d3": 0.02, "d5": -0.01},
    )
    assert "d5" in example.forward_returns
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_model_dataset_contract.py -v`  
Expected: fail because model dataset contract is missing.

- [ ] **Step 3: Implement dataset exporter**

Export features, score traces, agent tags, forward returns, sell-rule outcomes, and market regime labels. Do not use future data in feature columns.

- [ ] **Step 4: Run tests**

Run: `cd backend && pytest tests/unit/test_model_dataset_contract.py -v`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/modeling docs/operations/model_experiments.md backend/tests/unit/test_model_dataset_contract.py
git commit -m "feat: define model experiment dataset contract"
```

### Task 30: Professional Data And Level-2 Upgrade Design

**Files:**
- Create: `docs/operations/data_upgrade_plan.md`
- Create: `backend/app/data_sources/professional_provider_contract.py`
- Create: `backend/tests/unit/test_professional_provider_contract.py`

- [ ] **Step 1: Write provider contract tests**

```python
# backend/tests/unit/test_professional_provider_contract.py
from app.data_sources.professional_provider_contract import Level2Snapshot

def test_level2_snapshot_keeps_timestamp_and_symbol():
    snapshot = Level2Snapshot(symbol="000001.SZ", timestamp="2026-06-12T10:30:00+08:00", bid_levels=[], ask_levels=[])
    assert snapshot.symbol == "000001.SZ"
    assert snapshot.timestamp.endswith("+08:00")
```

- [ ] **Step 2: Run failing tests**

Run: `cd backend && pytest tests/unit/test_professional_provider_contract.py -v`  
Expected: fail because contract is missing.

- [ ] **Step 3: Implement contract only**

Define interfaces for Level-2 snapshots, tick trades, order queue snapshots, and provider health. Do not connect a paid provider in this task.

- [ ] **Step 4: Document upgrade criteria**

Criteria: backtest evidence that current signals are limited by data granularity, clear vendor cost, legal usage rights, latency requirements, and expected factor improvement.

- [ ] **Step 5: Run tests**

Run: `cd backend && pytest tests/unit/test_professional_provider_contract.py -v`  
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add docs/operations/data_upgrade_plan.md backend/app/data_sources/professional_provider_contract.py backend/tests/unit/test_professional_provider_contract.py
git commit -m "docs: define professional data upgrade path"
```

## 13. Phase Acceptance Checklists

### P0 Acceptance

- Backend `/health` returns `{"status": "ok", "auto_trade": false}`.
- PostgreSQL and Redis run from Docker Compose.
- Alembic migration applies from a clean database.
- Backend unit and integration tests pass.

### P1 Acceptance

- Fixture securities and bars ingest successfully.
- Holdings CSV imports valid rows and rejects invalid rows with reasons.
- Stock pool classification produces tradable, watch, forbidden, and holding pools.

### P2 Acceptance

- Factor functions are deterministic on fixture data.
- Four score engines return 0-100 scores.
- Each score includes factor contributions and Chinese decision reasons.

### P3 Acceptance

- Existing holdings receive one of five daily action states.
- P0/P1 conditions are triggered by hard stops, breakdowns, and major risk.
- New positions are blocked when holding risk or market risk is too high.

### P4 Acceptance

- Daily pipeline outputs 3-8 focus candidates from fixture data.
- Each focus candidate has entry trigger, buy range, stop loss, take-profit, position size, and invalidation conditions.
- High gap-up, poor liquidity, poor reward/risk, and forbidden stocks are blocked.

### P5 Acceptance

- Agents return typed outputs with source URL and source time.
- Agent summaries cannot mutate deterministic scores or hard stops.
- Daily markdown report contains all nine required sections.

### P6 Acceptance

- Dashboard shows market environment, holding risks, focus candidates, trade plans, and alerts in the first workflow.
- P0/P1 alerts push immediately through Feishu in live configuration.
- P2/P3 alerts are visible in dashboard and grouped summaries.

### P7 Acceptance

- Signal ledger records every generated candidate, sell signal, stop signal, take-profit signal, and forbidden filter.
- Backtest reports 1/3/5-day returns, win rate, reward/risk, max drawdown, stop effectiveness, take-profit effectiveness, false sell rate, and missed rebound rate.

### P8 Acceptance

- `scripts/run_daily_pipeline.py --mode fixture` runs end-to-end.
- Operations docs are enough for a teammate to start services, import holdings, generate reports, and run backtests.
- Audit logs exist for generated trade plans, alerts, reports, backtests, and manual notes.

## 14. Full Verification Commands

Backend:

```bash
cd backend
pytest -v
alembic upgrade head
```

Frontend:

```bash
cd frontend
npm install
npm test
npm run build
```

Infrastructure:

```bash
docker compose -f infra/docker-compose.yml --env-file infra/env.example config
docker compose -f infra/docker-compose.yml --env-file infra/env.example up -d
```

End-to-end fixture run:

```bash
python scripts/import_holdings.py --file backend/tests/fixtures/holdings_sample.csv
python scripts/run_daily_pipeline.py --date 2026-06-12 --mode fixture
python scripts/run_backtest.py --start 2026-06-01 --end 2026-06-12 --signal-type focus_candidate
```

Expected end state:

- API health passes.
- Fixture daily report is generated.
- Focus candidate count is 3-8 when fixture data supports it.
- Holding risk actions are generated before new candidate selection.
- Backtest summary includes 1/3/5-day metrics.
- No broker or order-placement API is called.

## 15. Implementation Order

Recommended order:

1. P0 Foundation.
2. P1 Data and holdings.
3. P2 Factors and scores.
4. P3 Portfolio risk.
5. P4 Candidate and trade plan pipeline.
6. P7 Signal ledger and basic backtest metrics.
7. P5 Agents and reports.
8. P6 Dashboard and alerts.
9. P8 Scheduler, deployment, and operations.
10. P9 Post-MVP expansion contracts.

Reasoning:

- Data and deterministic rules must exist before agents.
- Backtest logging should land before users rely on daily candidates.
- Dashboard is most useful after the backend output contracts are stable.
- Post-MVP contracts should not block the first usable trading assistant.

## 16. Commit Strategy

Commit after every task. Use these message prefixes:

- `feat:` for user-visible functionality.
- `fix:` for bug fixes.
- `test:` for test-only changes.
- `docs:` for documentation.
- `chore:` for infrastructure and tooling.

Do not combine unrelated phases in one commit. Do not commit generated reports, local database files, API keys, or downloaded market data caches.

## 17. Risk Register

Data reliability:

- Low-cost market and fund-flow data may be delayed or noisy.
- Mitigation: provider abstraction, fixture tests, source timestamps, quality checks, and reduced weight for noisy fund-flow inputs.

LLM hallucination:

- Agents may overstate uncertain news or invent causality.
- Mitigation: typed outputs, source URL/time requirement, confidence field, and deterministic scoring authority.

Overfitting:

- Weights may be tuned to a small sample.
- Mitigation: fixed MVP weights first, signal ledger, 1/3/5-day evaluation, and factor review summaries before weight changes.

Alert fatigue:

- Too many P2/P3 alerts can bury important messages.
- Mitigation: immediate push only for P0/P1, grouped summaries for P2/P3.

Compliance drift:

- Programmatic trading rules may change.
- Mitigation: MVP has no order placement, and automated/semi-automated trading requires a separate compliance plan before work starts.

Operational overload:

- The system can grow beyond a three-person team.
- Mitigation: single-repo MVP, fixture-first tests, one-command daily pipeline, and documented runbooks.

## 18. Definition Of Done For MVP

The MVP is complete when:

- A teammate can start the system from docs.
- Holdings can be imported from CSV.
- Data can be ingested from fixtures and at least one low-cost live provider.
- Existing holdings receive daily risk states and P0/P1 alert candidates.
- Market environment score blocks new positions in weak market conditions.
- Daily candidate selection outputs focus and watch lists.
- Focus candidates include complete trade plans.
- Agents add source-grounded explanations without changing hard rules.
- Dashboard displays holdings, market, candidates, plans, alerts, and backtest summaries.
- Signal ledger and backtest metrics show 1/3/5-day results.
- The daily pipeline runs from a single command.
- No automatic order placement exists.
