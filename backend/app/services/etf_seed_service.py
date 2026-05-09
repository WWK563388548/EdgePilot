from collections import Counter
from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.database import SessionLocal
from backend.app.schemas.ingestion import (
    ETFUniverseSeedRequest,
    ETFUniverseSeedResponse,
    ETFUniverseSeedSymbolResult,
)
from backend.app.schemas.pa import ETFOneilScannerRequest
from backend.app.services.market_data_provider import (
    DailyBar,
    DailyBarProvider,
    SymbolMetadata,
    coerce_daily_bar,
    provider_id,
    symbol_metadata,
)
from backend.app.services.pa_service import PAService
from backend.app.services.scanner_service import ETFScannerService
from backend.app.services.universes import default_symbols_when_omitted


class ETFSeedService:
    @staticmethod
    def seed_us_etf_universe(request: ETFUniverseSeedRequest) -> ETFUniverseSeedResponse:
        with SessionLocal() as session:
            response = ETFSeedService.seed_us_etf_universe_for_session(
                session=session,
                request=request,
                client=ETFSeedService._client(),
            )
            session.commit()
            return response

    @staticmethod
    def _client() -> DailyBarProvider:
        from backend.app.services.ingestion_service import IngestionService

        return IngestionService._daily_bar_provider()

    @staticmethod
    def seed_us_etf_universe_for_session(
        *,
        session: Session,
        request: ETFUniverseSeedRequest,
        client: DailyBarProvider,
    ) -> ETFUniverseSeedResponse:
        symbols = _normalize_symbols(default_symbols_when_omitted(request.symbols))
        successful_symbols: list[str] = []
        skipped_symbols: list[str] = []
        symbol_results: list[ETFUniverseSeedSymbolResult] = []
        bars_written = 0

        for symbol in symbols:
            result = ETFSeedService._ingest_symbol_bars(
                session=session,
                client=client,
                symbol=symbol,
                request=request,
            )
            symbol_results.append(result)
            bars_written += result.bars_written
            if result.status == "success":
                successful_symbols.append(symbol)
            else:
                skipped_symbols.append(symbol)

        session.flush()
        facts_written = 0
        if request.run_pa_facts and successful_symbols:
            facts_result = PAService.calculate_and_store_daily_facts(
                session=session,
                symbols=successful_symbols,
                timeframe=request.timeframe,
            )
            facts_written = facts_result.facts_written
            for symbol in facts_result.skipped_symbols:
                if symbol not in skipped_symbols:
                    skipped_symbols.append(symbol)

        setups_written = 0
        candidates_written = 0
        candidates = []
        decision_counts = {}
        latest_scan_date = None
        if request.run_scanner and successful_symbols:
            scanner_response = ETFScannerService.run_us_etf_oneil_core_for_session(
                session,
                ETFOneilScannerRequest(
                    symbols=successful_symbols,
                    timeframe=request.timeframe,
                    account_id=request.account_id,
                    min_score=request.min_score,
                    max_candidates=request.max_candidates,
                    recalculate_facts=not request.run_pa_facts,
                ),
            )
            facts_written += scanner_response.facts_written
            setups_written = scanner_response.setups_written
            candidates_written = scanner_response.candidates_written
            candidates = scanner_response.candidates
            decision_counts = scanner_response.decision_counts
            latest_scan_date = scanner_response.latest_scan_date
            for symbol in scanner_response.skipped_symbols:
                if symbol not in skipped_symbols:
                    skipped_symbols.append(symbol)

        if not decision_counts and candidates:
            decision_counts = dict(Counter(candidate.decision or "unknown" for candidate in candidates))
        latest_bar_date = ETFSeedService._latest_bar_date(
            session=session,
            symbols=successful_symbols,
            timeframe=request.timeframe,
        )

        return ETFUniverseSeedResponse(
            account_id=request.account_id,
            timeframe=request.timeframe,
            from_date=request.from_date,
            to_date=request.to_date,
            symbols_requested=symbols,
            bars_written=bars_written,
            facts_written=facts_written,
            setups_written=setups_written,
            candidates_written=candidates_written,
            decision_counts=decision_counts,
            latest_scan_date=latest_scan_date,
            latest_bar_date=latest_bar_date,
            skipped_symbols=skipped_symbols,
            symbol_results=symbol_results,
            candidates=candidates,
        )

    @staticmethod
    def _ingest_symbol_bars(
        *,
        session: Session,
        client: DailyBarProvider,
        symbol: str,
        request: ETFUniverseSeedRequest,
    ) -> ETFUniverseSeedSymbolResult:
        dataset_key = f"bars:{symbol}:{request.timeframe}"
        started_at = datetime.now(UTC)
        source = provider_id(client)
        source_label = _provider_display_name(source)
        try:
            rows = client.list_daily_bars(symbol, request.from_date, request.to_date)
            if not rows:
                raise RuntimeError(f"{source_label} returned no bars for {symbol}")

            ETFSeedService._upsert_symbol(session, symbol_metadata(client, symbol))
            records_written = 0
            for row in rows:
                bar = coerce_daily_bar(row, source=source)
                if bar is None:
                    continue
                ETFSeedService._upsert_bar(session, symbol, request.timeframe, bar)
                records_written += 1

            completed_at = datetime.now(UTC)
            if records_written == 0:
                raise RuntimeError(f"{source_label} returned no writable bars for {symbol}")

            ETFSeedService._upsert_freshness(
                session=session,
                dataset_key=dataset_key,
                last_updated_at=completed_at,
                source=source,
            )
            ETFSeedService._record_ingestion_run(
                session=session,
                dataset_key=dataset_key,
                status="success",
                records_written=records_written,
                source=source,
                started_at=started_at,
                completed_at=completed_at,
            )
            return ETFUniverseSeedSymbolResult(
                symbol=symbol,
                status="success",
                bars_written=records_written,
            )
        except Exception as exc:
            completed_at = datetime.now(UTC)
            ETFSeedService._record_ingestion_run(
                session=session,
                dataset_key=dataset_key,
                status="failed",
                records_written=0,
                source=source,
                started_at=started_at,
                completed_at=completed_at,
                error_message=str(exc),
            )
            return ETFUniverseSeedSymbolResult(
                symbol=symbol,
                status="failed",
                error_message=str(exc),
            )

    @staticmethod
    def _upsert_symbol(session: Session, metadata: SymbolMetadata) -> None:
        existing = session.get(db.Symbol, metadata.symbol_id)
        if existing:
            existing.active = True
            existing.ticker = metadata.ticker
            existing.asset_type = metadata.asset_type
            existing.market = metadata.market
            existing.exchange = metadata.exchange
            existing.name = metadata.name
            existing.sector = metadata.sector
            existing.industry = metadata.industry
            existing.currency = metadata.currency
            existing.source = metadata.source
            existing.updated_at = datetime.now(UTC)
            return

        session.add(
            db.Symbol(
                symbol_id=metadata.symbol_id,
                ticker=metadata.ticker,
                market=metadata.market,
                asset_type=metadata.asset_type,
                exchange=metadata.exchange,
                name=metadata.name,
                sector=metadata.sector,
                industry=metadata.industry,
                currency=metadata.currency,
                active=metadata.active,
                source=metadata.source,
            )
        )

    @staticmethod
    def _upsert_bar(session: Session, symbol: str, timeframe: str, bar: DailyBar) -> None:
        primary_key = (symbol, timeframe, bar.ts)
        existing = session.get(db.Bar, primary_key)
        if existing:
            existing.open = bar.open
            existing.high = bar.high
            existing.low = bar.low
            existing.close = bar.close
            existing.volume = bar.volume
            existing.vwap = bar.vwap
            existing.adjusted = bar.adjusted
            existing.source = bar.source
            return

        session.add(
            db.Bar(
                ts=bar.ts,
                symbol_id=symbol,
                timeframe=timeframe,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                vwap=bar.vwap,
                adjusted=bar.adjusted,
                source=bar.source,
            )
        )

    @staticmethod
    def _upsert_freshness(
        *,
        session: Session,
        dataset_key: str,
        last_updated_at: datetime,
        source: str,
    ) -> None:
        existing = session.get(db.DataFreshness, dataset_key)
        if existing:
            existing.last_updated_at = last_updated_at
            existing.source = source
            existing.updated_at = last_updated_at
            return

        session.add(
            db.DataFreshness(
                dataset_key=dataset_key,
                last_updated_at=last_updated_at,
                source=source,
                updated_at=last_updated_at,
            )
        )

    @staticmethod
    def _record_ingestion_run(
        *,
        session: Session,
        dataset_key: str,
        status: str,
        records_written: int,
        source: str,
        started_at: datetime,
        completed_at: datetime,
        error_message: str | None = None,
    ) -> None:
        from uuid import uuid4

        session.add(
            db.IngestionRun(
                run_id=f"run_{uuid4().hex}",
                dataset_key=dataset_key,
                status=status,
                records_written=records_written,
                source=source,
                started_at=started_at,
                completed_at=completed_at,
                error_message=error_message,
            )
        )

    @staticmethod
    def _latest_bar_date(*, session: Session, symbols: list[str], timeframe: str) -> date | None:
        if not symbols:
            return None
        latest_ts = session.scalar(
            select(func.max(db.Bar.ts)).where(
                db.Bar.symbol_id.in_(symbols),
                db.Bar.timeframe == timeframe,
            )
        )
        return latest_ts.date() if latest_ts else None


def _normalize_symbols(symbols: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for symbol in symbols:
        ticker = symbol.strip().upper()
        if ticker and ticker not in seen:
            normalized.append(ticker)
            seen.add(ticker)
    return normalized


def _provider_display_name(source: str) -> str:
    return "Polygon" if source == "polygon" else source
