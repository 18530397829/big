from pathlib import Path

import pytest

from trading_assistant.pools.focus_pool import (
    FocusPoolImportError,
    FocusStockStatus,
    load_focus_pool_csv,
    normalize_symbol,
    parse_focus_pool_csv_text,
)


def test_normalize_symbol_accepts_common_a_share_formats() -> None:
    assert normalize_symbol("000001") == "000001"
    assert normalize_symbol("000001.SZ") == "000001"
    assert normalize_symbol("SZ000001") == "000001"
    assert normalize_symbol("sh600519") == "600519"


def test_parse_focus_pool_csv_supports_optional_name_and_standard_fields() -> None:
    csv_text = "\n".join(
        [
            "symbol,name,focus_reason,tags,priority,status",
            "000001.SZ,平安银行,银行主线,银行|低估,5,active",
            "SZ300001,,AI 观察,,2,paused",
        ]
    )

    rows = parse_focus_pool_csv_text(csv_text)

    assert rows[0].symbol == "000001"
    assert rows[0].name == "平安银行"
    assert rows[0].focus_reason == "银行主线"
    assert rows[0].tags == ("银行", "低估")
    assert rows[0].priority == 5
    assert rows[0].status == FocusStockStatus.ACTIVE
    assert rows[1].symbol == "300001"
    assert rows[1].name is None
    assert rows[1].tags == ()
    assert rows[1].status == FocusStockStatus.PAUSED


def test_load_focus_pool_csv_requires_symbol_column(tmp_path: Path) -> None:
    path = tmp_path / "focus_pool.csv"
    path.write_text("name\n平安银行\n", encoding="utf-8")

    with pytest.raises(FocusPoolImportError, match="missing columns: \\['symbol'\\]"):
        load_focus_pool_csv(path)


def test_parse_focus_pool_csv_rejects_duplicate_symbols() -> None:
    csv_text = "\n".join(
        [
            "symbol,name",
            "000001,平安银行",
            "SZ000001,平安银行更新",
        ]
    )

    with pytest.raises(FocusPoolImportError, match="duplicate symbol: 000001"):
        parse_focus_pool_csv_text(csv_text)


@pytest.mark.parametrize(
    ("csv_text", "message"),
    [
        ("symbol,priority\n000001,6\n", "priority must be between 1 and 5"),
        ("symbol,status\n000001,watching\n", "status must be active, paused, or archived"),
        ("symbol,name\nABCDEF,错误\n", "symbol must contain exactly 6 digits"),
    ],
)
def test_parse_focus_pool_csv_rejects_invalid_rows(csv_text: str, message: str) -> None:
    with pytest.raises(FocusPoolImportError, match=message):
        parse_focus_pool_csv_text(csv_text)
