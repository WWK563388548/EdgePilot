from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Protocol

from backend.app.services.market_profiles import MarketProfile, market_profile
from backend.app.services.polygon_client import PolygonClient


@dataclass(frozen=True)
class DailyBar:
    ts: datetime
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None
    vwap: float | None = None
    adjusted: bool = True
    source: str = "unknown"


@dataclass(frozen=True)
class SymbolMetadata:
    symbol_id: str
    ticker: str
    market: str
    asset_type: str
    currency: str | None = None
    exchange: str | None = None
    name: str | None = None
    sector: str | None = None
    industry: str | None = None
    active: bool = True
    source: str = "unknown"


@dataclass(frozen=True)
class ProviderCapabilityProfile:
    capability_key: str
    provider: str
    market: str
    asset_type: str
    timeframe: str
    supports_daily_bars: bool
    supports_intraday_bars: bool = False
    supports_symbol_metadata: bool = False
    supports_corporate_actions: bool = False
    freshness_probe_symbol: str | None = None
    rate_limit_per_minute: int | None = None
    market_profile: MarketProfile | None = None


class DailyBarProvider(Protocol):
    provider_id: str
    profile: ProviderCapabilityProfile

    def list_daily_bars(
        self,
        symbol: str,
        from_date: date,
        to_date: date,
    ) -> list[DailyBar]:
        ...

    def get_symbol_metadata(self, symbol: str) -> SymbolMetadata:
        ...


POLYGON_US_ETF_DAILY_PROFILE = ProviderCapabilityProfile(
    capability_key="market_data.us_etf_daily",
    provider="polygon",
    market="US",
    asset_type="etf",
    timeframe="1d",
    supports_daily_bars=True,
    supports_symbol_metadata=True,
    freshness_probe_symbol="SPY",
    rate_limit_per_minute=None,
    market_profile=market_profile("US"),
)


class PolygonMarketDataProvider:
    provider_id = "polygon"
    profile = POLYGON_US_ETF_DAILY_PROFILE

    def __init__(self, client: PolygonClient) -> None:
        self.client = client

    def list_daily_bars(
        self,
        symbol: str,
        from_date: date,
        to_date: date,
    ) -> list[DailyBar]:
        rows = self.client.list_daily_bars(symbol, from_date, to_date)
        return [
            bar
            for row in rows
            if (bar := daily_bar_from_polygon_aggregate(row, source=self.provider_id)) is not None
        ]

    def get_symbol_metadata(self, symbol: str) -> SymbolMetadata:
        ticker = symbol.strip().upper()
        return SymbolMetadata(
            symbol_id=ticker,
            ticker=ticker,
            market=self.profile.market,
            asset_type=self.profile.asset_type,
            currency=self.profile.market_profile.currency if self.profile.market_profile else "USD",
            active=True,
            source=self.provider_id,
        )


def daily_bar_from_polygon_aggregate(row: dict[str, Any], *, source: str) -> DailyBar | None:
    timestamp_ms = row.get("t")
    if timestamp_ms is None:
        return None
    return DailyBar(
        ts=datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC),
        open=row.get("o"),
        high=row.get("h"),
        low=row.get("l"),
        close=row.get("c"),
        volume=row.get("v"),
        vwap=row.get("vw"),
        adjusted=True,
        source=source,
    )


def coerce_daily_bar(row: DailyBar | dict[str, Any], *, source: str) -> DailyBar | None:
    if isinstance(row, DailyBar):
        return row
    return daily_bar_from_polygon_aggregate(row, source=source)


def provider_id(provider: object) -> str:
    return str(getattr(provider, "provider_id", "polygon"))


def symbol_metadata(provider: object, symbol: str) -> SymbolMetadata:
    metadata_fn = getattr(provider, "get_symbol_metadata", None)
    if callable(metadata_fn):
        return metadata_fn(symbol)
    ticker = symbol.strip().upper()
    return SymbolMetadata(
        symbol_id=ticker,
        ticker=ticker,
        market="US",
        asset_type="etf",
        currency="USD",
        active=True,
        source=provider_id(provider),
    )
