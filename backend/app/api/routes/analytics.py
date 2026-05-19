from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from backend.app.api.dependencies import DbSession, VerifiedPrincipal
from backend.app.schemas.analytics import AnalyticsOverviewResponse
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _utc_today() -> date:
    return datetime.now(UTC).date()


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_overview(
    session: DbSession,
    principal: VerifiedPrincipal,
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
) -> AnalyticsOverviewResponse:
    resolved_to_date = to_date or _utc_today()
    resolved_from_date = from_date or (resolved_to_date - timedelta(days=90))
    try:
        return AnalyticsService.overview(
            session=session,
            principal=principal,
            from_date=resolved_from_date,
            to_date=resolved_to_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
