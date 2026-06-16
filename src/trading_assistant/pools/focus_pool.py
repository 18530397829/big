from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO
from pathlib import Path
import re


class FocusPoolImportError(ValueError):
    pass


class FocusStockStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class FocusStockImportRow:
    symbol: str
    name: str | None = None
    focus_reason: str = ""
    tags: tuple[str, ...] = ()
    priority: int = 3
    status: FocusStockStatus = FocusStockStatus.ACTIVE


def normalize_symbol(value: object) -> str:
    raw = str(value).strip().upper()
    if raw.endswith((".SZ", ".SH", ".BJ")):
        raw = raw[:6]
    if raw.startswith(("SZ", "SH", "BJ")):
        raw = raw[2:]
    if not re.fullmatch(r"\d{6}", raw):
        raise FocusPoolImportError("symbol must contain exactly 6 digits")
    return raw


def load_focus_pool_csv(path: Path) -> list[FocusStockImportRow]:
    return parse_focus_pool_csv_text(path.read_text(encoding="utf-8-sig"))


def parse_focus_pool_csv_text(text: str) -> list[FocusStockImportRow]:
    reader = csv.DictReader(StringIO(text))
    fieldnames = set(reader.fieldnames or [])
    missing = sorted({"symbol"} - fieldnames)
    if missing:
        raise FocusPoolImportError(f"focus pool csv missing columns: {missing}")

    rows: list[FocusStockImportRow] = []
    seen_symbols: set[str] = set()
    for line_number, raw_row in enumerate(reader, start=2):
        try:
            row = _parse_row(raw_row)
        except FocusPoolImportError as exc:
            raise FocusPoolImportError(f"line {line_number}: {exc}") from exc
        if row.symbol in seen_symbols:
            raise FocusPoolImportError(f"line {line_number}: duplicate symbol: {row.symbol}")
        seen_symbols.add(row.symbol)
        rows.append(row)
    return rows


def _parse_row(raw_row: dict[str, str | None]) -> FocusStockImportRow:
    symbol = normalize_symbol(raw_row.get("symbol", ""))
    return FocusStockImportRow(
        symbol=symbol,
        name=_optional_text(raw_row.get("name")),
        focus_reason=_optional_text(raw_row.get("focus_reason")) or "",
        tags=_parse_tags(raw_row.get("tags")),
        priority=_parse_priority(raw_row.get("priority")),
        status=_parse_status(raw_row.get("status")),
    )


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_tags(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(tag.strip() for tag in value.split("|") if tag.strip())


def _parse_priority(value: str | None) -> int:
    if value is None or not value.strip():
        return 3
    try:
        priority = int(value)
    except ValueError as exc:
        raise FocusPoolImportError("priority must be an integer") from exc
    if priority < 1 or priority > 5:
        raise FocusPoolImportError("priority must be between 1 and 5")
    return priority


def _parse_status(value: str | None) -> FocusStockStatus:
    if value is None or not value.strip():
        return FocusStockStatus.ACTIVE
    try:
        return FocusStockStatus(value.strip().lower())
    except ValueError as exc:
        raise FocusPoolImportError("status must be active, paused, or archived") from exc
