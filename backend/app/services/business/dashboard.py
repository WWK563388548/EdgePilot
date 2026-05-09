from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import (
    DashboardSummary,
    DataFreshnessSummary,
    MarketContextSummary,
)


class BusinessDashboardMixin:
    @staticmethod
    def dashboard_summary(session: Session, principal: AuthPrincipal) -> DashboardSummary:
        candidate_count = session.scalar(
            select(func.count()).select_from(db.Candidate).where(
                db.Candidate.account_id == principal.account_id,
                db.Candidate.decision == "candidate",
            )
        )
        open_position_count = session.scalar(
            select(func.count()).select_from(db.Position).where(
                db.Position.account_id == principal.account_id,
                db.Position.status.in_(("open", "reduce")),
            )
        )
        alert_count, highest_level = session.execute(
            select(func.count(), func.max(db.ExitAlert.level)).where(
                db.ExitAlert.account_id == principal.account_id,
                db.ExitAlert.acknowledged.is_(False),
            )
        ).one()
        market_context = session.scalar(
            select(db.MarketContextSnapshot).order_by(db.MarketContextSnapshot.snapshot_ts.desc()).limit(1)
        )
        freshness_rows = session.scalars(
            select(db.DataFreshness).order_by(db.DataFreshness.dataset_key)
        ).all()

        context = (
            MarketContextSummary.model_validate(market_context)
            if market_context
            else MarketContextSummary(risk_level="unknown")
        )
        return DashboardSummary(
            market_context=context,
            risk_mode=context.risk_level or "unknown",
            candidate_count=candidate_count or 0,
            open_position_count=open_position_count or 0,
            exit_alert_count=alert_count or 0,
            highest_exit_level=highest_level,
            data_freshness=[DataFreshnessSummary.model_validate(row) for row in freshness_rows],
        )
