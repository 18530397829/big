# 真实外部集成验收 Runbook

目标：在进入第二阶段前，用真实 AKShare、真实本地 LLM 和真实飞书 Webhook 完成一次可复现的端到端稳定性验收。Tushare 是可选增强项，不阻断核心业务闭环准入。

## 前置条件

- 使用本机受控 `.env` 或临时环境变量配置密钥，不把密钥写入仓库。
- `TUSHARE_TOKEN`、`OPENAI_API_KEY`、`FEISHU_WEBHOOK_URL` 不得出现在日志、截图、提交或报告正文中。
- 当前仓库已有 AKShare/Tushare Provider 外壳和飞书 Webhook sender。
- 当前仓库只有 `MockLLMClient`，尚未实现真实 LLM adapter；真实 LLM 验收前必须先补一个符合 `LLMClient.complete_json()` 协议的真实实现，并用 Mock 保持单元测试稳定。

## 环境准备

```powershell
$env:TUSHARE_TOKEN = "<optional-local-token>"
$env:OPENAI_API_KEY = "<local-key>"
$env:OPENAI_BASE_URL = "http://127.0.0.1:8317/v1"
$env:OPENAI_MODEL = "gpt-5.4-mini"
$env:FEISHU_WEBHOOK_URL = "<local-webhook>"
.\.venv\Scripts\python.exe -m pytest
```

验收日志目录：

```powershell
$stamp = Get-Date -Format yyyyMMdd-HHmmss
New-Item -ItemType Directory -Force "data/reports/integration-$stamp"
```

统一 smoke 入口。默认不会向飞书测试群发送消息，避免日常完整流程重复刷屏；需要真实飞书验收时必须显式增加 `--send-feishu`。`--require-real` 只要求核心必需链路（AKShare、本地 LLM、飞书）真实通过；Tushare 会进入报告，但不阻断退出码。

```powershell
.\.venv\Scripts\python.exe scripts/run_integration_acceptance.py --send-feishu --require-real --report-dir "data/reports/integration-$stamp"
```

日常检查真实 AKShare、本地 LLM、报告生成和脱敏时，不发送飞书消息：

```powershell
.\.venv\Scripts\python.exe scripts/run_integration_acceptance.py --report-dir "data/reports/integration-$stamp"
```

如果真实源当前日期窗口不可用，可显式固定验收日期窗口，报告会记录 `start_date` 和 `end_date`：

```powershell
$env:ACCEPTANCE_END_DATE = "2024-06-15"
```

## AKShare 验收

样本标的：`000001`、`600519`。

验收动作：

1. 拉取最近 10 个交易日的日线数据。
2. 校验字段：`trade_date`、`symbol`、`open`、`high`、`low`、`close`、`volume`、`turnover`。
3. 校验 `symbol` 不为空，`close` 可转成数值。
4. 记录耗时、行数、空数据、异常信息。
5. 人为断网或传入异常标的，确认失败能落日志，并能退回 `FakeMarketDataProvider` 或 `data/samples/`。

通过标准：

- 至少 2 个样本标的返回非空日线。
- 字段名归一化后与 Provider 协议一致。
- 异常路径不会中断整个盘后流程。

## Tushare 可选增强验收

Tushare 当前定位为可选增强数据源。没有 token、token 权限不足、`daily` 接口未开通或外部服务不可用时，验收报告必须记录状态和脱敏错误，但不阻断 `AKShare + 本地 LLM + 飞书` 核心闭环准入。

验收动作：

1. 如果配置了 `TUSHARE_TOKEN`，初始化真实 Tushare client。
2. 拉取最近 10 个交易日的日线数据。
3. 校验字段归一化和数值可用性。
4. 删除或置空 `TUSHARE_TOKEN`，确认报告记录为可选跳过，系统继续使用 AKShare。

通过标准：

- Token 有效且具备 `daily` 权限时返回非空数据。
- Token 缺失或接口权限不足时不泄露 token，并标记为可选增强不可用。
- Tushare 不参与核心准入退出码。

## 真实 LLM 验收

执行前置：

- 新增真实 LLM adapter，类必须实现 `LLMClient.complete_json(system_prompt: str, user_prompt: str) -> dict[str, object]`。
- 单元测试继续使用 `MockLLMClient`，真实 adapter 只在显式配置密钥时运行。

验收样本：

- 1 条正面公告。
- 1 条负面公告。
- 1 条新闻题材。
- 1 条格式异常或低信息量文本。

通过标准：

- 返回值是 JSON object。
- 事件类型、情绪、置信度字段可被 `EventAgent` 和 `NewsAgent` 消费。
- 超时、非 JSON、空响应能记录错误并降级到规则结果。
- 日志不包含 API Key、完整 prompt 中的敏感账户信息或 token。

## 飞书 Webhook 验收

验收动作：

1. 使用测试群机器人配置 `FEISHU_WEBHOOK_URL`。
2. 执行带 `--send-feishu` 的验收命令，发送 P0 文本、P1 文本和普通摘要各 1 条。
3. 临时改成无效 URL，确认非 2xx 或网络异常会被记录。
4. 重复发送同一 P0/P1 摘要，确认调度层不会无限重复推送。

通过标准：

- 测试群能收到 P0/P1。
- 发送失败时终端和运行日志能看到错误。
- Webhook URL 不出现在日志正文。

## 端到端验收

```powershell
.\.venv\Scripts\python.exe scripts/seed_sample_data.py
.\.venv\Scripts\python.exe scripts/run_daily_after_close.py
.\.venv\Scripts\python.exe scripts/run_intraday_monitor.py
```

补充真实源执行后必须归档：

- 命令。
- 开始和结束时间。
- 样本标的。
- 成功/失败数量。
- 降级路径是否触发。
- 失败堆栈脱敏摘要。
- 飞书测试群截图或人工确认记录。

## 第二阶段准入结论

只有满足以下条件，才能把核心真实外部链路标记为已验收：

- AKShare 完成一次真实源 smoke。
- 真实 LLM adapter 完成结构化输出 smoke。
- 飞书测试群收到 P0/P1。
- Tushare 状态已进入报告；可通过、可跳过或可选失败，但不阻断核心准入。
- 所有失败路径均有降级或人工复核路径。
- 归档日志已脱敏，且未提交真实密钥。
