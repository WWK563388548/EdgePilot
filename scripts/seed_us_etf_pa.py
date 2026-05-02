#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.schemas.ingestion import ETFUniverseSeedRequest  # noqa: E402
from backend.app.services.etf_seed_service import ETFSeedService  # noqa: E402


def main() -> None:
    args = _parse_args()
    request = ETFUniverseSeedRequest(
        symbols=args.symbols,
        from_date=_parse_date(args.from_date),
        to_date=_parse_date(args.to_date),
        account_id=args.account_id,
        run_pa_facts=not args.skip_pa_facts,
        run_scanner=not args.skip_scanner,
        min_score=args.min_score,
        max_candidates=args.max_candidates,
    )
    response = ETFSeedService.seed_us_etf_universe(request)
    print(json.dumps(response.model_dump(mode="json"), indent=2, sort_keys=True))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed US ETF daily bars, PA facts, PA setups, and candidates."
    )
    parser.add_argument("--symbols", nargs="*", help="Optional ETF tickers. Defaults to US ETF universe.")
    parser.add_argument("--from", dest="from_date", help="Start date, YYYY-MM-DD.")
    parser.add_argument("--to", dest="to_date", help="End date, YYYY-MM-DD. Defaults to today.")
    parser.add_argument("--account-id", default="acct_local")
    parser.add_argument("--min-score", type=float, default=60.0)
    parser.add_argument("--max-candidates", type=int, default=25)
    parser.add_argument("--skip-pa-facts", action="store_true")
    parser.add_argument("--skip-scanner", action="store_true")
    return parser.parse_args()


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


if __name__ == "__main__":
    main()
