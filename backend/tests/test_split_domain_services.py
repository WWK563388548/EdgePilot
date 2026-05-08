from datetime import date

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.core.database import Base
from backend.app.schemas.business import (
    AccountRiskSettingsUpdate,
    AutomationJobRunRequest,
    NotificationEventUpdate,
    NotificationPreferencesUpdate,
)
from backend.app.services.business_service import BusinessService
from backend.app.services.job_run_service import JobRunService
from backend.app.services.notification_service import NotificationService
from backend.app.services.portfolio_risk_service import PortfolioRiskService
from backend.app.services.risk_settings_service import RiskSettingsService


def _principal() -> AuthPrincipal:
    return AuthPrincipal(
        user_id="user_a",
        account_id="acct_a",
        tenant_id="tenant_acct_a",
        role="owner",
        external_subject="user_a",
        email_verified=True,
    )


@pytest.fixture
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _register_sqlite_now(dbapi_connection, connection_record) -> None:
        dbapi_connection.create_function("now", 0, lambda: "2026-04-26 00:00:00")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with session_factory() as db_session:
        db_session.add(db.User(user_id="user_a", external_subject="user_a"))
        db_session.add(
            db.Tenant(
                tenant_id="tenant_acct_a",
                name="acct_a",
                owner_user_id="user_a",
            )
        )
        db_session.add(
            db.TenantMembership(
                tenant_id="tenant_acct_a",
                user_id="user_a",
                role="owner",
            )
        )
        db_session.add(db.Account(account_id="acct_a", tenant_id="tenant_acct_a", name="acct_a"))
        db_session.add(
            db.AccountMembership(account_id="acct_a", user_id="user_a", role="owner")
        )
        db_session.commit()
        yield db_session


def test_risk_settings_service_defaults_update_and_audits(session) -> None:
    principal = _principal()

    defaults = RiskSettingsService.get_account_risk_settings(session, principal)
    assert defaults.account_equity == 10_000
    assert defaults.max_risk_per_trade_pct == 0.005

    updated = RiskSettingsService.update_account_risk_settings(
        session,
        principal,
        AccountRiskSettingsUpdate(account_equity=25_000, max_open_positions=5),
    )

    assert updated.account_equity == 25_000
    assert updated.max_open_positions == 5
    audit = session.scalar(
        select(db.AuditLog).where(db.AuditLog.action == "risk_settings.update")
    )
    assert audit is not None
    assert audit.account_id == principal.account_id
    assert audit.tenant_id == principal.tenant_id


def test_portfolio_risk_service_summarizes_positions_and_preview(session) -> None:
    principal = _principal()
    session.add_all(
        [
            db.Position(
                position_id="pos_planned",
                account_id=principal.account_id,
                symbol_id="IWM",
                asset_type="etf",
                strategy_name="oneil_core_us_etf",
                entry_price=100,
                quantity=2,
                initial_stop=90,
                current_stop=90,
                status="planned",
            ),
            db.Position(
                position_id="pos_open",
                account_id=principal.account_id,
                symbol_id="SPY",
                asset_type="etf",
                strategy_name="oneil_core_us_etf",
                entry_price=200,
                quantity=1,
                initial_stop=190,
                current_stop=190,
                status="open",
            ),
            db.Position(
                position_id="pos_closed",
                account_id=principal.account_id,
                symbol_id="QQQ",
                asset_type="etf",
                strategy_name="oneil_core_us_etf",
                entry_price=300,
                quantity=10,
                initial_stop=250,
                current_stop=250,
                status="closed",
            ),
        ]
    )
    session.flush()

    summary = PortfolioRiskService.get_portfolio_risk(session, principal)

    assert summary.active_position_count == 2
    assert summary.total_risk_amount == 30
    assert summary.planned_risk_amount == 20
    assert summary.open_risk_amount == 10
    assert summary.highest_symbol_risk is not None
    assert summary.highest_symbol_risk.symbol_id == "IWM"

    candidate = db.Candidate(
        candidate_id="cand_preview",
        account_id=principal.account_id,
        symbol_id="SMH",
        scan_date=date(2026, 4, 26),
        strategy_name="oneil_core_us_etf",
    )
    preview = PortfolioRiskService.preview_portfolio_risk_item(
        candidate=candidate,
        entry_price=50,
        initial_stop=45,
        quantity=4,
        risk_settings=RiskSettingsService.get_account_risk_settings(session, principal),
    )

    assert preview.position_id == "plan_cand_preview"
    assert preview.risk_amount == 20
    assert preview.source == "preview"
    assert session.get(db.Position, preview.position_id) is None


def test_notification_service_creates_delivery_logs_and_deduplicates(session) -> None:
    principal = _principal()
    NotificationService.update_notification_preferences(
        session,
        principal,
        NotificationPreferencesUpdate(email_enabled=True, email_to="alerts@example.com"),
    )

    notification = NotificationService.create_notification_event(
        session,
        principal,
        event_type="exit_alert_created",
        severity="warning",
        source_type="exit_alert",
        source_id="alert_1",
        title="Exit alert",
        target_view="exit_alerts",
        target_id="alert_1",
    )
    duplicate = NotificationService.create_notification_event(
        session,
        principal,
        event_type="exit_alert_created",
        severity="warning",
        source_type="exit_alert",
        source_id="alert_1",
        title="Exit alert",
    )

    assert notification is not None
    assert duplicate is not None
    assert duplicate.notification_id == notification.notification_id
    session.flush()
    logs = session.scalars(
        select(db.NotificationDeliveryLog).where(
            db.NotificationDeliveryLog.notification_id == notification.notification_id
        )
    ).all()
    assert sorted(log.channel for log in logs) == ["email", "in_app"]
    assert NotificationService.count_notifications(session, principal, acknowledged=False) == 1
    assert NotificationService.list_notifications(session, principal)[0].notification_id == (
        notification.notification_id
    )

    updated = NotificationService.update_notification(
        session,
        principal,
        notification.notification_id,
        NotificationEventUpdate(acknowledged=True),
    )
    assert updated.acknowledged_at is not None
    assert updated.read_at is not None


def test_job_run_service_persists_failure_and_audit(session, monkeypatch) -> None:
    principal = _principal()

    def _fake_refresh(db_session, request_principal, request):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(BusinessService, "refresh_account_oneil_core_universe", _fake_refresh)

    run = JobRunService.run_automation_job(
        session,
        principal,
        AutomationJobRunRequest(
            symbols=["SPY"],
            recalculate_outcomes=False,
            evaluate_alerts=False,
        ),
    )

    assert run.status == "failed"
    assert run.error_message == "provider unavailable"
    assert run.metadata_json["steps"][0]["status"] == "failed"
    audit = session.scalar(select(db.AuditLog).where(db.AuditLog.action == "job.run"))
    assert audit is not None
    assert audit.entity_id == run.run_id
