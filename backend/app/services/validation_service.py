from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from sqlalchemy import desc, distinct, func, select
from sqlalchemy.orm import Session

from backend.app.core.auth import AuthPrincipal
from backend.app import models as db
from backend.app.schemas.validation import (
    GoLiveGateEvaluateRequest,
    SignalFunnelSnapshotCreate,
    SimulatedTradeCreate,
    StrategyKillSwitch,
    StrategyKillSwitchUpdate,
    StrategyReadiness,
    TestRun,
    TestRunCreate,
)

DEFAULT_STRATEGIES = ("etf_rotation_us_etf", "oneil_core_us_etf")
DEFAULT_EVALUATION = GoLiveGateEvaluateRequest()


class ValidationService:
    @staticmethod
    def list_readiness(
        session: Session,
        principal: AuthPrincipal,
    ) -> list[StrategyReadiness]:
        return [
            ValidationService._build_readiness(
                session=session,
                principal=principal,
                strategy_name=strategy_name,
                request=DEFAULT_EVALUATION,
                persist=False,
            )
            for strategy_name in ValidationService._strategy_names(session, principal)
        ]

    @staticmethod
    def evaluate_strategy(
        session: Session,
        principal: AuthPrincipal,
        strategy_name: str,
        request: GoLiveGateEvaluateRequest,
    ) -> StrategyReadiness:
        ValidationService._build_readiness(
            session=session,
            principal=principal,
            strategy_name=strategy_name,
            request=request,
            persist=True,
        )
        session.commit()
        return ValidationService._build_readiness(
            session=session,
            principal=principal,
            strategy_name=strategy_name,
            request=request,
            persist=False,
        )

    @staticmethod
    def list_gates(
        session: Session,
        principal: AuthPrincipal,
        limit: int = 100,
        offset: int = 0,
    ) -> list[db.GoLiveGate]:
        return list(
            session.scalars(
                select(db.GoLiveGate)
                .where(db.GoLiveGate.account_id == principal.account_id)
                .order_by(desc(db.GoLiveGate.evaluated_at), db.GoLiveGate.strategy_name)
                .limit(limit)
                .offset(offset)
            )
        )

    @staticmethod
    def create_test_run(
        session: Session,
        principal: AuthPrincipal,
        request: TestRunCreate,
    ) -> db.TestRun:
        now = _now()
        test_run = db.TestRun(
            test_run_id=request.test_run_id or _random_id("test_run"),
            account_id=principal.account_id,
            strategy_name=_normalize_strategy_name(request.strategy_name),
            stage=request.stage,
            run_type=request.run_type,
            status=request.status,
            sample_count=request.sample_count,
            trades_count=request.trades_count,
            win_rate=request.win_rate,
            profit_factor=request.profit_factor,
            expectancy_r=request.expectancy_r,
            max_drawdown_pct=request.max_drawdown_pct,
            execution_drag_r=request.execution_drag_r,
            started_at=request.started_at or now,
            completed_at=request.completed_at
            or (now if request.status in {"succeeded", "failed"} else None),
            metadata_json=request.metadata_json,
            created_at=now,
            updated_at=now,
        )
        session.add(test_run)
        session.commit()
        session.refresh(test_run)
        return test_run

    @staticmethod
    def list_test_runs(
        session: Session,
        principal: AuthPrincipal,
        strategy_name: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[db.TestRun]:
        query = select(db.TestRun).where(db.TestRun.account_id == principal.account_id)
        if strategy_name:
            query = query.where(db.TestRun.strategy_name == _normalize_strategy_name(strategy_name))
        if status:
            query = query.where(db.TestRun.status == status)
        return list(
            session.scalars(
                query.order_by(desc(db.TestRun.completed_at), desc(db.TestRun.created_at))
                .limit(limit)
                .offset(offset)
            )
        )

    @staticmethod
    def count_test_runs(
        session: Session,
        principal: AuthPrincipal,
        strategy_name: str | None = None,
        status: str | None = None,
    ) -> int:
        query = (
            select(func.count())
            .select_from(db.TestRun)
            .where(db.TestRun.account_id == principal.account_id)
        )
        if strategy_name:
            query = query.where(db.TestRun.strategy_name == _normalize_strategy_name(strategy_name))
        if status:
            query = query.where(db.TestRun.status == status)
        return int(session.scalar(query) or 0)

    @staticmethod
    def create_simulated_trade(
        session: Session,
        principal: AuthPrincipal,
        request: SimulatedTradeCreate,
    ) -> db.SimulatedTrade:
        strategy_name = _normalize_strategy_name(request.strategy_name)
        if request.test_run_id:
            test_run = session.get(db.TestRun, request.test_run_id)
            if test_run is None or test_run.account_id != principal.account_id:
                raise ValueError("test_run_id does not exist for this account")
            strategy_name = test_run.strategy_name

        simulated_trade = db.SimulatedTrade(
            simulated_trade_id=request.simulated_trade_id or _random_id("sim_trade"),
            account_id=principal.account_id,
            test_run_id=request.test_run_id,
            strategy_name=strategy_name,
            symbol_id=request.symbol_id.strip().upper(),
            side=request.side,
            entry_ts=request.entry_ts,
            exit_ts=request.exit_ts,
            entry_price=request.entry_price,
            exit_price=request.exit_price,
            quantity=request.quantity,
            pnl=request.pnl,
            r_multiple=request.r_multiple,
            status=request.status,
            metadata_json=request.metadata_json,
            created_at=_now(),
        )
        session.add(simulated_trade)
        session.commit()
        session.refresh(simulated_trade)
        return simulated_trade

    @staticmethod
    def list_simulated_trades(
        session: Session,
        principal: AuthPrincipal,
        strategy_name: str | None = None,
        test_run_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[db.SimulatedTrade]:
        query = select(db.SimulatedTrade).where(
            db.SimulatedTrade.account_id == principal.account_id
        )
        if strategy_name:
            query = query.where(
                db.SimulatedTrade.strategy_name == _normalize_strategy_name(strategy_name)
            )
        if test_run_id:
            query = query.where(db.SimulatedTrade.test_run_id == test_run_id)
        return list(
            session.scalars(
                query.order_by(desc(db.SimulatedTrade.exit_ts), desc(db.SimulatedTrade.created_at))
                .limit(limit)
                .offset(offset)
            )
        )

    @staticmethod
    def create_funnel_snapshot(
        session: Session,
        principal: AuthPrincipal,
        request: SignalFunnelSnapshotCreate,
    ) -> db.SignalFunnelSnapshot:
        snapshot = db.SignalFunnelSnapshot(
            snapshot_id=request.snapshot_id or _random_id("funnel"),
            account_id=principal.account_id,
            strategy_name=_normalize_strategy_name(request.strategy_name),
            stage=request.stage,
            scan_date=request.scan_date,
            scanned_count=request.scanned_count,
            rejected_count=request.rejected_count,
            watch_count=request.watch_count,
            candidate_count=request.candidate_count,
            planned_count=request.planned_count,
            accepted_count=request.accepted_count,
            rejection_breakdown=request.rejection_breakdown,
            metadata_json=request.metadata_json,
            created_at=_now(),
        )
        session.add(snapshot)
        session.commit()
        session.refresh(snapshot)
        return snapshot

    @staticmethod
    def list_funnel_snapshots(
        session: Session,
        principal: AuthPrincipal,
        strategy_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[db.SignalFunnelSnapshot]:
        query = select(db.SignalFunnelSnapshot).where(
            db.SignalFunnelSnapshot.account_id == principal.account_id
        )
        if strategy_name:
            query = query.where(
                db.SignalFunnelSnapshot.strategy_name == _normalize_strategy_name(strategy_name)
            )
        return list(
            session.scalars(
                query.order_by(
                    desc(db.SignalFunnelSnapshot.scan_date),
                    desc(db.SignalFunnelSnapshot.created_at),
                )
                .limit(limit)
                .offset(offset)
            )
        )

    @staticmethod
    def update_kill_switch(
        session: Session,
        principal: AuthPrincipal,
        strategy_name: str,
        request: StrategyKillSwitchUpdate,
    ) -> db.StrategyKillSwitchStatus:
        strategy_name = _normalize_strategy_name(strategy_name)
        now = _now()
        kill_switch = session.scalar(
            select(db.StrategyKillSwitchStatus).where(
                db.StrategyKillSwitchStatus.account_id == principal.account_id,
                db.StrategyKillSwitchStatus.strategy_name == strategy_name,
            )
        )
        if kill_switch is None:
            kill_switch = db.StrategyKillSwitchStatus(
                account_id=principal.account_id,
                strategy_name=strategy_name,
            )
            session.add(kill_switch)

        kill_switch.status = request.status
        kill_switch.reason = request.reason
        kill_switch.expires_at = request.expires_at
        kill_switch.metadata_json = request.metadata_json
        kill_switch.updated_at = now
        if request.status == "active":
            kill_switch.paused_by_user_id = None
            kill_switch.paused_at = None
        else:
            kill_switch.paused_by_user_id = principal.user_id
            kill_switch.paused_at = now

        session.commit()
        session.refresh(kill_switch)
        return kill_switch

    @staticmethod
    def _build_readiness(
        session: Session,
        principal: AuthPrincipal,
        strategy_name: str,
        request: GoLiveGateEvaluateRequest,
        persist: bool,
    ) -> StrategyReadiness:
        strategy_name = _normalize_strategy_name(strategy_name)
        latest_test_run = _latest_test_run(session, principal, strategy_name)
        kill_switch = _kill_switch(session, principal, strategy_name)
        stage, status, reasons = _gate_decision(
            latest_test_run=latest_test_run,
            kill_switch=kill_switch,
            request=request,
        )
        now = _now()
        gate = _gate(session, principal, strategy_name) if persist else None
        if gate is None:
            gate = db.GoLiveGate(
                gate_id=_stable_gate_id(principal.account_id, strategy_name),
                account_id=principal.account_id,
                strategy_name=strategy_name,
                created_at=now,
            )
            if persist:
                session.add(gate)

        gate.stage = stage
        gate.status = status
        gate.required_trades = request.required_trades
        gate.min_profit_factor = request.min_profit_factor
        gate.min_expectancy_r = request.min_expectancy_r
        gate.max_drawdown_pct = request.max_drawdown_pct
        gate.max_execution_drag_r = request.max_execution_drag_r
        gate.current_trades = latest_test_run.trades_count if latest_test_run else None
        gate.current_profit_factor = latest_test_run.profit_factor if latest_test_run else None
        gate.current_expectancy_r = latest_test_run.expectancy_r if latest_test_run else None
        gate.current_max_drawdown_pct = (
            latest_test_run.max_drawdown_pct if latest_test_run else None
        )
        gate.current_execution_drag_r = (
            latest_test_run.execution_drag_r if latest_test_run else None
        )
        gate.reasons = reasons
        gate.evaluated_at = now
        gate.metadata_json = request.metadata_json
        gate.updated_at = now

        return StrategyReadiness(
            strategy_name=strategy_name,
            gate=gate,
            latest_test_run=TestRun.model_validate(latest_test_run) if latest_test_run else None,
            kill_switch=StrategyKillSwitch.model_validate(kill_switch) if kill_switch else None,
        )

    @staticmethod
    def _strategy_names(session: Session, principal: AuthPrincipal) -> list[str]:
        names = set(DEFAULT_STRATEGIES)
        sources = (
            (db.TestRun.strategy_name, db.TestRun.account_id),
            (db.GoLiveGate.strategy_name, db.GoLiveGate.account_id),
            (db.StrategyKillSwitchStatus.strategy_name, db.StrategyKillSwitchStatus.account_id),
            (db.Candidate.strategy_name, db.Candidate.account_id),
            (db.Position.strategy_name, db.Position.account_id),
        )
        for strategy_column, account_column in sources:
            for name in session.scalars(
                select(distinct(strategy_column)).where(
                    strategy_column.is_not(None),
                    account_column == principal.account_id,
                )
            ):
                if name:
                    names.add(name)
        return sorted(names)


def _gate_decision(
    latest_test_run: db.TestRun | None,
    kill_switch: db.StrategyKillSwitchStatus | None,
    request: GoLiveGateEvaluateRequest,
) -> tuple[str, str, list[str]]:
    if _kill_switch_blocks(kill_switch):
        return "data_quality", "blocked", ["strategy_kill_switch_active"]
    if latest_test_run is None:
        return "data_quality", "blocked", ["no_completed_test_run"]

    reasons: list[str] = []
    trades_count = latest_test_run.trades_count or 0
    if trades_count < request.required_trades:
        return "shadow", "shadow_only", ["insufficient_sample"]
    if latest_test_run.profit_factor is None:
        reasons.append("missing_profit_factor")
    elif latest_test_run.profit_factor < request.min_profit_factor:
        reasons.append("profit_factor_below_minimum")
    if latest_test_run.expectancy_r is None:
        reasons.append("missing_expectancy")
    elif latest_test_run.expectancy_r < request.min_expectancy_r:
        reasons.append("expectancy_below_minimum")
    if latest_test_run.max_drawdown_pct is None:
        reasons.append("missing_drawdown")
    elif abs(latest_test_run.max_drawdown_pct) > request.max_drawdown_pct:
        reasons.append("drawdown_above_limit")
    if (
        latest_test_run.execution_drag_r is not None
        and latest_test_run.execution_drag_r < -request.max_execution_drag_r
    ):
        reasons.append("execution_drag_above_limit")

    if reasons:
        return "backtest", "blocked", reasons
    if trades_count < request.required_trades * 2:
        return "paper", "paper_only", ["needs_more_paper_evidence"]
    return "micro_live_allowed", "micro_live_allowed", []


def _latest_test_run(
    session: Session,
    principal: AuthPrincipal,
    strategy_name: str,
) -> db.TestRun | None:
    return session.scalar(
        select(db.TestRun)
        .where(
            db.TestRun.account_id == principal.account_id,
            db.TestRun.strategy_name == strategy_name,
            db.TestRun.status == "succeeded",
        )
        .order_by(desc(db.TestRun.completed_at), desc(db.TestRun.created_at))
        .limit(1)
    )


def _gate(
    session: Session,
    principal: AuthPrincipal,
    strategy_name: str,
) -> db.GoLiveGate | None:
    return session.scalar(
        select(db.GoLiveGate).where(
            db.GoLiveGate.account_id == principal.account_id,
            db.GoLiveGate.strategy_name == strategy_name,
        )
    )


def _kill_switch(
    session: Session,
    principal: AuthPrincipal,
    strategy_name: str,
) -> db.StrategyKillSwitchStatus | None:
    return session.scalar(
        select(db.StrategyKillSwitchStatus).where(
            db.StrategyKillSwitchStatus.account_id == principal.account_id,
            db.StrategyKillSwitchStatus.strategy_name == strategy_name,
        )
    )


def _kill_switch_blocks(kill_switch: db.StrategyKillSwitchStatus | None) -> bool:
    if kill_switch is None or kill_switch.status not in {"paused", "blocked"}:
        return False
    return kill_switch.expires_at is None or kill_switch.expires_at > _now()


def _normalize_strategy_name(strategy_name: str) -> str:
    normalized = strategy_name.strip()
    if not normalized:
        raise ValueError("strategy_name is required")
    return normalized


def _random_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


def _stable_gate_id(account_id: str, strategy_name: str) -> str:
    digest = sha256(f"{account_id}:{strategy_name}".encode("utf-8")).hexdigest()[:20]
    return f"gate_{digest}"


def _now() -> datetime:
    return datetime.now(UTC)
