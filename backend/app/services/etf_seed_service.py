from collections import Counter
from datetime import UTC, date, datetime
from typing import Any

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
from backend.app.services.pa_service import PAService
from backend.app.services.polygon_client import PolygonClient
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
    def _client() -> PolygonClient:
        from backend.app.services.ingestion_service import IngestionService

        return IngestionService._client()

    @staticmethod
    def seed_us_etf_universe_for_session(
        *,
        session: Session,
        request: ETFUniverseSeedRequest,
        client: PolygonClient,
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
        client: PolygonClient,
        symbol: str,
        request: ETFUniverseSeedRequest,
    ) -> ETFUniverseSeedSymbolResult:
        dataset_key = f"bars:{symbol}:{request.timeframe}"
        started_at = datetime.now(UTC)
        try:
            rows = client.list_daily_bars(
                ticker=symbol,
                from_date=request.from_date,
                to_date=request.to_date,
            )
            if not rows:
                raise RuntimeError(f"Polygon returned no bars for {symbol}")

            ETFSeedService._upsert_symbol(session, symbol)
            records_written = 0
            for row in rows:
                if "t" not in row:
                    continue
                ETFSeedService._upsert_bar(session, symbol, request.timeframe, row)
                records_written += 1

            completed_at = datetime.now(UTC)
            if records_written == 0:
                raise RuntimeError(f"Polygon returned no writable bars for {symbol}")

            ETFSeedService._upsert_freshness(
                session=session,
                dataset_key=dataset_key,
                last_updated_at=completed_at,
                source="polygon",
            )
            ETFSeedService._record_ingestion_run(
                session=session,
                dataset_key=dataset_key,
                status="success",
                records_written=records_written,
                source="polygon",
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
                source="polygon",
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
    def _upsert_symbol(session: Session, symbol: str) -> None:
        existing = session.get(db.Symbol, symbol)
        if existing:
            existing.active = True
            existing.asset_type = "ETF"
            existing.market = "US"
            existing.source = "polygon"
            existing.updated_at = datetime.now(UTC)
            return

        session.add(
            db.Symbol(
                symbol_id=symbol,
                ticker=symbol,
                market="US",
                asset_type="ETF",
                currency="USD",
                active=True,
                source="polygon",
            )
        )

    @staticmethod
    def _upsert_bar(session: Session, symbol: str, timeframe: str, row: dict[str, Any]) -> None:
        ts = datetime.fromtimestamp(row["t"] / 1000, tz=UTC)
        primary_key = (symbol, timeframe, ts)
        existing = session.get(db.Bar, primary_key)
        if existing:
            existing.open = row.get("o")
            existing.high = row.get("h")
            existing.low = row.get("l")
            existing.close = row.get("c")
            existing.volume = row.get("v")
            existing.vwap = row.get("vw")
            existing.adjusted = True
            existing.source = "polygon"
            return

        session.add(
            db.Bar(
                ts=ts,
                symbol_id=symbol,
                timeframe=timeframe,
                open=row.get("o"),
                high=row.get("h"),
                low=row.get("l"),
                close=row.get("c"),
                volume=row.get("v"),
                vwap=row.get("vw"),
                adjusted=True,
                source="polygon",
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
