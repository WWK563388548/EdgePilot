from datetime import date

from fastapi import APIRouter, Query

from backend.app.schemas.analytics import AnalyticsOverviewResponse
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_overview(
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
) -> AnalyticsOverviewResponse:
    return AnalyticsService.overview(from_date=from_date, to_date=to_date)
