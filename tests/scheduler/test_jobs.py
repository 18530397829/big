import os
import subprocess
import sys
from datetime import UTC
from pathlib import Path

from trading_assistant.scheduler.jobs import build_job_plan, build_task_run_logs

ROOT = Path(__file__).resolve().parents[2]


def test_build_job_plan_contains_daily_and_intraday_jobs():
    jobs = build_job_plan()

    assert "daily_after_close" in jobs
    assert "intraday_monitor" in jobs


def test_build_task_run_logs_uses_timezone_aware_utc_times():
    logs = build_task_run_logs("2026-06-12")

    for log in logs.values():
        assert log.started_at.tzinfo is UTC
        assert log.finished_at.tzinfo is UTC


def test_script_entrypoints_run_from_repo_root_without_installed_package():
    jobs = build_job_plan()
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONIOENCODING"] = "utf-8"

    scripts = {
        "run_daily_after_close.py": jobs["daily_after_close"],
        "run_intraday_monitor.py": jobs["intraday_monitor"],
    }

    for script_name, expected_output in scripts.items():
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script_name)],
            capture_output=True,
            check=False,
            cwd=ROOT,
            encoding="utf-8",
            env=env,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == expected_output
