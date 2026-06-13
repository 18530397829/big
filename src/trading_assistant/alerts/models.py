from dataclasses import dataclass
from enum import StrEnum


class AlertLevel(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


@dataclass(frozen=True)
class Alert:
    level: AlertLevel
    symbol: str
    message: str
