from collections.abc import Iterable, Mapping
from dataclasses import dataclass

import pandas as pd

from trading_assistant.domain.enums import PoolType


@dataclass(frozen=True)
class PoolClassification:
    symbol: str
    pool_type: PoolType
    reason: str


@dataclass(frozen=True)
class PoolClassificationConfig:
    exclude_st: bool = True
    exclude_delisting_risk: bool = True
    min_daily_turnover_cny: float = 100_000_000
    min_listing_days: int = 60
    exclude_limit_down_days: int = 2
    exclude_one_word_limit_up: bool = True
    watch_boards: frozenset[str] = frozenset({"北交所"})
    tradable_boards: frozenset[str] | None = None


def _float_config_value(value: object) -> float:
    if isinstance(value, str | int | float):
        return float(value)
    msg = f"pool config value must be numeric, got {type(value).__name__}"
    raise TypeError(msg)


def _int_config_value(value: object) -> int:
    if isinstance(value, str | int):
        return int(value)
    msg = f"pool config value must be an integer, got {type(value).__name__}"
    raise TypeError(msg)


def _string_set(value: object, default: frozenset[str]) -> frozenset[str]:
    if value is None:
        return default
    if isinstance(value, str):
        return frozenset({value})
    if isinstance(value, Iterable):
        return frozenset(str(item) for item in value)
    return frozenset({str(value)})


def _optional_string_set(value: object) -> frozenset[str] | None:
    if value is None:
        return None
    return _string_set(value, frozenset())


def _resolve_config(
    config: Mapping[str, object] | PoolClassificationConfig | None,
) -> PoolClassificationConfig:
    if isinstance(config, PoolClassificationConfig):
        return config
    if config is None:
        return PoolClassificationConfig()
    return PoolClassificationConfig(
        exclude_st=bool(config.get("exclude_st", True)),
        exclude_delisting_risk=bool(config.get("exclude_delisting_risk", True)),
        min_daily_turnover_cny=_float_config_value(
            config.get("min_daily_turnover_cny", 100_000_000)
        ),
        min_listing_days=_int_config_value(config.get("min_listing_days", 60)),
        exclude_limit_down_days=_int_config_value(config.get("exclude_limit_down_days", 2)),
        exclude_one_word_limit_up=bool(config.get("exclude_one_word_limit_up", True)),
        watch_boards=_string_set(config.get("watch_boards"), frozenset({"北交所"})),
        tradable_boards=_optional_string_set(config.get("tradable_boards")),
    )


def _holding_symbol_set(holding_symbols: Iterable[str] | str | None) -> frozenset[str]:
    if holding_symbols is None:
        return frozenset()
    if isinstance(holding_symbols, str):
        return frozenset({holding_symbols})
    return frozenset(str(symbol) for symbol in holding_symbols)


def classify_stock_pool(
    stock: pd.Series,
    *,
    config: Mapping[str, object] | PoolClassificationConfig | None = None,
    holding_symbols: Iterable[str] | str | None = None,
) -> PoolClassification:
    rules = _resolve_config(config)
    symbol = str(stock["symbol"])
    if symbol in _holding_symbol_set(holding_symbols):
        return PoolClassification(symbol, PoolType.HOLDING, "当前持仓优先纳入持仓池")
    if rules.exclude_st and bool(stock.get("is_st", False)):
        return PoolClassification(symbol, PoolType.BLOCKED, "ST 股票禁入")
    if rules.exclude_delisting_risk and bool(stock.get("has_delisting_risk", False)):
        return PoolClassification(symbol, PoolType.BLOCKED, "存在退市风险")
    if float(stock.get("daily_turnover", 0)) < rules.min_daily_turnover_cny:
        reason = f"成交额低于 {rules.min_daily_turnover_cny:,.0f} 元"
        return PoolClassification(symbol, PoolType.BLOCKED, reason)
    if int(stock.get("listing_days", 0)) < rules.min_listing_days:
        return PoolClassification(symbol, PoolType.WATCH, f"上市不足 {rules.min_listing_days} 天")
    if rules.exclude_one_word_limit_up and bool(stock.get("one_word_limit_up", False)):
        return PoolClassification(symbol, PoolType.WATCH, "连续一字板不追")
    if int(stock.get("limit_down_days", 0)) >= rules.exclude_limit_down_days:
        return PoolClassification(symbol, PoolType.BLOCKED, "连续跌停风险")
    board = str(stock.get("board", ""))
    if board in rules.watch_boards:
        return PoolClassification(symbol, PoolType.WATCH, "高波动板块先观察")
    if rules.tradable_boards is not None and board not in rules.tradable_boards:
        return PoolClassification(symbol, PoolType.WATCH, "未纳入可交易板块配置")
    return PoolClassification(symbol, PoolType.TRADABLE, "满足可交易池基础条件")
