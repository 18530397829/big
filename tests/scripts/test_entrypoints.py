import os
import subprocess
import sys
from pathlib import Path

from trading_assistant.scheduler.jobs import build_job_plan

ROOT = Path(__file__).resolve().parents[2]


def run_script(script_name: str, *, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONIOENCODING"] = "utf-8"
    if extra_env:
        env.update(extra_env)

    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script_name)],
        capture_output=True,
        check=False,
        cwd=ROOT,
        encoding="utf-8",
        env=env,
        text=True,
    )


def test_seed_sample_data_seeds_sqlite_and_prints_loaded_holdings(tmp_path: Path):
    database_path = tmp_path / "sample.db"

    result = run_script(
        "seed_sample_data.py",
        extra_env={"DATABASE_URL": f"sqlite:///{database_path.as_posix()}"},
    )

    assert result.returncode == 0, result.stderr
    assert database_path.exists()
    assert "seeded 2 sample holdings" in result.stdout
    assert "000001 平安银行 market_value=10300.00 return=3.00%" in result.stdout
    assert "600519 贵州茅台 market_value=15180.00 return=1.20%" in result.stdout


def test_daily_after_close_entrypoint_outputs_plan_and_sample_summary():
    result = run_script("run_daily_after_close.py")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == build_job_plan()["daily_after_close"]
    assert "盘后样例摘要" in result.stderr
    assert "holdings=2" in result.stderr
    assert "candidates=1" in result.stderr
    assert "top_candidate=000001 平安银行" in result.stderr
    assert "win_rate_1d=N/A avg_return_1d=N/A" in result.stderr
    assert "max_drawdown_1d=N/A profit_loss_ratio_1d=N/A" in result.stderr
    assert "false_sell_rate_5d=N/A missed_rebound_rate_5d=N/A transaction_cost_rate=0.00%" in result.stderr


def test_intraday_monitor_entrypoint_outputs_plan_and_sample_watchlist():
    result = run_script("run_intraday_monitor.py")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == build_job_plan()["intraday_monitor"]
    assert "盘中样例摘要" in result.stderr
    assert "watch_items=2" in result.stderr
    assert "000001 平安银行 latest_price=10.36 change=0.58%" in result.stderr
    assert "600519 贵州茅台 latest_price=1512.00 change=-0.40%" in result.stderr
