from datetime import UTC, date, datetime
from uuid import uuid4

from backend.app.core.config import settings
from backend.app.core.database import connect
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


class IngestionService:
    @staticmethod
    def _client() -> PolygonClient:
        if not settings.polygon_api_key:
            raise ValueError("POLYGON_API_KEY is required")
        return PolygonClient(api_key=settings.polygon_api_key, base_url=settings.polygon_base_url)

    @staticmethod
    def _database_url() -> str:
        return settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)

    @staticmethod
    def _connect():
        return connect()

    @staticmethod
    def _upsert_freshness(cur, dataset_key: str, last_updated_at: datetime, source: str) -> None:
        cur.execute(
            """
            INSERT INTO data_freshness (dataset_key, last_updated_at, source)
            VALUES (%s, %s, %s)
            ON CONFLICT (dataset_key) DO UPDATE SET
                last_updated_at = EXCLUDED.last_updated_at,
                source = EXCLUDED.source,
                updated_at = now()
            """,
            (dataset_key, last_updated_at, source),
        )

    @staticmethod
    def _record_ingestion_run(
        cur,
        *,
        dataset_key: str,
        status: str,
        records_written: int,
        source: str,
        started_at: datetime,
        completed_at: datetime,
        error_message: str | None = None,
    ) -> None:
        cur.execute(
            """
            INSERT INTO ingestion_runs (
                run_id, dataset_key, status, records_written, source,
                started_at, completed_at, error_message
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(uuid4()),
                dataset_key,
                status,
                records_written,
                source,
                started_at,
                completed_at,
                error_message,
            ),
        )

    @staticmethod
    def _record_failed_run(dataset_key: str, started_at: datetime, error_message: str) -> None:
        completed_at = datetime.now(UTC)
        with IngestionService._connect() as conn:
            with conn.cursor() as cur:
                IngestionService._record_ingestion_run(
                    cur,
                    dataset_key=dataset_key,
                    status="failed",
                    records_written=0,
                    source="polygon",
                    started_at=started_at,
                    completed_at=completed_at,
                    error_message=error_message,
                )
            conn.commit()

    @staticmethod
    def ingest_bars(request: BarsIngestionRequest) -> IngestionResponse:
        dataset_key = f"bars:{request.ticker}:{request.timeframe}"
        started_at = datetime.now(UTC)
        try:
            rows = IngestionService._client().list_daily_bars(
                ticker=request.ticker,
                from_date=request.from_date,
                to_date=request.to_date,
            )
        except Exception as exc:
            IngestionService._record_failed_run(dataset_key, started_at, str(exc))
            raise

        if not rows:
            error_message = f"Polygon returned no bars for {request.ticker}"
            IngestionService._record_failed_run(dataset_key, started_at, error_message)
            raise RuntimeError(error_message)

        with IngestionService._connect() as conn:
            with conn.cursor() as cur:
                records_written = 0
                for row in rows:
                    if "t" not in row:
                        continue
                    ts = datetime.fromtimestamp(row["t"] / 1000, tz=UTC)
                    cur.execute(
                        """
                        INSERT INTO bars (
                            ts, symbol_id, timeframe, open, high, low, close,
                            volume, vwap, adjusted, source
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol_id, timeframe, ts) DO UPDATE SET
                            open = EXCLUDED.open,
                            high = EXCLUDED.high,
                            low = EXCLUDED.low,
                            close = EXCLUDED.close,
                            volume = EXCLUDED.volume,
                            vwap = EXCLUDED.vwap,
                            adjusted = EXCLUDED.adjusted,
                            source = EXCLUDED.source
                        """,
                        (
                            ts,
                            request.ticker,
                            request.timeframe,
                            row.get("o"),
                            row.get("h"),
                            row.get("l"),
                            row.get("c"),
                            row.get("v"),
                            row.get("vw"),
                            True,
                            "polygon",
                        ),
                    )
                    records_written += 1

                last_updated_at = datetime.now(UTC)
                if records_written == 0:
                    error_message = f"Polygon returned no writable bars for {request.ticker}"
                    IngestionService._record_ingestion_run(
                        cur,
                        dataset_key=dataset_key,
                        status="failed",
                        records_written=0,
                        source="polygon",
                        started_at=started_at,
                        completed_at=last_updated_at,
                        error_message=error_message,
                    )
                    conn.commit()
                    raise RuntimeError(error_message)

                IngestionService._upsert_freshness(
                    cur,
                    dataset_key=dataset_key,
                    last_updated_at=last_updated_at,
                    source="polygon",
                )
                IngestionService._record_ingestion_run(
                    cur,
                    dataset_key=dataset_key,
                    status="success",
                    records_written=records_written,
                    source="polygon",
                    started_at=started_at,
                    completed_at=last_updated_at,
                )
            conn.commit()

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

        with IngestionService._connect() as conn:
            with conn.cursor() as cur:
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

                    cur.execute(
                        """
                        INSERT INTO options_chain_snapshots (
                            snapshot_ts, underlying_symbol, option_symbol, expiration,
                            strike, option_type, bid, ask, mid, last, volume,
                            open_interest, iv, delta, gamma, theta, vega,
                            dte, spread_pct, source
                        )
                        VALUES (
                            %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s
                        )
                        ON CONFLICT (snapshot_ts, option_symbol) DO NOTHING
                        """,
                        (
                            snapshot_ts,
                            request.underlying_symbol,
                            option_symbol,
                            expiration,
                            strike,
                            option_type,
                            bid,
                            ask,
                            mid,
                            day.get("close"),
                            day.get("volume"),
                            row.get("open_interest"),
                            row.get("implied_volatility"),
                            greeks.get("delta"),
                            greeks.get("gamma"),
                            greeks.get("theta"),
                            greeks.get("vega"),
                            dte,
                            spread_pct,
                            "polygon",
                        ),
                    )
                    records_written += 1

                last_updated_at = datetime.now(UTC)
                if records_written == 0:
                    error_message = (
                        f"Polygon returned no writable option rows for {request.underlying_symbol}"
                    )
                    IngestionService._record_ingestion_run(
                        cur,
                        dataset_key=dataset_key,
                        status="failed",
                        records_written=0,
                        source="polygon",
                        started_at=started_at,
                        completed_at=last_updated_at,
                        error_message=error_message,
                    )
                    conn.commit()
                    raise RuntimeError(error_message)

                IngestionService._upsert_freshness(
                    cur,
                    dataset_key=dataset_key,
                    last_updated_at=last_updated_at,
                    source="polygon",
                )
                IngestionService._record_ingestion_run(
                    cur,
                    dataset_key=dataset_key,
                    status="success",
                    records_written=records_written,
                    source="polygon",
                    started_at=started_at,
                    completed_at=last_updated_at,
                )
            conn.commit()

        return IngestionResponse(records_written=records_written, last_updated_at=last_updated_at)

    @staticmethod
    def ingest_market_context(request: MarketContextIngestionRequest) -> IngestionResponse:
        snapshot_ts = request.snapshot_ts or datetime.now(UTC)

        with IngestionService._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO market_context_snapshots (
                        snapshot_ts, market, spy_return, qqq_return, iwm_return,
                        smh_return, soxx_return, vix_change, usdjpy_change,
                        dxy_change, us10y_change, nikkei_futures_change,
                        topix_return, japan_bias, us_bias, risk_level, notes
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (market, snapshot_ts) DO UPDATE SET
                        spy_return = EXCLUDED.spy_return,
                        qqq_return = EXCLUDED.qqq_return,
                        iwm_return = EXCLUDED.iwm_return,
                        smh_return = EXCLUDED.smh_return,
                        soxx_return = EXCLUDED.soxx_return,
                        vix_change = EXCLUDED.vix_change,
                        usdjpy_change = EXCLUDED.usdjpy_change,
                        dxy_change = EXCLUDED.dxy_change,
                        us10y_change = EXCLUDED.us10y_change,
                        nikkei_futures_change = EXCLUDED.nikkei_futures_change,
                        topix_return = EXCLUDED.topix_return,
                        japan_bias = EXCLUDED.japan_bias,
                        us_bias = EXCLUDED.us_bias,
                        risk_level = EXCLUDED.risk_level,
                        notes = EXCLUDED.notes
                    """,
                    (
                        snapshot_ts,
                        request.market,
                        request.spy_return,
                        request.qqq_return,
                        request.iwm_return,
                        request.smh_return,
                        request.soxx_return,
                        request.vix_change,
                        request.usdjpy_change,
                        request.dxy_change,
                        request.us10y_change,
                        request.nikkei_futures_change,
                        request.topix_return,
                        request.japan_bias,
                        request.us_bias,
                        request.risk_level,
                        request.notes,
                    ),
                )

                last_updated_at = datetime.now(UTC)
                IngestionService._upsert_freshness(
                    cur,
                    dataset_key=f"market_context:{request.market}",
                    last_updated_at=last_updated_at,
                    source="manual",
                )
                IngestionService._record_ingestion_run(
                    cur,
                    dataset_key=f"market_context:{request.market}",
                    status="success",
                    records_written=1,
                    source="manual",
                    started_at=snapshot_ts,
                    completed_at=last_updated_at,
                )
            conn.commit()

        return IngestionResponse(
            records_written=1,
            last_updated_at=last_updated_at,
            source="manual",
        )

    @staticmethod
    def recent_bars(ticker: str, timeframe: str, limit: int) -> BarsQueryResponse:
        from psycopg.rows import dict_row

        with IngestionService._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT ts, symbol_id, timeframe, open, high, low, close,
                           volume, vwap, adjusted, source
                    FROM bars
                    WHERE symbol_id = %s AND timeframe = %s
                    ORDER BY ts DESC
                    LIMIT %s
                    """,
                    (ticker, timeframe, limit),
                )
                rows = list(cur.fetchall())

        rows.reverse()
        return BarsQueryResponse(
            ticker=ticker,
            timeframe=timeframe,
            bars=[BarRecord(**row) for row in rows],
        )

    @staticmethod
    def latest_option_chain(underlying_symbol: str, limit: int) -> OptionChainSnapshotResponse:
        from psycopg.rows import dict_row

        with IngestionService._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT snapshot_ts
                    FROM options_chain_snapshots
                    WHERE underlying_symbol = %s
                    ORDER BY snapshot_ts DESC
                    LIMIT 1
                    """,
                    (underlying_symbol,),
                )
                latest = cur.fetchone()
                if latest is None:
                    return OptionChainSnapshotResponse(
                        underlying_symbol=underlying_symbol,
                        snapshot_ts=None,
                        options=[],
                    )

                snapshot_ts = latest["snapshot_ts"]
                cur.execute(
                    """
                    SELECT snapshot_ts, underlying_symbol, option_symbol, expiration,
                           strike, option_type, bid, ask, mid, last, volume,
                           open_interest, iv, delta, gamma, theta, vega,
                           dte, spread_pct, source
                    FROM options_chain_snapshots
                    WHERE underlying_symbol = %s AND snapshot_ts = %s
                    ORDER BY expiration, strike, option_type
                    LIMIT %s
                    """,
                    (underlying_symbol, snapshot_ts, limit),
                )
                rows = list(cur.fetchall())

        return OptionChainSnapshotResponse(
            underlying_symbol=underlying_symbol,
            snapshot_ts=snapshot_ts,
            options=[OptionChainSnapshotRecord(**row) for row in rows],
        )

    @staticmethod
    def data_freshness() -> DataFreshnessResponse:
        from psycopg.rows import dict_row

        with IngestionService._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT dataset_key, last_updated_at, source, updated_at
                    FROM data_freshness
                    ORDER BY dataset_key
                    """
                )
                rows = list(cur.fetchall())

        return DataFreshnessResponse(data=[DataFreshnessRecord(**row) for row in rows])

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None
        return date.fromisoformat(value)
