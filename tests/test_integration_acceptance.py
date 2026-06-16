import json
from datetime import date

from trading_assistant.integration_acceptance import (
    AcceptanceConfig,
    StepResult,
    build_acceptance_report,
    is_acceptance_successful,
    run_feishu_smoke,
    run_tushare_smoke,
)


def test_acceptance_report_redacts_runtime_secrets():
    config = AcceptanceConfig(
        tushare_token="tushare-secret",
        openai_api_key="llm-secret",
        openai_base_url="http://127.0.0.1:8317/v1",
        openai_model="gpt-5.4-mini",
        feishu_webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/webhook-secret",
    )
    report = build_acceptance_report(
        config=config,
        results=[
            StepResult(
                name="feishu",
                status="failed",
                details={
                    "error": (
                        "HTTPStatusError for https://open.feishu.cn/open-apis/bot/v2/"
                        "hook/webhook-secret with llm-secret"
                    )
                },
            )
        ],
    )

    encoded = json.dumps(report, ensure_ascii=False)

    assert "tushare-secret" not in encoded
    assert "llm-secret" not in encoded
    assert "webhook-secret" not in encoded
    assert "<redacted>" in encoded
    assert report["config"]["tushare_token"] == "set"
    assert report["config"]["openai_api_key"] == "set"
    assert report["config"]["feishu_webhook_url"] == "set"


def test_acceptance_config_reads_end_date_override(monkeypatch):
    monkeypatch.setenv("ACCEPTANCE_END_DATE", "2024-06-15")

    config = AcceptanceConfig.from_env()

    assert config.end_date == date(2024, 6, 15)


def test_acceptance_config_can_disable_feishu_message_sending(monkeypatch):
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://example.test/webhook")

    config = AcceptanceConfig.from_env(send_feishu_messages=False)

    assert config.feishu_webhook_url == "https://example.test/webhook"
    assert config.send_feishu_messages is False


def test_feishu_smoke_dispatches_critical_alerts_and_summary(monkeypatch):
    sent_texts: list[str] = []

    class FakeSender:
        def __init__(self, webhook_url: str) -> None:
            assert webhook_url == "https://example.test/webhook"

        def send_text(self, text: str) -> None:
            sent_texts.append(text)

    monkeypatch.setattr("trading_assistant.integration_acceptance.FeishuWebhookSender", FakeSender)

    result = run_feishu_smoke(
        AcceptanceConfig(feishu_webhook_url="https://example.test/webhook")
    )

    assert result.status == "passed"
    assert sent_texts == [
        "[P0] 000001 E2E acceptance P0 test message",
        "[P1] 600519 E2E acceptance P1 test message",
        "[SUMMARY] Real integration acceptance summary test message",
    ]
    assert result.details["critical_alert_messages"] == 2
    assert result.details["summary_messages"] == 1


def test_feishu_smoke_skips_when_message_sending_is_disabled(monkeypatch):
    class UnexpectedSender:
        def __init__(self, webhook_url: str) -> None:
            raise AssertionError(f"should not send to {webhook_url}")

    monkeypatch.setattr("trading_assistant.integration_acceptance.FeishuWebhookSender", UnexpectedSender)

    result = run_feishu_smoke(
        AcceptanceConfig(
            feishu_webhook_url="https://example.test/webhook",
            send_feishu_messages=False,
        )
    )

    assert result.name == "feishu"
    assert result.status == "skipped"
    assert result.required is True
    assert result.details["reason"] == "Feishu acceptance message sending is disabled"


def test_tushare_smoke_is_optional_when_token_is_not_configured():
    result = run_tushare_smoke(AcceptanceConfig(tushare_token=""))

    assert result.name == "tushare"
    assert result.status == "skipped"
    assert result.required is False
    assert result.details["required_for_core_acceptance"] is False


def test_optional_tushare_failure_does_not_fail_core_acceptance():
    results = [
        StepResult(name="akshare", status="passed", details={}, required=True),
        StepResult(name="tushare", status="failed", details={"error": "no daily access"}, required=False),
        StepResult(name="llm", status="passed", details={}, required=True),
        StepResult(name="feishu", status="passed", details={}, required=True),
    ]

    assert is_acceptance_successful(results, require_real=True) is True


def test_required_skip_fails_require_real_acceptance():
    results = [
        StepResult(name="akshare", status="passed", details={}, required=True),
        StepResult(name="tushare", status="skipped", details={}, required=False),
        StepResult(name="llm", status="skipped", details={}, required=True),
        StepResult(name="feishu", status="passed", details={}, required=True),
    ]

    assert is_acceptance_successful(results, require_real=True) is False
