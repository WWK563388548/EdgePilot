from __future__ import annotations

from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import JournalTrade, JournalTradeCreate


class BusinessJournalMixin:
    @classmethod
    def create_journal_trade(
        cls,
        session: Session,
        principal: AuthPrincipal,
        request: JournalTradeCreate,
    ) -> JournalTrade:
        if request.position_id:
            cls._get_position_model(session, principal, request.position_id)
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
        cls._audit(session, principal, "journal_trade.create", "journal_trade", trade.trade_id)
        session.commit()
        session.refresh(trade)
        return JournalTrade.model_validate(trade)

    @classmethod
    def list_journal_trades(
        cls,
        session: Session,
        principal: AuthPrincipal,
        limit: int = 100,
        offset: int = 0,
    ) -> list[JournalTrade]:
        rows = session.scalars(
            cls._journal_trade_list_statement(principal=principal)
            .order_by(db.TradeJournal.entry_ts.desc().nulls_last())
            .offset(offset)
            .limit(limit)
        ).all()
        return [JournalTrade.model_validate(row) for row in rows]

    @classmethod
    def count_journal_trades(
        cls,
        session: Session,
        principal: AuthPrincipal,
    ) -> int:
        statement = cls._journal_trade_list_statement(principal=principal)
        return session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def _journal_trade_list_statement(*, principal: AuthPrincipal):
        return select(db.TradeJournal).where(db.TradeJournal.account_id == principal.account_id)
