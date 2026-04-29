from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.database import SessionLocal
from backend.app.schemas.pa import (
    ETFUniverseFactsRequest,
    PACalibrationStat,
    PAFact,
    PAFactsCalculationResponse,
    PAStructure,
    PASetup,
)
from backend.app.services.pa_calculator import CalculatedPAFact, DailyPAFactsCalculator
from backend.app.services.universes import US_ETF_UNIVERSE


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
            statement.order_by(db.PASetup.detected_ts.desc()).limit(limit)
        ).all()
        return [PASetup.model_validate(row) for row in rows]

    @staticmethod
    def get_setup(session: Session, *, setup_id: str) -> PASetup | None:
        setup = session.get(db.PASetup, setup_id)
        return PASetup.model_validate(setup) if setup else None

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
                symbols=request.symbols or US_ETF_UNIVERSE,
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
