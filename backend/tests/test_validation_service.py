from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.core.database import Base
from backend.app.schemas.validation import (
    GoLiveGateEvaluateRequest,
    StrategyKillSwitchUpdate,
    TestRunCreate as ValidationTestRunCreate,
)
from backend.app.services.validation_service import ValidationService


def _principal(user_id: str = "user_a", account_id: str = "acct_a") -> AuthPrincipal:
    return AuthPrincipal(
        user_id=user_id,
        account_id=account_id,
        tenant_id=f"tenant_{account_id}",
        role="owner",
        external_subject=user_id,
        email_verified=True,
    )


@pytest.fixture
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _register_sqlite_now(dbapi_connection, connection_record) -> None:
        dbapi_connection.create_function("now", 0, lambda: "2026-05-20 00:00:00")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with session_factory() as db_session:
        for user_id, account_id in (("user_a", "acct_a"), ("user_b", "acct_b")):
            tenant_id = f"tenant_{account_id}"
            db_session.add(db.User(user_id=user_id, external_subject=user_id))
            db_session.add(db.Tenant(tenant_id=tenant_id, name=tenant_id))
            db_session.add(db.TenantMembership(tenant_id=tenant_id, user_id=user_id, role="owner"))
            db_session.add(db.Account(account_id=account_id, tenant_id=tenant_id, name=account_id))
            db_session.add(
                db.AccountMembership(account_id=account_id, user_id=user_id, role="owner")
            )
        db_session.commit()
        yield db_session


def test_evaluate_strategy_blocks_without_evidence(session) -> None:
    readiness = ValidationService.evaluate_strategy(
        session=session,
        principal=_principal(),
        strategy_name="etf_rotation_us_etf",
        request=GoLiveGateEvaluateRequest(),
    )

    assert readiness.gate.status == "blocked"
    assert readiness.gate.stage == "data_quality"
    assert readiness.gate.reasons == ["no_completed_test_run"]


def test_evaluate_strategy_shadow_only_for_small_sample(session) -> None:
    principal = _principal()
    ValidationService.create_test_run(
        session,
        principal,
        ValidationTestRunCreate(
            strategy_name="etf_rotation_us_etf",
            stage="shadow",
            trades_count=12,
            profit_factor=1.8,
            expectancy_r=0.3,
            max_drawdown_pct=-0.04,
            completed_at=datetime(2026, 5, 20, tzinfo=UTC),
        ),
    )

    readiness = ValidationService.evaluate_strategy(
        session=session,
        principal=principal,
        strategy_name="etf_rotation_us_etf",
        request=GoLiveGateEvaluateRequest(required_trades=30),
    )

    assert readiness.gate.status == "shadow_only"
    assert readiness.gate.stage == "shadow"
    assert readiness.gate.reasons == ["insufficient_sample"]


def test_evaluate_strategy_paper_only_after_minimum_evidence(session) -> None:
    principal = _principal()
    ValidationService.create_test_run(
        session,
        principal,
        ValidationTestRunCreate(
            strategy_name="etf_rotation_us_etf",
            stage="paper",
            trades_count=40,
            profit_factor=1.5,
            expectancy_r=0.2,
            max_drawdown_pct=-0.06,
            execution_drag_r=-0.05,
        ),
    )

    readiness = ValidationService.evaluate_strategy(
        session=session,
        principal=principal,
        strategy_name="etf_rotation_us_etf",
        request=GoLiveGateEvaluateRequest(required_trades=30),
    )

    assert readiness.gate.status == "paper_only"
    assert readiness.gate.stage == "paper"
    assert readiness.gate.reasons == ["needs_more_paper_evidence"]


def test_evaluate_strategy_allows_micro_live_after_mature_evidence(session) -> None:
    principal = _principal()
    ValidationService.create_test_run(
        session,
        principal,
        ValidationTestRunCreate(
            strategy_name="etf_rotation_us_etf",
            stage="paper",
            trades_count=80,
            profit_factor=1.6,
            expectancy_r=0.25,
            max_drawdown_pct=-0.05,
            execution_drag_r=-0.03,
        ),
    )

    readiness = ValidationService.evaluate_strategy(
        session=session,
        principal=principal,
        strategy_name="etf_rotation_us_etf",
        request=GoLiveGateEvaluateRequest(required_trades=30),
    )

    assert readiness.gate.status == "micro_live_allowed"
    assert readiness.gate.stage == "micro_live_allowed"
    assert readiness.gate.reasons == []


def test_evaluate_strategy_respects_kill_switch(session) -> None:
    principal = _principal()
    ValidationService.create_test_run(
        session,
        principal,
        ValidationTestRunCreate(
            strategy_name="etf_rotation_us_etf",
            trades_count=100,
            profit_factor=2,
            expectancy_r=0.4,
            max_drawdown_pct=-0.04,
        ),
    )
    ValidationService.update_kill_switch(
        session,
        principal,
        "etf_rotation_us_etf",
        StrategyKillSwitchUpdate(status="paused", reason="manual pause"),
    )

    readiness = ValidationService.evaluate_strategy(
        session=session,
        principal=principal,
        strategy_name="etf_rotation_us_etf",
        request=GoLiveGateEvaluateRequest(),
    )

    assert readiness.gate.status == "blocked"
    assert readiness.gate.reasons == ["strategy_kill_switch_active"]
    assert readiness.kill_switch is not None
    assert readiness.kill_switch.status == "paused"


def test_validation_records_are_account_scoped(session) -> None:
    principal_a = _principal("user_a", "acct_a")
    principal_b = _principal("user_b", "acct_b")
    ValidationService.create_test_run(
        session,
        principal_a,
        ValidationTestRunCreate(strategy_name="strategy_a", trades_count=60),
    )
    ValidationService.create_test_run(
        session,
        principal_b,
        ValidationTestRunCreate(strategy_name="strategy_b", trades_count=60),
    )

    assert [
        run.strategy_name for run in ValidationService.list_test_runs(session, principal_a)
    ] == ["strategy_a"]
    assert [
        run.strategy_name for run in ValidationService.list_test_runs(session, principal_b)
    ] == ["strategy_b"]
    assert session.scalar(select(db.GoLiveGate)) is None
