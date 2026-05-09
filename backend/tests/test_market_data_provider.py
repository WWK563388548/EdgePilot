from datetime import UTC, date, datetime

from backend.app.services.market_data_provider import PolygonMarketDataProvider
from backend.app.services.market_profiles import market_profile


class FakePolygonClient:
    def list_daily_bars(self, symbol, from_date, to_date):
        assert symbol == "SPY"
        assert from_date == date(2026, 5, 1)
        assert to_date == date(2026, 5, 8)
        return [
            {
                "t": int(datetime(2026, 5, 8, tzinfo=UTC).timestamp() * 1000),
                "o": 420,
                "h": 430,
                "l": 418,
                "c": 428,
                "v": 123456,
                "vw": 426,
            },
            {"c": 999},
        ]


def test_polygon_adapter_normalizes_daily_bars_and_metadata() -> None:
    provider = PolygonMarketDataProvider(FakePolygonClient())

    bars = provider.list_daily_bars("SPY", date(2026, 5, 1), date(2026, 5, 8))
    metadata = provider.get_symbol_metadata("spy")

    assert provider.provider_id == "polygon"
    assert provider.profile.capability_key == "market_data.us_etf_daily"
    assert len(bars) == 1
    assert bars[0].ts == datetime(2026, 5, 8, tzinfo=UTC)
    assert bars[0].close == 428
    assert bars[0].source == "polygon"
    assert metadata.symbol_id == "SPY"
    assert metadata.market == "US"
    assert metadata.asset_type == "ETF"
    assert metadata.currency == "USD"


def test_market_profiles_represent_first_multi_market_targets() -> None:
    us = market_profile("US")
    jp = market_profile("JP")
    crypto = market_profile("CRYPTO")

    assert us.trading_timezone == "America/New_York"
    assert us.default_lot_size == 1
    assert jp.trading_timezone == "Asia/Tokyo"
    assert jp.default_lot_size == 100
    assert jp.calendar_key == "XTKS"
    assert crypto.calendar_key == "24_7"
