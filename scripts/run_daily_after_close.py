from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from trading_assistant.scheduler.jobs import build_job_plan
    from trading_assistant.web.view_models import (
        build_backtest_view,
        build_candidates_view,
        build_dashboard_view,
    )

    print(build_job_plan()["daily_after_close"])
    dashboard = build_dashboard_view()
    candidates = build_candidates_view()
    backtest = build_backtest_view()
    print("盘后样例摘要", file=sys.stderr)
    print(
        f"holdings={dashboard['holding_count']} "
        f"portfolio_risk={dashboard['portfolio_risk']} "
        f"total_market_value={dashboard['total_market_value']}",
        file=sys.stderr,
    )
    print(
        f"candidates={candidates['candidate_count']} "
        f"top_candidate={dashboard['top_candidate']}",
        file=sys.stderr,
    )
    print(
        f"win_rate_1d={backtest['summary']['win_rate_1d']} "
        f"avg_return_1d={backtest['summary']['avg_return_1d']}",
        file=sys.stderr,
    )
    print(
        f"max_drawdown_1d={backtest['summary']['max_drawdown_1d']} "
        f"profit_loss_ratio_1d={backtest['summary']['profit_loss_ratio_1d']}",
        file=sys.stderr,
    )
    print(
        f"false_sell_rate_5d={backtest['summary']['false_sell_rate_5d']} "
        f"missed_rebound_rate_5d={backtest['summary']['missed_rebound_rate_5d']} "
        f"transaction_cost_rate={backtest['summary']['transaction_cost_rate']}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
