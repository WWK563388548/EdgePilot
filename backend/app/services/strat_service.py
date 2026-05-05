from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.database import SessionLocal
from backend.app.schemas.pa import StratScanRequest, StratScanResponse, StratSignal
from backend.app.services.universes import default_symbols_when_omitted


@dataclass(frozen=True)
class CalculatedStratSignal:
    symbol_id: str
    timeframe: str
    ts: datetime
    bar_type: str
    previous_bar_type: str | None
    pattern: str | None
    direction: str | None
    trigger_price: float | None
    trigger_stop: float | None
    invalidation: str | None
    timeframe_continuity: dict[str, str]
    quality_score: float | None
    can_create_trade_alone: bool = False


class StratService:
    @staticmethod
    def list_signals(
        session: Session,
        *,
        symbol: str | None = None,
        timeframe: str | None = "1d",
        limit: int = 100,
        offset: int = 0,
    ) -> list[StratSignal]:
        statement = select(db.StratSignal)
        if symbol:
            statement = statement.where(db.StratSignal.symbol_id == symbol.upper())
        if timeframe:
            statement = statement.where(db.StratSignal.timeframe == timeframe)
        rows = session.scalars(
            statement.order_by(db.StratSignal.ts.desc()).offset(offset).limit(limit)
        ).all()
        return [StratSignal.model_validate(row) for row in rows]

    @staticmethod
    def latest_signal(
        session: Session,
        *,
        symbol: str,
        timeframe: str = "1d",
        reference_ts: datetime | None = None,
    ) -> StratSignal | None:
        signal = StratService.latest_signal_model(
            session=session,
            symbol=symbol,
            timeframe=timeframe,
            reference_ts=reference_ts,
        )
        return StratSignal.model_validate(signal) if signal is not None else None

    @staticmethod
    def latest_signal_model(
        session: Session,
        *,
        symbol: str,
        timeframe: str = "1d",
        reference_ts: datetime | None = None,
    ) -> db.StratSignal | None:
        statement = select(db.StratSignal).where(
            db.StratSignal.symbol_id == symbol.upper(),
            db.StratSignal.timeframe == timeframe,
        )
        if reference_ts is not None:
            statement = statement.where(db.StratSignal.ts <= reference_ts)
        signal = session.scalar(statement.order_by(db.StratSignal.ts.desc()).limit(1))
        if signal is not None or reference_ts is None:
            return signal
        return session.scalar(
            select(db.StratSignal)
            .where(
                db.StratSignal.symbol_id == symbol.upper(),
                db.StratSignal.timeframe == timeframe,
            )
            .order_by(db.StratSignal.ts.desc())
            .limit(1)
        )

    @staticmethod
    def scan(request: StratScanRequest) -> StratScanResponse:
        with SessionLocal() as session:
            response = StratService.calculate_and_store_signals(
                session=session,
                symbols=default_symbols_when_omitted(request.symbols),
                timeframe=request.timeframe,
            )
            session.commit()
            return response

    @staticmethod
    def calculate_and_store_signals(
        session: Session,
        *,
        symbols: list[str],
        timeframe: str,
    ) -> StratScanResponse:
        signals_written = 0
        symbols_processed: list[str] = []
        skipped_symbols: list[str] = []
        for symbol in _normalize_symbols(symbols):
            bars = session.scalars(
                select(db.Bar)
                .where(db.Bar.symbol_id == symbol, db.Bar.timeframe == timeframe)
                .order_by(db.Bar.ts.asc())
            ).all()
            if len(bars) < 2:
                skipped_symbols.append(symbol)
                continue
            calculated = StratService.calculate_signals(bars)
            for signal in calculated:
                StratService._upsert_signal(session, signal)
                signals_written += 1
            symbols_processed.append(symbol)
        session.flush()
        return StratScanResponse(
            timeframe=timeframe,
            symbols_processed=symbols_processed,
            signals_written=signals_written,
            skipped_symbols=skipped_symbols,
        )

    @staticmethod
    def calculate_signals(bars: list[db.Bar]) -> list[CalculatedStratSignal]:
        signals: list[CalculatedStratSignal] = []
        previous_bar_type: str | None = None
        previous: db.Bar | None = None
        previous_two_bar_type: str | None = None
        for bar in bars:
            if previous is None:
                previous = bar
                continue
            if not _has_ohlc(bar) or not _has_ohlc(previous):
                previous_two_bar_type = previous_bar_type
                previous = bar
                previous_bar_type = None
                continue
            bar_type = _bar_type(bar, previous)
            pattern, direction = _pattern(
                bar_type=bar_type,
                previous_bar_type=previous_bar_type,
                previous_two_bar_type=previous_two_bar_type,
            )
            trigger_price, trigger_stop = _trigger_levels(
                bar=bar,
                previous=previous,
                pattern=pattern,
                direction=direction,
            )
            signals.append(
                CalculatedStratSignal(
                    symbol_id=bar.symbol_id,
                    timeframe=bar.timeframe,
                    ts=bar.ts,
                    bar_type=bar_type,
                    previous_bar_type=previous_bar_type,
                    pattern=pattern,
                    direction=direction,
                    trigger_price=trigger_price,
                    trigger_stop=trigger_stop,
                    invalidation=_invalidation(direction),
                    timeframe_continuity={bar.timeframe: _continuity_state(bar)},
                    quality_score=_quality_score(pattern, direction),
                )
            )
            previous_two_bar_type = previous_bar_type
            previous = bar
            previous_bar_type = bar_type
        return signals

    @staticmethod
    def _upsert_signal(session: Session, signal: CalculatedStratSignal) -> None:
        signal_id = _signal_id(signal.symbol_id, signal.timeframe, signal.ts)
        existing = session.get(db.StratSignal, signal_id)
        payload = {
            "symbol_id": signal.symbol_id,
            "timeframe": signal.timeframe,
            "ts": signal.ts,
            "bar_type": signal.bar_type,
            "previous_bar_type": signal.previous_bar_type,
            "pattern": signal.pattern,
            "direction": signal.direction,
            "trigger_price": signal.trigger_price,
            "trigger_stop": signal.trigger_stop,
            "invalidation": signal.invalidation,
            "timeframe_continuity": signal.timeframe_continuity,
            "quality_score": signal.quality_score,
            "can_create_trade_alone": signal.can_create_trade_alone,
        }
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
            return
        session.add(db.StratSignal(signal_id=signal_id, **payload))


def _has_ohlc(bar: db.Bar) -> bool:
    return all(value is not None for value in (bar.open, bar.high, bar.low, bar.close))


def _bar_type(bar: db.Bar, previous: db.Bar) -> str:
    high = float(bar.high)
    low = float(bar.low)
    previous_high = float(previous.high)
    previous_low = float(previous.low)
    if high <= previous_high and low >= previous_low:
        return "1"
    if high > previous_high and low < previous_low:
        return "3"
    if high > previous_high and low >= previous_low:
        return "2U"
    return "2D"


def _pattern(
    *,
    bar_type: str,
    previous_bar_type: str | None,
    previous_two_bar_type: str | None,
) -> tuple[str | None, str | None]:
    if previous_bar_type == "1" and bar_type == "2U":
        if previous_two_bar_type == "2U":
            return "2-1-2_continuation", "long"
        return "inside_breakout", "long"
    if previous_bar_type == "1" and bar_type == "2D":
        if previous_two_bar_type == "2D":
            return "2-1-2_continuation", "short"
        return "inside_breakdown", "short"
    if previous_bar_type == "2U" and bar_type == "2U":
        return "2U_continuation", "long"
    if previous_bar_type == "2D" and bar_type == "2D":
        return "2D_continuation", "short"
    return None, None


def _trigger_levels(
    *,
    bar: db.Bar,
    previous: db.Bar,
    pattern: str | None,
    direction: str | None,
) -> tuple[float | None, float | None]:
    if pattern is None or direction is None:
        return None, None
    if direction == "long":
        return _round_price(previous.high), _round_price(previous.low)
    if direction == "short":
        return _round_price(previous.low), _round_price(previous.high)
    return None, None


def _invalidation(direction: str | None) -> str | None:
    if direction == "long":
        return "close_below_trigger_bar_low"
    if direction == "short":
        return "close_above_trigger_bar_high"
    return None


def _continuity_state(bar: db.Bar) -> str:
    if bar.close is None or bar.open is None:
        return "neutral"
    if bar.close > bar.open:
        return "bullish"
    if bar.close < bar.open:
        return "bearish"
    return "neutral"


def _quality_score(pattern: str | None, direction: str | None) -> float | None:
    if pattern is None or direction is None:
        return None
    if pattern in {"2-1-2_continuation", "2U_continuation", "2D_continuation"}:
        return 70.0
    return 60.0


def _round_price(value: float | None) -> float | None:
    return round(float(value), 4) if value is not None else None


def _normalize_symbols(symbols: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for symbol in symbols:
        ticker = symbol.strip().upper()
        if ticker and ticker not in seen:
            seen.add(ticker)
            normalized.append(ticker)
    return normalized


def _signal_id(symbol: str, timeframe: str, ts: datetime) -> str:
    return f"strat_{symbol.lower()}_{timeframe}_{ts.date().isoformat()}"
