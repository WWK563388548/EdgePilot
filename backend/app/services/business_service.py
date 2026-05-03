import json
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal, AuthService
from backend.app.schemas.business import (
    Candidate,
    CandidateCreate,
    CandidateDetail,
    CandidatePASetup,
    CandidateUpdate,
    DashboardSummary,
    DataFreshnessSummary,
    ExitAlert,
    ExitAlertCreate,
    ExitAlertUpdate,
    JournalTrade,
    JournalTradeCreate,
    MarketContextSummary,
    Position,
    PositionCreate,
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
from backend.app.services.etf_seed_service import ETFSeedService
from backend.app.services.scanner_service import ETFScannerService

ONEIL_CORE_US_ETF_STRATEGY = "oneil_core_us_etf"


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
        statement = select(db.Candidate).where(db.Candidate.account_id == principal.account_id)
        if decision:
            statement = statement.where(db.Candidate.decision == decision)

        rows = session.scalars(
            statement.order_by(db.Candidate.scan_date.desc(), db.Candidate.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return [BusinessService._candidate_response(session, row) for row in rows]

    @staticmethod
    def run_account_oneil_core_scanner(
        session: Session,
        principal: AuthPrincipal,
        request: AccountETFOneilScannerRequest,
    ) -> ETFOneilScannerResponse:
        session.execute(
            delete(db.Candidate).where(
                db.Candidate.account_id == principal.account_id,
                db.Candidate.strategy_name == ONEIL_CORE_US_ETF_STRATEGY,
            )
        )
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
        session.execute(
            delete(db.Candidate).where(
                db.Candidate.account_id == principal.account_id,
                db.Candidate.strategy_name == ONEIL_CORE_US_ETF_STRATEGY,
            )
        )
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
    ) -> dict | None:
        scanner_decision = entry_plan.get("scanner_decision") if entry_plan else None
        if isinstance(scanner_decision, dict):
            return scanner_decision
        if not candidate.ai_review_json:
            return None
        try:
            payload = json.loads(candidate.ai_review_json)
        except json.JSONDecodeError:
            return None
        scanner_decision = payload.get("scanner_decision")
        return scanner_decision if isinstance(scanner_decision, dict) else None

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
    def list_positions(
        session: Session,
        principal: AuthPrincipal,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Position]:
        statement = select(db.Position).where(db.Position.account_id == principal.account_id)
        if status:
            statement = statement.where(db.Position.status == status)
        rows = session.scalars(
            statement.order_by(db.Position.updated_at.desc()).offset(offset).limit(limit)
        ).all()
        return [Position.model_validate(row) for row in rows]

    @staticmethod
    def update_position(
        session: Session,
        principal: AuthPrincipal,
        position_id: str,
        request: PositionUpdate,
    ) -> Position:
        position = BusinessService._get_position_model(session, principal, position_id)
        payload = request.model_dump(exclude_unset=True)
        for key, value in payload.items():
            setattr(position, key, value)
        if payload:
            BusinessService._audit(session, principal, "position.update", "position", position_id)
            session.commit()
            session.refresh(position)
        return Position.model_validate(position)

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
    def list_exit_alerts(
        session: Session,
        principal: AuthPrincipal,
        acknowledged: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExitAlert]:
        statement = select(db.ExitAlert).where(db.ExitAlert.account_id == principal.account_id)
        if acknowledged is not None:
            statement = statement.where(db.ExitAlert.acknowledged == acknowledged)
        rows = session.scalars(
            statement.order_by(db.ExitAlert.alert_ts.desc()).offset(offset).limit(limit)
        ).all()
        return [ExitAlert.model_validate(row) for row in rows]

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
            select(db.TradeJournal)
            .where(db.TradeJournal.account_id == principal.account_id)
            .order_by(db.TradeJournal.entry_ts.desc().nulls_last())
            .offset(offset)
            .limit(limit)
        ).all()
        return [JournalTrade.model_validate(row) for row in rows]

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
                db.Position.status == "open",
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
