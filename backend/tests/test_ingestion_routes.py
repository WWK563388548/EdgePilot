from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.api.routes.ingestion import (
    get_data_freshness,
    get_latest_options_chain,
    get_recent_bars,
    ingest_bars,
    ingest_market_context,
    ingest_options_chain,
)
from backend.app.core.config import settings
from backend.app.main import app
from backend.app.schemas.ingestion import (
    BarRecord,
    BarsIngestionRequest,
    BarsQueryResponse,
    DataFreshnessRecord,
    DataFreshnessResponse,
    IngestionResponse,
    MarketContextIngestionRequest,
    OptionChainSnapshotResponse,
    OptionChainIngestionRequest,
)


def test_ingest_bars_route(monkeypatch) -> None:
    from backend.app.api.routes import ingestion as ingestion_route

    def _fake_ingest_bars(request):
        return IngestionResponse(
            records_written=3,
            last_updated_at=datetime(2026, 4, 26, tzinfo=UTC),
            source="polygon",
        )

    monkeypatch.setattr(ingestion_route.IngestionService, "ingest_bars", _fake_ingest_bars)

    response = ingest_bars(
        BarsIngestionRequest(ticker="SPY", **{"from": "2026-04-01", "to": "2026-04-26"}),
    )

    assert response.records_written == 3


def test_bars_request_rejects_non_daily_timeframe() -> None:
    with pytest.raises(ValidationError):
        BarsIngestionRequest(
            ticker="SPY",
            timeframe="1h",
            **{"from": "2026-04-01", "to": "2026-04-26"},
        )


def test_ingest_options_chain_route(monkeypatch) -> None:
    from backend.app.api.routes import ingestion as ingestion_route

    def _fake_ingest_options_chain(request):
        return IngestionResponse(
            records_written=20,
            last_updated_at=datetime(2026, 4, 26, tzinfo=UTC),
            source="polygon",
        )

    monkeypatch.setattr(
        ingestion_route.IngestionService,
        "ingest_option_chain",
        _fake_ingest_options_chain,
    )

    response = ingest_options_chain(OptionChainIngestionRequest(underlying_symbol="QQQ"))

    assert response.records_written == 20


def test_ingest_market_context_route(monkeypatch) -> None:
    from backend.app.api.routes import ingestion as ingestion_route

    def _fake_ingest_market_context(request):
        return IngestionResponse(
            records_written=1,
            last_updated_at=datetime(2026, 4, 26, tzinfo=UTC),
            source="manual",
        )

    monkeypatch.setattr(
        ingestion_route.IngestionService,
        "ingest_market_context",
        _fake_ingest_market_context,
    )

    response = ingest_market_context(MarketContextIngestionRequest(spy_return=0.01))

    assert response.records_written == 1
    assert response.source == "manual"


def test_ingestion_post_requires_admin_token(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ingestion_admin_token", "secret")
    client = TestClient(app)

    response = client.post("/api/ingestion/market-context", json={"spy_return": 0.01})

    assert response.status_code == 401


def test_ingestion_post_accepts_admin_token(monkeypatch) -> None:
    from backend.app.api.routes import ingestion as ingestion_route

    monkeypatch.setattr(settings, "ingestion_admin_token", "secret")

    def _fake_ingest_market_context(request):
        return IngestionResponse(
            records_written=1,
            last_updated_at=datetime(2026, 4, 26, tzinfo=UTC),
            source="manual",
        )

    monkeypatch.setattr(
        ingestion_route.IngestionService,
        "ingest_market_context",
        _fake_ingest_market_context,
    )
    client = TestClient(app)

    response = client.post(
        "/api/ingestion/market-context",
        headers={"X-Ingestion-Admin-Token": "secret"},
        json={"spy_return": 0.01},
    )

    assert response.status_code == 200
    assert response.json()["records_written"] == 1


def test_recent_bars_route(monkeypatch) -> None:
    from backend.app.api.routes import ingestion as ingestion_route

    def _fake_recent_bars(ticker, timeframe, limit):
        assert ticker == "SPY"
        assert timeframe == "1d"
        assert limit == 2
        return BarsQueryResponse(
            ticker=ticker,
            timeframe=timeframe,
            bars=[
                BarRecord(
                    ts=datetime(2026, 4, 24, tzinfo=UTC),
                    symbol_id=ticker,
                    timeframe=timeframe,
                    open=100,
                    high=101,
                    low=99,
                    close=100.5,
                    volume=10,
                    vwap=100.2,
                    adjusted=True,
                    source="polygon",
                )
            ],
        )

    monkeypatch.setattr(ingestion_route.IngestionService, "recent_bars", _fake_recent_bars)

    response = get_recent_bars(ticker="SPY", timeframe="1d", limit=2)

    assert response.bars[0].symbol_id == "SPY"


def test_latest_options_chain_route(monkeypatch) -> None:
    from backend.app.api.routes import ingestion as ingestion_route

    def _fake_latest_option_chain(underlying_symbol, limit):
        assert underlying_symbol == "QQQ"
        assert limit == 10
        return OptionChainSnapshotResponse(
            underlying_symbol=underlying_symbol,
            snapshot_ts=None,
            options=[],
        )

    monkeypatch.setattr(
        ingestion_route.IngestionService,
        "latest_option_chain",
        _fake_latest_option_chain,
    )

    response = get_latest_options_chain(underlying_symbol="QQQ", limit=10)

    assert response.underlying_symbol == "QQQ"
    assert response.options == []


def test_data_freshness_route(monkeypatch) -> None:
    from backend.app.api.routes import ingestion as ingestion_route

    def _fake_data_freshness():
        return DataFreshnessResponse(
            data=[
                DataFreshnessRecord(
                    dataset_key="bars:SPY:1d",
                    last_updated_at=datetime(2026, 4, 26, tzinfo=UTC),
                    source="polygon",
                    updated_at=datetime(2026, 4, 26, tzinfo=UTC),
                )
            ]
        )

    monkeypatch.setattr(ingestion_route.IngestionService, "data_freshness", _fake_data_freshness)

    response = get_data_freshness()

    assert response.data[0].dataset_key == "bars:SPY:1d"
