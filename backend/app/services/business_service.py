from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import (
    DashboardSummary,
    DataFreshnessSummary,
    JournalTrade,
    JournalTradeCreate,
    MarketContextSummary,
)
from backend.app.services.audit_service import AuditService
from backend.app.services.business.candidates import BusinessCandidatesMixin
from backend.app.services.business.exit_alerts import BusinessExitAlertsMixin
from backend.app.services.business.jobs import BusinessJobsMixin
from backend.app.services.business.notifications import BusinessNotificationsMixin
from backend.app.services.business.positions import BusinessPositionsMixin
from backend.app.services.business.risk import BusinessRiskMixin
from backend.app.services.business.scanners import BusinessScannersMixin


class BusinessService(
    BusinessNotificationsMixin,
    BusinessRiskMixin,
    BusinessJobsMixin,
    BusinessScannersMixin,
    BusinessCandidatesMixin,
    BusinessPositionsMixin,
    BusinessExitAlertsMixin,
):
    @staticmethod
    def _audit(
        session: Session,
        principal: AuthPrincipal,
        action: str,
        entity_type: str,
        entity_id: str | None,
    ) -> None:
        AuditService.record(session, principal, action, entity_type, entity_id)

    @staticmethod
    def create_journal_trade(
        session: Session,
        principal: AuthPrincipal,
        request: JournalTradeCreate,
    ) -> JournalTrade:
        if request.position_id:
            BusinessService._get_position_model(session, principal, request.position_id)
        trade = db.TradeJournal(
            trade_id=request.trade_id or f"trade_{uuid4().hex}",
            account_id=principal.account_id,
            position_id=request.position_id,
            symbol_id=request.symbol_id,
            entry_ts=request.entry_ts,
            exit_ts=request.exit_ts,
            entry_price=request.entry_price,
            exit_price=request.exit_price,
            quantity=request.quantity,
            gross_pnl=request.gross_pnl,
            net_pnl=request.net_pnl,
            r_multiple=request.r_multiple,
            setup_type=request.setup_type,
            exit_reason=request.exit_reason,
            mistake_tags=request.mistake_tags,
            notes=request.notes,
        )
        session.add(trade)
        BusinessService._audit(session, principal, "journal_trade.create", "journal_trade", trade.trade_id)
        session.commit()
        session.refresh(trade)
        return JournalTrade.model_validate(trade)

    @staticmethod
    def list_journal_trades(
        session: Session,
        principal: AuthPrincipal,
        limit: int = 100,
        offset: int = 0,
    ) -> list[JournalTrade]:
        rows = session.scalars(
            BusinessService._journal_trade_list_statement(principal=principal)
            .order_by(db.TradeJournal.entry_ts.desc().nulls_last())
            .offset(offset)
            .limit(limit)
        ).all()
        return [JournalTrade.model_validate(row) for row in rows]

    @staticmethod
    def count_journal_trades(
        session: Session,
        principal: AuthPrincipal,
    ) -> int:
        statement = BusinessService._journal_trade_list_statement(principal=principal)
        return session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def _journal_trade_list_statement(*, principal: AuthPrincipal):
        return select(db.TradeJournal).where(db.TradeJournal.account_id == principal.account_id)

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
