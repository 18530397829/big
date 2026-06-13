from pathlib import Path


def test_ops_runbook_exists_and_mentions_core_workflows():
    text = Path("docs/ops-runbook.md").read_text(encoding="utf-8")

    assert "盘后任务" in text
    assert "盘中提醒" in text
    assert "数据源失败" in text
    assert "备份" in text
