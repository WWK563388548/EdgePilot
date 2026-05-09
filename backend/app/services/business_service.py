from datetime import datetime
import json
import math
from typing import Any
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import (
    AccountRiskSettings,
    Candidate,
    CandidateCreate,
    CandidateDetail,
    CandidatePlanPreview,
    CandidatePASetup,
    CandidatePlanCreate,
    CandidateStratSignal,
    CandidateStratTriggerPlan,
    CandidateUpdate,
    DashboardSummary,
    DataFreshnessSummary,
    JournalTrade,
    JournalTradeCreate,
    MarketContextSummary,
    PortfolioRiskSummary,
    GuardrailNotice,
)
from backend.app.schemas.scanner import ScannerDecision
from backend.app.services.audit_service import AuditService
from backend.app.services.business.exit_alerts import BusinessExitAlertsMixin
from backend.app.services.business.jobs import BusinessJobsMixin
from backend.app.services.business.notifications import BusinessNotificationsMixin
from backend.app.services.business.positions import (
    BusinessPositionsMixin,
    _candidate_plan_position_id,
    _risk_amount,
    _risk_per_unit,
)
from backend.app.services.business.risk import BusinessRiskMixin
from backend.app.services.business.scanners import BusinessScannersMixin
from backend.app.services.strat_service import StratService


def _number_from_plan(data: dict | None, key: str) -> float | None:
    value = data.get(key) if data else None
    if isinstance(value, int | float):
        return float(value)
    return None


class BusinessService(
    BusinessNotificationsMixin,
    BusinessRiskMixin,
    BusinessJobsMixin,
    BusinessScannersMixin,
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
        if candidate.decision == "candidate":
            BusinessService._create_notification_event(
                session,
                principal,
                event_type="scanner_candidate_created",
                severity="info",
                source_type="candidate",
                source_id=candidate.candidate_id,
                title="New scanner candidate",
                body=f"{candidate.symbol_id} was added as a candidate.",
                target_view="candidates",
                target_id=candidate.candidate_id,
                metadata_json={
                    "candidate_id": candidate.candidate_id,
                    "symbol_id": candidate.symbol_id,
                    "decision": candidate.decision,
                    "score_total": candidate.score_total,
                },
            )
        BusinessService._audit(session, principal, "candidate.create", "candidate", candidate.candidate_id)
        session.commit()
        session.refresh(candidate)
        return BusinessService._candidate_response(session, candidate)

    @staticmethod
    def list_candidates(
        session: Session,
        principal: AuthPrincipal,
        decision: str | None = None,
        strategy_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Candidate]:
        statement = BusinessService._candidate_list_statement(
            principal=principal,
            decision=decision,
            strategy_name=strategy_name,
        )
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
        strategy_name: str | None = None,
    ) -> int:
        statement = BusinessService._candidate_list_statement(
            principal=principal,
            decision=decision,
            strategy_name=strategy_name,
        )
        return session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def _candidate_list_statement(
        *,
        principal: AuthPrincipal,
        decision: str | None = None,
        strategy_name: str | None = None,
    ):
        statement = select(db.Candidate).where(db.Candidate.account_id == principal.account_id)
        if decision:
            statement = statement.where(db.Candidate.decision == decision)
        if strategy_name:
            statement = statement.where(db.Candidate.strategy_name == strategy_name.strip())
        return statement

    @staticmethod
    def get_candidate_detail(
        session: Session,
        principal: AuthPrincipal,
        candidate_id: str,
    ) -> CandidateDetail:
        candidate = BusinessService._get_candidate_model(session, principal, candidate_id)
        pa_setup = BusinessService._candidate_pa_setup(session, candidate)
        entry_plan = pa_setup.entry_plan if pa_setup else None
        strat_signal = BusinessService._candidate_strat_signal(session, candidate, pa_setup)
        strat_plan = BusinessService._candidate_strat_plan(session, candidate, pa_setup)
        return CandidateDetail(
            candidate=BusinessService._candidate_response(session, candidate, pa_setup),
            pa_setup=CandidatePASetup.model_validate(pa_setup) if pa_setup else None,
            strat_signal=(
                CandidateStratSignal.model_validate(strat_signal) if strat_signal else None
            ),
            strat_plan=CandidateStratTriggerPlan.model_validate(strat_plan.to_payload()),
            score_breakdown=entry_plan.get("score_breakdown") if entry_plan else None,
            scanner_decision=BusinessService._candidate_scanner_decision(candidate, entry_plan),
            entry_plan=entry_plan,
            exit_plan=pa_setup.exit_plan if pa_setup else None,
            invalidation=pa_setup.invalidation if pa_setup else None,
        )

    @staticmethod
    def preview_candidate_plan(
        session: Session,
        principal: AuthPrincipal,
        candidate_id: str,
        request: CandidatePlanCreate | None = None,
    ) -> CandidatePlanPreview:
        candidate = BusinessService._get_candidate_model(session, principal, candidate_id)
        setup = BusinessService._candidate_pa_setup(session, candidate)
        entry_plan = setup.entry_plan if setup else None
        exit_plan = setup.exit_plan if setup else None
        request = request or CandidatePlanCreate()
        entry_price = (
            request.entry_price
            or BusinessService._candidate_plan_trigger(candidate, entry_plan)
            or _number_from_plan(entry_plan, "trigger_price")
        )
        initial_stop = (
            request.initial_stop
            or candidate.initial_stop
            or _number_from_plan(exit_plan, "initial_stop")
        )
        risk_settings = BusinessService.get_account_risk_settings(session, principal)
        max_risk_amount = round(
            risk_settings.account_equity * risk_settings.max_risk_per_trade_pct,
            6,
        )
        risk_per_unit = _risk_per_unit(entry_price, initial_stop)
        suggested_quantity = (
            math.floor(max_risk_amount / risk_per_unit)
            if risk_per_unit is not None and risk_per_unit > 0
            else None
        )
        planned_quantity = request.quantity or (
            suggested_quantity if suggested_quantity is not None and suggested_quantity > 0 else None
        )
        planned_risk_amount = _risk_amount(entry_price, initial_stop, planned_quantity)
        portfolio_before = BusinessService._portfolio_risk_summary(session, principal)
        existing_plan = session.scalar(
            select(db.Position).where(
                db.Position.position_id == _candidate_plan_position_id(candidate.candidate_id),
                db.Position.account_id == principal.account_id,
            )
        )
        preview_item = BusinessService._preview_portfolio_risk_item(
            candidate=candidate,
            entry_price=entry_price,
            initial_stop=initial_stop,
            quantity=planned_quantity,
            risk_settings=risk_settings,
        )
        portfolio_after_plan = BusinessService._portfolio_risk_summary(
            session,
            principal,
            extra_item=preview_item,
            exclude_position_id=existing_plan.position_id if existing_plan is not None else None,
        )
        risk_distance_pct = (
            round(risk_per_unit / entry_price, 6)
            if risk_per_unit is not None and entry_price is not None and entry_price > 0
            else None
        )
        validation_status = setup.validation_status if setup is not None else None
        guardrails = BusinessService._candidate_plan_guardrails(
            entry_price=entry_price,
            initial_stop=initial_stop,
            risk_distance_pct=risk_distance_pct,
            suggested_quantity=suggested_quantity,
            active_position_count=portfolio_before.active_position_count,
            portfolio_after_plan=portfolio_after_plan,
            validation_status=validation_status,
            risk_settings=risk_settings,
        )
        return CandidatePlanPreview(
            account_id=principal.account_id,
            candidate_id=candidate.candidate_id,
            entry_price=entry_price,
            initial_stop=initial_stop,
            risk_per_unit=risk_per_unit,
            risk_distance_pct=risk_distance_pct,
            account_equity=risk_settings.account_equity,
            max_risk_per_trade_pct=risk_settings.max_risk_per_trade_pct,
            max_risk_amount=max_risk_amount,
            suggested_quantity=suggested_quantity,
            planned_quantity=planned_quantity,
            planned_risk_amount=planned_risk_amount,
            planned_risk_pct=(
                round(planned_risk_amount / risk_settings.account_equity, 6)
                if planned_risk_amount is not None
                else None
            ),
            max_open_positions=risk_settings.max_open_positions,
            active_position_count=portfolio_before.active_position_count,
            portfolio_before=portfolio_before,
            portfolio_after_plan=portfolio_after_plan,
            validation_status=validation_status,
            guardrails=guardrails,
        )

    @staticmethod
    def _candidate_plan_guardrails(
        *,
        entry_price: float | None,
        initial_stop: float | None,
        risk_distance_pct: float | None,
        suggested_quantity: int | None,
        active_position_count: int,
        portfolio_after_plan: PortfolioRiskSummary,
        validation_status: str | None,
        risk_settings: AccountRiskSettings,
    ) -> list[GuardrailNotice]:
        guardrails: list[GuardrailNotice] = []
        if entry_price is None:
            guardrails.append(GuardrailNotice(level="block", code="missing_entry"))
        if initial_stop is None:
            guardrails.append(GuardrailNotice(level="block", code="missing_stop"))
        if entry_price is not None and initial_stop is not None and initial_stop >= entry_price:
            guardrails.append(GuardrailNotice(level="block", code="stop_not_below_entry"))
        if risk_distance_pct is not None and risk_distance_pct > risk_settings.max_risk_distance_pct:
            guardrails.append(GuardrailNotice(level="warning", code="risk_distance_wide"))
        if max(active_position_count, portfolio_after_plan.active_position_count) >= risk_settings.max_open_positions:
            guardrails.append(GuardrailNotice(level="warning", code="max_open_positions_reached"))
        if portfolio_after_plan.total_risk_pct > risk_settings.max_total_risk_pct:
            guardrails.append(GuardrailNotice(level="block", code="portfolio_risk_budget_exceeded"))
        if validation_status == "shadow_only" and risk_settings.shadow_only_requires_paper:
            guardrails.append(GuardrailNotice(level="info", code="shadow_only_paper_only"))
        if suggested_quantity is not None and suggested_quantity <= 0:
            guardrails.append(GuardrailNotice(level="warning", code="no_suggested_quantity"))
        return guardrails

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
    def _candidate_strat_signal(
        session: Session,
        candidate: db.Candidate,
        setup: db.PASetup | None,
    ) -> db.StratSignal | None:
        timeframe = setup.timeframe if setup is not None else "1d"
        reference_ts = setup.detected_ts if setup is not None else None
        return StratService.latest_signal_model(
            session=session,
            symbol=candidate.symbol_id,
            timeframe=timeframe,
            reference_ts=reference_ts,
        )

    @staticmethod
    def _candidate_strat_plan(
        session: Session,
        candidate: db.Candidate,
        setup: db.PASetup | None,
    ):
        timeframe = setup.timeframe if setup is not None else "1d"
        reference_ts = setup.detected_ts if setup is not None else None
        facts = BusinessService._latest_fact_payload(
            session,
            symbol=candidate.symbol_id,
            timeframe=timeframe,
            reference_ts=reference_ts,
        )
        return StratService.latest_trigger_plan(
            session=session,
            symbol=candidate.symbol_id,
            timeframe=timeframe,
            reference_ts=reference_ts,
            facts=facts,
        )

    @staticmethod
    def _latest_fact_payload(
        session: Session,
        *,
        symbol: str,
        timeframe: str,
        reference_ts: datetime | None = None,
    ) -> dict[str, Any] | None:
        statement = select(db.PAFact).where(
            db.PAFact.symbol_id == symbol,
            db.PAFact.timeframe == timeframe,
        )
        if reference_ts is not None:
            statement = statement.where(db.PAFact.ts <= reference_ts)
        fact = session.scalar(statement.order_by(db.PAFact.ts.desc()).limit(1))
        return fact.facts if fact is not None else None

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
    def _candidate_plan_trigger(candidate: db.Candidate, entry_plan: dict | None) -> float | None:
        scanner_decision = entry_plan.get("scanner_decision") if entry_plan else None
        strat_confirmation = (
            scanner_decision.get("strat_confirmation")
            if isinstance(scanner_decision, dict)
            else None
        )
        if isinstance(strat_confirmation, dict) and strat_confirmation.get("status") == "armed":
            trigger_price = _number_from_plan(strat_confirmation, "trigger_price")
            if trigger_price is not None:
                return trigger_price
        return candidate.entry_trigger

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
