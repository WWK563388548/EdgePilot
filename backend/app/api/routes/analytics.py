from datetime import date, timedelta

from fastapi import APIRouter, Query

from backend.app.api.dependencies import DbSession, VerifiedPrincipal
from backend.app.schemas.analytics import AnalyticsOverviewResponse
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_overview(
    session: DbSession,
    principal: VerifiedPrincipal,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
) -> AnalyticsOverviewResponse:
    resolved_to_date = to_date or date.today()
    resolved_from_date = from_date or (resolved_to_date - timedelta(days=90))
    return AnalyticsService.overview(
        session=session,
        principal=principal,
        from_date=resolved_from_date,
        to_date=resolved_to_date,
    )
