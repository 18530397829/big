# A 股保守型短线交易辅助系统

第一阶段目标：盘后选股、持仓风控、完整交易计划、盘中分级提醒、智能体解释和回测复盘。

## 本地测试

```powershell
python -m pytest -v
python -m ruff check .
python -m mypy src
```

## 本地启动

```powershell
docker compose up -d postgres redis
python scripts/seed_sample_data.py
python -m uvicorn --app-dir src trading_assistant.web.app:app --reload --port 8000
```

访问 http://127.0.0.1:8000 查看仪表盘。
