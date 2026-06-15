from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from trading_assistant.scheduler.jobs import build_job_plan

    print(build_job_plan()["intraday_monitor"])


if __name__ == "__main__":
    main()
