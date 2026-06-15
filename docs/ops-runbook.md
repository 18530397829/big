# 运维运行手册

本文档面向 A 股保守型短线交易辅助系统的本地运行、日常检查和故障处理。所有命令默认在仓库根目录执行。

## 本地启动和停止

启动依赖服务：

```powershell
docker compose up -d postgres redis
```

加载样例持仓，并启动 Web 仪表盘：

```powershell
python scripts/seed_sample_data.py
python -m uvicorn --app-dir src trading_assistant.web.app:app --reload --port 8000
```

访问 `http://127.0.0.1:8000` 查看仪表盘。

停止 Web 服务时，在运行 `uvicorn` 的终端按 `Ctrl+C`。停止依赖服务：

```powershell
docker compose stop postgres redis
```

如需连同容器一起清理，但保留 PostgreSQL 数据卷：

```powershell
docker compose down
```

## 环境变量说明

项目通过 `.env` 或进程环境变量读取配置，字段定义见 `src/trading_assistant/settings.py`。

| 变量 | 默认值 | 用途 |
| --- | --- | --- |
| `APP_NAME` | `a-share-short-term-trading-assistant` | 应用名称。 |
| `ENVIRONMENT` | `local` | 运行环境标识，用于区分本地、测试和生产。 |
| `DATABASE_URL` | `sqlite:///./trading_assistant.db` | SQLAlchemy 数据库连接串。本地默认 SQLite；使用 PostgreSQL 时指向 docker compose 中的 `postgres` 服务。 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接串，用于后续调度、缓存或队列能力。 |
| `TUSHARE_TOKEN` | 空字符串 | Tushare 数据源 token；为空时应使用 Akshare 或样例数据降级。 |
| `OPENAI_API_KEY` | 空字符串 | LLM 能力密钥；为空时跳过智能体解释，保留规则结果。 |
| `FEISHU_WEBHOOK_URL` | 空字符串 | 飞书告警 webhook；为空时只在本地输出或仪表盘查看提醒。 |

本地 PostgreSQL 示例：

```powershell
$env:DATABASE_URL = "postgresql://trading_assistant:trading_assistant@localhost:5432/trading_assistant"
```

## 盘后任务执行步骤

盘后任务用于收盘后生成选股、风控和次日计划。建议在交易日 15:30 之后执行。

1. 确认依赖服务运行：

```powershell
docker compose up -d postgres redis
```

2. 确认样例或真实持仓已导入：

```powershell
python scripts/seed_sample_data.py
```

3. 执行盘后任务：

```powershell
python scripts/run_daily_after_close.py
```

4. 检查终端输出，确认包含盘后任务计划；随后打开仪表盘复核候选股、持仓风险和交易计划。

5. 若当日使用外部数据源，记录数据源名称、更新时间和是否发生降级。

## 盘中提醒执行步骤

盘中提醒用于在交易时段检查持仓和候选股关键价位。当前脚本输出监控计划，后续可接入调度器定时执行。

1. 交易日前确认样例数据或真实持仓可读取：

```powershell
python scripts/seed_sample_data.py
```

2. 在交易时段启动盘中提醒检查：

```powershell
python scripts/run_intraday_monitor.py
```

3. 根据提醒等级处理：

- `P0`：立即查看风险，优先确认是否触发止损、异常波动或系统性风险。
- `P1`：在 5 分钟内复核价格、成交量和持仓影响。
- `P2/P3`：进入仪表盘汇总，盘后复盘即可。

4. 如果 `FEISHU_WEBHOOK_URL` 已配置，确认飞书群收到消息；未配置时以终端输出和 Web 仪表盘为准。

## 样例数据重置步骤

样例数据位于 `data/samples/`，用于本地演示和测试。重置前先确认没有需要保留的本地改动：

```powershell
git status --short data/samples
```

如只想恢复仓库中的样例文件：

```powershell
git restore -- data/samples
```

恢复后重新加载样例持仓：

```powershell
python scripts/seed_sample_data.py
```

如果本地 SQLite 文件需要一起重置，先停止 Web 服务，再删除本地库文件并重新执行样例加载：

```powershell
Remove-Item .\trading_assistant.db -ErrorAction SilentlyContinue
python scripts/seed_sample_data.py
```

## 数据源失败降级策略

当 Tushare、Akshare 或外部行情接口发生数据源失败时，按以下顺序处理：

1. 记录失败时间、接口名称、请求参数和错误信息。
2. 如果 `TUSHARE_TOKEN` 缺失或 Tushare 返回空数据，切换到 Akshare 数据源。
3. 如果实时外部数据仍不可用，切换到 `FakeMarketDataProvider` 和 `data/samples/` 样例数据，仅用于演示、回归检查和流程验证。
4. 对盘后任务，允许使用最近一次成功落库或样例数据生成报告，但必须在报告中标注“数据不完整”。
5. 对盘中提醒，外部数据不可用时只保留本地持仓风控和仪表盘查看，不发送高优先级交易动作建议。
6. 恢复后重新执行对应脚本，并对比降级期间生成的候选股和风险提示。

降级原则：系统可以继续辅助复核，但不能把样例数据或过期行情当作真实交易依据。

## LLM 或 Webhook 不可用处理

LLM 不可用时：

- 检查 `OPENAI_API_KEY` 是否配置。
- 保留规则因子、评分、风险和交易计划输出。
- 跳过智能体解释、新闻总结和公告解释。
- 在盘后记录中标注“LLM unavailable”，待服务恢复后可重新执行盘后解释流程。

Webhook 不可用时：

- 检查 `FEISHU_WEBHOOK_URL` 是否为空或已过期。
- 确认网络、防火墙和飞书机器人权限。
- 暂停自动推送，改用终端输出和 Web 仪表盘人工查看。
- 服务恢复后重新发送必要的 P0/P1 提醒摘要，避免重复发送全部历史消息。

## PostgreSQL 和本地报告备份方式

创建备份目录：

```powershell
New-Item -ItemType Directory -Force backups
```

PostgreSQL 备份：

```powershell
$stamp = Get-Date -Format yyyyMMdd-HHmmss
docker compose exec -T postgres pg_dump -U trading_assistant -d trading_assistant | Set-Content -Encoding UTF8 "backups/postgres-$stamp.sql"
```

PostgreSQL 恢复前先确认目标库可覆盖，再执行：

```powershell
Get-Content "backups/postgres-YYYYMMDD-HHMMSS.sql" | docker compose exec -T postgres psql -U trading_assistant -d trading_assistant
```

本地 SQLite 备份：

```powershell
$stamp = Get-Date -Format yyyyMMdd-HHmmss
Copy-Item .\trading_assistant.db "backups/trading_assistant-$stamp.db" -ErrorAction SilentlyContinue
```

本地报告备份。若当前环境已将报告输出到 `reports/`，按日期复制；若目录不存在，说明当前 MVP 尚未落盘报告：

```powershell
$stamp = Get-Date -Format yyyyMMdd-HHmmss
if (Test-Path reports) {
    Copy-Item -Recurse reports "backups/reports-$stamp"
} else {
    Write-Host "reports directory not found"
}
```

建议至少在每日盘后任务完成后备份一次 PostgreSQL 或 SQLite，并在发布前额外备份本地报告。

## 常见错误排查

| 现象 | 处理方式 |
| --- | --- |
| `ModuleNotFoundError: No module named 'trading_assistant'` | 使用脚本入口，或启动 Web 时带上 `python -m uvicorn --app-dir src trading_assistant.web.app:app --reload --port 8000`。 |
| `database is locked` | 停止多余的本地进程，确认没有多个写入任务同时访问 SQLite；生产或多人环境切换 PostgreSQL。 |
| Web 页面打不开 | 确认 `uvicorn` 进程仍在运行，端口为 `8000`，并检查终端异常日志。 |
| PostgreSQL 连接失败 | 运行 `docker compose ps`，确认 `postgres` 健康；检查 `DATABASE_URL` 用户名、密码、端口和库名。 |
| Redis 连接失败 | 运行 `docker compose up -d redis`，检查 `REDIS_URL` 是否仍为 `redis://localhost:6379/0`。 |
| 数据源返回空结果 | 检查日期是否为交易日、token 是否有效、网络是否可访问；必要时按数据源失败降级策略处理。 |
| 飞书没有收到提醒 | 检查 `FEISHU_WEBHOOK_URL`、机器人权限和告警级别；未配置时查看本地输出。 |
| LLM 解释缺失 | 检查 `OPENAI_API_KEY`；密钥缺失时按规则结果继续运行。 |

## 每日运维检查清单

- 开盘前确认 `docker compose ps` 中 PostgreSQL 和 Redis 状态正常。
- 开盘前执行 `python scripts/seed_sample_data.py`，确认持仓数据可读取。
- 盘中提醒时段执行或调度 `python scripts/run_intraday_monitor.py`，关注 P0/P1 输出。
- 盘中如发生数据源失败，立即记录并启用降级策略。
- 收盘后执行 `python scripts/run_daily_after_close.py`，复核盘后任务输出。
- 收盘后打开 Web 仪表盘，检查候选股、持仓风险和交易计划是否更新。
- 收盘后备份 PostgreSQL 或 SQLite，并备份本地报告目录。
- 每日结束前记录 LLM、Webhook、数据源和数据库是否有异常。
- 发布或切换配置前运行 `python -m pytest -v` 和 `python -m ruff check .`。
