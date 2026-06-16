from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from datetime import datetime
    import argparse

    from trading_assistant.integration_acceptance import (
        AcceptanceConfig,
        build_acceptance_report,
        is_acceptance_successful,
        run_all_acceptance,
        write_acceptance_report,
    )

    parser = argparse.ArgumentParser(description="Run real external integration acceptance smoke.")
    parser.add_argument(
        "--require-real",
        action="store_true",
        help="Fail if any required core step is skipped.",
    )
    parser.add_argument(
        "--send-feishu",
        action="store_true",
        help="Actually send Feishu acceptance messages. Omit for no-send dry runs.",
    )
    parser.add_argument("--report-dir", type=Path, default=None)
    args = parser.parse_args()

    config = AcceptanceConfig.from_env(send_feishu_messages=args.send_feishu)
    results = run_all_acceptance(config)
    report = build_acceptance_report(config=config, results=results)
    report_dir = args.report_dir or (
        ROOT / "data" / "reports" / f"integration-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    report_path = write_acceptance_report(report, report_dir)

    status_counts: dict[str, int] = {}
    for result in results:
        status_counts[result.status] = status_counts.get(result.status, 0) + 1

    print(f"integration_acceptance_report={report_path}")
    print(f"status_counts={status_counts}")
    for result in results:
        print(f"{result.name}={result.status}")

    if not is_acceptance_successful(results, require_real=args.require_real):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
