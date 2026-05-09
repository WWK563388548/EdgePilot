# Provider Adapter And Multi-Market Readiness

This note records the scope of the `feat/provider-adapter-multi-market-foundation`
work and the sequencing decision around US ETF research versus Japan expansion.

## Current Scope

This PR introduces a provider-neutral market data boundary without changing the
current production scanner behavior.

Implemented in this PR:

- Daily bar provider contract.
- Provider capability profile.
- Polygon adapter behind the provider interface.
- Symbol metadata normalization.
- Market profile registry for US, JP, HK, CN, and CRYPTO.
- Capability metadata enrichment for the existing `market_data.us_etf_daily`
  capability.
- Existing US ETF refresh and ingestion paths routed through the provider
  interface.

Not implemented in this PR:

- Japan scanner.
- Japan data ingestion.
- HK, A-share, crypto, or options market launch.
- Multi-provider routing.
- Strategy changes.
- Broker adapter.

## Why Not Directly Japan Yet

The release plan still keeps US ETF research and validation first.

The immediate strategy path remains:

1. Finish the US ETF operational loop.
2. Add ETF Rotation / Momentum Horizon as the first production line.
3. Add volatility-scaled sizing and strategy-aware exit profiles.
4. Add MAX_20D analytics as a warning, not as a hard veto.
5. Keep O'Neil-core as a satellite scanner once ETF Rotation exists.
6. Only then begin market expansion, starting with JP daily representation and
   import requirements.

Japan support is represented in the market profile registry now so future code
does not need schema hacks for timezone, currency, calendar, lot size, or
adjustment mode. It does not mean JP daily scanning is production-ready.

## Database Impact

This PR does not add tables or columns, so no migration is required.

Existing rows in `tenant_data_capabilities` remain valid. The existing JSON
`metadata_json` column is used to store provider and market profile metadata.
Older rows that do not have this metadata are backfilled lazily when tenant data
capabilities are listed or checked.

## Current Capability Semantics

`market_data.us_etf_daily` means:

- Provider: Polygon.
- Market: US.
- Asset type: ETF.
- Timeframe: 1d.
- Status is based on actual credential/configuration and runtime checks.
- Metadata describes provider support and the US market profile.

The presence of `JP`, `HK`, `CN`, and `CRYPTO` market profiles means only that
the domain can represent those markets. It does not mean data is configured,
licensed, fresh, tradable, or eligible for scanner output.

## Next After This PR

The next implementation PR should return to the US ETF roadmap:

- ETF Rotation / Momentum Horizon foundation.
- Momentum windows: 3M, 6M, 12M.
- 1M overextension penalty.
- Entry mode: breakout allowed, pullback required, retest required, watch only.
- Validation hooks for backtest, shadow, and paper states.

MAX_20D should follow as an analytics/warning layer after the ETF Rotation
foundation, not as an unvalidated hard reject.
