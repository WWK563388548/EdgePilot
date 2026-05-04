from datetime import UTC, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.schemas.outcome import ScannerOutcome

OUTCOME_HORIZONS = (5, 10, 20, 60)


class ScannerOutcomeService:
    @staticmethod
    def calculate_for_candidate(
        session: Session,
        candidate: db.Candidate,
    ) -> ScannerOutcome:
        setup = session.get(db.PASetup, candidate.pa_setup_id) if candidate.pa_setup_id else None
        detected_ts = (
            setup.detected_ts
            if setup is not None
            else datetime.combine(candidate.scan_date, time.min, tzinfo=UTC)
        )
        timeframe = setup.timeframe if setup is not None else "1d"
        reference_bar = ScannerOutcomeService._reference_bar(
            session=session,
            symbol_id=candidate.symbol_id,
            timeframe=timeframe,
            detected_ts=detected_ts,
        )
        future_bars = (
            ScannerOutcomeService._future_bars(
                session=session,
                symbol_id=candidate.symbol_id,
                timeframe=timeframe,
                reference_ts=reference_bar.ts,
            )
            if reference_bar is not None
            else []
        )
        payload = ScannerOutcomeService._outcome_payload(
            candidate=candidate,
            setup=setup,
            detected_ts=detected_ts,
            timeframe=timeframe,
            reference_bar=reference_bar,
            future_bars=future_bars,
        )
        outcome = session.get(db.ScannerOutcome, payload["outcome_id"])
        if outcome is None:
            outcome = db.ScannerOutcome(**payload)
            session.add(outcome)
        else:
            for key, value in payload.items():
                setattr(outcome, key, value)
        session.flush()
        return ScannerOutcome.model_validate(outcome)

    @staticmethod
    def calculate_by_candidate_id(
        session: Session,
        candidate_id: str,
    ) -> ScannerOutcome:
        candidate = session.get(db.Candidate, candidate_id)
        if candidate is None:
            raise ValueError(f"Candidate not found: {candidate_id}")
        return ScannerOutcomeService.calculate_for_candidate(session=session, candidate=candidate)

    @staticmethod
    def _reference_bar(
        *,
        session: Session,
        symbol_id: str,
        timeframe: str,
        detected_ts: datetime,
    ) -> db.Bar | None:
        return session.scalar(
            select(db.Bar)
            .where(
                db.Bar.symbol_id == symbol_id,
                db.Bar.timeframe == timeframe,
                db.Bar.ts <= detected_ts,
            )
            .order_by(db.Bar.ts.desc())
            .limit(1)
        )

    @staticmethod
    def _future_bars(
        *,
        session: Session,
        symbol_id: str,
        timeframe: str,
        reference_ts: datetime,
    ) -> list[db.Bar]:
        return list(
            session.scalars(
                select(db.Bar)
                .where(
                    db.Bar.symbol_id == symbol_id,
                    db.Bar.timeframe == timeframe,
                    db.Bar.ts > reference_ts,
                )
                .order_by(db.Bar.ts.asc())
                .limit(max(OUTCOME_HORIZONS))
            ).all()
        )

    @staticmethod
    def _outcome_payload(
        *,
        candidate: db.Candidate,
        setup: db.PASetup | None,
        detected_ts: datetime,
        timeframe: str,
        reference_bar: db.Bar | None,
        future_bars: list[db.Bar],
    ) -> dict:
        reference_close = _number(reference_bar.close) if reference_bar is not None else None
        bars_available = len(future_bars)
        entry_trigger = (
            candidate.entry_trigger
            if candidate.entry_trigger is not None
            else _plan_number(setup.entry_plan if setup else None, "trigger_price")
        )
        initial_stop = (
            candidate.initial_stop
            if candidate.initial_stop is not None
            else _plan_number(setup.exit_plan if setup else None, "initial_stop")
        )
        trigger_index = _first_index_at_or_above(future_bars, entry_trigger)
        trigger_bar = future_bars[trigger_index] if trigger_index is not None else None
        stop_index = (
            _first_index_at_or_below(future_bars[trigger_index:], initial_stop, offset=trigger_index)
            if trigger_index is not None
            else None
        )
        stop_before_trigger = (
            _first_index_at_or_below(future_bars[:trigger_index], initial_stop) is not None
            if trigger_index is not None
            else _first_index_at_or_below(future_bars, initial_stop) is not None
        )
        stop_bar = future_bars[stop_index] if stop_index is not None else None
        payload = {
            "outcome_id": f"outcome_{candidate.candidate_id}",
            "account_id": candidate.account_id,
            "candidate_id": candidate.candidate_id,
            "pa_setup_id": candidate.pa_setup_id,
            "symbol_id": candidate.symbol_id,
            "timeframe": timeframe,
            "detected_ts": detected_ts,
            "setup_type": setup.setup_type if setup is not None else candidate.setup_type,
            "setup_grade": setup.setup_grade if setup is not None else None,
            "score_total": (
                setup.pa_quality_score
                if setup is not None and setup.pa_quality_score is not None
                else candidate.score_total
            ),
            "reference_close": reference_close,
            "entry_trigger": entry_trigger,
            "initial_stop": initial_stop,
            "bars_available": bars_available,
            "evaluation_status": _evaluation_status(reference_bar, bars_available),
            "latest_evaluated_ts": future_bars[-1].ts if future_bars else None,
            "triggered_entry": trigger_bar is not None,
            "trigger_ts": trigger_bar.ts if trigger_bar is not None else None,
            "stopped_out": stop_bar is not None,
            "stop_ts": stop_bar.ts if stop_bar is not None else None,
            "stop_hit_before_trigger": stop_before_trigger,
            "false_breakout": bool(trigger_bar is not None and stop_bar is not None),
            "updated_at": datetime.now(UTC),
        }
        payload.update(_horizon_metrics(reference_close=reference_close, future_bars=future_bars))
        return payload


def _horizon_metrics(*, reference_close: float | None, future_bars: list[db.Bar]) -> dict[str, float | None]:
    metrics: dict[str, float | None] = {}
    for horizon in OUTCOME_HORIZONS:
        sample = future_bars[:horizon]
        suffix = f"{horizon}d"
        if reference_close is None or reference_close == 0 or len(sample) < horizon:
            metrics[f"forward_return_{suffix}"] = None
            metrics[f"mfe_{suffix}"] = None
            metrics[f"mae_{suffix}"] = None
            continue
        metrics[f"forward_return_{suffix}"] = _rounded_return(sample[-1].close, reference_close)
        highs = [_number(bar.high) for bar in sample if _number(bar.high) is not None]
        lows = [_number(bar.low) for bar in sample if _number(bar.low) is not None]
        metrics[f"mfe_{suffix}"] = _rounded_return(max(highs, default=None), reference_close)
        metrics[f"mae_{suffix}"] = _rounded_return(min(lows, default=None), reference_close)
    return metrics


def _evaluation_status(reference_bar: db.Bar | None, bars_available: int) -> str:
    if reference_bar is None:
        return "missing_reference"
    return "matured_60d" if bars_available >= max(OUTCOME_HORIZONS) else "pending"


def _first_index_at_or_above(bars: list[db.Bar], threshold: float | None, offset: int = 0) -> int | None:
    if threshold is None:
        return None
    for index, bar in enumerate(bars):
        high = _number(bar.high)
        if high is not None and high >= threshold:
            return index + offset
    return None


def _first_index_at_or_below(bars: list[db.Bar], threshold: float | None, offset: int = 0) -> int | None:
    if threshold is None:
        return None
    for index, bar in enumerate(bars):
        low = _number(bar.low)
        if low is not None and low <= threshold:
            return index + offset
    return None


def _plan_number(data: dict | None, key: str) -> float | None:
    value = (data or {}).get(key)
    return _number(value)


def _number(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _rounded_return(value: object, reference: float) -> float | None:
    numeric = _number(value)
    if numeric is None:
        return None
    return round((numeric / reference) - 1, 6)
