from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import sessionmaker

from backend.app import models as db
from backend.app.core.database import Base
from backend.app.schemas.ingestion import ETFUniverseSeedRequest
from backend.app.services.etf_seed_service import ETFSeedService


class FakePolygonClient:
    def __init__(self):
        self.calls: list[str] = []

    def list_daily_bars(self, ticker, from_date, to_date):
        self.calls.append(ticker)
        if ticker == "EMPTY":
            return []
        start = datetime(2025, 8, 13, tzinfo=UTC)
        rows = []
        for index in range(260):
            close = 100 + (index * 0.8)
            rows.append(
                {
                    "t": int((start + timedelta(days=index)).timestamp() * 1000),
                    "o": close - 1,
                    "h": close + 0.2,
                    "l": close - 2,
                    "c": close,
                    "v": 1_000_000 + (index * 2_000),
                    "vw": close,
                }
            )
        return rows


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
        db_session.commit()
        yield db_session


def test_seed_us_etf_universe_populates_bars_facts_setups_and_candidates(session) -> None:
    response = ETFSeedService.seed_us_etf_universe_for_session(
        session=session,
        client=FakePolygonClient(),
        request=ETFUniverseSeedRequest(
            symbols=["SPY"],
            account_id="acct_local",
            min_score=60,
            **{"from": "2025-08-13", "to": "2026-04-30"},
        ),
    )
    session.commit()

    assert response.bars_written == 260
    assert response.facts_written == 260
    assert response.setups_written == 1
    assert response.candidates_written == 1
    assert response.candidates[0].symbol_id == "SPY"
    assert response.decision_counts == {"candidate": 1}
    assert response.latest_scan_date == response.candidates[0].scan_date
    assert response.latest_bar_date == response.candidates[0].scan_date

    bar_count = session.scalar(select(func.count()).select_from(db.Bar))
    fact_count = session.scalar(select(func.count()).select_from(db.PAFact))
    setup_count = session.scalar(select(func.count()).select_from(db.PASetup))
    candidate_count = session.scalar(select(func.count()).select_from(db.Candidate))

    assert bar_count == 260
    assert fact_count == 260
    assert setup_count == 1
    assert candidate_count == 1


def test_seed_us_etf_universe_records_empty_symbol_as_skipped(session) -> None:
    response = ETFSeedService.seed_us_etf_universe_for_session(
        session=session,
        client=FakePolygonClient(),
        request=ETFUniverseSeedRequest(
            symbols=["EMPTY"],
            account_id="acct_local",
            **{"from": "2025-08-13", "to": "2026-04-30"},
        ),
    )

    assert response.bars_written == 0
    assert response.skipped_symbols == ["EMPTY"]
    assert response.symbol_results[0].status == "failed"
    assert response.symbol_results[0].error_message == "Polygon returned no bars for EMPTY"


def test_seed_us_etf_universe_treats_explicit_empty_symbols_as_noop(session) -> None:
    client = FakePolygonClient()

    response = ETFSeedService.seed_us_etf_universe_for_session(
        session=session,
        client=client,
        request=ETFUniverseSeedRequest(
            symbols=[],
            account_id="acct_local",
            **{"from": "2025-08-13", "to": "2026-04-30"},
        ),
    )

    assert response.symbols_requested == []
    assert response.bars_written == 0
    assert response.facts_written == 0
    assert response.setups_written == 0
    assert response.candidates_written == 0
    assert response.symbol_results == []
    assert client.calls == []
