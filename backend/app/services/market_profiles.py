from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketProfile:
    market: str
    name: str
    trading_timezone: str
    currency: str
    calendar_key: str
    default_exchange: str | None
    default_tick_size: float | None
    default_lot_size: int | None
    adjusted_price_mode: str
    corporate_action_mode: str
    daily_session_close: str | None

    def metadata(self) -> dict[str, str | float | int | None]:
        return {
            "market": self.market,
            "name": self.name,
            "trading_timezone": self.trading_timezone,
            "currency": self.currency,
            "calendar_key": self.calendar_key,
            "default_exchange": self.default_exchange,
            "default_tick_size": self.default_tick_size,
            "default_lot_size": self.default_lot_size,
            "adjusted_price_mode": self.adjusted_price_mode,
            "corporate_action_mode": self.corporate_action_mode,
            "daily_session_close": self.daily_session_close,
        }


MARKET_PROFILES: dict[str, MarketProfile] = {
    "US": MarketProfile(
        market="US",
        name="United States",
        trading_timezone="America/New_York",
        currency="USD",
        calendar_key="XNYS",
        default_exchange=None,
        default_tick_size=0.01,
        default_lot_size=1,
        adjusted_price_mode="split_dividend_adjusted",
        corporate_action_mode="provider_adjusted_daily",
        daily_session_close="16:00",
    ),
    "JP": MarketProfile(
        market="JP",
        name="Japan",
        trading_timezone="Asia/Tokyo",
        currency="JPY",
        calendar_key="XTKS",
        default_exchange="TSE",
        default_tick_size=None,
        default_lot_size=100,
        adjusted_price_mode="split_adjusted_required",
        corporate_action_mode="provider_or_import_required",
        daily_session_close="15:30",
    ),
    "HK": MarketProfile(
        market="HK",
        name="Hong Kong",
        trading_timezone="Asia/Hong_Kong",
        currency="HKD",
        calendar_key="XHKG",
        default_exchange="HKEX",
        default_tick_size=None,
        default_lot_size=None,
        adjusted_price_mode="split_adjusted_required",
        corporate_action_mode="provider_or_import_required",
        daily_session_close="16:00",
    ),
    "CN": MarketProfile(
        market="CN",
        name="China A-share",
        trading_timezone="Asia/Shanghai",
        currency="CNY",
        calendar_key="XSHG_XSHE",
        default_exchange=None,
        default_tick_size=0.01,
        default_lot_size=100,
        adjusted_price_mode="split_dividend_adjusted_required",
        corporate_action_mode="provider_or_import_required",
        daily_session_close="15:00",
    ),
    "CRYPTO": MarketProfile(
        market="CRYPTO",
        name="Crypto",
        trading_timezone="UTC",
        currency="USD",
        calendar_key="24_7",
        default_exchange=None,
        default_tick_size=None,
        default_lot_size=None,
        adjusted_price_mode="not_applicable",
        corporate_action_mode="not_applicable",
        daily_session_close="00:00",
    ),
}


def market_profile(market: str) -> MarketProfile:
    key = market.strip().upper()
    if key not in MARKET_PROFILES:
        raise ValueError(f"Unsupported market profile: {market}")
    return MARKET_PROFILES[key]
