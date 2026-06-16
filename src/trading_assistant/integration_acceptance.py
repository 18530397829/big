from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
import json
import os
from pathlib import Path
import time
from typing import Literal

import pandas as pd

from trading_assistant.agents.event_agent import EventAgent
from trading_assistant.agents.llm_client import OpenAICompatibleLLMClient
from trading_assistant.agents.news_agent import NewsAgent
from trading_assistant.alerts.dispatcher import AlertDispatcher
from trading_assistant.alerts.feishu import FeishuWebhookSender
from trading_assistant.alerts.models import Alert, AlertLevel
from trading_assistant.data_sources.akshare_provider import AkshareMarketDataProvider


StepStatus = Literal["passed", "failed", "skipped"]


@dataclass(frozen=True)
class AcceptanceConfig:
    tushare_token: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "http://127.0.0.1:8317/v1"
    openai_model: str = "gpt-5.4-mini"
    feishu_webhook_url: str = ""
    send_feishu_messages: bool = True
    symbols: list[str] = field(default_factory=lambda: ["000001", "600519"])
    end_date: date = field(default_factory=date.today)
    lookback_days: int = 45

    @classmethod
    def from_env(cls, *, send_feishu_messages: bool = True) -> AcceptanceConfig:
        end_date_text = os.getenv("ACCEPTANCE_END_DATE", "")
        return cls(
            tushare_token=os.getenv("TUSHARE_TOKEN", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_base_url=os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:8317/v1"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
            feishu_webhook_url=os.getenv("FEISHU_WEBHOOK_URL", ""),
            send_feishu_messages=send_feishu_messages,
            end_date=date.fromisoformat(end_date_text) if end_date_text else date.today(),
        )

    @property
    def start_date(self) -> date:
        return self.end_date - timedelta(days=self.lookback_days)


@dataclass(frozen=True)
class StepResult:
    name: str
    status: StepStatus
    details: dict[str, object]
    required: bool = True


def run_all_acceptance(config: AcceptanceConfig) -> list[StepResult]:
    return [
        _capture_step("akshare", lambda: run_akshare_smoke(config)),
        _capture_step("tushare", lambda: run_tushare_smoke(config), required=False),
        _capture_step("llm", lambda: run_llm_smoke(config)),
        _capture_step("feishu", lambda: run_feishu_smoke(config)),
    ]


def is_acceptance_successful(results: list[StepResult], *, require_real: bool) -> bool:
    required_results = [result for result in results if result.required]
    has_required_failure = any(result.status == "failed" for result in required_results)
    has_required_skip = any(result.status == "skipped" for result in required_results)
    return not has_required_failure and not (require_real and has_required_skip)


def run_akshare_smoke(config: AcceptanceConfig) -> StepResult:
    started = time.perf_counter()
    provider = AkshareMarketDataProvider(config.symbols)
    frame = provider.get_daily_bars(config.start_date, config.end_date)
    details = _validate_daily_bars(frame, config.symbols)
    details["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    return StepResult(name="akshare", status="passed", details=details)


def run_tushare_smoke(config: AcceptanceConfig) -> StepResult:
    if not config.tushare_token:
        return StepResult(
            name="tushare",
            status="skipped",
            details={
                "reason": "TUSHARE_TOKEN is not configured",
                "required_for_core_acceptance": False,
            },
            required=False,
        )

    started = time.perf_counter()
    import tushare as ts

    client = ts.pro_api(config.tushare_token)
    frames: list[pd.DataFrame] = []
    for symbol in config.symbols:
        raw = client.daily(
            ts_code=_to_tushare_symbol(symbol),
            start_date=config.start_date.strftime("%Y%m%d"),
            end_date=config.end_date.strftime("%Y%m%d"),
        )
        if not raw.empty:
            frames.append(raw)
    frame = _normalize_tushare_daily(frames)
    details = _validate_daily_bars(frame, config.symbols)
    details["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    details["required_for_core_acceptance"] = False
    return StepResult(name="tushare", status="passed", details=details, required=False)


def run_llm_smoke(config: AcceptanceConfig) -> StepResult:
    if not config.openai_api_key:
        return StepResult(
            name="llm",
            status="skipped",
            details={"reason": "OPENAI_API_KEY is not configured"},
        )

    started = time.perf_counter()
    client = OpenAICompatibleLLMClient(
        base_url=config.openai_base_url,
        api_key=config.openai_api_key,
        model=config.openai_model,
        timeout=60,
    )
    event_agent = EventAgent(client)
    news_agent = NewsAgent(client)

    samples: list[dict[str, object]] = []
    samples.append(
        event_agent.extract(
            symbol="000001",
            source="acceptance-positive-announcement",
            text="公司公告称核心产品订单同比增长明显，预计本季度收入和利润继续改善。",
        )
    )
    samples.append(
        event_agent.extract(
            symbol="600519",
            source="acceptance-negative-announcement",
            text="公司公告称主要股东计划减持不超过总股本 2%，短期可能压制市场情绪。",
        )
    )
    samples.append(
        news_agent.extract_theme(
            source="acceptance-theme-news",
            text="多家银行股午后放量走强，市场关注低估值和高股息题材的持续性。",
        )
    )

    low_information_result: str
    try:
        event_agent.extract(symbol="000001", source="acceptance-low-info", text="公告：详见正文。")
        low_information_result = "structured"
    except Exception as exc:  # noqa: BLE001 - acceptance records graceful degradation.
        low_information_result = f"degraded:{exc.__class__.__name__}"

    return StepResult(
        name="llm",
        status="passed",
        details={
            "base_url": config.openai_base_url,
            "model": config.openai_model,
            "structured_samples": len(samples),
            "low_information_result": low_information_result,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        },
    )


def run_feishu_smoke(config: AcceptanceConfig) -> StepResult:
    if not config.feishu_webhook_url:
        return StepResult(
            name="feishu",
            status="skipped",
            details={"reason": "FEISHU_WEBHOOK_URL is not configured"},
        )
    if not config.send_feishu_messages:
        return StepResult(
            name="feishu",
            status="skipped",
            details={"reason": "Feishu acceptance message sending is disabled"},
        )

    started = time.perf_counter()
    sender = FeishuWebhookSender(config.feishu_webhook_url)
    dispatcher = AlertDispatcher(sender)
    dispatcher.dispatch(
        [
            Alert(level=AlertLevel.P0, symbol="000001", message="E2E acceptance P0 test message"),
            Alert(level=AlertLevel.P1, symbol="600519", message="E2E acceptance P1 test message"),
            Alert(
                level=AlertLevel.P2,
                symbol="000001",
                message="E2E acceptance P2 should not be dispatched",
            ),
        ]
    )
    sender.send_text("[SUMMARY] Real integration acceptance summary test message")
    return StepResult(
        name="feishu",
        status="passed",
        details={
            "sent_messages": 3,
            "critical_alert_messages": 2,
            "summary_messages": 1,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        },
    )


def build_acceptance_report(
    *,
    config: AcceptanceConfig,
    results: list[StepResult],
) -> dict[str, object]:
    secrets = [config.tushare_token, config.openai_api_key, config.feishu_webhook_url]
    report: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "config": {
            "tushare_token": _presence(config.tushare_token),
            "openai_api_key": _presence(config.openai_api_key),
            "openai_base_url": config.openai_base_url,
            "openai_model": config.openai_model,
            "feishu_webhook_url": _presence(config.feishu_webhook_url),
            "send_feishu_messages": config.send_feishu_messages,
            "symbols": config.symbols,
            "start_date": config.start_date.isoformat(),
            "end_date": config.end_date.isoformat(),
        },
        "results": [
            {
                "name": result.name,
                "status": result.status,
                "required": result.required,
                "details": result.details,
            }
            for result in results
        ],
    }
    redacted = _redact(report, secrets)
    if not isinstance(redacted, dict):
        raise TypeError("redacted report must be an object")
    return redacted


def write_acceptance_report(report: dict[str, object], report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "integration-acceptance-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path


def _capture_step(name: str, action: object, *, required: bool = True) -> StepResult:
    if not callable(action):
        raise TypeError("action must be callable")
    try:
        result = action()
    except Exception as exc:  # noqa: BLE001 - acceptance must record failures and continue.
        details: dict[str, object] = {"error_type": exc.__class__.__name__, "error": str(exc)}
        if not required:
            details["required_for_core_acceptance"] = False
        return StepResult(
            name=name,
            status="failed",
            details=details,
            required=required,
        )
    if not isinstance(result, StepResult):
        raise TypeError("acceptance step must return StepResult")
    return result


def _validate_daily_bars(frame: pd.DataFrame, symbols: list[str]) -> dict[str, object]:
    required = {"trade_date", "symbol", "open", "high", "low", "close", "volume", "turnover"}
    missing_columns = sorted(required - set(frame.columns))
    if missing_columns:
        raise ValueError(f"daily bars missing columns: {', '.join(missing_columns)}")
    if frame.empty:
        raise ValueError("daily bars are empty")
    frame = frame.copy()
    frame["symbol"] = frame["symbol"].astype(str).str[:6]
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    if frame["symbol"].isna().any() or (frame["symbol"].str.len() == 0).any():
        raise ValueError("daily bars contain empty symbols")
    if frame["close"].isna().any():
        raise ValueError("daily bars contain non-numeric close values")
    rows_by_symbol = {
        symbol: int(frame[frame["symbol"] == symbol].tail(10).shape[0]) for symbol in symbols
    }
    missing_symbols = [symbol for symbol, rows in rows_by_symbol.items() if rows == 0]
    if missing_symbols:
        raise ValueError(f"daily bars missing symbols: {', '.join(missing_symbols)}")
    return {
        "rows": int(frame.shape[0]),
        "symbols": symbols,
        "rows_by_symbol": rows_by_symbol,
        "columns": sorted(required),
    }


def _normalize_tushare_daily(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame(
            columns=["trade_date", "symbol", "open", "high", "low", "close", "volume", "turnover"]
        )
    frame = pd.concat(frames, ignore_index=True)
    frame = frame.rename(columns={"ts_code": "symbol", "vol": "volume", "amount": "turnover"})
    frame["symbol"] = frame["symbol"].astype(str).str[:6]
    frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
    return frame[["trade_date", "symbol", "open", "high", "low", "close", "volume", "turnover"]]


def _to_tushare_symbol(symbol: str) -> str:
    if symbol.startswith(("0", "3")):
        return f"{symbol}.SZ"
    return f"{symbol}.SH"


def _presence(value: str) -> str:
    return "set" if value else "unset"


def _redact(value: object, secrets: list[str]) -> object:
    active_secrets = [secret for secret in secrets if secret]
    if isinstance(value, str):
        redacted = value
        for secret in active_secrets:
            redacted = redacted.replace(secret, "<redacted>")
        return redacted
    if isinstance(value, list):
        return [_redact(item, active_secrets) for item in value]
    if isinstance(value, dict):
        return {str(key): _redact(item, active_secrets) for key, item in value.items()}
    return value
