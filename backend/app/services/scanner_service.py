import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.database import SessionLocal
from backend.app.schemas.business import Candidate
from backend.app.schemas.pa import (
    ETFOneilScannerRequest,
    ETFOneilScannerResponse,
    PAFactsCalculationResponse,
)
from backend.app.services.pa_service import PAService
from backend.app.services.universes import US_ETF_UNIVERSE


@dataclass(frozen=True)
class ScoredETFSetup:
    symbol_id: str
    timeframe: str
    detected_ts: datetime
    setup_type: str
    setup_grade: str
    total_score: float
    trend_score: float
    rs_score: float
    volume_score: float
    base_score: float
    market_score: float
    fundamental_lite_score: float
    risk_stop_score: float
    followthrough_score: float
    entry_plan: dict[str, Any]
    exit_plan: dict[str, Any]
    invalidation: dict[str, Any]
    metrics: dict[str, Any]


class ETFScannerService:
    @staticmethod
    def run_us_etf_oneil_core(request: ETFOneilScannerRequest) -> ETFOneilScannerResponse:
        with SessionLocal() as session:
            response = ETFScannerService.run_us_etf_oneil_core_for_session(session, request)
            session.commit()
            return response

    @staticmethod
    def run_us_etf_oneil_core_for_session(
        session: Session,
        request: ETFOneilScannerRequest,
    ) -> ETFOneilScannerResponse:
        if session.get(db.Account, request.account_id) is None:
            raise ValueError(f"Account not found: {request.account_id}")

        symbols = _normalize_symbols(request.symbols or US_ETF_UNIVERSE)
        if request.recalculate_facts:
            facts_result = PAService.calculate_and_store_daily_facts(
                session=session,
                symbols=symbols,
                timeframe=request.timeframe,
            )
        else:
            facts_result = PAFactsCalculationResponse(
                timeframe=request.timeframe,
                symbols_processed=symbols,
                facts_written=0,
            )
        latest_facts = _latest_facts(session, symbols, request.timeframe)
        ranks_3m = _percentile_ranks(latest_facts, "return_3m")
        ranks_6m = _percentile_ranks(latest_facts, "return_6m")
        market_score, market_context = _market_context_score(session)

        scored_setups: list[ScoredETFSetup] = []
        skipped_symbols = list(facts_result.skipped_symbols)
        for symbol in symbols:
            fact = latest_facts.get(symbol)
            if fact is None:
                if symbol not in skipped_symbols:
                    skipped_symbols.append(symbol)
                continue
            scored = _score_oneil_core_setup(
                fact=fact,
                rank_3m=ranks_3m.get(symbol, 0),
                rank_6m=ranks_6m.get(symbol, 0),
                market_score=market_score,
                market_context=market_context,
            )
            if scored and scored.total_score >= request.min_score:
                scored_setups.append(scored)

        scored_setups.sort(key=lambda item: item.total_score, reverse=True)
        selected_setups = scored_setups[: request.max_candidates]

        candidates: list[Candidate] = []
        for scored in selected_setups:
            setup = _upsert_pa_setup(session, scored)
            session.flush()
            candidate = _upsert_candidate(
                session=session,
                account_id=request.account_id,
                scored=scored,
                setup_id=setup.setup_id,
            )
            candidate_schema = Candidate.model_validate(candidate)
            candidate_schema.pa_setup_grade = setup.setup_grade
            candidate_schema.validation_status = setup.validation_status
            candidates.append(candidate_schema)

        return ETFOneilScannerResponse(
            account_id=request.account_id,
            timeframe=request.timeframe,
            symbols_scanned=sorted(latest_facts),
            facts_written=facts_result.facts_written,
            setups_written=len(selected_setups),
            candidates_written=len(candidates),
            skipped_symbols=skipped_symbols,
            candidates=candidates,
        )


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


def _score_oneil_core_setup(
    *,
    fact: db.PAFact,
    rank_3m: float,
    rank_6m: float,
    market_score: float,
    market_context: dict[str, Any],
) -> ScoredETFSetup | None:
    facts = fact.facts
    close = _number(facts.get("close"))
    high = _number(facts.get("high"))
    low = _number(facts.get("low"))
    sma_20 = _number(facts.get("sma_20"))
    sma_50 = _number(facts.get("sma_50"))
    sma_200 = _number(facts.get("sma_200"))
    high_60d = _number(facts.get("high_60d"))
    base_depth = _number(facts.get("base_depth_60d"))
    pct_from_52w_high = _number(facts.get("pct_from_52w_high"))
    relative_volume = _number(facts.get("relative_volume"))
    volume_sma_20 = _number(facts.get("volume_sma_20"))
    distance_to_sma_20 = _number(facts.get("distance_to_sma_20_pct"))
    sma_20_slope = _number(facts.get("sma_20_slope_pct"))

    if close is None or high is None or low is None:
        return None

    trend_score = _trend_score(
        close=close,
        sma_20=sma_20,
        sma_50=sma_50,
        sma_200=sma_200,
        sma_20_slope=sma_20_slope,
        pct_from_52w_high=pct_from_52w_high,
    )
    rs_score = round((rank_3m * 12.5) + (rank_6m * 12.5), 2)
    volume_score = _volume_score(close=close, volume_sma_20=volume_sma_20, relative_volume=relative_volume)
    setup_type, base_score = _detect_setup_type(
        close=close,
        high=high,
        low=low,
        high_60d=high_60d,
        sma_20=sma_20,
        sma_50=sma_50,
        relative_volume=relative_volume,
        distance_to_sma_20=distance_to_sma_20,
        base_depth=base_depth,
        trend_score=trend_score,
        pct_from_52w_high=pct_from_52w_high,
    )
    if setup_type is None:
        return None

    fundamental_lite_score = 8.0
    total_score = round(
        trend_score
        + rs_score
        + volume_score
        + base_score
        + market_score
        + fundamental_lite_score,
        2,
    )
    initial_stop = _initial_stop(close=close, sma_20=sma_20, sma_50=sma_50)
    risk_stop_score = _risk_stop_score(close=close, initial_stop=initial_stop)
    followthrough_score = _followthrough_score(facts)
    setup_grade = _setup_grade(total_score)
    trigger_price = _trigger_price(setup_type=setup_type, close=close, high=high)
    score_breakdown = {
        "trend": trend_score,
        "relative_strength": rs_score,
        "volume_liquidity": volume_score,
        "base_setup": base_score,
        "market_context": market_score,
        "fundamental_lite": fundamental_lite_score,
        "total": total_score,
    }

    return ScoredETFSetup(
        symbol_id=fact.symbol_id,
        timeframe=fact.timeframe,
        detected_ts=fact.ts,
        setup_type=setup_type,
        setup_grade=setup_grade,
        total_score=total_score,
        trend_score=trend_score,
        rs_score=rs_score,
        volume_score=volume_score,
        base_score=base_score,
        market_score=market_score,
        fundamental_lite_score=fundamental_lite_score,
        risk_stop_score=risk_stop_score,
        followthrough_score=followthrough_score,
        entry_plan={
            "side": "long",
            "trigger_type": "break_above_high" if setup_type != "pullback_to_20ma" else "reclaim_momentum",
            "trigger_price": trigger_price,
            "timeframe": fact.timeframe,
            "score_breakdown": score_breakdown,
        },
        exit_plan={
            "initial_stop": initial_stop,
            "trail_reference": "20ma",
            "first_trim_r": 2.0,
        },
        invalidation={
            "price_below": initial_stop,
            "reason": "daily close below initial stop or setup loses 20/50MA support",
        },
        metrics={
            "oneil_core": score_breakdown,
            "market_context": market_context,
            "facts_snapshot": {
                key: facts.get(key)
                for key in (
                    "close",
                    "relative_volume",
                    "pct_from_52w_high",
                    "base_depth_60d",
                    "sma_20_slope_pct",
                    "return_3m",
                    "return_6m",
                )
            },
        },
    )


def _trend_score(
    *,
    close: float,
    sma_20: float | None,
    sma_50: float | None,
    sma_200: float | None,
    sma_20_slope: float | None,
    pct_from_52w_high: float | None,
) -> float:
    score = 0.0
    if sma_50 is not None and sma_200 is not None and close > sma_50 > sma_200:
        score += 10
    elif sma_50 is not None and close > sma_50:
        score += 5
    if sma_20 is not None and sma_50 is not None and close > sma_20 > sma_50:
        score += 5
    elif sma_20 is not None and close > sma_20:
        score += 3
    if sma_20_slope is not None and sma_20_slope > 0:
        score += 5
    if pct_from_52w_high is not None and pct_from_52w_high >= -0.15:
        score += 5
    return score


def _volume_score(
    *,
    close: float,
    volume_sma_20: float | None,
    relative_volume: float | None,
) -> float:
    score = 0.0
    if volume_sma_20 is not None and volume_sma_20 >= 1_000_000:
        score += 7
    elif volume_sma_20 is not None and volume_sma_20 >= 250_000:
        score += 5
    elif volume_sma_20 is not None and volume_sma_20 >= 100_000:
        score += 3
    if relative_volume is not None and relative_volume >= 1.5:
        score += 5
    elif relative_volume is not None and relative_volume >= 1.0:
        score += 3
    if close >= 20:
        score += 3
    return score


def _detect_setup_type(
    *,
    close: float,
    high: float,
    low: float,
    high_60d: float | None,
    sma_20: float | None,
    sma_50: float | None,
    relative_volume: float | None,
    distance_to_sma_20: float | None,
    base_depth: float | None,
    trend_score: float,
    pct_from_52w_high: float | None,
) -> tuple[str | None, float]:
    if (
        high_60d is not None
        and close >= high_60d * 0.98
        and (base_depth is None or base_depth <= 0.35)
        and (relative_volume is None or relative_volume >= 1.0)
    ):
        return "breakout", 15.0
    if (
        sma_20 is not None
        and sma_50 is not None
        and distance_to_sma_20 is not None
        and abs(distance_to_sma_20) <= 0.04
        and close > sma_50
        and (relative_volume is None or relative_volume <= 1.25)
    ):
        return "pullback_to_20ma", 12.0
    if (
        sma_50 is not None
        and low < sma_50 < close
        and (relative_volume is None or relative_volume >= 1.0)
    ):
        return "failed_breakdown_reclaim", 11.0
    if pct_from_52w_high is not None and pct_from_52w_high >= -0.12 and trend_score >= 18:
        return "oneil_leader_watch", 9.0
    return None, 0.0


def _initial_stop(*, close: float, sma_20: float | None, sma_50: float | None) -> float:
    stop_candidates = [close * 0.92]
    if sma_20 is not None and sma_20 < close:
        stop_candidates.append(sma_20 * 0.98)
    if sma_50 is not None and sma_50 < close:
        stop_candidates.append(sma_50 * 0.98)
    return round(max(stop_candidates), 2)


def _risk_stop_score(*, close: float, initial_stop: float) -> float:
    stop_distance = 1 - (initial_stop / close)
    if stop_distance <= 0.08:
        return 10.0
    if stop_distance <= 0.12:
        return 7.0
    return 4.0


def _followthrough_score(facts: dict[str, Any]) -> float:
    score = 0.0
    if facts.get("close_near_high"):
        score += 5
    relative_volume = _number(facts.get("relative_volume"))
    if relative_volume is not None and relative_volume >= 1.2:
        score += 5
    return score


def _trigger_price(*, setup_type: str, close: float, high: float) -> float:
    if setup_type == "pullback_to_20ma":
        return round(close * 1.005, 2)
    return round(high * 1.001, 2)


def _setup_grade(total_score: float) -> str:
    if total_score >= 85:
        return "A"
    if total_score >= 75:
        return "B"
    if total_score >= 65:
        return "C"
    return "D"


def _upsert_pa_setup(session: Session, scored: ScoredETFSetup) -> db.PASetup:
    setup_id = _setup_id(scored)
    setup = session.get(db.PASetup, setup_id)
    payload = {
        "symbol_id": scored.symbol_id,
        "timeframe": scored.timeframe,
        "detected_ts": scored.detected_ts,
        "setup_type": scored.setup_type,
        "setup_grade": scored.setup_grade,
        "pa_quality_score": scored.total_score,
        "structure_score": scored.trend_score,
        "location_score": scored.base_score,
        "volume_score": scored.volume_score,
        "trend_rs_score": scored.rs_score,
        "context_score": scored.market_score,
        "risk_stop_score": scored.risk_stop_score,
        "followthrough_score": scored.followthrough_score,
        "entry_plan": scored.entry_plan,
        "exit_plan": scored.exit_plan,
        "invalidation": scored.invalidation,
        "status": "candidate" if scored.total_score >= 75 else "watch",
        "validation_status": "shadow_only",
        "updated_at": datetime.now(UTC),
    }
    if setup is None:
        setup = db.PASetup(setup_id=setup_id, **payload)
        session.add(setup)
    else:
        for key, value in payload.items():
            setattr(setup, key, value)
    return setup


def _upsert_candidate(
    *,
    session: Session,
    account_id: str,
    scored: ScoredETFSetup,
    setup_id: str,
) -> db.Candidate:
    candidate_id = _candidate_id(account_id, scored)
    candidate = session.get(db.Candidate, candidate_id)
    decision = "candidate" if scored.total_score >= 75 else "watch"
    payload = {
        "account_id": account_id,
        "symbol_id": scored.symbol_id,
        "scan_date": scored.detected_ts.date(),
        "strategy_name": "oneil_core_us_etf",
        "setup_type": scored.setup_type,
        "pa_setup_id": setup_id,
        "score_total": scored.total_score,
        "entry_trigger": scored.entry_plan.get("trigger_price"),
        "initial_stop": scored.exit_plan.get("initial_stop"),
        "decision": decision,
        "option_suitability": "stock_etf_only",
        "ai_review_json": _candidate_ai_review_placeholder(scored, setup_id),
    }
    if candidate is None:
        candidate = db.Candidate(candidate_id=candidate_id, **payload)
        session.add(candidate)
    else:
        for key, value in payload.items():
            setattr(candidate, key, value)
    return candidate


def _candidate_ai_review_placeholder(scored: ScoredETFSetup, setup_id: str) -> str:
    return json.dumps(
        {
            "source": "pa_scanner_v1",
            "pa_setup_id": setup_id,
            "validation_status": "shadow_only",
            "score_breakdown": scored.entry_plan["score_breakdown"],
        },
        sort_keys=True,
    )


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


def _normalize_symbols(symbols: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for symbol in symbols:
        ticker = symbol.strip().upper()
        if ticker and ticker not in seen:
            normalized.append(ticker)
            seen.add(ticker)
    return normalized


def _number(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _setup_id(scored: ScoredETFSetup) -> str:
    return (
        f"pasetup_{scored.symbol_id.lower()}_{scored.timeframe}_"
        f"{scored.detected_ts.date().isoformat()}_{scored.setup_type}"
    )


def _candidate_id(account_id: str, scored: ScoredETFSetup) -> str:
    return (
        f"cand_pa_{account_id}_{scored.symbol_id}_{scored.detected_ts.date().isoformat()}_"
        f"{scored.setup_type}"
    ).lower()
