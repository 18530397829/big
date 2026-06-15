import json
from datetime import UTC, datetime

from trading_assistant.observability import TaskRunLog
from trading_assistant.scheduler.jobs import build_task_run_logs


def test_task_run_log_to_dict_contains_required_fields():
    started_at = datetime(2026, 6, 12, 15, 30, tzinfo=UTC)
    finished_at = datetime(2026, 6, 12, 15, 35, tzinfo=UTC)

    log = TaskRunLog(
        task_name="daily_after_close",
        trade_date="2026-06-12",
        started_at=started_at,
        finished_at=finished_at,
        input_count=120,
        output_count=12,
        status="success",
        error_reason=None,
    )

    serialized = log.to_dict()

    assert serialized == {
        "task_name": "daily_after_close",
        "trade_date": "2026-06-12",
        "started_at": "2026-06-12T15:30:00+00:00",
        "finished_at": "2026-06-12T15:35:00+00:00",
        "input_count": 120,
        "output_count": 12,
        "status": "success",
        "error_reason": None,
    }
    json.dumps(serialized)


def test_scheduler_build_task_run_logs_connects_key_entrypoints():
    logs = build_task_run_logs("2026-06-12")

    expected_task_names = {
        "daily_after_close",
        "intraday_monitor",
        "evening_agent_report",
        "weekly_review",
    }
    assert set(logs) == expected_task_names

    for task_name in expected_task_names:
        log = logs[task_name]
        assert log.task_name == task_name
        assert log.trade_date == "2026-06-12"
        assert log.started_at <= log.finished_at
        assert log.input_count == 0
        assert log.output_count == 0
        assert log.status == "scheduled"
        assert log.error_reason is None
