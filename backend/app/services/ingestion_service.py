from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.schemas.ingestion import (
    BarRecord,
    BarsIngestionRequest,
    BarsQueryResponse,
    DataFreshnessRecord,
    DataFreshnessResponse,
    IngestionResponse,
    MarketContextIngestionRequest,
    OptionChainSnapshotRecord,
    OptionChainSnapshotResponse,
    OptionChainIngestionRequest,
)
from backend.app.services.polygon_client import PolygonClient
from backend.app.services.market_data_provider import DailyBarProvider, PolygonMarketDataProvider


class IngestionService:
    @staticmethod
    def _client() -> PolygonClient:
        if not settings.polygon_api_key:
            raise ValueError("POLYGON_API_KEY is required")
        return PolygonClient(api_key=settings.polygon_api_key, base_url=settings.polygon_base_url)

    @staticmethod
    def _daily_bar_provider() -> DailyBarProvider:
        return PolygonMarketDataProvider(IngestionService._client())

    @staticmethod
    def _upsert_freshness(
        session: Session,
        dataset_key: str,
        last_updated_at: datetime,
        source: str,
    ) -> None:
        statement = insert(db.DataFreshness).values(
            dataset_key=dataset_key,
            last_updated_at=last_updated_at,
            source=source,
            updated_at=last_updated_at,
        )
        session.execute(
            statement.on_conflict_do_update(
                index_elements=[db.DataFreshness.dataset_key],
                set_={
                    "last_updated_at": statement.excluded.last_updated_at,
                    "source": statement.excluded.source,
                    "updated_at": statement.excluded.updated_at,
                },
            )
        )

    @staticmethod
    def _record_ingestion_run(
        session: Session,
        *,
        dataset_key: str,
        status: str,
        records_written: int,
        source: str,
        started_at: datetime,
        completed_at: datetime,
        error_message: str | None = None,
    ) -> None:
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
    def _record_failed_run(
        dataset_key: str,
        started_at: datetime,
        error_message: str,
        *,
        source: str = "polygon",
    ) -> None:
        completed_at = datetime.now(UTC)
        with SessionLocal() as session:
            IngestionService._record_ingestion_run(
                session,
                dataset_key=dataset_key,
                status="failed",
                records_written=0,
                source=source,
                started_at=started_at,
                completed_at=completed_at,
                error_message=error_message,
            )
            session.commit()

    @staticmethod
    def ingest_bars(request: BarsIngestionRequest) -> IngestionResponse:
        dataset_key = f"bars:{request.ticker}:{request.timeframe}"
        started_at = datetime.now(UTC)
        source = "polygon"
        try:
            provider = IngestionService._daily_bar_provider()
            source = provider.provider_id
            rows = provider.list_daily_bars(request.ticker, request.from_date, request.to_date)
        except Exception as exc:
            IngestionService._record_failed_run(dataset_key, started_at, str(exc), source=source)
            raise

        if not rows:
            error_message = f"{_provider_display_name(source)} returned no bars for {request.ticker}"
            IngestionService._record_failed_run(dataset_key, started_at, error_message, source=source)
            raise RuntimeError(error_message)

        with SessionLocal() as session:
            records_written = 0
            for bar in rows:
                statement = insert(db.Bar).values(
                    ts=bar.ts,
                    symbol_id=request.ticker,
                    timeframe=request.timeframe,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    vwap=bar.vwap,
                    adjusted=bar.adjusted,
                    source=bar.source,
                )
                session.execute(
                    statement.on_conflict_do_update(
                        index_elements=[
                            db.Bar.symbol_id,
                            db.Bar.timeframe,
                            db.Bar.ts,
                        ],
                        set_={
                            "open": statement.excluded.open,
                            "high": statement.excluded.high,
                            "low": statement.excluded.low,
                            "close": statement.excluded.close,
                            "volume": statement.excluded.volume,
                            "vwap": statement.excluded.vwap,
                            "adjusted": statement.excluded.adjusted,
                            "source": statement.excluded.source,
                        },
                    )
                )
                records_written += 1

            last_updated_at = datetime.now(UTC)
            if records_written == 0:
                error_message = (
                    f"{_provider_display_name(source)} returned no writable bars for {request.ticker}"
                )
                IngestionService._record_ingestion_run(
                    session,
                    dataset_key=dataset_key,
                    status="failed",
                    records_written=0,
                    source=source,
                    started_at=started_at,
                    completed_at=last_updated_at,
                    error_message=error_message,
                )
                session.commit()
                raise RuntimeError(error_message)

            IngestionService._upsert_freshness(
                session,
                dataset_key=dataset_key,
                last_updated_at=last_updated_at,
                source=source,
            )
            IngestionService._record_ingestion_run(
                session,
                dataset_key=dataset_key,
                status="success",
                records_written=records_written,
                source=source,
                started_at=started_at,
                completed_at=last_updated_at,
            )
            session.commit()

        return IngestionResponse(records_written=records_written, last_updated_at=last_updated_at)

    @staticmethod
    def ingest_option_chain(request: OptionChainIngestionRequest) -> IngestionResponse:
        dataset_key = f"options:{request.underlying_symbol}"
        started_at = datetime.now(UTC)
        try:
            rows = IngestionService._client().option_chain_snapshot(
                underlying_symbol=request.underlying_symbol,
            )
        except Exception as exc:
            IngestionService._record_failed_run(dataset_key, started_at, str(exc))
            raise

        if not rows:
            error_message = f"Polygon returned no option chain rows for {request.underlying_symbol}"
            IngestionService._record_failed_run(dataset_key, started_at, error_message)
            raise RuntimeError(error_message)

        snapshot_ts = datetime.now(UTC)
        snapshot_date = snapshot_ts.date()

        with SessionLocal() as session:
            records_written = 0
            for row in rows:
                details = row.get("details", {})
                greeks = row.get("greeks", {})
                quote = row.get("last_quote", {})
                day = row.get("day", {})
                bid = quote.get("bid")
                ask = quote.get("ask")
                mid = ((ask + bid) / 2) if (ask is not None and bid is not None) else None
                spread_pct = (
                    (ask - bid) / mid
                    if (ask is not None and bid is not None and mid not in (None, 0))
                    else None
                )
                expiration = IngestionService._parse_date(details.get("expiration_date"))
                dte = (expiration - snapshot_date).days if expiration else None
                option_symbol = details.get("ticker")
                strike = details.get("strike_price")
                option_type = details.get("contract_type")
                if not (option_symbol and expiration and strike is not None and option_type):
                    continue

                statement = insert(db.OptionChainSnapshot).values(
                    snapshot_ts=snapshot_ts,
                    underlying_symbol=request.underlying_symbol,
                    option_symbol=option_symbol,
                    expiration=expiration,
                    strike=strike,
                    option_type=option_type,
                    bid=bid,
                    ask=ask,
                    mid=mid,
                    last=day.get("close"),
                    volume=day.get("volume"),
                    open_interest=row.get("open_interest"),
                    iv=row.get("implied_volatility"),
                    delta=greeks.get("delta"),
                    gamma=greeks.get("gamma"),
                    theta=greeks.get("theta"),
                    vega=greeks.get("vega"),
                    dte=dte,
                    spread_pct=spread_pct,
                    source="polygon",
                )
                session.execute(
                    statement.on_conflict_do_nothing(
                        index_elements=[
                            db.OptionChainSnapshot.snapshot_ts,
                            db.OptionChainSnapshot.option_symbol,
                        ]
                    )
                )
                records_written += 1

            last_updated_at = datetime.now(UTC)
            if records_written == 0:
                error_message = (
                    f"Polygon returned no writable option rows for {request.underlying_symbol}"
                )
                IngestionService._record_ingestion_run(
                    session,
                    dataset_key=dataset_key,
                    status="failed",
                    records_written=0,
                    source="polygon",
                    started_at=started_at,
                    completed_at=last_updated_at,
                    error_message=error_message,
                )
                session.commit()
                raise RuntimeError(error_message)

            IngestionService._upsert_freshness(
                session,
                dataset_key=dataset_key,
                last_updated_at=last_updated_at,
                source="polygon",
            )
            IngestionService._record_ingestion_run(
                session,
                dataset_key=dataset_key,
                status="success",
                records_written=records_written,
                source="polygon",
                started_at=started_at,
                completed_at=last_updated_at,
            )
            session.commit()

        return IngestionResponse(records_written=records_written, last_updated_at=last_updated_at)

    @staticmethod
    def ingest_market_context(request: MarketContextIngestionRequest) -> IngestionResponse:
        snapshot_ts = request.snapshot_ts or datetime.now(UTC)
        last_updated_at = datetime.now(UTC)
        dataset_key = f"market_context:{request.market}"

        with SessionLocal() as session:
            statement = insert(db.MarketContextSnapshot).values(
                snapshot_ts=snapshot_ts,
                market=request.market,
                spy_return=request.spy_return,
                qqq_return=request.qqq_return,
                iwm_return=request.iwm_return,
                smh_return=request.smh_return,
                soxx_return=request.soxx_return,
                vix_change=request.vix_change,
                usdjpy_change=request.usdjpy_change,
                dxy_change=request.dxy_change,
                us10y_change=request.us10y_change,
                nikkei_futures_change=request.nikkei_futures_change,
                topix_return=request.topix_return,
                japan_bias=request.japan_bias,
                us_bias=request.us_bias,
                risk_level=request.risk_level,
                notes=request.notes,
            )
            session.execute(
                statement.on_conflict_do_update(
                    index_elements=[
                        db.MarketContextSnapshot.market,
                        db.MarketContextSnapshot.snapshot_ts,
                    ],
                    set_={
                        "spy_return": statement.excluded.spy_return,
                        "qqq_return": statement.excluded.qqq_return,
                        "iwm_return": statement.excluded.iwm_return,
                        "smh_return": statement.excluded.smh_return,
                        "soxx_return": statement.excluded.soxx_return,
                        "vix_change": statement.excluded.vix_change,
                        "usdjpy_change": statement.excluded.usdjpy_change,
                        "dxy_change": statement.excluded.dxy_change,
                        "us10y_change": statement.excluded.us10y_change,
                        "nikkei_futures_change": statement.excluded.nikkei_futures_change,
                        "topix_return": statement.excluded.topix_return,
                        "japan_bias": statement.excluded.japan_bias,
                        "us_bias": statement.excluded.us_bias,
                        "risk_level": statement.excluded.risk_level,
                        "notes": statement.excluded.notes,
                    },
                )
            )
            IngestionService._upsert_freshness(
                session,
                dataset_key=dataset_key,
                last_updated_at=last_updated_at,
                source="manual",
            )
            IngestionService._record_ingestion_run(
                session,
                dataset_key=dataset_key,
                status="success",
                records_written=1,
                source="manual",
                started_at=snapshot_ts,
                completed_at=last_updated_at,
            )
            session.commit()

        return IngestionResponse(
            records_written=1,
            last_updated_at=last_updated_at,
            source="manual",
        )

    @staticmethod
    def recent_bars(ticker: str, timeframe: str, limit: int) -> BarsQueryResponse:
        with SessionLocal() as session:
            rows = session.scalars(
                select(db.Bar)
                .where(db.Bar.symbol_id == ticker, db.Bar.timeframe == timeframe)
                .order_by(db.Bar.ts.desc())
                .limit(limit)
            ).all()

        rows.reverse()
        return BarsQueryResponse(
            ticker=ticker,
            timeframe=timeframe,
            bars=[BarRecord.model_validate(row) for row in rows],
        )

    @staticmethod
    def latest_option_chain(underlying_symbol: str, limit: int) -> OptionChainSnapshotResponse:
        with SessionLocal() as session:
            snapshot_ts = session.scalar(
                select(db.OptionChainSnapshot.snapshot_ts)
                .where(db.OptionChainSnapshot.underlying_symbol == underlying_symbol)
                .order_by(db.OptionChainSnapshot.snapshot_ts.desc())
                .limit(1)
            )
            if snapshot_ts is None:
                return OptionChainSnapshotResponse(
                    underlying_symbol=underlying_symbol,
                    snapshot_ts=None,
                    options=[],
                )
            rows = session.scalars(
                select(db.OptionChainSnapshot)
                .where(
                    db.OptionChainSnapshot.underlying_symbol == underlying_symbol,
                    db.OptionChainSnapshot.snapshot_ts == snapshot_ts,
                )
                .order_by(
                    db.OptionChainSnapshot.expiration,
                    db.OptionChainSnapshot.strike,
                    db.OptionChainSnapshot.option_type,
                )
                .limit(limit)
            ).all()

        return OptionChainSnapshotResponse(
            underlying_symbol=underlying_symbol,
            snapshot_ts=snapshot_ts,
            options=[OptionChainSnapshotRecord.model_validate(row) for row in rows],
        )

    @staticmethod
    def data_freshness() -> DataFreshnessResponse:
        with SessionLocal() as session:
            rows = session.scalars(
                select(db.DataFreshness).order_by(db.DataFreshness.dataset_key)
            ).all()

        return DataFreshnessResponse(data=[DataFreshnessRecord.model_validate(row) for row in rows])

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        return date.fromisoformat(value)


def _provider_display_name(source: str) -> str:
    return "Polygon" if source == "polygon" else source
