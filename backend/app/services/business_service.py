import json
from collections import Counter
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal, AuthService
from backend.app.schemas.business import (
    Candidate,
    CandidateCreate,
    CandidateDetail,
    CandidatePASetup,
    CandidatePlanCreate,
    CandidateUpdate,
    DashboardSummary,
    DataFreshnessSummary,
    ExitAlert,
    ExitAlertCreate,
    ExitAlertEvaluationRequest,
    ExitAlertEvaluationResponse,
    ExitAlertUpdate,
    JournalTrade,
    JournalTradeCreate,
    MarketContextSummary,
    Position,
    PositionActivate,
    PositionClose,
    PositionCloseResponse,
    PositionCreate,
    PositionReduce,
    PositionStopUpdate,
    PositionUpdate,
)
from backend.app.schemas.ingestion import (
    AccountETFUniverseRefreshRequest,
    ETFUniverseSeedRequest,
    ETFUniverseSeedResponse,
)
from backend.app.schemas.pa import (
    AccountETFOneilScannerRequest,
    ETFOneilScannerRequest,
    ETFOneilScannerResponse,
)
from backend.app.schemas.outcome import (
    ScannerOutcome,
    ScannerOutcomeRecalculateRequest,
    ScannerOutcomeRecalculateResponse,
    ScannerOutcomeSummary,
)
from backend.app.schemas.scanner import ScannerDecision
from backend.app.services.etf_seed_service import ETFSeedService
from backend.app.services.scanner_outcome_service import ScannerOutcomeService
from backend.app.services.scanner_service import ETFScannerService

ONEIL_CORE_US_ETF_STRATEGY = "oneil_core_us_etf"


def _average(values) -> float | None:
    numbers = [value for value in values if value is not None]
    if not numbers:
        return None
    return round(sum(numbers) / len(numbers), 6)


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def _number_from_plan(data: dict | None, key: str) -> float | None:
    value = data.get(key) if data else None
    if isinstance(value, int | float):
        return float(value)
    return None


def _number_from_record(data: dict | None, key: str) -> float | None:
    value = data.get(key) if data else None
    if isinstance(value, int | float):
        return float(value)
    return None


def _candidate_plan_position_id(candidate_id: str) -> str:
    return f"plan_{candidate_id}"


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


def _touch_position(position: db.Position) -> None:
    position.updated_at = datetime.now(UTC)


class BusinessService:
    @staticmethod
    def _audit(
        session: Session,
        principal: AuthPrincipal,
        action: str,
        entity_type: str,
        entity_id: str | None,
    ) -> None:
        session.add(
            db.AuditLog(
                audit_id=AuthService.audit_id(),
                account_id=principal.account_id,
                actor_user_id=principal.user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
            )
        )

    @staticmethod
    def create_candidate(
        session: Session,
        principal: AuthPrincipal,
        request: CandidateCreate,
    ) -> Candidate:
        pa_setup_id = BusinessService._validated_pa_setup_id(session, request.pa_setup_id)
        candidate = db.Candidate(
            candidate_id=request.candidate_id or f"cand_{uuid4().hex}",
            account_id=principal.account_id,
            symbol_id=request.symbol_id,
            scan_date=request.scan_date,
            strategy_name=request.strategy_name,
            setup_type=request.setup_type,
            pa_setup_id=pa_setup_id,
            score_total=request.score_total,
            entry_trigger=request.entry_trigger,
            initial_stop=request.initial_stop,
            decision=request.decision,
            option_suitability=request.option_suitability,
            ai_review_json=request.ai_review_json,
        )
        session.add(candidate)
        BusinessService._audit(session, principal, "candidate.create", "candidate", candidate.candidate_id)
        session.commit()
        session.refresh(candidate)
        return BusinessService._candidate_response(session, candidate)

    @staticmethod
    def list_candidates(
        session: Session,
        principal: AuthPrincipal,
        decision: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Candidate]:
        statement = BusinessService._candidate_list_statement(principal=principal, decision=decision)
        rows = session.scalars(
            statement.order_by(db.Candidate.scan_date.desc(), db.Candidate.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return [BusinessService._candidate_response(session, row) for row in rows]

    @staticmethod
    def count_candidates(
        session: Session,
        principal: AuthPrincipal,
        decision: str | None = None,
    ) -> int:
        statement = BusinessService._candidate_list_statement(principal=principal, decision=decision)
        return session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def _candidate_list_statement(
        *,
        principal: AuthPrincipal,
        decision: str | None = None,
    ):
        statement = select(db.Candidate).where(db.Candidate.account_id == principal.account_id)
        if decision:
            statement = statement.where(db.Candidate.decision == decision)
        return statement

    @staticmethod
    def run_account_oneil_core_scanner(
        session: Session,
        principal: AuthPrincipal,
        request: AccountETFOneilScannerRequest,
    ) -> ETFOneilScannerResponse:
        BusinessService._delete_account_oneil_candidates_and_outcomes(session, principal)
        response = ETFScannerService.run_us_etf_oneil_core_for_session(
            session,
            ETFOneilScannerRequest(
                symbols=request.symbols,
                timeframe=request.timeframe,
                account_id=principal.account_id,
                min_score=request.min_score,
                max_candidates=request.max_candidates,
                recalculate_facts=request.recalculate_facts,
            ),
        )
        BusinessService._audit(
            session,
            principal,
            "candidate.scan",
            "scanner",
            ONEIL_CORE_US_ETF_STRATEGY,
        )
        session.commit()
        return response

    @staticmethod
    def refresh_account_oneil_core_universe(
        session: Session,
        principal: AuthPrincipal,
        request: AccountETFUniverseRefreshRequest,
    ) -> ETFUniverseSeedResponse:
        BusinessService._delete_account_oneil_candidates_and_outcomes(session, principal)
        response = ETFSeedService.seed_us_etf_universe_for_session(
            session=session,
            client=ETFSeedService._client(),
            request=ETFUniverseSeedRequest(
                symbols=request.symbols,
                from_date=request.from_date,
                to_date=request.to_date,
                timeframe=request.timeframe,
                lookback_days=request.lookback_days,
                account_id=principal.account_id,
                run_pa_facts=True,
                run_scanner=True,
                min_score=request.min_score,
                max_candidates=request.max_candidates,
            ),
        )
        BusinessService._audit(
            session,
            principal,
            "candidate.refresh_scan",
            "scanner",
            ONEIL_CORE_US_ETF_STRATEGY,
        )
        session.commit()
        return response

    @staticmethod
    def list_scanner_outcomes(
        session: Session,
        principal: AuthPrincipal,
        evaluation_status: str | None = None,
        symbol: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ScannerOutcome]:
        statement = BusinessService._scanner_outcome_statement(
            principal=principal,
            evaluation_status=evaluation_status,
            symbol=symbol,
        )
        rows = session.scalars(
            statement.order_by(db.ScannerOutcome.detected_ts.desc(), db.ScannerOutcome.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return [ScannerOutcome.model_validate(row) for row in rows]

    @staticmethod
    def count_scanner_outcomes(
        session: Session,
        principal: AuthPrincipal,
        evaluation_status: str | None = None,
        symbol: str | None = None,
    ) -> int:
        statement = BusinessService._scanner_outcome_statement(
            principal=principal,
            evaluation_status=evaluation_status,
            symbol=symbol,
        )
        return session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def scanner_outcome_summary(
        session: Session,
        principal: AuthPrincipal,
        evaluation_status: str | None = None,
        symbol: str | None = None,
    ) -> ScannerOutcomeSummary:
        statement = BusinessService._scanner_outcome_statement(
            principal=principal,
            evaluation_status=evaluation_status,
            symbol=symbol,
        )
        rows = list(session.scalars(statement).all())
        total = len(rows)
        pending_count = sum(row.evaluation_status == "pending" for row in rows)
        matured_count = sum(row.evaluation_status.startswith("matured") for row in rows)
        triggered_count = sum(row.triggered_entry is True for row in rows)
        stopped_count = sum(row.stopped_out is True for row in rows)
        false_breakout_count = sum(row.false_breakout is True for row in rows)
        positive_20d_count = sum((row.forward_return_20d or 0) > 0 for row in rows)
        positive_60d_count = sum((row.forward_return_60d or 0) > 0 for row in rows)
        return ScannerOutcomeSummary(
            total=total,
            pending_count=pending_count,
            matured_count=matured_count,
            triggered_count=triggered_count,
            stopped_count=stopped_count,
            false_breakout_count=false_breakout_count,
            positive_20d_count=positive_20d_count,
            positive_60d_count=positive_60d_count,
            trigger_rate=_rate(triggered_count, total),
            stop_rate=_rate(stopped_count, triggered_count),
            false_breakout_rate=_rate(false_breakout_count, triggered_count),
            positive_20d_rate=_rate(
                positive_20d_count,
                sum(row.forward_return_20d is not None for row in rows),
            ),
            positive_60d_rate=_rate(
                positive_60d_count,
                sum(row.forward_return_60d is not None for row in rows),
            ),
            avg_forward_return_20d=_average(row.forward_return_20d for row in rows),
            avg_forward_return_60d=_average(row.forward_return_60d for row in rows),
            avg_mfe_20d=_average(row.mfe_20d for row in rows),
            avg_mfe_60d=_average(row.mfe_60d for row in rows),
            avg_mae_20d=_average(row.mae_20d for row in rows),
            avg_mae_60d=_average(row.mae_60d for row in rows),
        )

    @staticmethod
    def get_candidate_outcome(
        session: Session,
        principal: AuthPrincipal,
        candidate_id: str,
    ) -> ScannerOutcome:
        outcome = session.scalar(
            select(db.ScannerOutcome).where(
                db.ScannerOutcome.account_id == principal.account_id,
                db.ScannerOutcome.candidate_id == candidate_id,
            )
        )
        if outcome is None:
            raise ValueError(f"Scanner outcome not found for candidate: {candidate_id}")
        return ScannerOutcome.model_validate(outcome)

    @staticmethod
    def recalculate_scanner_outcomes(
        session: Session,
        principal: AuthPrincipal,
        request: ScannerOutcomeRecalculateRequest,
    ) -> ScannerOutcomeRecalculateResponse:
        statement = BusinessService._candidate_list_statement(principal=principal)
        if request.candidate_id:
            statement = statement.where(db.Candidate.candidate_id == request.candidate_id)
        if request.symbol:
            statement = statement.where(db.Candidate.symbol_id == request.symbol.strip().upper())
        if request.strategy_name:
            statement = statement.where(db.Candidate.strategy_name == request.strategy_name.strip())
        statement = statement.order_by(db.Candidate.scan_date.desc(), db.Candidate.created_at.desc())
        if request.limit is not None:
            statement = statement.limit(request.limit)

        candidates = list(session.scalars(statement).all())
        if request.candidate_id and not candidates:
            raise ValueError(f"Candidate not found: {request.candidate_id}")

        status_counts: Counter[str] = Counter()
        symbols: set[str] = set()
        for candidate in candidates:
            outcome = ScannerOutcomeService.calculate_for_candidate(session=session, candidate=candidate)
            status_counts[outcome.evaluation_status] += 1
            symbols.add(outcome.symbol_id)

        if candidates:
            BusinessService._audit(
                session,
                principal,
                "candidate.outcome_recalculate",
                "scanner_outcome",
                request.candidate_id,
            )
        session.commit()
        return ScannerOutcomeRecalculateResponse(
            account_id=principal.account_id,
            candidates_scanned=len(candidates),
            outcomes_written=len(candidates),
            skipped_candidates=0,
            status_counts=dict(status_counts),
            symbols_processed=sorted(symbols),
        )

    @staticmethod
    def get_candidate_detail(
        session: Session,
        principal: AuthPrincipal,
        candidate_id: str,
    ) -> CandidateDetail:
        candidate = BusinessService._get_candidate_model(session, principal, candidate_id)
        pa_setup = BusinessService._candidate_pa_setup(session, candidate)
        entry_plan = pa_setup.entry_plan if pa_setup else None
        return CandidateDetail(
            candidate=BusinessService._candidate_response(session, candidate, pa_setup),
            pa_setup=CandidatePASetup.model_validate(pa_setup) if pa_setup else None,
            score_breakdown=entry_plan.get("score_breakdown") if entry_plan else None,
            scanner_decision=BusinessService._candidate_scanner_decision(candidate, entry_plan),
            entry_plan=entry_plan,
            exit_plan=pa_setup.exit_plan if pa_setup else None,
            invalidation=pa_setup.invalidation if pa_setup else None,
        )

    @staticmethod
    def update_candidate(
        session: Session,
        principal: AuthPrincipal,
        candidate_id: str,
        request: CandidateUpdate,
    ) -> Candidate:
        candidate = BusinessService._get_candidate_model(session, principal, candidate_id)
        payload = request.model_dump(exclude_unset=True)
        if "pa_setup_id" in payload:
            payload["pa_setup_id"] = BusinessService._validated_pa_setup_id(
                session,
                payload["pa_setup_id"],
            )
        for key, value in payload.items():
            setattr(candidate, key, value)
        if payload:
            BusinessService._audit(session, principal, "candidate.update", "candidate", candidate_id)
            session.commit()
            session.refresh(candidate)
        return BusinessService._candidate_response(session, candidate)

    @staticmethod
    def _candidate_response(
        session: Session,
        candidate: db.Candidate,
        pa_setup: db.PASetup | None = None,
    ) -> Candidate:
        setup = pa_setup if pa_setup is not None else BusinessService._candidate_pa_setup(session, candidate)
        response = Candidate.model_validate(candidate)
        if setup:
            response.pa_setup_grade = setup.setup_grade
            response.validation_status = setup.validation_status
        return response

    @staticmethod
    def _candidate_pa_setup(session: Session, candidate: db.Candidate) -> db.PASetup | None:
        setup_id = candidate.pa_setup_id or BusinessService._legacy_pa_setup_id(candidate)
        if not setup_id:
            return None
        return session.get(db.PASetup, setup_id)

    @staticmethod
    def _validated_pa_setup_id(session: Session, pa_setup_id: str | None) -> str | None:
        if pa_setup_id is None:
            return None

        setup_id = pa_setup_id.strip()
        if not setup_id:
            return None
        if any(
            isinstance(model, db.PASetup) and model.setup_id == setup_id
            for model in session.new
        ):
            return setup_id
        if session.get(db.PASetup, setup_id) is None:
            raise ValueError(f"PA setup not found: {setup_id}")
        return setup_id

    @staticmethod
    def _legacy_pa_setup_id(candidate: db.Candidate) -> str | None:
        if not candidate.ai_review_json:
            return None
        try:
            payload = json.loads(candidate.ai_review_json)
        except json.JSONDecodeError:
            return None
        setup_id = payload.get("pa_setup_id")
        return setup_id if isinstance(setup_id, str) else None

    @staticmethod
    def _candidate_scanner_decision(
        candidate: db.Candidate,
        entry_plan: dict | None,
    ) -> ScannerDecision | None:
        scanner_decision = entry_plan.get("scanner_decision") if entry_plan else None
        if isinstance(scanner_decision, dict):
            return BusinessService._normalize_scanner_decision(scanner_decision)
        if not candidate.ai_review_json:
            return None
        try:
            payload = json.loads(candidate.ai_review_json)
        except json.JSONDecodeError:
            return None
        scanner_decision = payload.get("scanner_decision")
        return (
            BusinessService._normalize_scanner_decision(scanner_decision)
            if isinstance(scanner_decision, dict)
            else None
        )

    @staticmethod
    def _normalize_scanner_decision(payload: dict) -> ScannerDecision | None:
        try:
            return ScannerDecision.from_payload(payload)
        except ValidationError:
            return None

    @staticmethod
    def _get_candidate_model(
        session: Session,
        principal: AuthPrincipal,
        candidate_id: str,
    ) -> db.Candidate:
        candidate = session.scalar(
            select(db.Candidate).where(
                db.Candidate.candidate_id == candidate_id,
                db.Candidate.account_id == principal.account_id,
            )
        )
        if candidate is None:
            raise ValueError(f"Candidate not found: {candidate_id}")
        return candidate

    @staticmethod
    def _scanner_outcome_statement(
        *,
        principal: AuthPrincipal,
        evaluation_status: str | None = None,
        symbol: str | None = None,
    ):
        statement = select(db.ScannerOutcome).where(db.ScannerOutcome.account_id == principal.account_id)
        if evaluation_status:
            statement = statement.where(db.ScannerOutcome.evaluation_status == evaluation_status)
        if symbol:
            statement = statement.where(db.ScannerOutcome.symbol_id == symbol.strip().upper())
        return statement

    @staticmethod
    def _delete_account_oneil_candidates_and_outcomes(
        session: Session,
        principal: AuthPrincipal,
    ) -> None:
        candidate_ids = select(db.Candidate.candidate_id).where(
            db.Candidate.account_id == principal.account_id,
            db.Candidate.strategy_name == ONEIL_CORE_US_ETF_STRATEGY,
        )
        session.execute(
            delete(db.ScannerOutcome).where(db.ScannerOutcome.candidate_id.in_(candidate_ids))
        )
        session.execute(
            delete(db.Candidate).where(
                db.Candidate.account_id == principal.account_id,
                db.Candidate.strategy_name == ONEIL_CORE_US_ETF_STRATEGY,
            )
        )

    @staticmethod
    def create_position(
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
        BusinessService._audit(session, principal, "position.create", "position", position.position_id)
        session.commit()
        session.refresh(position)
        return Position.model_validate(position)

    @staticmethod
    def create_candidate_plan(
        session: Session,
        principal: AuthPrincipal,
        candidate_id: str,
        request: CandidatePlanCreate,
    ) -> Position:
        candidate = BusinessService._get_candidate_model(session, principal, candidate_id)
        setup = BusinessService._candidate_pa_setup(session, candidate)
        entry_plan = setup.entry_plan if setup else None
        exit_plan = setup.exit_plan if setup else None
        entry_price = (
            request.entry_price
            or candidate.entry_trigger
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
        if existing is not None:
            return Position.model_validate(existing)

        position = db.Position(
            position_id=position_id,
            account_id=principal.account_id,
            symbol_id=candidate.symbol_id,
            asset_type=request.asset_type,
            strategy_name=candidate.strategy_name,
            entry_date=None,
            entry_price=entry_price,
            quantity=request.quantity,
            initial_stop=initial_stop,
            current_stop=initial_stop,
            status="planned",
            current_r=0,
            realized_pnl=0,
            unrealized_pnl=0,
        )
        session.add(position)
        BusinessService._audit(
            session,
            principal,
            "candidate.plan_create",
            "position",
            position.position_id,
        )
        session.commit()
        session.refresh(position)
        return Position.model_validate(position)

    @staticmethod
    def get_candidate_plan(
        session: Session,
        principal: AuthPrincipal,
        candidate_id: str,
    ) -> Position | None:
        candidate = BusinessService._get_candidate_model(session, principal, candidate_id)
        position = session.scalar(
            select(db.Position).where(
                db.Position.position_id == _candidate_plan_position_id(candidate.candidate_id),
                db.Position.account_id == principal.account_id,
            )
        )
        return Position.model_validate(position) if position else None

    @staticmethod
    def list_positions(
        session: Session,
        principal: AuthPrincipal,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Position]:
        statement = BusinessService._position_list_statement(principal=principal, status=status)
        rows = session.scalars(
            statement.order_by(db.Position.updated_at.desc()).offset(offset).limit(limit)
        ).all()
        return [Position.model_validate(row) for row in rows]

    @staticmethod
    def count_positions(
        session: Session,
        principal: AuthPrincipal,
        status: str | None = None,
    ) -> int:
        statement = BusinessService._position_list_statement(principal=principal, status=status)
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

    @staticmethod
    def update_position(
        session: Session,
        principal: AuthPrincipal,
        position_id: str,
        request: PositionUpdate,
    ) -> Position:
        position = BusinessService._get_position_model(session, principal, position_id)
        payload = request.model_dump(exclude_unset=True)
        next_status = payload.get("status")
        if next_status is not None and next_status != position.status:
            raise ValueError("Use lifecycle actions to change position status")
        for key, value in payload.items():
            setattr(position, key, value)
        if payload:
            _touch_position(position)
            BusinessService._audit(session, principal, "position.update", "position", position_id)
            session.commit()
            session.refresh(position)
        return Position.model_validate(position)

    @staticmethod
    def activate_position(
        session: Session,
        principal: AuthPrincipal,
        position_id: str,
        request: PositionActivate,
    ) -> Position:
        position = BusinessService._get_position_model(session, principal, position_id)
        if position.status != "planned":
            raise ValueError("Position must be planned before activation")

        position.status = "open"
        position.entry_price = request.entry_price
        if request.quantity is not None:
            position.quantity = request.quantity
        position.entry_date = request.entry_date or datetime.now(UTC)
        position.current_r = 0
        position.realized_pnl = position.realized_pnl or 0
        position.unrealized_pnl = 0
        _touch_position(position)
        BusinessService._audit(session, principal, "position.activate", "position", position_id)
        session.commit()
        session.refresh(position)
        return Position.model_validate(position)

    @staticmethod
    def update_position_stop(
        session: Session,
        principal: AuthPrincipal,
        position_id: str,
        request: PositionStopUpdate,
    ) -> Position:
        position = BusinessService._get_position_model(session, principal, position_id)
        if position.status == "closed":
            raise ValueError("Closed positions cannot update stops")

        position.current_stop = request.new_stop
        if position.status == "planned" or position.initial_stop is None:
            position.initial_stop = request.new_stop
        _touch_position(position)
        BusinessService._audit(session, principal, "position.stop_update", "position", position_id)
        session.commit()
        session.refresh(position)
        return Position.model_validate(position)

    @staticmethod
    def reduce_position(
        session: Session,
        principal: AuthPrincipal,
        position_id: str,
        request: PositionReduce,
    ) -> Position:
        position = BusinessService._get_position_model(session, principal, position_id)
        if position.status not in ("open", "reduce"):
            raise ValueError("Position must be open or reduced before marking a trim")

        reduced_quantity = request.quantity
        if (
            reduced_quantity is not None
            and position.quantity is not None
            and reduced_quantity >= position.quantity
        ):
            raise ValueError("Reduced quantity must be smaller than current quantity; use close instead")

        realized_delta = _position_pnl(position.entry_price, request.exit_price, reduced_quantity)
        if realized_delta is not None:
            position.realized_pnl = round((position.realized_pnl or 0) + realized_delta, 6)
        if reduced_quantity is not None and position.quantity is not None:
            position.quantity = round(position.quantity - reduced_quantity, 6)
        if request.current_stop is not None:
            position.current_stop = request.current_stop
        position.current_r = _position_r_multiple(position, request.exit_price)
        position.status = "reduce"
        _touch_position(position)
        BusinessService._audit(session, principal, "position.reduce", "position", position_id)
        session.commit()
        session.refresh(position)
        return Position.model_validate(position)

    @staticmethod
    def close_position(
        session: Session,
        principal: AuthPrincipal,
        position_id: str,
        request: PositionClose,
    ) -> PositionCloseResponse:
        position = BusinessService._get_position_model(session, principal, position_id)
        if position.status == "closed":
            raise ValueError("Position is already closed")
        if position.status == "planned":
            raise ValueError("Planned positions must be activated before closing")
        if position.entry_price is None:
            raise ValueError("Position is missing entry price")
        if (
            request.quantity is not None
            and position.quantity is not None
            and request.quantity < position.quantity
        ):
            raise ValueError("Close quantity is smaller than current quantity; use reduce instead")

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
            gross_pnl=gross_pnl,
            net_pnl=gross_pnl,
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
        BusinessService._audit(session, principal, "position.close", "position", position_id)
        BusinessService._audit(session, principal, "journal_trade.create", "journal_trade", trade.trade_id)
        session.commit()
        session.refresh(position)
        session.refresh(trade)
        return PositionCloseResponse(
            position=Position.model_validate(position),
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

    @staticmethod
    def create_exit_alert(
        session: Session,
        principal: AuthPrincipal,
        request: ExitAlertCreate,
    ) -> ExitAlert:
        BusinessService._get_position_model(session, principal, request.position_id)
        alert = db.ExitAlert(
            alert_id=request.alert_id or f"alert_{uuid4().hex}",
            account_id=principal.account_id,
            position_id=request.position_id,
            level=request.level,
            action=request.action,
            reason=request.reason,
            new_stop=request.new_stop,
            triggered_rules=request.triggered_rules,
            acknowledged=request.acknowledged,
        )
        session.add(alert)
        BusinessService._audit(session, principal, "exit_alert.create", "exit_alert", alert.alert_id)
        session.commit()
        session.refresh(alert)
        return ExitAlert.model_validate(alert)

    @staticmethod
    def evaluate_exit_alerts(
        session: Session,
        principal: AuthPrincipal,
        request: ExitAlertEvaluationRequest,
    ) -> ExitAlertEvaluationResponse:
        statement = select(db.Position).where(
            db.Position.account_id == principal.account_id,
            db.Position.status.in_(("planned", "open", "reduce")),
        )
        if request.position_id:
            statement = statement.where(db.Position.position_id == request.position_id)
        statement = statement.order_by(db.Position.updated_at.desc())
        if request.limit is not None:
            statement = statement.limit(request.limit)

        positions = list(session.scalars(statement).all())
        if request.position_id and not positions:
            raise ValueError(f"Position not found: {request.position_id}")

        skipped_positions = 0
        duplicate_alerts = 0
        symbols: set[str] = set()
        created: list[db.ExitAlert] = []
        for position in positions:
            latest_bar = BusinessService._latest_bar(session, position.symbol_id)
            latest_fact = BusinessService._latest_fact(session, position.symbol_id)
            if latest_bar is None:
                skipped_positions += 1
                continue
            symbols.add(position.symbol_id)
            for spec in BusinessService._exit_alert_specs(position, latest_bar, latest_fact):
                alert_id = f"alert_{position.position_id}_{spec['rule']}_{latest_bar.ts.date().isoformat()}"
                if session.get(db.ExitAlert, alert_id) is not None:
                    duplicate_alerts += 1
                    continue
                alert = db.ExitAlert(
                    alert_id=alert_id,
                    account_id=principal.account_id,
                    position_id=position.position_id,
                    alert_ts=latest_bar.ts,
                    level=spec["level"],
                    action=spec["action"],
                    reason=spec["reason"],
                    new_stop=spec["new_stop"],
                    triggered_rules=spec["rule"],
                    acknowledged=False,
                )
                session.add(alert)
                created.append(alert)

        if positions:
            BusinessService._audit(
                session,
                principal,
                "exit_alert.evaluate",
                "exit_alert",
                request.position_id,
            )
        session.commit()
        for alert in created:
            session.refresh(alert)
        return ExitAlertEvaluationResponse(
            account_id=principal.account_id,
            positions_evaluated=len(positions),
            alerts_created=len(created),
            skipped_positions=skipped_positions,
            duplicate_alerts=duplicate_alerts,
            symbols_processed=sorted(symbols),
            alerts=[ExitAlert.model_validate(alert) for alert in created],
        )

    @staticmethod
    def _latest_bar(session: Session, symbol_id: str, timeframe: str = "1d") -> db.Bar | None:
        return session.scalar(
            select(db.Bar)
            .where(db.Bar.symbol_id == symbol_id, db.Bar.timeframe == timeframe)
            .order_by(db.Bar.ts.desc())
            .limit(1)
        )

    @staticmethod
    def _latest_fact(session: Session, symbol_id: str, timeframe: str = "1d") -> db.PAFact | None:
        return session.scalar(
            select(db.PAFact)
            .where(db.PAFact.symbol_id == symbol_id, db.PAFact.timeframe == timeframe)
            .order_by(db.PAFact.ts.desc())
            .limit(1)
        )

    @staticmethod
    def _exit_alert_specs(
        position: db.Position,
        latest_bar: db.Bar,
        latest_fact: db.PAFact | None,
    ) -> list[dict[str, object]]:
        close = latest_bar.close
        high = latest_bar.high
        if close is None:
            return []

        stop = position.current_stop or position.initial_stop
        if position.status == "planned":
            if position.entry_price is not None and high is not None and high >= position.entry_price:
                return [
                    {
                        "rule": "planned_entry_trigger_reached",
                        "level": 1,
                        "action": "review_entry",
                        "reason": "planned_entry_trigger_reached",
                        "new_stop": stop,
                    }
                ]
            return []

        specs: list[dict[str, object]] = []
        if stop is not None and close <= stop:
            specs.append(
                {
                    "rule": "daily_close_below_current_stop",
                    "level": 3,
                    "action": "exit",
                    "reason": "daily_close_below_current_stop",
                    "new_stop": stop,
                }
            )

        facts = latest_fact.facts if latest_fact else None
        sma_20 = _number_from_record(facts, "sma_20")
        sma_50 = _number_from_record(facts, "sma_50")
        if sma_20 is not None and sma_50 is not None and close < sma_20 and close < sma_50:
            specs.append(
                {
                    "rule": "close_below_20_50ma_support",
                    "level": 2,
                    "action": "review_exit",
                    "reason": "close_below_20_50ma_support",
                    "new_stop": stop,
                }
            )
        elif sma_50 is not None and close < sma_50:
            specs.append(
                {
                    "rule": "close_below_50ma",
                    "level": 2,
                    "action": "tighten_stop",
                    "reason": "close_below_50ma",
                    "new_stop": stop,
                }
            )
        elif sma_20 is not None and close < sma_20:
            specs.append(
                {
                    "rule": "close_below_20ma",
                    "level": 1,
                    "action": "watch_pullback",
                    "reason": "close_below_20ma",
                    "new_stop": stop,
                }
            )

        risk = position.entry_price - stop if position.entry_price is not None and stop is not None else None
        if risk is not None and risk > 0 and close >= position.entry_price + (2 * risk):
            specs.append(
                {
                    "rule": "first_trim_target_reached_2r",
                    "level": 1,
                    "action": "trim",
                    "reason": "first_trim_target_reached_2r",
                    "new_stop": max(stop, position.entry_price),
                }
            )
        return specs

    @staticmethod
    def list_exit_alerts(
        session: Session,
        principal: AuthPrincipal,
        acknowledged: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExitAlert]:
        statement = BusinessService._exit_alert_list_statement(
            principal=principal,
            acknowledged=acknowledged,
        )
        rows = session.scalars(
            statement.order_by(db.ExitAlert.alert_ts.desc()).offset(offset).limit(limit)
        ).all()
        return [ExitAlert.model_validate(row) for row in rows]

    @staticmethod
    def count_exit_alerts(
        session: Session,
        principal: AuthPrincipal,
        acknowledged: bool | None = None,
    ) -> int:
        statement = BusinessService._exit_alert_list_statement(
            principal=principal,
            acknowledged=acknowledged,
        )
        return session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def _exit_alert_list_statement(
        *,
        principal: AuthPrincipal,
        acknowledged: bool | None = None,
    ):
        statement = select(db.ExitAlert).where(db.ExitAlert.account_id == principal.account_id)
        if acknowledged is not None:
            statement = statement.where(db.ExitAlert.acknowledged == acknowledged)
        return statement

    @staticmethod
    def update_exit_alert(
        session: Session,
        principal: AuthPrincipal,
        alert_id: str,
        request: ExitAlertUpdate,
    ) -> ExitAlert:
        alert = BusinessService._get_exit_alert_model(session, principal, alert_id)
        payload = request.model_dump(exclude_unset=True)
        for key, value in payload.items():
            setattr(alert, key, value)
        if payload:
            BusinessService._audit(session, principal, "exit_alert.update", "exit_alert", alert_id)
            session.commit()
            session.refresh(alert)
        return ExitAlert.model_validate(alert)

    @staticmethod
    def _get_exit_alert_model(
        session: Session,
        principal: AuthPrincipal,
        alert_id: str,
    ) -> db.ExitAlert:
        alert = session.scalar(
            select(db.ExitAlert).where(
                db.ExitAlert.alert_id == alert_id,
                db.ExitAlert.account_id == principal.account_id,
            )
        )
        if alert is None:
            raise ValueError(f"Exit alert not found: {alert_id}")
        return alert

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
