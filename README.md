# A 股保守型短线交易辅助系统

第一阶段目标：盘后选股、持仓风控、完整交易计划、盘中分级提醒、智能体解释和回测复盘。

## 本地测试

```powershell
python -m pytest -v
python -m ruff check .
python -m mypy src
```

## MVP 验收

MVP 验收清单见 [docs/mvp-acceptance-checklist.md](docs/mvp-acceptance-checklist.md)。

本轮 MVP 验收使用的质量门禁：`pytest -v`、`ruff check .`、`mypy src` 和 Web 服务 smoke 验收。

## 运行手册

日常启动、盘后任务、盘中提醒、降级策略和备份步骤见 [docs/ops-runbook.md](docs/ops-runbook.md)。

## 本地启动

```powershell
docker compose up -d postgres redis
python scripts/seed_sample_data.py
python -m uvicorn --app-dir src trading_assistant.web.app:app --reload --port 8000
```

访问 http://127.0.0.1:8000 查看仪表盘。

## 最小闭环执行命令

```powershell
python scripts/seed_sample_data.py
python scripts/run_daily_after_close.py
python scripts/run_intraday_monitor.py
python -m uvicorn --app-dir src trading_assistant.web.app:app --reload --port 8000
```
