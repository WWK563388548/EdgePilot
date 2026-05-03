from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.database import SessionLocal
from backend.app.schemas.pa import (
    ETFUniverseFactsRequest,
    PACalibrationStat,
    PAEvidenceBar,
    PAEvidenceLevel,
    PAFact,
    PAFactsCalculationResponse,
    PASetupEvidence,
    PASetupExplain,
    PAStructure,
    PASetup,
)
from backend.app.services.pa_calculator import CalculatedPAFact, DailyPAFactsCalculator
from backend.app.services.universes import default_symbols_when_omitted


class PAService:
    @staticmethod
    def list_facts(
        session: Session,
        *,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 200,
    ) -> list[PAFact]:
        rows = session.scalars(
            select(db.PAFact)
            .where(
                db.PAFact.symbol_id == symbol.upper(),
                db.PAFact.timeframe == timeframe,
            )
            .order_by(db.PAFact.ts.desc())
            .limit(limit)
        ).all()
        rows.reverse()
        return [PAFact.model_validate(row) for row in rows]

    @staticmethod
    def list_structures(
        session: Session,
        *,
        symbol: str,
        timeframe: str = "1d",
        structure_type: str | None = None,
        limit: int = 200,
    ) -> list[PAStructure]:
        statement = select(db.PAStructure).where(
            db.PAStructure.symbol_id == symbol.upper(),
            db.PAStructure.timeframe == timeframe,
        )
        if structure_type:
            statement = statement.where(db.PAStructure.structure_type == structure_type)
        rows = session.scalars(statement.order_by(db.PAStructure.ts.desc()).limit(limit)).all()
        rows.reverse()
        return [PAStructure.model_validate(row) for row in rows]

    @staticmethod
    def list_setups(
        session: Session,
        *,
        symbol: str | None = None,
        timeframe: str | None = None,
        setup_type: str | None = None,
        status: str | None = None,
        validation_status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PASetup]:
        statement = select(db.PASetup)
        if symbol:
            statement = statement.where(db.PASetup.symbol_id == symbol.upper())
        if timeframe:
            statement = statement.where(db.PASetup.timeframe == timeframe)
        if setup_type:
            statement = statement.where(db.PASetup.setup_type == setup_type)
        if status:
            statement = statement.where(db.PASetup.status == status)
        if validation_status:
            statement = statement.where(db.PASetup.validation_status == validation_status)
        rows = session.scalars(
            statement.order_by(db.PASetup.detected_ts.desc()).offset(offset).limit(limit)
        ).all()
        return [PASetup.model_validate(row) for row in rows]

    @staticmethod
    def get_setup(session: Session, *, setup_id: str) -> PASetup | None:
        setup = session.get(db.PASetup, setup_id)
        return PASetup.model_validate(setup) if setup else None

    @staticmethod
    def explain_setup(session: Session, *, setup_id: str, bar_limit: int = 90) -> PASetupExplain | None:
        setup = session.get(db.PASetup, setup_id)
        if setup is None:
            return None

        bars = session.scalars(
            select(db.Bar)
            .where(db.Bar.symbol_id == setup.symbol_id, db.Bar.timeframe == setup.timeframe)
            .order_by(db.Bar.ts.desc())
            .limit(bar_limit)
        ).all()
        bars.reverse()
        facts = session.scalars(
            select(db.PAFact)
            .where(db.PAFact.symbol_id == setup.symbol_id, db.PAFact.timeframe == setup.timeframe)
            .order_by(db.PAFact.ts.desc())
            .limit(bar_limit)
        ).all()
        facts_by_ts = {fact.ts: fact.facts for fact in facts}
        latest_fact = PAService._latest_fact_for_setup(session, setup)
        score_breakdown = _nested_record(setup.entry_plan, "score_breakdown")

        evidence_bars = [
            PAEvidenceBar(
                ts=bar.ts,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                sma_20=_number((facts_by_ts.get(bar.ts) or {}).get("sma_20")),
                sma_50=_number((facts_by_ts.get(bar.ts) or {}).get("sma_50")),
                sma_200=_number((facts_by_ts.get(bar.ts) or {}).get("sma_200")),
            )
            for bar in bars
        ]

        return PASetupExplain(
            setup_id=setup.setup_id,
            symbol_id=setup.symbol_id,
            timeframe=setup.timeframe,
            detected_ts=setup.detected_ts,
            setup_type=setup.setup_type,
            validation_status=setup.validation_status,
            summary=_explain_summary(setup),
            strengths=_strengths(setup, latest_fact.facts if latest_fact else None),
            watchouts=_watchouts(setup, latest_fact.facts if latest_fact else None, bars),
            score_breakdown=score_breakdown,
            evidence=PASetupEvidence(
                bars=evidence_bars,
                levels=_evidence_levels(setup),
                latest_facts=latest_fact.facts if latest_fact else None,
            ),
        )

    @staticmethod
    def _latest_fact_for_setup(session: Session, setup: db.PASetup) -> db.PAFact | None:
        fact = session.scalar(
            select(db.PAFact)
            .where(
                db.PAFact.symbol_id == setup.symbol_id,
                db.PAFact.timeframe == setup.timeframe,
                db.PAFact.ts <= setup.detected_ts,
            )
            .order_by(db.PAFact.ts.desc())
            .limit(1)
        )
        if fact is not None:
            return fact
        return session.scalar(
            select(db.PAFact)
            .where(db.PAFact.symbol_id == setup.symbol_id, db.PAFact.timeframe == setup.timeframe)
            .order_by(db.PAFact.ts.desc())
            .limit(1)
        )

    @staticmethod
    def list_calibration_stats(
        session: Session,
        *,
        setup_type: str | None = None,
        market_regime: str | None = None,
        timeframe: str | None = None,
        limit: int = 100,
    ) -> list[PACalibrationStat]:
        statement = select(db.PACalibrationStat)
        if setup_type:
            statement = statement.where(db.PACalibrationStat.setup_type == setup_type)
        if market_regime:
            statement = statement.where(db.PACalibrationStat.market_regime == market_regime)
        if timeframe:
            statement = statement.where(db.PACalibrationStat.timeframe == timeframe)
        rows = session.scalars(
            statement.order_by(db.PACalibrationStat.updated_at.desc()).limit(limit)
        ).all()
        return [PACalibrationStat.model_validate(row) for row in rows]

    @staticmethod
    def calculate_etf_daily_facts(request: ETFUniverseFactsRequest) -> PAFactsCalculationResponse:
        with SessionLocal() as session:
            result = PAService.calculate_and_store_daily_facts(
                session=session,
                symbols=default_symbols_when_omitted(request.symbols),
                timeframe=request.timeframe,
            )
            session.commit()
            return result

    @staticmethod
    def calculate_and_store_daily_facts(
        session: Session,
        *,
        symbols: list[str],
        timeframe: str,
    ) -> PAFactsCalculationResponse:
        facts_written = 0
        symbols_processed: list[str] = []
        skipped_symbols: list[str] = []
        for symbol in _normalize_symbols(symbols):
            rows = session.scalars(
                select(db.Bar)
                .where(db.Bar.symbol_id == symbol, db.Bar.timeframe == timeframe)
                .order_by(db.Bar.ts.asc())
            ).all()
            if not rows:
                skipped_symbols.append(symbol)
                continue

            calculated_facts = DailyPAFactsCalculator.calculate(rows)
            for fact in calculated_facts:
                PAService._upsert_fact(session, fact)
                facts_written += 1
            symbols_processed.append(symbol)

        session.flush()
        return PAFactsCalculationResponse(
            timeframe=timeframe,
            symbols_processed=symbols_processed,
            facts_written=facts_written,
            skipped_symbols=skipped_symbols,
        )

    @staticmethod
    def _upsert_fact(session: Session, fact: CalculatedPAFact) -> None:
        fact_id = _pa_fact_id(fact.symbol_id, fact.timeframe, fact.ts)
        existing = session.get(db.PAFact, fact_id)
        if existing:
            existing.facts = fact.facts
            existing.ts = fact.ts
            return

        session.add(
            db.PAFact(
                fact_id=fact_id,
                symbol_id=fact.symbol_id,
                timeframe=fact.timeframe,
                ts=fact.ts,
                facts=fact.facts,
            )
        )


def _normalize_symbols(symbols: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for symbol in symbols:
        ticker = symbol.strip().upper()
        if ticker and ticker not in seen:
            seen.add(ticker)
            normalized.append(ticker)
    return normalized


def _pa_fact_id(symbol: str, timeframe: str, ts) -> str:
    return f"pafact_{symbol.lower()}_{timeframe}_{ts.date().isoformat()}"


def _nested_record(data: dict[str, Any] | None, key: str) -> dict[str, Any] | None:
    value = (data or {}).get(key)
    return value if isinstance(value, dict) else None


def _number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _evidence_levels(setup: db.PASetup) -> list[PAEvidenceLevel]:
    levels: list[PAEvidenceLevel] = []
    for key, source, payload in (
        ("trigger_price", "entry_plan", setup.entry_plan),
        ("initial_stop", "exit_plan", setup.exit_plan),
        ("price_below", "invalidation", setup.invalidation),
    ):
        value = _number((payload or {}).get(key))
        if value is not None:
            levels.append(PAEvidenceLevel(key=key, value=value, source=source))
    return levels


def _explain_summary(setup: db.PASetup) -> str:
    score = _format_plain_number(setup.pa_quality_score)
    grade = setup.setup_grade or "ungraded"
    return (
        f"{setup.symbol_id} is a {setup.setup_type} setup on {setup.timeframe}. "
        f"The current PA score is {score}, grade {grade}, and validation is "
        f"{setup.validation_status or 'unknown'}."
    )


def _strengths(setup: db.PASetup, facts: dict[str, Any] | None) -> list[str]:
    strengths: list[str] = []
    if setup.pa_quality_score is not None and setup.pa_quality_score >= 75:
        strengths.append("High composite PA score.")
    if setup.trend_rs_score is not None and setup.trend_rs_score >= 18:
        strengths.append("Relative strength is leading inside the current ETF universe.")
    if setup.volume_score is not None and setup.volume_score >= 8:
        strengths.append("Liquidity and volume conditions support the setup.")
    if facts:
        if facts.get("above_sma_20") and facts.get("above_sma_50"):
            strengths.append("Price is holding above the 20MA and 50MA.")
        relative_volume = _number(facts.get("relative_volume"))
        if relative_volume is not None and relative_volume >= 1:
            strengths.append("Current volume is at or above the 20-day average.")
        pct_from_52w_high = _number(facts.get("pct_from_52w_high"))
        if pct_from_52w_high is not None and pct_from_52w_high >= -0.15:
            strengths.append("Price is within 15% of the 52-week high.")
    return strengths or ["Setup has enough structure to be tracked in shadow mode."]


def _watchouts(setup: db.PASetup, facts: dict[str, Any] | None, bars: list[db.Bar]) -> list[str]:
    watchouts: list[str] = []
    if setup.validation_status == "shadow_only":
        watchouts.append("This setup is shadow-only and should be used for observation, not live execution.")
    if not bars:
        watchouts.append("No recent bars are available for chart evidence.")
    if not facts:
        watchouts.append("No PA facts snapshot is available yet.")
    if facts:
        if facts.get("close_near_low"):
            watchouts.append("The latest close is near the low of the daily range.")
        relative_volume = _number(facts.get("relative_volume"))
        if relative_volume is not None and relative_volume < 0.8:
            watchouts.append("Volume is below the 20-day average.")
    return watchouts or ["Watch the trigger, stop, and invalidation levels before acting."]


def _format_plain_number(value: float | None) -> str:
    if value is None:
        return "unknown"
    return f"{value:.1f}".rstrip("0").rstrip(".")
