import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pandas as pd

from trading_assistant.backtest.engine import evaluate_forward_returns
from trading_assistant.backtest.metrics import summarize_returns
from trading_assistant.domain.enums import ActionAdvice, RiskLevel
from trading_assistant.domain.models import Holding
from trading_assistant.planning.candidate_selector import CandidateGroups, select_candidate_groups
from trading_assistant.pools.focus_pool import (
    FocusStockImportRow,
    FocusStockStatus,
    load_focus_pool_csv,
)
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
RISK_LEVEL_KEYS = {
    RiskLevel.LOW: "low",
    RiskLevel.MEDIUM: "medium",
    RiskLevel.HIGH: "high",
    RiskLevel.CRITICAL: "critical",
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
MarketView = dict[str, Any]
FocusPoolView = dict[str, Any]


def build_dashboard_view(
    sample_dir: Path | None = None,
    focus_stocks: Sequence[FocusStockImportRow] | None = None,
) -> DashboardView:
    holdings_view = build_holdings_view(sample_dir)
    candidates_view = build_candidates_view(sample_dir, focus_stocks=focus_stocks)
    backtest_view = build_backtest_view(sample_dir)
    intraday_view = build_intraday_monitor_view(sample_dir, focus_stocks=focus_stocks)
    market_view = build_market_view(sample_dir)
    focus_pool_view = build_focus_pool_view(sample_dir, focus_stocks=focus_stocks)
    market_score = market_view["summary"]["market_score"]

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
            "href": "/holdings",
            "status": holdings_view["summary"]["max_risk_level"],
            "status_key": holdings_view["summary"]["max_risk_level_key"],
            "action": "查看持仓",
            "is_available": True,
            "data_freshness": holdings_view["summary"]["data_freshness"],
        },
        {
            "title": "市场环境",
            "summary": f"样例板块平均涨幅 {_average_sector_pct(sample_dir):.2f}%，环境分 {market_score}",
            "href": "/market",
            "status": str(market_score),
            "status_key": _score_tone(float(market_score), positive_threshold=60.0),
            "action": "查看市场",
            "is_available": True,
            "data_freshness": market_view["summary"]["data_freshness"],
        },
        {
            "title": "重点候选",
            "summary": (
                f"{candidates_view['candidate_count']} 只候选，"
                f"{candidates_view['outside_observation_count']} 只池外观察，首选 {top_candidate}"
            ),
            "href": "/candidates",
            "status": f"{candidates_view['candidate_count']} 只",
            "status_key": "info" if candidates_view["candidate_count"] else "neutral",
            "action": "查看候选",
            "is_available": True,
            "data_freshness": candidates_view["data_freshness"],
        },
        {
            "title": "盘中提醒",
            "summary": (
                f"{intraday_view['watch_items']} 个监控项，"
                f"{intraday_view['critical_label']}"
            ),
            "href": "/intraday",
            "status": f"{intraday_view['critical_alerts']} 条",
            "status_key": "critical" if intraday_view["critical_alerts"] else "low",
            "action": "查看提醒",
            "is_available": True,
            "data_freshness": intraday_view["data_freshness"],
        },
        {
            "title": "回测复盘",
            "summary": (
                f"1日胜率 {backtest_view['summary']['win_rate_1d']}，"
                f"平均收益 {backtest_view['summary']['avg_return_1d']}，"
                f"最大回撤 {backtest_view['summary']['max_drawdown_1d']}"
            ),
            "href": "/backtest",
            "status": f"{backtest_view['summary']['signal_count']} 条",
            "status_key": "info" if backtest_view["summary"]["signal_count"] else "neutral",
            "action": "查看回测",
            "is_available": True,
            "data_freshness": backtest_view["summary"]["data_freshness"],
        },
        {
            "title": "关注股票池",
            "summary": (
                f"{focus_pool_view['summary']['active_count']} 只启用，"
                f"{focus_pool_view['summary']['total_count']} 只总关注"
            ),
            "href": "/focus-pool",
            "status": f"{focus_pool_view['summary']['active_count']} 只",
            "status_key": "info" if focus_pool_view["summary"]["active_count"] else "neutral",
            "action": "查看股票池",
            "is_available": True,
            "data_freshness": "样例数据 / 关注池",
        },
    ]

    return {
        "market_score": market_score,
        "portfolio_risk": holdings_view["summary"]["max_risk_level"],
        "portfolio_risk_key": holdings_view["summary"]["max_risk_level_key"],
        "holding_count": holdings_view["summary"]["holding_count"],
        "focus_pool_count": focus_pool_view["summary"]["active_count"],
        "total_market_value": holdings_view["summary"]["total_market_value"],
        "candidate_count": candidates_view["candidate_count"],
        "critical_alerts": intraday_view["critical_alerts"],
        "critical_alert_label": intraday_view["critical_label"],
        "intraday_priority_label": intraday_view["priority_label"],
        "watch_items": intraday_view["watch_items"],
        "top_candidate": top_candidate,
        "page_generated_at": f"页面生成时间 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "sections": sections,
    }


def build_market_view(sample_dir: Path | None = None) -> MarketView:
    sample_path = _resolve_sample_dir(sample_dir)
    sectors = _load_sectors(sample_path)
    market_score = _market_score(sectors)
    rows = []
    for row in sectors.to_dict(orient="records"):
        pct_chg = float(row["pct_chg"])
        rows.append(
            {
                "sector_name": str(row["sector_name"]),
                "sector_type": str(row["sector_type"]),
                "pct_chg": _format_pct_points(pct_chg),
                "pct_tone": _tone_for_signed(pct_chg),
                "turnover": _format_money(float(row["turnover"])),
                "limit_up_count": int(row["limit_up_count"]),
                "leader_symbol": str(row["leader_symbol"]),
            }
        )
    return {
        "summary": {
            "market_score": market_score,
            "market_score_key": _score_tone(float(market_score), positive_threshold=60.0),
            "average_sector_pct": _format_pct_points(_average_sector_pct(sample_dir)),
            "sector_count": len(rows),
            "data_freshness": _latest_sector_freshness(sample_path),
        },
        "sectors": rows,
    }


def build_focus_pool_view(
    sample_dir: Path | None = None,
    focus_stocks: Sequence[FocusStockImportRow] | None = None,
    *,
    import_result: str | None = None,
    import_error: str | None = None,
) -> FocusPoolView:
    sample_path = _resolve_sample_dir(sample_dir)
    focus_rows = _resolve_focus_stocks(sample_path, focus_stocks)
    rows = [_focus_stock_row(item) for item in focus_rows]
    rows.sort(key=lambda row: (_status_sort_key(row["status"]), -int(row["priority"]), row["symbol"]))
    return {
        "summary": {
            "total_count": len(rows),
            "active_count": sum(1 for row in rows if row["status"] == "active"),
            "paused_count": sum(1 for row in rows if row["status"] == "paused"),
            "archived_count": sum(1 for row in rows if row["status"] == "archived"),
        },
        "focus_stocks": rows,
        "import_result": import_result,
        "import_error": import_error,
    }


def build_holdings_view(sample_dir: Path | None = None) -> HoldingsView:
    sample_path = _resolve_sample_dir(sample_dir)
    holdings = load_holdings_csv(sample_path / "holdings.csv")
    decisions = _risk_decisions(holdings, sample_path)
    total_market_value = sum(holding.market_value for holding in holdings)
    max_risk_level = _max_risk_level(decisions)

    rows: list[dict[str, Any]] = []
    for holding, decision in zip(holdings, decisions, strict=True):
        rows.append(
            {
                "symbol": holding.symbol,
                "name": holding.name,
                "identity": _identity(holding.symbol, holding.name),
                "quantity": holding.quantity,
                "market_value": _format_money(holding.market_value),
                "unrealized_return_pct": _format_pct(holding.unrealized_return_pct),
                "return_tone": _tone_for_signed(holding.unrealized_return_pct),
                "risk_level": RISK_LABELS[decision.risk_level],
                "risk_level_key": RISK_LEVEL_KEYS[decision.risk_level],
                "risk_sort_key": RISK_PRIORITY[decision.risk_level],
                "action_advice": ACTION_LABELS[decision.action_advice],
                "reasons": "、".join(decision.reasons),
                "row_id": _row_id("holding", holding.symbol),
                "_original_order": len(rows),
            }
        )
    rows.sort(key=lambda row: (-int(cast(Any, row["risk_sort_key"])), int(cast(Any, row["_original_order"]))))
    for row in rows:
        row.pop("_original_order", None)

    return {
        "summary": {
            "holding_count": len(holdings),
            "total_market_value": _format_money(total_market_value),
            "max_risk_level": RISK_LABELS[max_risk_level],
            "max_risk_level_key": RISK_LEVEL_KEYS[max_risk_level],
            "data_freshness": _latest_minute_freshness(sample_path),
        },
        "holdings": rows,
    }


def build_candidates_view(
    sample_dir: Path | None = None,
    focus_stocks: Sequence[FocusStockImportRow] | None = None,
) -> CandidatesView:
    sample_path = _resolve_sample_dir(sample_dir)
    focus_rows = _resolve_focus_stocks(sample_path, focus_stocks)
    groups = _select_sample_candidate_groups(sample_path, focus_rows)
    selected = groups.primary
    holding_symbols = {holding.symbol for holding in load_holdings_csv(sample_path / "holdings.csv")}
    signal_symbols = _candidate_signal_symbols(selected, sample_path)
    rows = _candidate_rows(
        selected,
        holding_symbols=holding_symbols,
        signal_symbols=signal_symbols,
        pool_scope_label="关注池",
    )
    outside_rows = _candidate_rows(
        groups.outside_observation,
        holding_symbols=holding_symbols,
        signal_symbols=set(),
        pool_scope_label="池外观察",
    )
    return {
        "candidate_count": len(rows),
        "outside_observation_count": len(outside_rows),
        "data_freshness": _latest_daily_freshness(sample_path),
        "candidates": rows,
        "outside_observations": outside_rows,
    }


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
    has_enough_metrics = not pd.isna(summary["win_rate_1d"])
    available_return_1d_count = _available_metric_count(evaluated, "return_1d")
    rows = []
    name_by_symbol = {
        str(row["symbol"]): str(row["name"]) for row in selected.to_dict(orient="records")
    }
    for row in evaluated.to_dict(orient="records"):
        return_1d = row.get("return_1d")
        max_return_5d = row.get("max_return_5d")
        rows.append(
            {
                "symbol": row["symbol"],
                "name": name_by_symbol.get(str(row["symbol"]), ""),
                "identity": _identity(row["symbol"], name_by_symbol.get(str(row["symbol"]), "")),
                "trade_date": str(pd.to_datetime(row["trade_date"]).date()),
                "score": f"{float(row['score']):.2f}",
                "return_1d": _format_optional_pct(return_1d),
                "return_1d_tone": _optional_tone_for_signed(return_1d),
                "max_return_5d": _format_optional_pct(max_return_5d),
                "max_return_5d_tone": _optional_tone_for_signed(max_return_5d),
                "row_id": _row_id("signal", row["symbol"]),
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
            "data_freshness": _signal_freshness(rows),
            "has_enough_metrics": has_enough_metrics,
            "insufficient_metrics_message": _insufficient_metrics_message(
                signal_count=len(rows),
                available_return_1d_count=available_return_1d_count,
            ),
        },
        "signals": rows,
    }


def build_intraday_monitor_view(
    sample_dir: Path | None = None,
    focus_stocks: Sequence[FocusStockImportRow] | None = None,
) -> IntradayMonitorView:
    sample_path = _resolve_sample_dir(sample_dir)
    holdings = load_holdings_csv(sample_path / "holdings.csv")
    latest_prices = _latest_minute_prices(_load_minute_bars(sample_path))
    latest_daily_prices = _latest_daily_prices(_load_daily_bars(sample_path))
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
                "identity": _identity(holding.symbol, holding.name),
                "latest_price": _format_money(latest_price),
                "change_pct": _format_pct(change),
                "change_tone": _tone_for_signed(change),
                "priority": priority,
                "priority_key": "critical" if priority == "P1" else "medium",
            }
        )

    holding_symbols = {holding.symbol for holding in holdings}
    focus_rows = _resolve_focus_stocks(sample_path, focus_stocks)
    for focus_stock in focus_rows:
        if focus_stock.status != FocusStockStatus.ACTIVE or focus_stock.symbol in holding_symbols:
            continue
        focus_latest_price = latest_prices.get(
            focus_stock.symbol,
            latest_daily_prices.get(focus_stock.symbol),
        )
        if focus_latest_price is None:
            continue
        base_price = latest_daily_prices.get(focus_stock.symbol, focus_latest_price)
        change = (focus_latest_price - base_price) / base_price if base_price else 0.0
        items.append(
            {
                "symbol": focus_stock.symbol,
                "name": focus_stock.name or focus_stock.symbol,
                "identity": _identity(focus_stock.symbol, focus_stock.name or focus_stock.symbol),
                "latest_price": _format_money(focus_latest_price),
                "change_pct": _format_pct(change),
                "change_tone": _tone_for_signed(change),
                "priority": "P2",
                "priority_key": "medium",
            }
        )

    return {
        "watch_items": len(items),
        "critical_alerts": critical_alerts,
        "priority_label": "P1 提醒",
        "critical_label": f"P1 {critical_alerts} 条",
        "data_freshness": _latest_minute_freshness(sample_path),
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


def _resolve_focus_stocks(
    sample_dir: Path,
    focus_stocks: Sequence[FocusStockImportRow] | None,
) -> list[FocusStockImportRow]:
    if focus_stocks is not None:
        return list(focus_stocks)
    path = sample_dir / "focus_pool.csv"
    if not path.exists():
        return []
    return load_focus_pool_csv(path)


def _active_focus_priorities(focus_stocks: Sequence[FocusStockImportRow]) -> dict[str, int]:
    return {
        item.symbol: item.priority
        for item in focus_stocks
        if item.status == FocusStockStatus.ACTIVE
    }


def _inactive_focus_symbols(focus_stocks: Sequence[FocusStockImportRow]) -> set[str]:
    return {
        item.symbol
        for item in focus_stocks
        if item.status in {FocusStockStatus.PAUSED, FocusStockStatus.ARCHIVED}
    }


def _focus_stock_row(item: FocusStockImportRow) -> dict[str, Any]:
    tags = list(item.tags)
    status_label, status_key = _focus_status_display(item.status)
    return {
        "symbol": item.symbol,
        "name": item.name,
        "display_name": item.name or item.symbol,
        "focus_reason": item.focus_reason,
        "tags": tags,
        "tags_label": "、".join(tags) if tags else "未分组",
        "priority": item.priority,
        "status": item.status.value,
        "status_label": status_label,
        "status_key": status_key,
    }


def _focus_status_display(status: FocusStockStatus) -> tuple[str, str]:
    return {
        FocusStockStatus.ACTIVE: ("启用", "positive"),
        FocusStockStatus.PAUSED: ("暂停", "warning"),
        FocusStockStatus.ARCHIVED: ("归档", "neutral"),
    }[status]


def _status_sort_key(status: object) -> int:
    return {"active": 0, "paused": 1, "archived": 2}.get(str(status), 3)


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
    return _select_sample_candidate_groups(
        sample_dir,
        _resolve_focus_stocks(sample_dir, None),
    ).primary


def _select_sample_candidate_groups(
    sample_dir: Path,
    focus_stocks: Sequence[FocusStockImportRow],
) -> CandidateGroups:
    scored = _sample_scored_stocks(sample_dir)
    holdings = load_holdings_csv(sample_dir / "holdings.csv")
    return select_candidate_groups(
        scored,
        active_focus_priorities=_active_focus_priorities(focus_stocks),
        holding_symbols={holding.symbol for holding in holdings},
        inactive_focus_symbols=_inactive_focus_symbols(focus_stocks),
        min_opportunity_score=76,
        min_plan_confidence_score=70,
        limit=5,
        outside_limit=8,
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
                "event_sentiment": sentiment_by_symbol.get(symbol, "none"),
                "reasons": (
                    f"{sector['sector_name']}板块涨幅 {sector_pct:.2f}%；"
                    f"日线涨幅 {daily_return_pct:.2f}%；"
                    f"{_event_label(sentiment_by_symbol.get(symbol, 'none'))}"
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


def _latest_daily_prices(daily_bars: pd.DataFrame) -> dict[str, float]:
    latest = (
        daily_bars.sort_values("trade_date")
        .groupby("symbol", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )
    return {str(row["symbol"]): float(row["close"]) for row in latest.to_dict(orient="records")}


def _name_for_symbol(symbol: str, sample_dir: Path) -> str:
    for focus_stock in _resolve_focus_stocks(sample_dir, None):
        if focus_stock.symbol == symbol and focus_stock.name:
            return focus_stock.name
    for holding in load_holdings_csv(sample_dir / "holdings.csv"):
        if holding.symbol == symbol:
            return holding.name
    return symbol


def _format_money(value: float) -> str:
    return f"{value:.2f}"


def _format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _format_pct_points(value: float) -> str:
    return f"{value:.2f}%"


def _format_optional_pct(value: object) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return _format_pct(float(cast(Any, value)))


def _format_optional_number(value: object) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(cast(Any, value)):.2f}"


def _row_id(prefix: str, symbol: object) -> str:
    return f"{prefix}-{str(symbol)}"


def _identity(symbol: object, name: object) -> str:
    return f"{symbol} {name}".strip()


def _tone_for_signed(value: float) -> str:
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "neutral"


def _optional_tone_for_signed(value: object) -> str:
    if value is None or pd.isna(value):
        return "neutral"
    return _tone_for_signed(float(cast(Any, value)))


def _score_tone(value: float, *, positive_threshold: float = 75.0) -> str:
    if value >= positive_threshold:
        return "positive"
    if value < 60:
        return "danger"
    return "neutral"


def _split_reasons(reasons: str) -> list[str]:
    return [reason.strip() for reason in reasons.split("；") if reason.strip()]


def _event_label(sentiment: str) -> str:
    return {
        "positive": "正面事件",
        "negative": "负面事件",
        "neutral": "中性事件",
        "uncertain": "事件待确认",
        "none": "暂无事件",
    }.get(sentiment, "暂无事件")


def _candidate_signal_symbols(selected: pd.DataFrame, sample_path: Path) -> set[str]:
    if selected.empty:
        return set()
    signals = _candidate_signals(selected, _load_daily_bars(sample_path))
    if signals.empty or "symbol" not in signals:
        return set()
    return {str(symbol) for symbol in signals["symbol"].to_list()}


def _candidate_rows(
    selected: pd.DataFrame,
    *,
    holding_symbols: set[str],
    signal_symbols: set[str],
    pool_scope_label: str,
) -> list[dict[str, Any]]:
    rows = []
    for candidate in selected.to_dict(orient="records"):
        symbol = str(candidate["symbol"])
        opportunity_score = float(candidate["opportunity_score"])
        confidence_score = float(candidate["plan_confidence_score"])
        reason_items = _split_reasons(str(candidate["reasons"]))
        rows.append(
            {
                "symbol": symbol,
                "name": candidate["name"],
                "opportunity_score": f"{opportunity_score:.2f}",
                "score_tone": _score_tone(opportunity_score),
                "plan_confidence_score": f"{confidence_score:.2f}",
                "confidence_tone": _score_tone(confidence_score),
                "reasons": candidate["reasons"],
                "reason_items": reason_items,
                "summary_reason": reason_items[0] if reason_items else "暂无触发条件",
                "event_label": _event_label(str(candidate.get("event_sentiment", "none"))),
                "pool_scope_label": pool_scope_label,
                "detail_id": _row_id("candidate", symbol),
                "holding_href": f"/holdings#{_row_id('holding', symbol)}"
                if symbol in holding_symbols
                else None,
                "backtest_href": f"/backtest#{_row_id('signal', symbol)}"
                if symbol in signal_symbols
                else None,
            }
        )
    return rows


def _latest_minute_freshness(sample_path: Path) -> str:
    minutes = _load_minute_bars(sample_path)
    if minutes.empty:
        return "样例数据 / 暂无分钟数据"
    latest = pd.to_datetime(minutes["datetime"]).max()
    return f"样例数据 / 最近更新 {latest.strftime('%Y-%m-%d %H:%M')}"


def _latest_daily_freshness(sample_path: Path) -> str:
    daily = _load_daily_bars(sample_path)
    if daily.empty:
        return "样例数据 / 暂无交易日"
    latest = pd.to_datetime(daily["trade_date"]).max()
    return f"样例数据 / 最近交易日 {latest.strftime('%Y-%m-%d')}"


def _latest_sector_freshness(sample_path: Path) -> str:
    sectors = _load_sectors(sample_path)
    if sectors.empty:
        return "样例数据 / 暂无板块交易日"
    latest = pd.to_datetime(sectors["trade_date"]).max()
    return f"样例数据 / 最近板块交易日 {latest.strftime('%Y-%m-%d')}"


def _signal_freshness(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "样例数据 / 暂无信号"
    latest = max(str(row["trade_date"]) for row in rows)
    return f"样例数据 / 最近信号 {latest}"


def _available_metric_count(evaluated: pd.DataFrame, column: str) -> int:
    if column not in evaluated:
        return 0
    return int(pd.to_numeric(evaluated[column], errors="coerce").dropna().shape[0])


def _insufficient_metrics_message(
    *,
    signal_count: int,
    available_return_1d_count: int,
) -> str:
    return (
        f"当前 {signal_count} 条信号，1 日后续收益可用 {available_return_1d_count} 条；"
        "至少需要 1 条带后续收益的信号完成基础胜率统计。"
        "正式复盘建议覆盖 60 个交易日历史样本。"
    )
