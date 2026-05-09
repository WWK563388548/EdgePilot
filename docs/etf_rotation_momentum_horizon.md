# ETF Rotation Momentum Horizon

This note records the scope of the `feat/etf-rotation-momentum-horizon`
implementation.

## Goal

US ETF Rotation becomes the first primary strategy line for the private beta.
O'Neil-core remains available as a satellite scanner, but the default candidate
workflow can now generate rotation candidates separately.

This PR implements the scanner foundation, not the full strategy-governance
platform.

The UI should keep a single candidate pool. ETF Rotation and O'Neil are
candidate sources inside that pool, not separate pages. Users can filter by
source and choose which strategy to rescan.

## Implemented

- New strategy name: `etf_rotation_us_etf`.
- New scanner endpoints:
  - `POST /api/pa/scanners/us-etf/rotation`
  - `POST /api/candidates/scanners/us-etf/rotation`
  - `POST /api/candidates/scanners/us-etf/rotation/refresh`
- Account automation can run either O'Neil-core or ETF Rotation by
  `strategy_name`.
- Candidate UI quick rescan and market refresh now use ETF Rotation explicitly.
- The candidate page stays unified and adds source filtering for ETF Rotation
  versus O'Neil satellite results.
- Scanner output still writes to the existing `pa_setups`, `candidates`, and
  `scanner_outcomes` tables.
- No migration is required.

## Scoring Model

ETF Rotation uses the v1.5.1 Momentum Horizon model:

```text
6M momentum: 30
3M momentum: 30
12M momentum: 15
trend score: 15
relative strength vs benchmark: 10
1M overextension penalty: 0 to -20
```

The scanner uses 3M, 6M, and 12M momentum to identify medium-term leadership.
The 1M return is not treated as a positive alpha input. It is used as an
overextension or pullback signal.

## Entry Modes

Every rotation setup includes an `entry_mode`:

- `breakout_allowed`
- `pullback_required`
- `retest_required`
- `watch_only`

These modes are explanation and planning inputs. They do not place broker
orders, and they do not override risk controls.

## Integration With Existing Flow

Rotation candidates use the same downstream operating loop as other candidates:

```text
ETF Rotation scanner
  -> PA setup and candidate
  -> scanner decision explanation
  -> Strat trigger context
  -> risk preview and plan creation
  -> exit engine and outcome review
```

The scanner stores its evidence in:

- `PASetup.entry_plan`
- `PASetup.exit_plan`
- `PASetup.invalidation`
- `Candidate.ai_review_json`

This keeps the current data model stable while making the strategy line
traceable.

O'Neil-core remains useful for strong leader discovery. It should not be treated
as the final production line once ETF Rotation exists; instead it is a
secondary evidence source that can produce candidates in the same candidate pool.

## Out Of Scope

- Japan, HK, A-share, crypto, or all-stock expansion.
- MAX_20D analytics.
- Full walk-forward validation.
- Strategy kill switch tables.
- Paper-trade promotion gates.
- Volatility-scaled position sizing.
- Broker execution.

## Next

The next implementation step should be Volatility Scaled Position Sizing and
strategy-aware exit profiles, followed by MAX_20D as analytics/warning only.
