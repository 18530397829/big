from dataclasses import dataclass

import pandas as pd

from trading_assistant.domain.enums import PoolType


@dataclass(frozen=True)
class PoolClassification:
    symbol: str
    pool_type: PoolType
    reason: str


def classify_stock_pool(stock: pd.Series) -> PoolClassification:
    symbol = str(stock["symbol"])
    if bool(stock.get("is_st", False)):
        return PoolClassification(symbol, PoolType.BLOCKED, "ST 股票禁入")
    if bool(stock.get("has_delisting_risk", False)):
        return PoolClassification(symbol, PoolType.BLOCKED, "存在退市风险")
    if float(stock.get("daily_turnover", 0)) < 100_000_000:
        return PoolClassification(symbol, PoolType.BLOCKED, "成交额低于 1 亿元")
    if int(stock.get("listing_days", 0)) < 60:
        return PoolClassification(symbol, PoolType.WATCH, "上市不足 60 天")
    if bool(stock.get("one_word_limit_up", False)):
        return PoolClassification(symbol, PoolType.WATCH, "连续一字板不追")
    if int(stock.get("limit_down_days", 0)) >= 2:
        return PoolClassification(symbol, PoolType.BLOCKED, "连续跌停风险")
    if stock.get("board") in {"北交所"}:
        return PoolClassification(symbol, PoolType.WATCH, "高波动板块先观察")
    return PoolClassification(symbol, PoolType.TRADABLE, "满足可交易池基础条件")
