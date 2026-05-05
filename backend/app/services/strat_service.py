from dataclasses import dataclass
from datetime import datetime
from typing import Any

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


@dataclass(frozen=True)
class CalculatedStratTriggerPlan:
    symbol_id: str
    timeframe: str
    latest_bar_ts: datetime | None
    latest_bar_type: str | None
    previous_bar_type: str | None
    status: str
    pattern: str | None
    direction: str | None
    trigger_price: float | None
    trigger_stop: float | None
    order_type: str | None
    stop_limit_price: float | None
    max_entry_price: float | None
    risk_per_share: float | None
    risk_distance_pct: float | None
    atr_14: float | None
    distance_to_sma_20_pct: float | None
    consecutive_2u_count: int
    timeframe_continuity: dict[str, str]
    no_chase_rules: list[dict[str, Any]]
    can_create_trade_alone: bool = False

    def to_payload(self) -> dict[str, Any]:
        return {
            "symbol_id": self.symbol_id,
            "timeframe": self.timeframe,
            "latest_bar_ts": self.latest_bar_ts.isoformat() if self.latest_bar_ts else None,
            "latest_bar_type": self.latest_bar_type,
            "previous_bar_type": self.previous_bar_type,
            "status": self.status,
            "pattern": self.pattern,
            "direction": self.direction,
            "trigger_price": self.trigger_price,
            "trigger_stop": self.trigger_stop,
            "order_type": self.order_type,
            "stop_limit_price": self.stop_limit_price,
            "max_entry_price": self.max_entry_price,
            "risk_per_share": self.risk_per_share,
            "risk_distance_pct": self.risk_distance_pct,
            "atr_14": self.atr_14,
            "distance_to_sma_20_pct": self.distance_to_sma_20_pct,
            "consecutive_2u_count": self.consecutive_2u_count,
            "timeframe_continuity": self.timeframe_continuity,
            "no_chase_rules": self.no_chase_rules,
            "can_create_trade_alone": self.can_create_trade_alone,
        }


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
    def latest_trigger_plan(
        session: Session,
        *,
        symbol: str,
        timeframe: str = "1d",
        direction: str = "long",
        reference_ts: datetime | None = None,
        facts: dict[str, Any] | None = None,
    ) -> CalculatedStratTriggerPlan:
        statement = select(db.Bar).where(
            db.Bar.symbol_id == symbol.upper(),
            db.Bar.timeframe == timeframe,
        )
        if reference_ts is not None:
            statement = statement.where(db.Bar.ts <= reference_ts)
        bars = list(
            reversed(
                session.scalars(statement.order_by(db.Bar.ts.desc()).limit(40)).all()
            )
        )
        return StratService.calculate_trigger_plan(
            bars=bars,
            direction=direction,
            facts=facts,
        )

    @staticmethod
    def calculate_trigger_plan(
        *,
        bars: list[db.Bar],
        direction: str = "long",
        facts: dict[str, Any] | None = None,
    ) -> CalculatedStratTriggerPlan:
        if not bars:
            return _empty_trigger_plan(status="none", symbol_id="", timeframe="1d")
        latest = bars[-1]
        if len(bars) < 2 or not _has_ohlc(latest) or not _has_ohlc(bars[-2]):
            return _empty_trigger_plan(
                status="none",
                symbol_id=latest.symbol_id,
                timeframe=latest.timeframe,
                latest_bar_ts=latest.ts,
            )

        previous = bars[-2]
        latest_bar_type = _bar_type(latest, previous)
        previous_bar_type = (
            _bar_type(previous, bars[-3])
            if len(bars) >= 3 and _has_ohlc(previous) and _has_ohlc(bars[-3])
            else None
        )
        pattern = _pending_pattern(
            latest_bar_type=latest_bar_type,
            previous_bar_type=previous_bar_type,
            direction=direction,
        )
        continuity = {latest.timeframe: _continuity_state(latest)}
        if pattern is None:
            return CalculatedStratTriggerPlan(
                symbol_id=latest.symbol_id,
                timeframe=latest.timeframe,
                latest_bar_ts=latest.ts,
                latest_bar_type=latest_bar_type,
                previous_bar_type=previous_bar_type,
                status="bar_only",
                pattern=None,
                direction=None,
                trigger_price=None,
                trigger_stop=None,
                order_type=None,
                stop_limit_price=None,
                max_entry_price=None,
                risk_per_share=None,
                risk_distance_pct=None,
                atr_14=_average_true_range(bars),
                distance_to_sma_20_pct=_distance_to_sma_20(latest, facts),
                consecutive_2u_count=_consecutive_bar_count(bars, "2U"),
                timeframe_continuity=continuity,
                no_chase_rules=[],
            )

        trigger_price, trigger_stop = _pending_trigger_levels(
            latest=latest,
            direction=direction,
        )
        risk_per_share = (
            round(trigger_price - trigger_stop, 4)
            if direction == "long" and trigger_price is not None and trigger_stop is not None
            else None
        )
        risk_distance_pct = (
            round(risk_per_share / trigger_price, 6)
            if risk_per_share is not None and trigger_price is not None and trigger_price > 0
            else None
        )
        atr_14 = _average_true_range(bars)
        distance_to_sma_20_pct = _distance_to_sma_20(latest, facts)
        consecutive_2u_count = _consecutive_bar_count(bars, "2U")
        no_chase_rules = _no_chase_rules(
            bars=bars,
            latest_bar_type=latest_bar_type,
            pattern=pattern,
            trigger_price=trigger_price,
            risk_distance_pct=risk_distance_pct,
            risk_per_share=risk_per_share,
            atr_14=atr_14,
            distance_to_sma_20_pct=distance_to_sma_20_pct,
            consecutive_2u_count=consecutive_2u_count,
            facts=facts,
        )
        stop_limit_price = _stop_limit_price(
            trigger_price=trigger_price,
            risk_per_share=risk_per_share,
            atr_14=atr_14,
        )
        status = "blocked" if any(rule.get("level") == "block" for rule in no_chase_rules) else "armed"
        return CalculatedStratTriggerPlan(
            symbol_id=latest.symbol_id,
            timeframe=latest.timeframe,
            latest_bar_ts=latest.ts,
            latest_bar_type=latest_bar_type,
            previous_bar_type=previous_bar_type,
            status=status,
            pattern=pattern,
            direction=direction,
            trigger_price=trigger_price,
            trigger_stop=trigger_stop,
            order_type="buy_stop_limit" if direction == "long" else "sell_stop_limit",
            stop_limit_price=stop_limit_price,
            max_entry_price=stop_limit_price,
            risk_per_share=risk_per_share,
            risk_distance_pct=risk_distance_pct,
            atr_14=atr_14,
            distance_to_sma_20_pct=distance_to_sma_20_pct,
            consecutive_2u_count=consecutive_2u_count,
            timeframe_continuity=continuity,
            no_chase_rules=no_chase_rules,
        )

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


def _pending_pattern(
    *,
    latest_bar_type: str,
    previous_bar_type: str | None,
    direction: str,
) -> str | None:
    if direction == "long":
        if latest_bar_type == "1":
            return "2-1-2_continuation" if previous_bar_type == "2U" else "inside_breakout"
        if latest_bar_type == "2U":
            return "2U_continuation"
    if direction == "short":
        if latest_bar_type == "1":
            return "2-1-2_continuation" if previous_bar_type == "2D" else "inside_breakdown"
        if latest_bar_type == "2D":
            return "2D_continuation"
    return None


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


def _pending_trigger_levels(
    *,
    latest: db.Bar,
    direction: str,
) -> tuple[float | None, float | None]:
    if direction == "long":
        return _round_price(float(latest.high) + _tick_size(float(latest.high))), _round_price(latest.low)
    if direction == "short":
        return _round_price(float(latest.low) - _tick_size(float(latest.low))), _round_price(latest.high)
    return None, None


def _invalidation(direction: str | None) -> str | None:
    if direction == "long":
        return "close_below_trigger_bar_low"
    if direction == "short":
        return "close_above_trigger_bar_high"
    return None


def _empty_trigger_plan(
    *,
    status: str,
    symbol_id: str,
    timeframe: str,
    latest_bar_ts: datetime | None = None,
) -> CalculatedStratTriggerPlan:
    return CalculatedStratTriggerPlan(
        symbol_id=symbol_id,
        timeframe=timeframe,
        latest_bar_ts=latest_bar_ts,
        latest_bar_type=None,
        previous_bar_type=None,
        status=status,
        pattern=None,
        direction=None,
        trigger_price=None,
        trigger_stop=None,
        order_type=None,
        stop_limit_price=None,
        max_entry_price=None,
        risk_per_share=None,
        risk_distance_pct=None,
        atr_14=None,
        distance_to_sma_20_pct=None,
        consecutive_2u_count=0,
        timeframe_continuity={},
        no_chase_rules=[],
    )


def _continuity_state(bar: db.Bar) -> str:
    if bar.close is None or bar.open is None:
        return "neutral"
    if bar.close > bar.open:
        return "bullish"
    if bar.close < bar.open:
        return "bearish"
    return "neutral"


def _average_true_range(bars: list[db.Bar], period: int = 14) -> float | None:
    if len(bars) < 2:
        return None
    true_ranges: list[float] = []
    previous_close: float | None = None
    for bar in bars:
        if not _has_ohlc(bar):
            previous_close = float(bar.close) if bar.close is not None else previous_close
            continue
        high = float(bar.high)
        low = float(bar.low)
        if previous_close is None:
            true_range = high - low
        else:
            true_range = max(high - low, abs(high - previous_close), abs(low - previous_close))
        true_ranges.append(true_range)
        previous_close = float(bar.close)
    sample = true_ranges[-period:]
    if not sample:
        return None
    return _round_price(sum(sample) / len(sample))


def _distance_to_sma_20(bar: db.Bar, facts: dict[str, Any] | None) -> float | None:
    value = _number_from_mapping(facts, "distance_to_sma_20_pct")
    if value is not None:
        return round(value, 6)
    sma_20 = _number_from_mapping(facts, "sma_20")
    if sma_20 is None or bar.close is None or sma_20 == 0:
        return None
    return round((float(bar.close) - sma_20) / sma_20, 6)


def _consecutive_bar_count(bars: list[db.Bar], target_bar_type: str) -> int:
    count = 0
    for index in range(len(bars) - 1, 0, -1):
        current = bars[index]
        previous = bars[index - 1]
        if not _has_ohlc(current) or not _has_ohlc(previous):
            break
        if _bar_type(current, previous) != target_bar_type:
            break
        count += 1
    return count


def _no_chase_rules(
    *,
    bars: list[db.Bar],
    latest_bar_type: str,
    pattern: str,
    trigger_price: float | None,
    risk_distance_pct: float | None,
    risk_per_share: float | None,
    atr_14: float | None,
    distance_to_sma_20_pct: float | None,
    consecutive_2u_count: int,
    facts: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    if risk_distance_pct is not None and risk_distance_pct > 0.12:
        rules.append(_guard("block", "strat_risk_too_wide", value=risk_distance_pct, threshold=0.12))
    if distance_to_sma_20_pct is not None and distance_to_sma_20_pct > 0.08:
        rules.append(
            _guard("block", "strat_overextended_from_20ma", value=distance_to_sma_20_pct, threshold=0.08)
        )
    sma_20 = _number_from_mapping(facts, "sma_20")
    if (
        trigger_price is not None
        and sma_20 is not None
        and atr_14 is not None
        and trigger_price - sma_20 > atr_14 * 2
    ):
        rules.append(
            _guard(
                "block",
                "strat_atr_extension",
                value=round((trigger_price - sma_20) / atr_14, 4),
                threshold=2.0,
            )
        )
    if latest_bar_type == "2U" and consecutive_2u_count >= 3:
        rules.append(
            _guard("block", "strat_consecutive_2u_no_chase", value=consecutive_2u_count, threshold=3)
        )
    mother_bar = bars[-2] if len(bars) >= 2 and pattern in {"inside_breakout", "2-1-2_continuation"} else None
    if mother_bar is not None and _has_ohlc(mother_bar):
        mother_range = float(mother_bar.high) - float(mother_bar.low)
        mother_range_pct = mother_range / float(mother_bar.close) if mother_bar.close else None
        if mother_range_pct is not None and mother_range_pct > 0.08:
            rules.append(
                _guard("block", "strat_wide_mother_bar", value=mother_range_pct, threshold=0.08)
            )
        elif mother_range_pct is not None and mother_range_pct > 0.06:
            rules.append(
                _guard("warning", "strat_wide_mother_bar", value=mother_range_pct, threshold=0.06)
            )
        if atr_14 is not None and mother_range > atr_14 * 2:
            rules.append(
                _guard(
                    "block",
                    "strat_mother_bar_exceeds_atr",
                    value=round(mother_range / atr_14, 4),
                    threshold=2.0,
                )
            )
    stop_limit_price = _stop_limit_price(
        trigger_price=trigger_price,
        risk_per_share=risk_per_share,
        atr_14=atr_14,
    )
    if stop_limit_price is not None:
        rules.append(
            _guard(
                "info",
                "strat_gap_no_chase_limit",
                value=stop_limit_price,
                threshold=stop_limit_price,
            )
        )
    return rules


def _stop_limit_price(
    *,
    trigger_price: float | None,
    risk_per_share: float | None,
    atr_14: float | None,
) -> float | None:
    if trigger_price is None:
        return None
    buffers = []
    if risk_per_share is not None and risk_per_share > 0:
        buffers.append(risk_per_share * 0.5)
    if atr_14 is not None and atr_14 > 0:
        buffers.append(atr_14 * 0.75)
    if not buffers:
        buffers.append(trigger_price * 0.005)
    return _round_price(trigger_price + min(buffers))


def _guard(level: str, code: str, *, value: float | int, threshold: float | int) -> dict[str, Any]:
    return {
        "level": level,
        "code": code,
        "value": value,
        "threshold": threshold,
    }


def _number_from_mapping(data: dict[str, Any] | None, key: str) -> float | None:
    if not data:
        return None
    value = data.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _tick_size(value: float) -> float:
    return 0.01 if value >= 1 else 0.0001


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
