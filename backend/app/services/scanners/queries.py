from __future__ import annotations

from statistics import pstdev
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.services.scanners.common import _number
from backend.app.services.strat_service import StratService

def _latest_facts(
    session: Session,
    symbols: list[str],
    timeframe: str,
) -> dict[str, db.PAFact]:
    latest: dict[str, db.PAFact] = {}
    for symbol in symbols:
        fact = session.scalar(
            select(db.PAFact)
            .where(db.PAFact.symbol_id == symbol, db.PAFact.timeframe == timeframe)
            .order_by(db.PAFact.ts.desc())
            .limit(1)
        )
        if fact is not None:
            latest[symbol] = fact
    return latest

def _latest_strat_signals(
    session: Session,
    symbols: list[str],
    timeframe: str,
) -> dict[str, db.StratSignal]:
    latest: dict[str, db.StratSignal] = {}
    for symbol in symbols:
        signal = session.scalar(
            select(db.StratSignal)
            .where(db.StratSignal.symbol_id == symbol, db.StratSignal.timeframe == timeframe)
            .order_by(db.StratSignal.ts.desc())
            .limit(1)
        )
        if signal is not None:
            latest[symbol] = signal
    return latest

def _latest_strat_plans(
    *,
    session: Session,
    latest_facts: dict[str, db.PAFact],
    timeframe: str,
) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for symbol, fact in latest_facts.items():
        latest[symbol] = StratService.latest_trigger_plan(
            session=session,
            symbol=symbol,
            timeframe=timeframe,
            reference_ts=fact.ts,
            facts=fact.facts,
        ).to_payload()
    return latest

def _market_context_score(session: Session) -> tuple[float, dict[str, Any]]:
    context = session.scalar(
        select(db.MarketContextSnapshot)
        .where(db.MarketContextSnapshot.market == "global")
        .order_by(db.MarketContextSnapshot.snapshot_ts.desc())
        .limit(1)
    )
    if context is None:
        return 8.0, {"source": "missing", "risk_level": "unknown"}
    if context.risk_level == "shock" or context.us_bias == "bearish":
        score = 0.0
    elif context.risk_level == "watch":
        score = 5.0
    else:
        score = 10.0
    return score, {
        "source": "market_context_snapshots",
        "snapshot_ts": context.snapshot_ts.isoformat(),
        "risk_level": context.risk_level,
        "us_bias": context.us_bias,
    }

def _percentile_ranks(latest_facts: dict[str, db.PAFact], key: str) -> dict[str, float]:
    values = [
        (symbol, _number(fact.facts.get(key)))
        for symbol, fact in latest_facts.items()
        if _number(fact.facts.get(key)) is not None
    ]
    if not values:
        return {symbol: 0 for symbol in latest_facts}
    if len(values) == 1:
        return {values[0][0]: 1.0}
    values.sort(key=lambda item: item[1])
    return {symbol: rank / (len(values) - 1) for rank, (symbol, _value) in enumerate(values)}

def _one_month_return_zscores(
    *,
    session: Session,
    symbols: list[str],
    timeframe: str,
    latest_facts: dict[str, db.PAFact],
) -> dict[str, float | None]:
    zscores: dict[str, float | None] = {}
    for symbol in symbols:
        latest_fact = latest_facts.get(symbol)
        latest_return = _number(latest_fact.facts.get("return_1m")) if latest_fact else None
        rows = session.scalars(
            select(db.PAFact)
            .where(db.PAFact.symbol_id == symbol, db.PAFact.timeframe == timeframe)
            .order_by(db.PAFact.ts.asc())
        ).all()
        values = [_number(row.facts.get("return_1m")) for row in rows]
        sample = [value for value in values if value is not None]
        if latest_return is None or len(sample) < 20:
            zscores[symbol] = None
            continue
        average = sum(sample) / len(sample)
        deviation = pstdev(sample)
        zscores[symbol] = round((latest_return - average) / deviation, 6) if deviation > 0 else 0.0
    return zscores

def _normalize_symbols(symbols: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for symbol in symbols:
        ticker = symbol.strip().upper()
        if ticker and ticker not in seen:
            normalized.append(ticker)
            seen.add(ticker)
    return normalized
