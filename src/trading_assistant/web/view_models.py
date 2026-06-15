import json
from pathlib import Path
from typing import Any, cast

import pandas as pd

from trading_assistant.backtest.engine import evaluate_forward_returns
from trading_assistant.backtest.metrics import summarize_returns
from trading_assistant.domain.enums import ActionAdvice, RiskLevel
from trading_assistant.domain.models import Holding
from trading_assistant.planning.candidate_selector import select_candidates
from trading_assistant.portfolio.importer import load_holdings_csv
from trading_assistant.portfolio.risk_engine import PortfolioRiskDecision, PortfolioRiskEngine

ROOT = Path(__file__).resolve().parents[3]
SAMPLE_DIR = ROOT / "data" / "samples"

RISK_LABELS = {
    RiskLevel.LOW: "低",
    RiskLevel.MEDIUM: "中",
    RiskLevel.HIGH: "高",
    RiskLevel.CRITICAL: "严重",
}
RISK_PRIORITY = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}
ACTION_LABELS = {
    ActionAdvice.HOLD: "持有",
    ActionAdvice.TIGHTEN_STOP: "收紧止损",
    ActionAdvice.REDUCE: "减仓",
    ActionAdvice.SELL_ON_REBOUND: "反弹卖出",
    ActionAdvice.CLEAR_OR_STOP: "清仓/止损",
    ActionAdvice.WATCH_FOR_TRIGGER: "等待触发",
    ActionAdvice.NO_ACTION: "不操作",
}

DashboardView = dict[str, Any]
HoldingsView = dict[str, Any]
CandidatesView = dict[str, Any]
BacktestView = dict[str, Any]
IntradayMonitorView = dict[str, Any]


def build_dashboard_view(sample_dir: Path | None = None) -> DashboardView:
    holdings_view = build_holdings_view(sample_dir)
    candidates_view = build_candidates_view(sample_dir)
    backtest_view = build_backtest_view(sample_dir)
    intraday_view = build_intraday_monitor_view(sample_dir)
    market_score = _market_score(_load_sectors(_resolve_sample_dir(sample_dir)))

    top_candidate = "暂无候选"
    if candidates_view["candidates"]:
        first_candidate = candidates_view["candidates"][0]
        top_candidate = f"{first_candidate['symbol']} {first_candidate['name']}"

    sections = [
        {
            "title": "持仓风险",
            "summary": (
                f"{holdings_view['summary']['holding_count']} 只持仓，"
                f"总市值 {holdings_view['summary']['total_market_value']}，"
                f"最高风险 {holdings_view['summary']['max_risk_level']}"
            ),
        },
        {
            "title": "市场环境",
            "summary": f"样例板块平均涨幅 {_average_sector_pct(sample_dir):.2f}%，环境分 {market_score}",
        },
        {
            "title": "重点候选",
            "summary": f"{candidates_view['candidate_count']} 只候选，首选 {top_candidate}",
        },
        {
            "title": "盘中提醒",
            "summary": (
                f"{intraday_view['watch_items']} 个监控项，"
                f"P0/P1 {intraday_view['critical_alerts']} 条"
            ),
        },
        {
            "title": "回测复盘",
            "summary": (
                f"1日胜率 {backtest_view['summary']['win_rate_1d']}，"
                f"平均收益 {backtest_view['summary']['avg_return_1d']}，"
                f"最大回撤 {backtest_view['summary']['max_drawdown_1d']}"
            ),
        },
    ]

    return {
        "market_score": market_score,
        "portfolio_risk": holdings_view["summary"]["max_risk_level"],
        "holding_count": holdings_view["summary"]["holding_count"],
        "total_market_value": holdings_view["summary"]["total_market_value"],
        "candidate_count": candidates_view["candidate_count"],
        "critical_alerts": intraday_view["critical_alerts"],
        "top_candidate": top_candidate,
        "sections": sections,
    }


def build_holdings_view(sample_dir: Path | None = None) -> HoldingsView:
    sample_path = _resolve_sample_dir(sample_dir)
    holdings = load_holdings_csv(sample_path / "holdings.csv")
    decisions = _risk_decisions(holdings, sample_path)
    total_market_value = sum(holding.market_value for holding in holdings)
    max_risk_level = _max_risk_level(decisions)

    rows = []
    for holding, decision in zip(holdings, decisions, strict=True):
        rows.append(
            {
                "symbol": holding.symbol,
                "name": holding.name,
                "quantity": holding.quantity,
                "market_value": _format_money(holding.market_value),
                "unrealized_return_pct": _format_pct(holding.unrealized_return_pct),
                "risk_level": RISK_LABELS[decision.risk_level],
                "action_advice": ACTION_LABELS[decision.action_advice],
                "reasons": "、".join(decision.reasons),
            }
        )

    return {
        "summary": {
            "holding_count": len(holdings),
            "total_market_value": _format_money(total_market_value),
            "max_risk_level": RISK_LABELS[max_risk_level],
        },
        "holdings": rows,
    }


def build_candidates_view(sample_dir: Path | None = None) -> CandidatesView:
    selected = _select_sample_candidates(_resolve_sample_dir(sample_dir))
    rows = []
    for candidate in selected.to_dict(orient="records"):
        rows.append(
            {
                "symbol": candidate["symbol"],
                "name": candidate["name"],
                "opportunity_score": f"{float(candidate['opportunity_score']):.2f}",
                "plan_confidence_score": f"{float(candidate['plan_confidence_score']):.2f}",
                "reasons": candidate["reasons"],
            }
        )
    return {"candidate_count": len(rows), "candidates": rows}


def build_backtest_view(sample_dir: Path | None = None) -> BacktestView:
    sample_path = _resolve_sample_dir(sample_dir)
    selected = _select_sample_candidates(sample_path)
    prices = _load_daily_bars(sample_path)
    if selected.empty:
        evaluated = pd.DataFrame()
    else:
        signals = _candidate_signals(selected, prices)
        evaluated = evaluate_forward_returns(signals, prices)

    summary = summarize_returns(evaluated)
    rows = []
    name_by_symbol = {
        str(row["symbol"]): str(row["name"]) for row in selected.to_dict(orient="records")
    }
    for row in evaluated.to_dict(orient="records"):
        rows.append(
            {
                "symbol": row["symbol"],
                "name": name_by_symbol.get(str(row["symbol"]), ""),
                "trade_date": str(pd.to_datetime(row["trade_date"]).date()),
                "score": f"{float(row['score']):.2f}",
                "return_1d": _format_optional_pct(row.get("return_1d")),
                "max_return_5d": _format_optional_pct(row.get("max_return_5d")),
            }
        )

    return {
        "summary": {
            "signal_count": len(rows),
            "win_rate_1d": _format_optional_pct(summary["win_rate_1d"]),
            "avg_return_1d": _format_optional_pct(summary["avg_return_1d"]),
            "net_win_rate_1d": _format_optional_pct(summary["net_win_rate_1d"]),
            "net_avg_return_1d": _format_optional_pct(summary["net_avg_return_1d"]),
            "profit_loss_ratio_1d": _format_optional_number(summary["profit_loss_ratio_1d"]),
            "max_drawdown_1d": _format_optional_pct(summary["max_drawdown_1d"]),
            "false_sell_rate_5d": _format_optional_pct(summary["false_sell_rate_5d"]),
            "missed_rebound_rate_5d": _format_optional_pct(summary["missed_rebound_rate_5d"]),
            "transaction_cost_rate": _format_optional_pct(summary["transaction_cost_rate"]),
        },
        "signals": rows,
    }


def build_intraday_monitor_view(sample_dir: Path | None = None) -> IntradayMonitorView:
    sample_path = _resolve_sample_dir(sample_dir)
    holdings = load_holdings_csv(sample_path / "holdings.csv")
    latest_prices = _latest_minute_prices(_load_minute_bars(sample_path))
    items = []
    critical_alerts = 0
    for holding in holdings:
        latest_price = latest_prices.get(holding.symbol, holding.current_price)
        change = (latest_price - holding.current_price) / holding.current_price
        priority = "P1" if change <= -0.03 else "P2"
        if priority == "P1":
            critical_alerts += 1
        items.append(
            {
                "symbol": holding.symbol,
                "name": holding.name,
                "latest_price": _format_money(latest_price),
                "change_pct": _format_pct(change),
                "priority": priority,
            }
        )

    return {
        "watch_items": len(items),
        "critical_alerts": critical_alerts,
        "items": items,
    }


def _resolve_sample_dir(sample_dir: Path | None) -> Path:
    return sample_dir if sample_dir is not None else SAMPLE_DIR


def _load_daily_bars(sample_dir: Path) -> pd.DataFrame:
    frame = pd.read_csv(sample_dir / "daily_bars.csv", dtype={"symbol": str})
    frame["trade_date"] = pd.to_datetime(frame["trade_date"])
    return frame


def _load_minute_bars(sample_dir: Path) -> pd.DataFrame:
    frame = pd.read_csv(sample_dir / "minute_bars.csv", dtype={"symbol": str})
    frame["datetime"] = pd.to_datetime(frame["datetime"])
    return frame


def _load_sectors(sample_dir: Path) -> pd.DataFrame:
    frame = pd.read_csv(sample_dir / "sectors.csv", dtype={"leader_symbol": str})
    frame["trade_date"] = pd.to_datetime(frame["trade_date"])
    return frame


def _load_events(sample_dir: Path) -> list[dict[str, str]]:
    events = []
    for line in (sample_dir / "events.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def _market_score(sectors: pd.DataFrame) -> int:
    if sectors.empty:
        return 50
    score = 50 + float(sectors["pct_chg"].mean()) * 5
    return max(0, min(100, round(score)))


def _average_sector_pct(sample_dir: Path | None) -> float:
    sectors = _load_sectors(_resolve_sample_dir(sample_dir))
    if sectors.empty:
        return 0.0
    return round(float(sectors["pct_chg"].mean()), 2)


def _risk_decisions(holdings: list[Holding], sample_dir: Path) -> list[PortfolioRiskDecision]:
    engine = PortfolioRiskEngine(default_stop_loss_pct=0.04, hard_stop_loss_pct=0.05)
    market_score = _market_score(_load_sectors(sample_dir))
    sector_pct_by_name = _sector_pct_by_name(_load_sectors(sample_dir))
    latest_prices = _latest_minute_prices(_load_minute_bars(sample_dir))
    sentiment_by_symbol = _sentiment_by_symbol(_load_events(sample_dir))

    decisions = []
    for holding in holdings:
        latest_price = latest_prices.get(holding.symbol, holding.current_price)
        decisions.append(
            engine.evaluate(
                holding=holding,
                technical_broken=False,
                sector_cooling=sector_pct_by_name.get(holding.theme, 0.0) < 0,
                negative_event=sentiment_by_symbol.get(holding.symbol) == "negative",
                fund_outflow=latest_price < holding.current_price,
                market_score=market_score,
            )
        )
    return decisions


def _max_risk_level(decisions: list[PortfolioRiskDecision]) -> RiskLevel:
    if not decisions:
        return RiskLevel.LOW
    return max((decision.risk_level for decision in decisions), key=lambda level: RISK_PRIORITY[level])


def _select_sample_candidates(sample_dir: Path) -> pd.DataFrame:
    scored = _sample_scored_stocks(sample_dir)
    return select_candidates(
        scored,
        min_opportunity_score=76,
        min_plan_confidence_score=70,
        limit=5,
    )


def _sample_scored_stocks(sample_dir: Path) -> pd.DataFrame:
    latest_daily = (
        _load_daily_bars(sample_dir)
        .sort_values("trade_date")
        .groupby("symbol", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )
    sector_by_symbol = _sector_by_leader(_load_sectors(sample_dir))
    sentiment_by_symbol = _sentiment_by_symbol(_load_events(sample_dir))

    rows = []
    for row in latest_daily.to_dict(orient="records"):
        symbol = str(row["symbol"])
        sector = sector_by_symbol.get(symbol, {"sector_name": "未知", "pct_chg": 0.0})
        daily_return_pct = (float(row["close"]) - float(row["pre_close"])) / float(
            row["pre_close"]
        ) * 100
        sector_pct = float(sector["pct_chg"])
        opportunity_score = round(75 + sector_pct * 5 + daily_return_pct, 2)
        plan_confidence_score = round(72 + max(sector_pct, 0.0) * 2, 2)
        rows.append(
            {
                "trade_date": row["trade_date"],
                "symbol": symbol,
                "name": _name_for_symbol(symbol, sample_dir),
                "pool_type": "tradable",
                "opportunity_score": opportunity_score,
                "plan_confidence_score": plan_confidence_score,
                "reasons": (
                    f"{sector['sector_name']}板块涨幅 {sector_pct:.2f}%；"
                    f"日线涨幅 {daily_return_pct:.2f}%；"
                    f"事件 {sentiment_by_symbol.get(symbol, 'none')}"
                ),
            }
        )
    return pd.DataFrame(rows)


def _candidate_signals(selected: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for candidate in selected.to_dict(orient="records"):
        symbol_prices = prices[prices["symbol"] == candidate["symbol"]].sort_values("trade_date")
        if symbol_prices.empty:
            continue
        rows.append(
            {
                "trade_date": candidate["trade_date"],
                "symbol": candidate["symbol"],
                "signal_type": "candidate",
                "score": candidate["opportunity_score"],
                "action": "watch",
            }
        )
    return pd.DataFrame(rows)


def _sector_by_leader(sectors: pd.DataFrame) -> dict[str, dict[str, float | str]]:
    return {
        str(row["leader_symbol"]): {
            "sector_name": str(row["sector_name"]),
            "pct_chg": float(row["pct_chg"]),
        }
        for row in sectors.to_dict(orient="records")
    }


def _sector_pct_by_name(sectors: pd.DataFrame) -> dict[str, float]:
    return {
        str(row["sector_name"]): float(row["pct_chg"])
        for row in sectors.to_dict(orient="records")
    }


def _sentiment_by_symbol(events: list[dict[str, str]]) -> dict[str, str]:
    return {str(event["symbol"]): str(event["sentiment"]) for event in events}


def _latest_minute_prices(minute_bars: pd.DataFrame) -> dict[str, float]:
    latest = (
        minute_bars.sort_values("datetime")
        .groupby("symbol", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )
    return {str(row["symbol"]): float(row["close"]) for row in latest.to_dict(orient="records")}


def _name_for_symbol(symbol: str, sample_dir: Path) -> str:
    for holding in load_holdings_csv(sample_dir / "holdings.csv"):
        if holding.symbol == symbol:
            return holding.name
    return symbol


def _format_money(value: float) -> str:
    return f"{value:.2f}"


def _format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _format_optional_pct(value: object) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return _format_pct(float(cast(Any, value)))


def _format_optional_number(value: object) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(cast(Any, value)):.2f}"
