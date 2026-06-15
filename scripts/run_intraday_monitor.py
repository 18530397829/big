from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from trading_assistant.scheduler.jobs import build_job_plan
    from trading_assistant.web.view_models import build_intraday_monitor_view

    print(build_job_plan()["intraday_monitor"])
    view = build_intraday_monitor_view()
    print("盘中样例摘要", file=sys.stderr)
    print(
        f"watch_items={view['watch_items']} critical_alerts={view['critical_alerts']}",
        file=sys.stderr,
    )
    for item in view["items"]:
        print(
            f"{item['symbol']} {item['name']} "
            f"latest_price={item['latest_price']} change={item['change_pct']} "
            f"priority={item['priority']}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
