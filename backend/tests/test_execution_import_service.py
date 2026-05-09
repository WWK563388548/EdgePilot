from concurrent.futures import ThreadPoolExecutor
import os
from threading import Barrier

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

import pytest

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.core.database import Base
from backend.app.schemas.business import ExecutionCSVImportRequest, ExecutionFillReconcileRequest
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


@pytest.fixture
def disposable_postgres_session_factory():
    database_url = os.environ.get("EDGEPILOT_DISPOSABLE_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set EDGEPILOT_DISPOSABLE_TEST_DATABASE_URL to run Postgres concurrency tests.")
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        pytest.skip("Execution import concurrency coverage requires a disposable Postgres database.")

    sqlalchemy_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(sqlalchemy_url, pool_pre_ping=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    try:
        with session_factory() as db_session:
            principal = _principal()
            tenant_id = principal.tenant_id
            db_session.add(db.User(user_id=principal.user_id, external_subject=principal.user_id))
            db_session.add(db.Tenant(tenant_id=tenant_id, name=tenant_id))
            db_session.flush()
            db_session.add(
                db.TenantMembership(
                    tenant_id=tenant_id,
                    user_id=principal.user_id,
                    role="owner",
                )
            )
            db_session.add(
                db.Account(
                    account_id=principal.account_id,
                    tenant_id=tenant_id,
                    name=principal.account_id,
                )
            )
            db_session.flush()
            db_session.add(
                db.AccountMembership(
                    account_id=principal.account_id,
                    user_id=principal.user_id,
                    role="owner",
                )
            )
            db_session.add(
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
            db_session.flush()
            db_session.commit()
        yield session_factory
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


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


def test_import_csv_treats_unique_conflict_as_skipped(session, monkeypatch) -> None:
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

    ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(csv_text=csv_text, source_filename="fills.csv"),
    )
    monkeypatch.setattr(
        ExecutionImportService,
        "_fill_exists",
        staticmethod(lambda _session, _idempotency_key: False),
    )
    duplicate = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(csv_text=csv_text, source_filename="fills.csv"),
    )
    position = session.get(db.Position, "pos_spy")
    assert position is not None
    session.refresh(position)

    assert duplicate.import_record.status == "completed"
    assert duplicate.import_record.rows_imported == 0
    assert duplicate.import_record.rows_skipped == 1
    assert duplicate.fills == []
    assert ExecutionImportService.count_fills(session, principal) == 1
    assert position.quantity == 10
    assert position.entry_price == 425.5


def test_import_csv_concurrent_duplicate_uploads_are_idempotent(
    disposable_postgres_session_factory,
    monkeypatch,
) -> None:
    principal = _principal()
    csv_text = "\n".join(
        [
            "executed_at,symbol,side,quantity,price,fees,position_id,execution_id",
            "2026-05-08T14:30:00+00:00,SPY,buy,10,425.50,1.25,pos_spy,exec_1",
        ]
    )
    original_fill_exists = ExecutionImportService._fill_exists
    barrier = Barrier(2)

    def racing_fill_exists(db_session, idempotency_key: str) -> bool:
        exists = original_fill_exists(db_session, idempotency_key)
        barrier.wait(timeout=10)
        return exists

    monkeypatch.setattr(
        ExecutionImportService,
        "_fill_exists",
        staticmethod(racing_fill_exists),
    )

    def run_import():
        with disposable_postgres_session_factory() as db_session:
            return ExecutionImportService.import_csv(
                db_session,
                principal,
                ExecutionCSVImportRequest(csv_text=csv_text, source_filename="fills.csv"),
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: run_import(), range(2)))

    imported_counts = sorted(result.import_record.rows_imported for result in results)
    skipped_counts = sorted(result.import_record.rows_skipped for result in results)
    with disposable_postgres_session_factory() as db_session:
        position = db_session.get(db.Position, "pos_spy")
        fills_count = ExecutionImportService.count_fills(db_session, principal)

    assert imported_counts == [0, 1]
    assert skipped_counts == [0, 1]
    assert fills_count == 1
    assert position is not None
    assert position.quantity == 10
    assert position.entry_price == 425.5


def test_import_csv_deduplicates_reordered_rows_without_execution_ids(session) -> None:
    principal = _principal()
    csv_text = "\n".join(
        [
            "executed_at,symbol,side,quantity,price",
            "2026-05-08T14:30:00+00:00,SPY,buy,1,425.50",
            "2026-05-08T14:31:00+00:00,SPY,buy,2,426.50",
        ]
    )
    reordered_csv_text = "\n".join(
        [
            "executed_at,symbol,side,quantity,price",
            "2026-05-08T14:31:00+00:00,SPY,buy,2,426.50",
            "2026-05-08T14:30:00+00:00,SPY,buy,1,425.50",
        ]
    )

    result = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(csv_text=csv_text),
    )
    duplicate = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(csv_text=reordered_csv_text),
    )

    assert result.import_record.rows_imported == 2
    assert duplicate.import_record.rows_imported == 0
    assert duplicate.import_record.rows_skipped == 2
    assert ExecutionImportService.count_fills(session, principal) == 2


def test_import_csv_deduplicates_equivalent_timestamps_without_execution_ids(session) -> None:
    principal = _principal()
    utc_csv_text = "\n".join(
        [
            "executed_at,symbol,side,quantity,price",
            "2026-05-08T14:30:00Z,SPY,buy,1,425.50",
        ]
    )
    offset_csv_text = "\n".join(
        [
            "executed_at,symbol,side,quantity,price",
            "2026-05-08T10:30:00-04:00,SPY,buy,1,425.50",
        ]
    )

    result = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(csv_text=utc_csv_text),
    )
    duplicate = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(csv_text=offset_csv_text),
    )

    assert result.import_record.rows_imported == 1
    assert duplicate.import_record.rows_imported == 0
    assert duplicate.import_record.rows_skipped == 1
    assert ExecutionImportService.count_fills(session, principal) == 1


def test_import_csv_strips_utf8_bom_from_headers(session) -> None:
    principal = _principal()
    csv_text = "\n".join(
        [
            "\ufeffexecuted_at,symbol,side,quantity,price,execution_id",
            "2026-05-08T14:30:00+00:00,SPY,buy,1,425.50,exec_bom",
        ]
    )

    result = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(csv_text=csv_text),
    )

    assert result.import_record.status == "completed"
    assert result.import_record.rows_imported == 1
    assert result.errors == []
    assert ExecutionImportService.count_fills(session, principal) == 1


def test_import_csv_marks_ambiguous_symbol_only_match_for_review(session) -> None:
    principal = _principal()
    for index, quantity in enumerate((3, 5), start=1):
        session.add(
            db.Position(
                position_id=f"pos_spy_{index}",
                account_id=principal.account_id,
                symbol_id="SPY",
                asset_type="etf",
                strategy_name="oneil_core_us_etf",
                entry_price=420 + index,
                quantity=quantity,
                initial_stop=400,
                current_stop=400,
                status="open",
            )
        )
    session.commit()
    csv_text = "\n".join(
        [
            "executed_at,symbol,side,quantity,price,execution_id",
            "2026-05-08T14:30:00+00:00,SPY,buy,2,425.50,exec_ambiguous",
        ]
    )

    result = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(csv_text=csv_text),
    )
    original_positions = session.scalars(
        select(db.Position).where(db.Position.position_id.in_(("pos_spy_1", "pos_spy_2")))
    ).all()
    review_position = session.scalar(
        select(db.Position).where(
            db.Position.account_id == principal.account_id,
            db.Position.symbol_id == "SPY",
            db.Position.status == "review_needed",
        )
    )

    assert result.import_record.rows_imported == 1
    assert result.errors == []
    assert {position.position_id: position.quantity for position in original_positions} == {
        "pos_spy_1": 3,
        "pos_spy_2": 5,
    }
    assert review_position is not None
    assert review_position.quantity == 2
    assert result.fills[0].position_id == review_position.position_id


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


def test_import_csv_rejects_position_symbol_mismatch(session) -> None:
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
            "executed_at,symbol,side,quantity,price,position_id,execution_id",
            "2026-05-08T14:30:00+00:00,QQQ,buy,10,425.50,pos_spy,exec_wrong_symbol",
        ]
    )

    result = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(csv_text=csv_text),
    )
    position = session.get(db.Position, "pos_spy")

    assert result.import_record.status == "failed"
    assert result.import_record.rows_failed == 1
    assert "Position symbol mismatch" in result.errors[0].message
    assert ExecutionImportService.count_fills(session, principal) == 0
    assert position is not None
    assert position.status == "planned"
    assert position.quantity == 3


def test_reconcile_fill_confirms_review_needed_buy_as_standalone_position(session) -> None:
    principal = _principal()
    result = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(
            csv_text="\n".join(
                [
                    "executed_at,symbol,side,quantity,price,execution_id",
                    "2026-05-08T14:30:00+00:00,SMH,buy,2,150.25,exec_confirm",
                ]
            )
        ),
    )
    fill = result.fills[0]

    reconciled = ExecutionImportService.reconcile_fill(
        session,
        principal,
        fill.fill_id,
        ExecutionFillReconcileRequest(action="confirm_position", note="verified broker fill"),
    )
    position = session.get(db.Position, fill.position_id)

    assert reconciled.fill.reconciliation_status == "confirmed"
    assert reconciled.fill.status == "active"
    assert reconciled.fill.reconciliation_note == "verified broker fill"
    assert reconciled.target_position is not None
    assert reconciled.target_position.position_id == fill.position_id
    assert position is not None
    assert position.status == "open"
    assert position.quantity == 2
    assert position.entry_price == 150.25


def test_reconcile_fill_binds_review_needed_buy_to_planned_position(session) -> None:
    principal = _principal()
    result = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(
            csv_text="\n".join(
                [
                    "executed_at,symbol,side,quantity,price,execution_id",
                    "2026-05-08T14:30:00+00:00,SMH,buy,2,150.25,exec_bind",
                ]
            )
        ),
    )
    fill = result.fills[0]
    review_position_id = fill.position_id
    session.add(
        db.Position(
            position_id="pos_smh_plan",
            account_id=principal.account_id,
            symbol_id="SMH",
            asset_type="etf",
            strategy_name="oneil_core_us_etf",
            entry_price=149,
            quantity=3,
            initial_stop=140,
            current_stop=140,
            status="planned",
        )
    )
    session.commit()

    reconciled = ExecutionImportService.reconcile_fill(
        session,
        principal,
        fill.fill_id,
        ExecutionFillReconcileRequest(
            action="bind_position",
            target_position_id="pos_smh_plan",
        ),
    )
    target = session.get(db.Position, "pos_smh_plan")
    review_position = session.get(db.Position, review_position_id)

    assert reconciled.fill.position_id == "pos_smh_plan"
    assert reconciled.fill.reconciliation_status == "bound"
    assert target is not None
    assert target.status == "open"
    assert target.quantity == 2
    assert target.entry_price == 150.25
    assert review_position is not None
    assert review_position.status == "cancelled"
    assert review_position.quantity == 0


def test_reconcile_fill_ignores_review_needed_fill(session) -> None:
    principal = _principal()
    result = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(
            csv_text="\n".join(
                [
                    "executed_at,symbol,side,quantity,price,execution_id",
                    "2026-05-08T14:30:00+00:00,SMH,buy,2,150.25,exec_ignore",
                ]
            )
        ),
    )
    fill = result.fills[0]

    reconciled = ExecutionImportService.reconcile_fill(
        session,
        principal,
        fill.fill_id,
        ExecutionFillReconcileRequest(action="ignore_fill", note="duplicate broker export"),
    )
    position = session.get(db.Position, fill.position_id)

    assert reconciled.fill.status == "ignored"
    assert reconciled.fill.reconciliation_status == "ignored"
    assert reconciled.fill.reconciliation_note == "duplicate broker export"
    assert position is not None
    assert position.status == "cancelled"
    assert position.quantity == 0


def test_reconcile_fill_rejects_binding_to_mismatched_symbol(session) -> None:
    principal = _principal()
    session.add(
        db.Position(
            position_id="pos_qqq",
            account_id=principal.account_id,
            symbol_id="QQQ",
            asset_type="etf",
            strategy_name="oneil_core_us_etf",
            entry_price=420,
            quantity=1,
            initial_stop=400,
            current_stop=400,
            status="open",
        )
    )
    session.commit()
    result = ExecutionImportService.import_csv(
        session,
        principal,
        ExecutionCSVImportRequest(
            csv_text="\n".join(
                [
                    "executed_at,symbol,side,quantity,price,execution_id",
                    "2026-05-08T14:30:00+00:00,SMH,buy,2,150.25,exec_wrong_bind",
                ]
            )
        ),
    )

    with pytest.raises(ValueError, match="Target position symbol mismatch"):
        ExecutionImportService.reconcile_fill(
            session,
            principal,
            result.fills[0].fill_id,
            ExecutionFillReconcileRequest(
                action="bind_position",
                target_position_id="pos_qqq",
            ),
        )
