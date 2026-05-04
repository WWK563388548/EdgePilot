from datetime import datetime, timedelta

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app import models as db
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


def test_explain_setup_returns_chart_evidence_and_levels() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _register_sqlite_now(dbapi_connection, connection_record) -> None:
        dbapi_connection.create_function("now", 0, lambda: "2026-04-30 00:00:00")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = session_factory()
    detected_ts = datetime(2026, 4, 30)

    for index in range(30):
        ts = detected_ts - timedelta(days=29 - index)
        close = 100 + index
        session.add(
            db.Bar(
                symbol_id="SPY",
                timeframe="1d",
                ts=ts,
                open=close - 1,
                high=close + 2,
                low=close - 3,
                close=close,
                volume=1_000_000 + index,
                source="test",
            )
        )
    session.add(
        db.PAFact(
            fact_id="pafact_spy_1d_2026-04-30",
            symbol_id="SPY",
            timeframe="1d",
            ts=detected_ts,
            facts={
                "close": 129,
                "sma_20": 118,
                "sma_50": 112,
                "above_sma_20": True,
                "above_sma_50": True,
                "relative_volume": 1.2,
                "pct_from_52w_high": -0.04,
            },
        )
    )
    session.add(
        db.PASetup(
            setup_id="pasetup_spy_1d_2026-04-30_breakout",
            symbol_id="SPY",
            timeframe="1d",
            detected_ts=detected_ts,
            setup_type="breakout",
            setup_grade="A",
            pa_quality_score=85,
            trend_rs_score=22,
            volume_score=10,
            entry_plan={
                "trigger_price": 131.13,
                "score_breakdown": {"total": 85, "trend": 25},
            },
            exit_plan={"initial_stop": 119.5},
            invalidation={"price_below": 119.5},
            validation_status="shadow_only",
            status="candidate",
        )
    )
    session.flush()

    assert PAService.count_setups(
        session,
        symbol="spy",
        timeframe="1d",
        validation_status="shadow_only",
    ) == 1

    explain = PAService.explain_setup(
        session,
        setup_id="pasetup_spy_1d_2026-04-30_breakout",
        bar_limit=20,
    )

    assert explain is not None
    assert explain.score_breakdown == {"total": 85, "trend": 25}
    assert len(explain.evidence.bars) == 20
    assert explain.evidence.bars[-1].sma_20 == 118
    assert explain.evidence.levels[0].key == "trigger_price"
    assert explain.evidence.latest_facts["relative_volume"] == 1.2
    assert any("shadow-only" in watchout for watchout in explain.watchouts)
