from datetime import UTC, date, datetime

from pydantic import BaseModel, Field, model_validator

from trading_assistant.domain.enums import ActionAdvice, PoolType, RiskLevel


class Holding(BaseModel):
    symbol: str
    name: str
    quantity: int = Field(gt=0)
    cost_price: float = Field(gt=0)
    current_price: float = Field(gt=0)
    buy_date: date
    theme: str
    buy_reason: str

    @property
    def market_value(self) -> float:
        return round(self.quantity * self.current_price, 2)

    @property
    def unrealized_return_pct(self) -> float:
        return round((self.current_price - self.cost_price) / self.cost_price, 4)


class ScoreBreakdown(BaseModel):
    total_score: float = Field(ge=0, le=100)
    components: dict[str, float]
    reasons: list[str]


class TradePlan(BaseModel):
    symbol: str
    name: str
    pool_type: PoolType
    opportunity_score: float = Field(ge=0, le=100)
    plan_confidence_score: float = Field(ge=0, le=100)
    entry_trigger: str
    entry_price_low: float = Field(gt=0)
    entry_price_high: float = Field(gt=0)
    stop_loss_price: float = Field(gt=0)
    first_take_profit_price: float = Field(gt=0)
    second_take_profit_price: float = Field(gt=0)
    position_pct: float = Field(ge=0, le=1)
    invalidation_condition: str
    risk_level: RiskLevel
    action_advice: ActionAdvice
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_price_relationships(self) -> "TradePlan":
        if self.entry_price_high < self.entry_price_low:
            msg = "entry_price_high must be greater than or equal to entry_price_low"
            raise ValueError(msg)
        if self.stop_loss_price >= self.entry_price_low:
            msg = "stop_loss_price must be less than entry_price_low"
            raise ValueError(msg)
        if self.first_take_profit_price <= self.entry_price_high:
            msg = "first_take_profit_price must be greater than entry_price_high"
            raise ValueError(msg)
        if self.second_take_profit_price < self.first_take_profit_price:
            msg = (
                "second_take_profit_price must be greater than or equal to "
                "first_take_profit_price"
            )
            raise ValueError(msg)
        return self

    @property
    def reward_risk_ratio(self) -> float:
        planned_entry = self.entry_price_low
        risk = planned_entry - self.stop_loss_price
        reward = self.first_take_profit_price - planned_entry
        if risk <= 0:
            return 0.0
        return round(reward / risk, 2)
