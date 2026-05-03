import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker

from backend.app import models as db
from backend.app.core.database import Base
from backend.app.schemas.pa import ETFOneilScannerRequest
from backend.app.services.scanner_service import ETFScannerService


@pytest.fixture
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _register_sqlite_now(dbapi_connection, connection_record) -> None:
        dbapi_connection.create_function("now", 0, lambda: "2026-04-30 00:00:00")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with session_factory() as db_session:
        db_session.add(db.Account(account_id="acct_local", name="Local Dev"))
        _add_trending_bars(db_session, "SPY")
        db_session.commit()
        yield db_session


def test_us_etf_oneil_core_scanner_generates_pa_setup_and_candidate(session) -> None:
    response = ETFScannerService.run_us_etf_oneil_core_for_session(
        session,
        ETFOneilScannerRequest(symbols=["SPY"], account_id="acct_local", min_score=60),
    )
    session.commit()

    assert response.facts_written == 260
    assert response.setups_written == 1
    assert response.candidates_written == 1
    assert response.candidates[0].strategy_name == "oneil_core_us_etf"
    assert response.candidates[0].decision == "candidate"
    assert response.candidates[0].pa_setup_id is not None
    assert response.decision_counts == {"candidate": 1}
    assert response.latest_scan_date == response.candidates[0].scan_date
    assert response.latest_bar_date == response.candidates[0].scan_date

    setup = session.scalar(select(db.PASetup).where(db.PASetup.symbol_id == "SPY"))
    candidate = session.scalar(select(db.Candidate).where(db.Candidate.account_id == "acct_local"))
    setup_count = session.scalar(
        select(func.count()).select_from(db.PASetup).where(db.PASetup.symbol_id == "SPY")
    )
    candidate_count = session.scalar(
        select(func.count()).select_from(db.Candidate).where(db.Candidate.account_id == "acct_local")
    )

    assert setup_count == 1
    assert candidate_count == 1
    assert setup is not None
    assert setup.entry_plan is not None
    assert setup.entry_plan["scanner_decision"]["decision"] == "candidate"
    assert setup.entry_plan["scanner_decision"]["passed_rules"]
    assert candidate is not None
    assert candidate.ai_review_json is not None
    assert json.loads(candidate.ai_review_json)["scanner_decision"]["upgrade_conditions"]


def test_us_etf_oneil_core_scanner_is_idempotent_for_same_scan_date(session) -> None:
    request = ETFOneilScannerRequest(symbols=["SPY"], account_id="acct_local", min_score=60)

    ETFScannerService.run_us_etf_oneil_core_for_session(session, request)
    ETFScannerService.run_us_etf_oneil_core_for_session(session, request)
    session.commit()

    candidate_count = session.scalar(
        select(func.count()).select_from(db.Candidate).where(db.Candidate.account_id == "acct_local")
    )

    assert candidate_count == 1


def test_us_etf_oneil_core_scanner_treats_explicit_empty_symbols_as_noop(session) -> None:
    response = ETFScannerService.run_us_etf_oneil_core_for_session(
        session,
        ETFOneilScannerRequest(symbols=[], account_id="acct_local", min_score=60),
    )

    assert response.symbols_scanned == []
    assert response.facts_written == 0
    assert response.setups_written == 0
    assert response.candidates_written == 0
    assert response.decision_counts == {}
    assert response.latest_scan_date is None
    assert response.latest_bar_date is None
    assert response.skipped_symbols == []

    candidate_count = session.scalar(
        select(func.count()).select_from(db.Candidate).where(db.Candidate.account_id == "acct_local")
    )
    assert candidate_count == 0


def _add_trending_bars(session, symbol: str) -> None:
    start = datetime(2025, 8, 13, tzinfo=UTC)
    for index in range(260):
        close = 100 + (index * 0.8)
        session.add(
            db.Bar(
                symbol_id=symbol,
                timeframe="1d",
                ts=start + timedelta(days=index),
                open=close - 1,
                high=close + 0.2,
                low=close - 2,
                close=close,
                volume=1_000_000 + (index * 2_000),
                adjusted=True,
                source="test",
            )
        )
