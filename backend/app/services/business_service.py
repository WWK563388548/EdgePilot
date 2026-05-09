from datetime import UTC, datetime
import json
import math
from typing import Any
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import func, or_, select
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
    ExitAlert,
    ExitAlertCreate,
    ExitAlertEvaluationRequest,
    ExitAlertEvaluationResponse,
    ExitAlertUpdate,
    JournalTrade,
    JournalTradeCreate,
    MarketContextSummary,
    PortfolioRiskSummary,
    GuardrailNotice,
)
from backend.app.schemas.scanner import ScannerDecision
from backend.app.services.audit_service import AuditService
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


def _number_from_record(data: dict | None, key: str) -> float | None:
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
            snoozed_until=request.snoozed_until,
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
            market_context = BusinessService._latest_market_context(session)
            if latest_bar is None:
                skipped_positions += 1
                continue
            symbols.add(position.symbol_id)
            for spec in BusinessService._exit_alert_specs(position, latest_bar, latest_fact, market_context):
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
                BusinessService._create_notification_event(
                    session,
                    principal,
                    event_type=BusinessService._exit_alert_notification_type(spec["rule"]),
                    severity=BusinessService._exit_alert_notification_severity(spec["rule"], spec["level"]),
                    source_type="exit_alert",
                    source_id=alert.alert_id,
                    title=BusinessService._exit_alert_notification_title(position, spec),
                    body=BusinessService._exit_alert_notification_body(position, spec),
                    target_view="alerts",
                    target_id=alert.alert_id,
                    metadata_json={
                        "alert_id": alert.alert_id,
                        "position_id": position.position_id,
                        "symbol_id": position.symbol_id,
                        "level": spec["level"],
                        "action": spec["action"],
                        "reason": spec["reason"],
                        "rule": spec["rule"],
                        "new_stop": spec["new_stop"],
                        "bar_ts": latest_bar.ts.isoformat() if latest_bar.ts else None,
                    },
                )

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
    def _exit_alert_notification_type(rule: object) -> str:
        if rule == "planned_entry_trigger_reached":
            return "position_entry_triggered"
        if rule == "daily_close_below_current_stop":
            return "position_hard_stop"
        if rule == "first_trim_target_reached_2r":
            return "position_trim_target"
        if rule == "move_stop_to_breakeven_after_1r":
            return "position_breakeven_stop"
        if rule == "trail_stop_to_20ma_after_profit":
            return "position_trailing_stop"
        if rule == "market_regime_risk_off":
            return "portfolio_risk_warning"
        return "position_exit_alert"

    @staticmethod
    def _exit_alert_notification_severity(rule: object, level: object) -> str:
        if rule in {"planned_entry_trigger_reached", "daily_close_below_current_stop"}:
            return "action_required"
        if rule in {"first_trim_target_reached_2r", "market_regime_risk_off"}:
            return "warning"
        numeric_level = level if isinstance(level, int) else 0
        if numeric_level >= 4:
            return "action_required"
        if numeric_level >= 2:
            return "warning"
        return "info"

    @staticmethod
    def _exit_alert_notification_title(position: db.Position, spec: dict[str, object]) -> str:
        rule = spec["rule"]
        if rule == "planned_entry_trigger_reached":
            return f"{position.symbol_id} entry trigger reached"
        if rule == "daily_close_below_current_stop":
            return f"{position.symbol_id} hard stop alert"
        if rule == "first_trim_target_reached_2r":
            return f"{position.symbol_id} reached 2R trim area"
        return f"{position.symbol_id} position alert"

    @staticmethod
    def _exit_alert_notification_body(position: db.Position, spec: dict[str, object]) -> str:
        rule = spec["rule"]
        if rule == "planned_entry_trigger_reached":
            return "Review the planned entry trigger and decide whether to enter."
        if rule == "daily_close_below_current_stop":
            return "Daily close is below the tracked stop. Review exit action."
        if rule == "first_trim_target_reached_2r":
            return "Price reached the first trim area. Review partial profit taking."
        if rule == "move_stop_to_breakeven_after_1r":
            return "Position reached 1R. Review moving stop to breakeven."
        if rule == "trail_stop_to_20ma_after_profit":
            return "Position is profitable. Review trailing stop near the 20MA."
        return "Review the latest position alert."

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
    def _latest_market_context(session: Session) -> db.MarketContextSnapshot | None:
        return session.scalar(
            select(db.MarketContextSnapshot)
            .order_by(db.MarketContextSnapshot.snapshot_ts.desc())
            .limit(1)
        )

    @staticmethod
    def _exit_alert_specs(
        position: db.Position,
        latest_bar: db.Bar,
        latest_fact: db.PAFact | None,
        market_context: db.MarketContextSnapshot | None,
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
                    "level": 4,
                    "action": "exit",
                    "reason": "daily_close_below_current_stop",
                    "new_stop": stop,
                }
            )

        facts = latest_fact.facts if latest_fact else None
        sma_20 = _number_from_record(facts, "sma_20")
        sma_50 = _number_from_record(facts, "sma_50")
        relative_volume = _number_from_record(facts, "relative_volume")
        current_r = BusinessService._position_r_from_close(position, close, stop)
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

        risk_stop = position.initial_stop or stop
        risk = position.entry_price - risk_stop if position.entry_price is not None and risk_stop is not None else None
        if (
            risk is not None
            and risk > 0
            and position.entry_price is not None
            and close >= position.entry_price + risk
            and close < position.entry_price + (2 * risk)
            and (stop is None or stop < position.entry_price)
        ):
            specs.append(
                {
                    "rule": "move_stop_to_breakeven_after_1r",
                    "level": 1,
                    "action": "tighten_stop",
                    "reason": "move_stop_to_breakeven_after_1r",
                    "new_stop": position.entry_price,
                }
            )
        if risk is not None and risk > 0 and position.entry_price is not None and close >= position.entry_price + (2 * risk):
            specs.append(
                {
                    "rule": "first_trim_target_reached_2r",
                    "level": 1,
                    "action": "trim",
                    "reason": "first_trim_target_reached_2r",
                    "new_stop": max(stop, position.entry_price),
                }
            )
        if (
            current_r is not None
            and current_r >= 2
            and sma_20 is not None
            and stop is not None
            and sma_20 > stop
            and close > sma_20
        ):
            specs.append(
                {
                    "rule": "trail_stop_to_20ma_after_profit",
                    "level": 1,
                    "action": "tighten_stop",
                    "reason": "trail_stop_to_20ma_after_profit",
                    "new_stop": round(max(stop, sma_20 * 0.98), 6),
                }
            )
        if (
            current_r is not None
            and current_r < 0.5
            and position.entry_date is not None
            and (BusinessService._days_since_entry(latest_bar, position) or 0) >= 20
        ):
            specs.append(
                {
                    "rule": "time_stop_no_progress_20d",
                    "level": 1,
                    "action": "review_exit",
                    "reason": "time_stop_no_progress_20d",
                    "new_stop": stop,
                }
            )
        if (
            position.entry_price is not None
            and position.entry_date is not None
            and (BusinessService._days_since_entry(latest_bar, position) or 9999) <= 10
            and close < position.entry_price
            and relative_volume is not None
            and relative_volume >= 1.2
        ):
            specs.append(
                {
                    "rule": "failed_breakout_heavy_volume",
                    "level": 2,
                    "action": "review_exit",
                    "reason": "failed_breakout_heavy_volume",
                    "new_stop": stop,
                }
            )
        if (
            market_context is not None
            and BusinessService._market_context_is_risk_off(market_context)
            and sma_20 is not None
            and close < sma_20
        ):
            specs.append(
                {
                    "rule": "market_regime_risk_off",
                    "level": 2,
                    "action": "review_exit",
                    "reason": "market_regime_risk_off",
                    "new_stop": stop,
                }
            )
        return specs

    @staticmethod
    def _position_r_from_close(
        position: db.Position,
        close: float,
        stop: float | None,
    ) -> float | None:
        risk_stop = position.initial_stop or stop
        if position.entry_price is None or risk_stop is None:
            return None
        risk = position.entry_price - risk_stop
        if risk <= 0:
            return None
        return round((close - position.entry_price) / risk, 6)

    @staticmethod
    def _days_since_entry(latest_bar: db.Bar, position: db.Position) -> int | None:
        if position.entry_date is None:
            return None
        bar_ts = latest_bar.ts
        entry_ts = position.entry_date
        if bar_ts.tzinfo is not None and entry_ts.tzinfo is None:
            entry_ts = entry_ts.replace(tzinfo=bar_ts.tzinfo)
        elif bar_ts.tzinfo is None and entry_ts.tzinfo is not None:
            entry_ts = entry_ts.replace(tzinfo=None)
        return (bar_ts - entry_ts).days

    @staticmethod
    def _market_context_is_risk_off(market_context: db.MarketContextSnapshot) -> bool:
        risk_level = (market_context.risk_level or "").lower()
        us_bias = (market_context.us_bias or "").lower()
        return risk_level in {"shock", "risk_off", "red"} or us_bias in {
            "bearish",
            "risk_off",
            "down",
        }

    @staticmethod
    def list_exit_alerts(
        session: Session,
        principal: AuthPrincipal,
        acknowledged: bool | None = None,
        include_snoozed: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExitAlert]:
        statement = BusinessService._exit_alert_list_statement(
            principal=principal,
            acknowledged=acknowledged,
            include_snoozed=include_snoozed,
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
        include_snoozed: bool = False,
    ) -> int:
        statement = BusinessService._exit_alert_list_statement(
            principal=principal,
            acknowledged=acknowledged,
            include_snoozed=include_snoozed,
        )
        return session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def _exit_alert_list_statement(
        *,
        principal: AuthPrincipal,
        acknowledged: bool | None = None,
        include_snoozed: bool = False,
    ):
        statement = select(db.ExitAlert).where(db.ExitAlert.account_id == principal.account_id)
        if acknowledged is not None:
            statement = statement.where(db.ExitAlert.acknowledged == acknowledged)
        if not include_snoozed:
            statement = statement.where(
                or_(
                    db.ExitAlert.snoozed_until.is_(None),
                    db.ExitAlert.snoozed_until <= datetime.now(UTC),
                )
            )
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
            if payload.get("acknowledged") is True:
                BusinessService._acknowledge_notifications_for_source(
                    session,
                    principal,
                    source_type="exit_alert",
                    source_id=alert.alert_id,
                )
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
