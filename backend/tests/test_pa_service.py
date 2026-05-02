from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base
from backend.app.schemas.pa import ETFUniverseFactsRequest
from backend.app.services.pa_service import PAService


def test_calculate_etf_daily_facts_treats_explicit_empty_symbols_as_noop(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = session_factory()
    monkeypatch.setattr("backend.app.services.pa_service.SessionLocal", lambda: session)

    result = PAService.calculate_etf_daily_facts(ETFUniverseFactsRequest(symbols=[" "]))

    assert result.symbols_processed == []
    assert result.facts_written == 0
    assert result.skipped_symbols == []
