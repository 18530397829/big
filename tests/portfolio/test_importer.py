from pathlib import Path
import subprocess
import sys

from trading_assistant.portfolio.importer import load_holdings_csv


def test_load_holdings_csv_parses_holdings():
    path = Path("data/samples/holdings.csv")

    holdings = load_holdings_csv(path)

    assert len(holdings) == 2
    assert holdings[0].symbol == "000001"
    assert holdings[0].unrealized_return_pct == 0.03


def test_import_holdings_script_runs_from_repo_root():
    result = subprocess.run(
        [sys.executable, "scripts/import_holdings.py"],
        capture_output=True,
        check=True,
        text=True,
    )

    assert "000001 平安银行 10300.00" in result.stdout
