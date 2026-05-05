from datetime import datetime, timedelta

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.app import models as db
from backend.app.core.database import Base
from backend.app.schemas.pa import StratScanRequest
from backend.app.services.strat_service import StratService


def _bar(*, symbol: str = "SPY", ts: datetime, open_: float, high: float, low: float, close: float):
    return db.Bar(
        symbol_id=symbol,
        timeframe="1d",
        ts=ts,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=1_000_000,
        source="test",
    )


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _register_sqlite_now(dbapi_connection, connection_record) -> None:
        dbapi_connection.create_function("now", 0, lambda: "2026-05-05 00:00:00")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return session_factory()


def test_calculate_signals_labels_bar_state_and_patterns() -> None:
    start = datetime(2026, 5, 1)
    bars = [
        _bar(ts=start, open_=100, high=105, low=95, close=104),
        _bar(ts=start + timedelta(days=1), open_=103, high=104, low=96, close=102),
        _bar(ts=start + timedelta(days=2), open_=103, high=106, low=99, close=105),
        _bar(ts=start + timedelta(days=3), open_=105, high=108, low=101, close=107),
    ]

    signals = StratService.calculate_signals(bars)

    assert [signal.bar_type for signal in signals] == ["1", "2U", "2U"]
    assert signals[0].pattern is None
    assert signals[1].pattern == "inside_breakout"
    assert signals[1].direction == "long"
    assert signals[1].trigger_price == 104
    assert signals[1].trigger_stop == 96
    assert signals[1].can_create_trade_alone is False
    assert signals[2].pattern == "2U_continuation"


def test_calculate_and_store_signals_is_idempotent() -> None:
    session = _session()
    start = datetime(2026, 5, 1)
    for offset, ohlc in enumerate(
        (
            (100, 105, 95, 104),
            (103, 104, 96, 102),
            (103, 106, 99, 105),
        )
    ):
        session.add(
            _bar(
                ts=start + timedelta(days=offset),
                open_=ohlc[0],
                high=ohlc[1],
                low=ohlc[2],
                close=ohlc[3],
            )
        )
    session.flush()

    first = StratService.calculate_and_store_signals(
        session=session,
        symbols=["SPY"],
        timeframe="1d",
    )
    second = StratService.calculate_and_store_signals(
        session=session,
        symbols=["SPY"],
        timeframe="1d",
    )

    assert first.signals_written == 2
    assert second.signals_written == 2
    assert len(StratService.list_signals(session, symbol="SPY")) == 2
    assert StratService.latest_signal(session, symbol="SPY").pattern == "inside_breakout"


def test_scan_treats_explicit_empty_symbols_as_noop(monkeypatch) -> None:
    session = _session()
    monkeypatch.setattr("backend.app.services.strat_service.SessionLocal", lambda: session)

    result = StratService.scan(StratScanRequest(symbols=[" "]))

    assert result.symbols_processed == []
    assert result.signals_written == 0
    assert result.skipped_symbols == []
