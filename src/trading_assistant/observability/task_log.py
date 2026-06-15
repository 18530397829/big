from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class TaskRunLog:
    task_name: str
    trade_date: str
    started_at: datetime
    finished_at: datetime
    input_count: int
    output_count: int
    status: str
    error_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["started_at"] = self.started_at.isoformat()
        data["finished_at"] = self.finished_at.isoformat()
        return data


def build_task_log(
    *,
    task_name: str,
    trade_date: str,
    started_at: datetime,
    finished_at: datetime,
    input_count: int = 0,
    output_count: int = 0,
    status: str = "scheduled",
    error_reason: str | None = None,
) -> TaskRunLog:
    return TaskRunLog(
        task_name=task_name,
        trade_date=trade_date,
        started_at=started_at,
        finished_at=finished_at,
        input_count=input_count,
        output_count=output_count,
        status=status,
        error_reason=error_reason,
    )
