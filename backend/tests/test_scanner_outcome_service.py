from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app import models as db
from backend.app.core.database import Base
from backend.app.services.scanner_outcome_service import ScannerOutcomeService


@pytest.fixture
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _register_sqlite_now(dbapi_connection, connection_record) -> None:
        dbapi_connection.create_function("now", 0, lambda: "2026-05-04 00:00:00")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with session_factory() as db_session:
        db_session.add(db.Account(account_id="acct_local", name="Local Dev"))
        yield db_session


def test_calculate_scanner_outcome_for_matured_candidate(session) -> None:
    detected_ts = datetime(2026, 1, 1)
    _add_trending_outcome_bars(session, "SPY", detected_ts)
    _add_setup_and_candidate(session, symbol="SPY", detected_ts=detected_ts)

    outcome = ScannerOutcomeService.calculate_by_candidate_id(session, "cand_spy")

    assert outcome.evaluation_status == "matured_60d"
    assert outcome.bars_available == 60
    assert outcome.reference_close == 100
    assert outcome.triggered_entry is True
    assert outcome.stopped_out is False
    assert outcome.false_breakout is False
    assert outcome.stop_hit_before_trigger is False
    assert outcome.forward_return_5d == pytest.approx(0.05)
    assert outcome.forward_return_60d == pytest.approx(0.6)
    assert outcome.mfe_5d == pytest.approx(0.06)
    assert outcome.mae_5d == pytest.approx(0.0)


def test_calculate_scanner_outcome_marks_false_breakout_after_trigger_stop(session) -> None:
    detected_ts = datetime(2026, 1, 1)
    _add_false_breakout_bars(session, "QQQ", detected_ts)
    _add_setup_and_candidate(session, symbol="QQQ", detected_ts=detected_ts, candidate_id="cand_qqq")

    outcome = ScannerOutcomeService.calculate_by_candidate_id(session, "cand_qqq")

    assert outcome.triggered_entry is True
    assert outcome.stopped_out is True
    assert outcome.false_breakout is True
    assert outcome.trigger_ts == detected_ts + timedelta(days=1)
    assert outcome.stop_ts == detected_ts + timedelta(days=2)


def _add_setup_and_candidate(
    session,
    *,
    symbol: str,
    detected_ts: datetime,
    candidate_id: str = "cand_spy",
) -> None:
    setup_id = f"pasetup_{symbol.lower()}"
    session.add(
        db.PASetup(
            setup_id=setup_id,
            symbol_id=symbol,
            timeframe="1d",
            detected_ts=detected_ts,
            setup_type="breakout",
            setup_grade="A",
            pa_quality_score=82,
            entry_plan={"trigger_price": 105},
            exit_plan={"initial_stop": 95},
        )
    )
    session.add(
        db.Candidate(
            candidate_id=candidate_id,
            account_id="acct_local",
            symbol_id=symbol,
            scan_date=date(2026, 1, 1),
            strategy_name="oneil_core_us_etf",
            setup_type="breakout",
            pa_setup_id=setup_id,
            score_total=82,
            entry_trigger=105,
            initial_stop=95,
            decision="candidate",
        )
    )
    session.flush()


def _add_trending_outcome_bars(session, symbol: str, detected_ts: datetime) -> None:
    session.add(_bar(symbol=symbol, ts=detected_ts, close=100, high=101, low=99))
    for index in range(1, 61):
        session.add(
            _bar(
                symbol=symbol,
                ts=detected_ts + timedelta(days=index),
                close=100 + index,
                high=101 + index,
                low=99 + index,
            )
        )
    session.flush()


def _add_false_breakout_bars(session, symbol: str, detected_ts: datetime) -> None:
    session.add(_bar(symbol=symbol, ts=detected_ts, close=100, high=101, low=99))
    session.add(_bar(symbol=symbol, ts=detected_ts + timedelta(days=1), close=105, high=106, low=103))
    session.add(_bar(symbol=symbol, ts=detected_ts + timedelta(days=2), close=96, high=104, low=94))
    for index in range(3, 12):
        session.add(
            _bar(
                symbol=symbol,
                ts=detected_ts + timedelta(days=index),
                close=96 + index,
                high=97 + index,
                low=95 + index,
            )
        )
    session.flush()


def _bar(*, symbol: str, ts: datetime, close: float, high: float, low: float) -> db.Bar:
    return db.Bar(
        symbol_id=symbol,
        timeframe="1d",
        ts=ts,
        open=close - 1,
        high=high,
        low=low,
        close=close,
        volume=1_000_000,
        source="test",
    )
