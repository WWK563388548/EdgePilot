from datetime import date

from pydantic import BaseModel, Field


class AnalyticsStrategyBreakdown(BaseModel):
    strategy_name: str
    trades_count: int
    realized_pnl: float
    win_rate: float | None = None
    profit_factor: float | None = None
    average_r: float | None = None


class AnalyticsExecutionQuality(BaseModel):
    fills_count: int
    matched_fills_count: int
    review_needed_fills_count: int
    planned_entry_count: int
    average_entry_drag_r: float | None = None
    average_entry_slippage_pct: float | None = None
    planned_exit_count: int
    average_exit_drag_r: float | None = None


class AnalyticsOverviewResponse(BaseModel):
    from_date: date
    to_date: date
    equity: float
    total_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    win_rate: float
    profit_factor: float
    expectancy_r: float
    average_r: float
    max_drawdown_pct: float
    current_drawdown_pct: float
    trades_count: int
    open_risk_pct: float
    open_positions_count: int = 0
    closed_positions_count: int = 0
    strategy_breakdown: list[AnalyticsStrategyBreakdown] = Field(default_factory=list)
    execution_quality: AnalyticsExecutionQuality = Field(
        default_factory=lambda: AnalyticsExecutionQuality(
            fills_count=0,
            matched_fills_count=0,
            review_needed_fills_count=0,
            planned_entry_count=0,
            planned_exit_count=0,
        )
    )
