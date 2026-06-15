from dataclasses import dataclass
from typing import Literal

import pandas as pd


RecommendedPool = Literal["tradable", "watch", "blocked"]

DEFAULT_REQUIRED_COLUMNS: frozenset[str] = frozenset({"trade_date", "symbol", "close"})


@dataclass(frozen=True)
class DataQualityResult:
    passed: bool
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    recommended_pool: RecommendedPool = "tradable"


def validate_market_data(
    frame: pd.DataFrame,
    *,
    required_columns: set[str] | None = None,
) -> DataQualityResult:
    required = DEFAULT_REQUIRED_COLUMNS if required_columns is None else frozenset(required_columns)
    available_columns = {str(column) for column in frame.columns}
    missing_columns = tuple(sorted(required.difference(available_columns)))
    if missing_columns:
        return DataQualityResult(
            passed=False,
            errors=(f"missing required columns: {', '.join(missing_columns)}",),
            recommended_pool="blocked",
        )

    warnings: list[str] = []
    if frame.duplicated(subset=["symbol", "trade_date"]).any():
        warnings.append("duplicate symbol/trade_date rows detected")

    return DataQualityResult(passed=True, warnings=tuple(warnings))
