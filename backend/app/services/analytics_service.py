from datetime import date

from backend.app.schemas.analytics import AnalyticsOverviewResponse


class AnalyticsService:
    """MVP placeholder service.

    TODO(D3): Replace with TimescaleDB query over portfolio_snapshots,
    analytics_daily and trades_journal.
    """

    @staticmethod
    def overview(from_date: date, to_date: date) -> AnalyticsOverviewResponse:
        return AnalyticsOverviewResponse(
            from_date=from_date,
            to_date=to_date,
            equity=2150.4,
            total_pnl=150.4,
            realized_pnl=120.1,
            unrealized_pnl=30.3,
            win_rate=0.482,
            profit_factor=1.42,
            expectancy_r=0.18,
            average_r=0.12,
            max_drawdown_pct=-0.064,
            current_drawdown_pct=-0.018,
            trades_count=83,
            open_risk_pct=0.012,
        )
