from datetime import date

from pydantic import BaseModel


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
