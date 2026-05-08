from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

import pytest

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.core.database import Base
from backend.app.schemas.business import ExecutionCSVImportRequest
from backend.app.services.execution_import_service import ExecutionImportService


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
        dbapi_connection.create_function("now", 0, lambda: "2026-05-09 00:00:00")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with session_factory() as db_session:
        for user_id, account_id in (("user_a", "acct_a"), ("user_b", "acct_b")):
            tenant_id = f"tenant_{account_id}"
            db_session.add(db.User(user_id=user_id, external_subject=user_id))
            db_session.add(db.Tenant(tenant_id=tenant_id, name=tenant_id))
            db_session.add(
                db.TenantMembership(tenant_id=tenant_id, user_id=user_id, role="owner")
            )
            db_session.add(db.Account(account_id=account_id, tenant_id=tenant_id, name=account_id))
            db_session.add(
                db.AccountMembership(account_id=account_id, user_id=user_id, role="owner")
            )
        db_session.commit()
        yield db_session


def test_import_csv_is_idempotent_and_matches_planned_position(session) -> None:
    principal = _principal()
    session.add(
        db.Position(
            position_id="pos_spy",
            account_id=principal.account_id,
            symbol_id="SPY",
            asset_type="etf",
            strategy_name="oneil_core_us_etf",
            entry_price=421,
            quantity=3,
            initial_stop=400,
            current_stop=400,
            status="planned",
        )
    )
    session.commit()
    csv_text = "\n".join(
        [
            "executed_at,symbol,side,quantity,price,fees,position_id,execution_id",
            "2026-05-08T14:30:00+00:00,SPY,buy,10,425.50,1.25,pos_spy,exec_1",
        ]
    )

    result = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(csv_text=csv_text, source_filename="fills.csv"),
    )
    duplicate = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(csv_text=csv_text, source_filename="fills.csv"),
    )
    position = session.get(db.Position, "pos_spy")

    assert result.import_record.status == "completed"
    assert result.import_record.rows_imported == 1
    assert duplicate.import_record.rows_skipped == 1
    assert duplicate.fills == []
    assert ExecutionImportService.count_fills(session, principal) == 1
    assert position is not None
    assert position.status == "open"
    assert position.quantity == 10
    assert position.entry_price == 425.5


def test_import_csv_represents_partial_sell_and_close_flows(session) -> None:
    principal = _principal()
    session.add(
        db.Position(
            position_id="pos_iwm",
            account_id=principal.account_id,
            symbol_id="IWM",
            asset_type="etf",
            strategy_name="oneil_core_us_etf",
            entry_price=100,
            quantity=10,
            initial_stop=90,
            current_stop=90,
            status="open",
        )
    )
    session.commit()
    csv_text = "\n".join(
        [
            "executed_at,symbol,side,quantity,price,position_id,execution_id",
            "2026-05-08T15:00:00+00:00,IWM,sell,4,110,pos_iwm,exec_sell_1",
            "2026-05-09T15:00:00+00:00,IWM,sell,6,115,pos_iwm,exec_sell_2",
        ]
    )

    result = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(csv_text=csv_text),
    )
    position = session.get(db.Position, "pos_iwm")

    assert result.import_record.rows_imported == 2
    assert position is not None
    assert position.status == "closed"
    assert position.quantity == 0
    assert position.realized_pnl == 130


def test_import_csv_reports_malformed_rows_and_creates_review_needed_position(session) -> None:
    principal = _principal()
    csv_text = "\n".join(
        [
            "executed_at,symbol,side,quantity,price,execution_id",
            "2026-05-08T14:30:00+00:00,SMH,buy,2,150.25,exec_good",
            "2026-05-08T14:31:00+00:00,SMH,buy,2,,exec_bad",
        ]
    )

    result = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(csv_text=csv_text),
    )
    review_position = session.scalar(
        select(db.Position).where(
            db.Position.account_id == principal.account_id,
            db.Position.symbol_id == "SMH",
        )
    )

    assert result.import_record.status == "partial"
    assert result.import_record.rows_imported == 1
    assert result.import_record.rows_failed == 1
    assert result.errors[0].row_number == 3
    assert review_position is not None
    assert review_position.status == "review_needed"
    assert review_position.quantity == 2


def test_import_csv_does_not_link_cross_account_positions(session) -> None:
    principal_a = _principal("user_a", "acct_a")
    principal_b = _principal("user_b", "acct_b")
    session.add(
        db.Position(
            position_id="pos_other_account",
            account_id=principal_b.account_id,
            symbol_id="QQQ",
            asset_type="etf",
            strategy_name="oneil_core_us_etf",
            entry_price=300,
            quantity=1,
            initial_stop=280,
            current_stop=280,
            status="open",
        )
    )
    session.commit()
    csv_text = "\n".join(
        [
            "executed_at,symbol,side,quantity,price,position_id,execution_id",
            "2026-05-08T14:30:00+00:00,QQQ,buy,1,301,pos_other_account,exec_cross",
        ]
    )

    result = ExecutionImportService.import_csv(
        session,
        principal_a,
        ExecutionCSVImportRequest(csv_text=csv_text),
    )

    assert result.import_record.status == "failed"
    assert result.import_record.rows_failed == 1
    assert ExecutionImportService.count_fills(session, principal_a) == 0
    assert ExecutionImportService.count_fills(session, principal_b) == 0
