from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import (
    CandidatePlanCreate,
    JournalTrade,
    Position,
    PositionActivate,
    PositionClose,
    PositionCloseResponse,
    PositionCreate,
    PositionReduce,
    PositionStopUpdate,
    PositionUpdate,
)


def _number_from_plan(data: dict | None, key: str) -> float | None:
    value = data.get(key) if data else None
    if isinstance(value, int | float):
        return float(value)
    return None


def _candidate_plan_position_id(candidate_id: str) -> str:
    return f"plan_{candidate_id}"


def _position_exit_profile(strategy_name: str | None, exit_plan: dict | None = None) -> str | None:
    exit_profile = exit_plan.get("exit_profile") if exit_plan else None
    if isinstance(exit_profile, str) and exit_profile.strip():
        return exit_profile.strip()
    if strategy_name == "etf_rotation_us_etf":
        return "etf_rotation_trend"
    if strategy_name == "oneil_core_us_etf":
        return "momentum_leader"
    return None


def _position_pnl(entry_price: float | None, exit_price: float, quantity: float | None) -> float | None:
    if entry_price is None or quantity is None:
        return None
    return round((exit_price - entry_price) * quantity, 6)


def _position_r_multiple(position: db.Position, exit_price: float) -> float | None:
    if position.entry_price is None:
        return None
    stop = position.initial_stop or position.current_stop
    if stop is None:
        return None
    risk = position.entry_price - stop
    if risk <= 0:
        return None
    return round((exit_price - position.entry_price) / risk, 6)


def _risk_per_unit(entry_price: float | None, stop: float | None) -> float | None:
    if entry_price is None or stop is None:
        return None
    risk = entry_price - stop
    return round(risk, 6) if risk > 0 else None


def _risk_amount(entry_price: float | None, stop: float | None, quantity: float | None) -> float | None:
    risk = _risk_per_unit(entry_price, stop)
    if risk is None or quantity is None:
        return None
    return round(risk * quantity, 6)


def _touch_position(position: db.Position) -> None:
    position.updated_at = datetime.now(UTC)


class BusinessPositionsMixin:
    @classmethod
    def create_position(
        cls,
        session: Session,
        principal: AuthPrincipal,
        request: PositionCreate,
    ) -> Position:
        position = db.Position(
            position_id=request.position_id or f"pos_{uuid4().hex}",
            account_id=principal.account_id,
            symbol_id=request.symbol_id,
            asset_type=request.asset_type,
            strategy_name=request.strategy_name,
            exit_profile=request.exit_profile,
            entry_date=request.entry_date,
            entry_price=request.entry_price,
            quantity=request.quantity,
            initial_stop=request.initial_stop,
            current_stop=request.current_stop,
            status=request.status,
            current_r=request.current_r,
            realized_pnl=request.realized_pnl,
            unrealized_pnl=request.unrealized_pnl,
        )
        session.add(position)
        cls._audit(session, principal, "position.create", "position", position.position_id)
        session.commit()
        session.refresh(position)
        return cls._position_response(session, principal, position)

    @classmethod
    def create_candidate_plan(
        cls,
        session: Session,
        principal: AuthPrincipal,
        candidate_id: str,
        request: CandidatePlanCreate,
    ) -> Position:
        candidate = cls._get_candidate_model(session, principal, candidate_id)
        setup = cls._candidate_pa_setup(session, candidate)
        entry_plan = setup.entry_plan if setup else None
        exit_plan = setup.exit_plan if setup else None
        exit_profile = _position_exit_profile(candidate.strategy_name, exit_plan)
        entry_price = (
            request.entry_price
            or cls._candidate_plan_trigger(candidate, entry_plan)
            or _number_from_plan(entry_plan, "trigger_price")
        )
        initial_stop = (
            request.initial_stop
            or candidate.initial_stop
            or _number_from_plan(exit_plan, "initial_stop")
        )
        if entry_price is None or initial_stop is None:
            raise ValueError("Candidate is missing entry trigger or initial stop")
        position_id = _candidate_plan_position_id(candidate.candidate_id)
        existing = session.scalar(
            select(db.Position).where(
                db.Position.position_id == position_id,
                db.Position.account_id == principal.account_id,
            )
        )
        if existing is not None and not cls._candidate_plan_needs_fill(existing):
            return cls._position_response(session, principal, existing)

        preview = cls.preview_candidate_plan(
            session,
            principal,
            candidate_id,
            request,
        )
        blocking_guardrails = [notice.code for notice in preview.guardrails if notice.level == "block"]
        if blocking_guardrails:
            raise ValueError(f"Candidate plan blocked: {', '.join(blocking_guardrails)}")

        if existing is not None:
            updated = cls._fill_missing_candidate_plan_fields(
                existing,
                entry_price=entry_price,
                initial_stop=initial_stop,
                exit_profile=exit_profile,
                quantity=request.quantity
                or (
                    preview.suggested_quantity
                    if preview.suggested_quantity is not None and preview.suggested_quantity > 0
                    else None
                ),
            )
            if updated:
                _touch_position(existing)
                cls._audit(
                    session,
                    principal,
                    "candidate.plan_update",
                    "position",
                    existing.position_id,
                )
                session.commit()
                session.refresh(existing)
            return cls._position_response(session, principal, existing)

        position = db.Position(
            position_id=position_id,
            account_id=principal.account_id,
            symbol_id=candidate.symbol_id,
            asset_type=request.asset_type,
            strategy_name=candidate.strategy_name,
            exit_profile=exit_profile,
            entry_date=None,
            entry_price=entry_price,
            quantity=request.quantity
            or (preview.suggested_quantity if preview.suggested_quantity and preview.suggested_quantity > 0 else None),
            initial_stop=initial_stop,
            current_stop=initial_stop,
            status="planned",
            current_r=0,
            realized_pnl=0,
            unrealized_pnl=0,
        )
        session.add(position)
        cls._create_notification_event(
            session,
            principal,
            event_type="candidate_plan_created",
            severity="info",
            source_type="position",
            source_id=position.position_id,
            title="Plan added to tracking",
            body=f"{position.symbol_id} is now tracked as a planned position.",
            target_view="positions",
            target_id=position.position_id,
            metadata_json={
                "position_id": position.position_id,
                "candidate_id": candidate.candidate_id,
                "symbol_id": position.symbol_id,
                "entry_price": position.entry_price,
                "initial_stop": position.initial_stop,
                "quantity": position.quantity,
                "exit_profile": position.exit_profile,
            },
        )
        cls._audit(
            session,
            principal,
            "candidate.plan_create",
            "position",
            position.position_id,
        )
        session.commit()
        session.refresh(position)
        return cls._position_response(session, principal, position)

    @staticmethod
    def _candidate_plan_needs_fill(position: db.Position) -> bool:
        return (
            position.status == "planned"
            and (
                position.entry_price is None
                or position.initial_stop is None
                or position.current_stop is None
                or position.quantity is None
                or position.exit_profile is None
            )
        )

    @staticmethod
    def _fill_missing_candidate_plan_fields(
        position: db.Position,
        *,
        entry_price: float | None,
        initial_stop: float | None,
        exit_profile: str | None,
        quantity: float | None,
    ) -> bool:
        if position.status != "planned":
            return False
        updated = False
        if position.entry_price is None and entry_price is not None:
            position.entry_price = entry_price
            updated = True
        if position.initial_stop is None and initial_stop is not None:
            position.initial_stop = initial_stop
            updated = True
        if position.current_stop is None and initial_stop is not None:
            position.current_stop = initial_stop
            updated = True
        if position.exit_profile is None and exit_profile is not None:
            position.exit_profile = exit_profile
            updated = True
        if position.quantity is None and quantity is not None:
            position.quantity = quantity
            updated = True
        return updated

    @classmethod
    def get_candidate_plan(
        cls,
        session: Session,
        principal: AuthPrincipal,
        candidate_id: str,
    ) -> Position | None:
        candidate = cls._get_candidate_model(session, principal, candidate_id)
        position = session.scalar(
            select(db.Position).where(
                db.Position.position_id == _candidate_plan_position_id(candidate.candidate_id),
                db.Position.account_id == principal.account_id,
            )
        )
        return cls._position_response(session, principal, position) if position else None

    @classmethod
    def list_positions(
        cls,
        session: Session,
        principal: AuthPrincipal,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Position]:
        statement = cls._position_list_statement(principal=principal, status=status)
        rows = session.scalars(
            statement.order_by(db.Position.updated_at.desc()).offset(offset).limit(limit)
        ).all()
        return [cls._position_response(session, principal, row) for row in rows]

    @classmethod
    def count_positions(
        cls,
        session: Session,
        principal: AuthPrincipal,
        status: str | None = None,
    ) -> int:
        statement = cls._position_list_statement(principal=principal, status=status)
        return session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def _position_list_statement(
        *,
        principal: AuthPrincipal,
        status: str | None = None,
    ):
        statement = select(db.Position).where(db.Position.account_id == principal.account_id)
        if status:
            statement = statement.where(db.Position.status == status)
        return statement

    @classmethod
    def _position_response(
        cls,
        session: Session,
        principal: AuthPrincipal,
        position: db.Position,
    ) -> Position:
        response = Position.model_validate(position)
        risk_settings = cls.get_account_risk_settings(session, principal)
        stop = position.current_stop or position.initial_stop
        response.risk_per_unit = _risk_per_unit(position.entry_price, stop)
        response.risk_amount = _risk_amount(position.entry_price, stop, position.quantity)
        response.risk_pct = (
            round(response.risk_amount / risk_settings.account_equity, 6)
            if response.risk_amount is not None
            else None
        )
        return response

    @classmethod
    def update_position(
        cls,
        session: Session,
        principal: AuthPrincipal,
        position_id: str,
        request: PositionUpdate,
    ) -> Position:
        position = cls._get_position_model(session, principal, position_id)
        payload = request.model_dump(exclude_unset=True)
        next_status = payload.get("status")
        if next_status is not None and next_status != position.status:
            raise ValueError("Use lifecycle actions to change position status")
        for key, value in payload.items():
            setattr(position, key, value)
        if payload:
            _touch_position(position)
            cls._audit(session, principal, "position.update", "position", position_id)
            session.commit()
            session.refresh(position)
        return cls._position_response(session, principal, position)

    @classmethod
    def activate_position(
        cls,
        session: Session,
        principal: AuthPrincipal,
        position_id: str,
        request: PositionActivate,
    ) -> Position:
        position = cls._get_position_model(session, principal, position_id)
        if position.status != "planned":
            raise ValueError("Position must be planned before activation")

        quantity = request.quantity if request.quantity is not None else position.quantity
        if quantity is None or quantity <= 0:
            raise ValueError("Position quantity is required before activation")
        stop = position.current_stop or position.initial_stop
        if stop is None:
            raise ValueError("Position stop is required before activation")
        if stop >= request.entry_price:
            raise ValueError("Position stop must be below entry price")

        position.status = "open"
        position.entry_price = request.entry_price
        position.quantity = quantity
        position.entry_date = request.entry_date or datetime.now(UTC)
        position.current_r = 0
        position.realized_pnl = position.realized_pnl or 0
        position.unrealized_pnl = 0
        _touch_position(position)
        cls._audit(session, principal, "position.activate", "position", position_id)
        session.commit()
        session.refresh(position)
        return cls._position_response(session, principal, position)

    @classmethod
    def update_position_stop(
        cls,
        session: Session,
        principal: AuthPrincipal,
        position_id: str,
        request: PositionStopUpdate,
    ) -> Position:
        position = cls._get_position_model(session, principal, position_id)
        if position.status in ("closed", "cancelled"):
            raise ValueError("Closed or cancelled positions cannot update stops")

        position.current_stop = request.new_stop
        if position.status == "planned" or position.initial_stop is None:
            position.initial_stop = request.new_stop
        _touch_position(position)
        cls._audit(session, principal, "position.stop_update", "position", position_id)
        session.commit()
        session.refresh(position)
        return cls._position_response(session, principal, position)

    @classmethod
    def cancel_position(
        cls,
        session: Session,
        principal: AuthPrincipal,
        position_id: str,
    ) -> Position:
        position = cls._get_position_model(session, principal, position_id)
        if position.status != "planned":
            raise ValueError("Only planned positions can be cancelled")

        position.status = "cancelled"
        position.quantity = 0
        position.current_r = 0
        position.realized_pnl = position.realized_pnl or 0
        position.unrealized_pnl = 0
        _touch_position(position)
        session.execute(
            delete(db.ExitAlert).where(
                db.ExitAlert.account_id == principal.account_id,
                db.ExitAlert.position_id == position.position_id,
            )
        )
        cls._audit(session, principal, "position.cancel", "position", position_id)
        session.commit()
        session.refresh(position)
        return cls._position_response(session, principal, position)

    @classmethod
    def reduce_position(
        cls,
        session: Session,
        principal: AuthPrincipal,
        position_id: str,
        request: PositionReduce,
    ) -> Position:
        position = cls._get_position_model(session, principal, position_id)
        if position.status not in ("open", "reduce"):
            raise ValueError("Position must be open or reduced before marking a trim")
        if position.entry_price is None:
            raise ValueError("Position is missing entry price")
        if position.quantity is None or position.quantity <= 0:
            raise ValueError("Position quantity is required before marking a trim")
        if request.quantity is None:
            raise ValueError("Reduced quantity is required")

        reduced_quantity = request.quantity
        if reduced_quantity >= position.quantity:
            raise ValueError("Reduced quantity must be smaller than current quantity; use close instead")

        realized_delta = _position_pnl(position.entry_price, request.exit_price, reduced_quantity)
        exit_ts = request.exit_date or datetime.now(UTC)
        r_multiple = _position_r_multiple(position, request.exit_price)
        trade = db.TradeJournal(
            trade_id=f"trade_{position.position_id}_trim_{uuid4().hex[:8]}",
            account_id=principal.account_id,
            position_id=position.position_id,
            symbol_id=position.symbol_id,
            entry_ts=position.entry_date,
            exit_ts=exit_ts,
            entry_price=position.entry_price,
            exit_price=request.exit_price,
            quantity=reduced_quantity,
            gross_pnl=realized_delta,
            net_pnl=realized_delta,
            r_multiple=r_multiple,
            setup_type=position.strategy_name,
            exit_reason="trim",
            mistake_tags=None,
            notes=request.notes,
        )
        session.add(trade)
        if realized_delta is not None:
            position.realized_pnl = round((position.realized_pnl or 0) + realized_delta, 6)
        position.quantity = round(position.quantity - reduced_quantity, 6)
        if request.current_stop is not None:
            position.current_stop = request.current_stop
        position.current_r = r_multiple
        position.status = "reduce"
        _touch_position(position)
        cls._audit(session, principal, "position.reduce", "position", position_id)
        cls._audit(session, principal, "journal_trade.create", "journal_trade", trade.trade_id)
        session.commit()
        session.refresh(position)
        return cls._position_response(session, principal, position)

    @classmethod
    def close_position(
        cls,
        session: Session,
        principal: AuthPrincipal,
        position_id: str,
        request: PositionClose,
    ) -> PositionCloseResponse:
        position = cls._get_position_model(session, principal, position_id)
        if position.status == "closed":
            raise ValueError("Position is already closed")
        if position.status == "planned":
            raise ValueError("Planned positions must be activated before closing")
        if position.status == "cancelled":
            raise ValueError("Cancelled positions cannot be closed")
        if position.entry_price is None:
            raise ValueError("Position is missing entry price")
        if position.quantity is None or position.quantity <= 0:
            raise ValueError("Position quantity is required before closing")
        if request.quantity is not None:
            if request.quantity < position.quantity:
                raise ValueError("Close quantity is smaller than current quantity; use reduce instead")
            if request.quantity > position.quantity:
                raise ValueError("Close quantity exceeds current quantity")

        exit_ts = request.exit_date or datetime.now(UTC)
        close_quantity = request.quantity if request.quantity is not None else position.quantity
        closing_pnl = _position_pnl(position.entry_price, request.exit_price, close_quantity)
        gross_pnl = (
            None
            if closing_pnl is None and position.realized_pnl is None
            else round((position.realized_pnl or 0) + (closing_pnl or 0), 6)
        )
        r_multiple = _position_r_multiple(position, request.exit_price)
        trade_id = f"trade_{position.position_id}"
        if session.get(db.TradeJournal, trade_id) is not None:
            raise ValueError(f"Journal trade already exists for position: {position_id}")

        trade = db.TradeJournal(
            trade_id=trade_id,
            account_id=principal.account_id,
            position_id=position.position_id,
            symbol_id=position.symbol_id,
            entry_ts=position.entry_date,
            exit_ts=exit_ts,
            entry_price=position.entry_price,
            exit_price=request.exit_price,
            quantity=close_quantity,
            gross_pnl=closing_pnl,
            net_pnl=closing_pnl,
            r_multiple=r_multiple,
            setup_type=position.strategy_name,
            exit_reason=request.exit_reason,
            mistake_tags=None,
            notes=request.notes,
        )
        session.add(trade)

        position.status = "closed"
        position.realized_pnl = gross_pnl
        position.unrealized_pnl = 0
        position.current_r = r_multiple
        position.quantity = 0 if close_quantity is not None else position.quantity
        _touch_position(position)
        cls._audit(session, principal, "position.close", "position", position_id)
        cls._audit(session, principal, "journal_trade.create", "journal_trade", trade.trade_id)
        session.commit()
        session.refresh(position)
        session.refresh(trade)
        return PositionCloseResponse(
            position=cls._position_response(session, principal, position),
            journal_trade=JournalTrade.model_validate(trade),
        )

    @staticmethod
    def _get_position_model(
        session: Session,
        principal: AuthPrincipal,
        position_id: str,
    ) -> db.Position:
        position = session.scalar(
            select(db.Position).where(
                db.Position.position_id == position_id,
                db.Position.account_id == principal.account_id,
            )
        )
        if position is None:
            raise ValueError(f"Position not found: {position_id}")
        return position
