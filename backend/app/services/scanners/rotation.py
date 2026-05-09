from __future__ import annotations

from typing import Any

from backend.app import models as db
from backend.app.schemas.scanner import ScannerDecision
from backend.app.services.scanners.common import (
    ETF_ROTATION_US_ETF_STRATEGY,
    ETF_ROTATION_US_ETF_VERSION,
    ScoredETFSetup,
    _add_boolean_rule,
    _add_rule_key,
    _add_score_rule,
    _apply_strat_confirmation,
    _dedupe,
    _initial_stop,
    _number,
    _risk_stop_score,
    _setup_grade,
    _trend_score,
)

def _score_etf_rotation_setup(
    *,
    fact: db.PAFact,
    rank_3m: float,
    rank_6m: float,
    rank_12m: float,
    one_month_zscore: float | None,
    benchmark_fact: db.PAFact | None,
    benchmark_symbol: str,
    market_score: float,
    market_context: dict[str, Any],
    strat_signal: db.StratSignal | None,
    strat_plan: dict[str, Any] | None,
) -> ScoredETFSetup | None:
    facts = fact.facts
    close = _number(facts.get("close"))
    high = _number(facts.get("high"))
    sma_20 = _number(facts.get("sma_20"))
    sma_50 = _number(facts.get("sma_50"))
    sma_200 = _number(facts.get("sma_200"))
    pct_from_52w_high = _number(facts.get("pct_from_52w_high"))
    sma_20_slope = _number(facts.get("sma_20_slope_pct"))
    return_1m = _number(facts.get("return_1m"))
    return_3m = _number(facts.get("return_3m"))
    return_6m = _number(facts.get("return_6m"))
    return_12m = _number(facts.get("return_12m"))
    distance_to_sma_20 = _number(facts.get("distance_to_sma_20_pct"))

    if close is None or high is None:
        return None

    momentum_6m_score = _rank_score(rank_6m, 30)
    momentum_3m_score = _rank_score(rank_3m, 30)
    momentum_12m_score = _rank_score(rank_12m, 15)
    trend_score = round(
        _trend_score(
            close=close,
            sma_20=sma_20,
            sma_50=sma_50,
            sma_200=sma_200,
            sma_20_slope=sma_20_slope,
            pct_from_52w_high=pct_from_52w_high,
        )
        * 0.6,
        2,
    )
    benchmark_score, benchmark_metrics = _benchmark_relative_strength_score(
        facts=facts,
        benchmark_facts=benchmark_fact.facts if benchmark_fact else None,
        benchmark_symbol=benchmark_symbol,
    )
    overextension_penalty = _one_month_overextension_penalty(one_month_zscore)
    medium_term_strong = rank_3m >= 0.65 and rank_6m >= 0.65
    entry_mode = _rotation_entry_mode(
        medium_term_strong=medium_term_strong,
        rank_3m=rank_3m,
        rank_6m=rank_6m,
        one_month_zscore=one_month_zscore,
    )
    setup_type = _rotation_setup_type(
        entry_mode=entry_mode,
        medium_term_strong=medium_term_strong,
        rank_3m=rank_3m,
        rank_6m=rank_6m,
        one_month_zscore=one_month_zscore,
    )
    entry_mode_score = _entry_mode_score(entry_mode)
    raw_total = (
        momentum_6m_score
        + momentum_3m_score
        + momentum_12m_score
        + trend_score
        + benchmark_score
        + overextension_penalty
    )
    total_score = round(max(0.0, min(100.0, raw_total)), 2)
    initial_stop = _initial_stop(close=close, sma_20=sma_20, sma_50=sma_50)
    risk_stop_score = _risk_stop_score(close=close, initial_stop=initial_stop)
    setup_grade = _setup_grade(total_score)
    decision = "candidate" if total_score >= 75 and entry_mode != "watch_only" else "watch"
    trigger_type = _rotation_trigger_type(entry_mode)
    trigger_price = _rotation_trigger_price(
        close=close,
        high=high,
        sma_20=sma_20,
        entry_mode=entry_mode,
    )
    score_breakdown = {
        "total": total_score,
        "momentum_6m": momentum_6m_score,
        "momentum_3m": momentum_3m_score,
        "momentum_12m": momentum_12m_score,
        "trend": trend_score,
        "benchmark_relative_strength": benchmark_score,
        "overextension_penalty": overextension_penalty,
    }
    scanner_decision = _rotation_scanner_decision(
        benchmark_metrics=benchmark_metrics,
        decision=decision,
        distance_to_sma_20=distance_to_sma_20,
        entry_mode=entry_mode,
        initial_stop=initial_stop,
        market_context=market_context,
        market_score=market_score,
        medium_term_strong=medium_term_strong,
        one_month_zscore=one_month_zscore,
        rank_3m=rank_3m,
        rank_6m=rank_6m,
        rank_12m=rank_12m,
        returns={
            "return_1m": return_1m,
            "return_3m": return_3m,
            "return_6m": return_6m,
            "return_12m": return_12m,
        },
        score_breakdown=score_breakdown,
        setup_grade=setup_grade,
        setup_type=setup_type,
        strat_plan=strat_plan,
        strat_signal=strat_signal,
        total_score=total_score,
        trend_score=trend_score,
        trigger_price=trigger_price,
    )
    decision = scanner_decision.get("decision", decision)

    return ScoredETFSetup(
        symbol_id=fact.symbol_id,
        timeframe=fact.timeframe,
        detected_ts=fact.ts,
        setup_type=setup_type,
        setup_grade=setup_grade,
        total_score=total_score,
        trend_score=trend_score,
        rs_score=benchmark_score,
        volume_score=0,
        base_score=entry_mode_score,
        market_score=market_score,
        fundamental_lite_score=0,
        risk_stop_score=risk_stop_score,
        followthrough_score=0,
        decision=decision,
        entry_plan={
            "side": "long",
            "strategy_name": ETF_ROTATION_US_ETF_STRATEGY,
            "entry_mode": entry_mode,
            "trigger_type": trigger_type,
            "trigger_price": trigger_price,
            "timeframe": fact.timeframe,
            "desired_pullback_level": round(sma_20, 2) if sma_20 is not None else None,
            "strat_trigger_plan": strat_plan,
            "momentum_horizon": {
                "return_1m": return_1m,
                "return_3m": return_3m,
                "return_6m": return_6m,
                "return_12m": return_12m,
                "rank_3m": round(rank_3m * 100, 1),
                "rank_6m": round(rank_6m * 100, 1),
                "rank_12m": round(rank_12m * 100, 1),
                "one_month_zscore": round(one_month_zscore, 2)
                if one_month_zscore is not None
                else None,
            },
            "score_breakdown": score_breakdown,
            "scanner_decision": scanner_decision,
        },
        exit_plan={
            "initial_stop": initial_stop,
            "trail_reference": "20ma",
            "exit_profile": "etf_rotation_trend",
            "first_trim_r": 2.0,
        },
        invalidation={
            "price_below": initial_stop,
            "reason": "daily close below initial stop or medium-term momentum loses 20/50MA support",
        },
        metrics={
            "momentum_horizon": score_breakdown,
            "entry_mode": entry_mode,
            "benchmark_relative_strength": benchmark_metrics,
        },
        scanner_decision=scanner_decision,
        strategy_name=ETF_ROTATION_US_ETF_STRATEGY,
        strategy_version=ETF_ROTATION_US_ETF_VERSION,
    )

def _rotation_scanner_decision(
    *,
    benchmark_metrics: dict[str, Any],
    decision: str,
    distance_to_sma_20: float | None,
    entry_mode: str,
    initial_stop: float,
    market_context: dict[str, Any],
    market_score: float,
    medium_term_strong: bool,
    one_month_zscore: float | None,
    rank_3m: float,
    rank_6m: float,
    rank_12m: float,
    returns: dict[str, float | None],
    score_breakdown: dict[str, float],
    setup_grade: str,
    setup_type: str,
    strat_plan: dict[str, Any] | None,
    strat_signal: db.StratSignal | None,
    total_score: float,
    trend_score: float,
    trigger_price: float,
) -> dict[str, Any]:
    passed_rules: list[dict[str, Any]] = []
    failed_rules: list[dict[str, Any]] = []
    _add_boolean_rule(
        passed_rules,
        failed_rules,
        passed=medium_term_strong,
        passed_key="rotation_medium_momentum_leader",
        failed_key="rotation_medium_momentum_weak",
    )
    _add_boolean_rule(
        passed_rules,
        failed_rules,
        passed=rank_12m >= 0.5,
        passed_key="rotation_12m_support",
        failed_key="rotation_12m_lagging",
    )
    _add_score_rule(
        passed_rules,
        failed_rules,
        score=trend_score,
        max_score=15,
        threshold=9,
        passed_key="trend_aligned",
        failed_key="trend_needs_alignment",
    )
    _add_score_rule(
        passed_rules,
        failed_rules,
        score=float(benchmark_metrics.get("score") or 0),
        max_score=10,
        threshold=7,
        passed_key="rotation_benchmark_rs_leader",
        failed_key="rotation_benchmark_rs_lagging",
    )
    if entry_mode == "breakout_allowed":
        _add_rule_key(passed_rules, key="rotation_breakout_allowed", passed=True)
    elif entry_mode == "pullback_required":
        _add_rule_key(failed_rules, key="rotation_pullback_required", passed=False)
    elif entry_mode == "retest_required":
        _add_rule_key(failed_rules, key="rotation_retest_required", passed=False)
    else:
        _add_rule_key(failed_rules, key="rotation_watch_only", passed=False)
    if one_month_zscore is not None and one_month_zscore > 2:
        _add_rule_key(failed_rules, key="rotation_one_month_overextended", passed=False)
    if one_month_zscore is not None and one_month_zscore < -1 and medium_term_strong:
        _add_rule_key(passed_rules, key="rotation_healthy_pullback", passed=True)

    watch_reasons = ["shadow_only"]
    upgrade_conditions = ["respect_strategy_entry_mode", "hold_above_20_50ma"]
    risk_notes = ["initial_stop_required", "invalidates_below_stop"]
    if decision == "watch":
        watch_reasons.append("score_below_candidate")
    if entry_mode == "pullback_required":
        watch_reasons.append("rotation_pullback_required")
        upgrade_conditions.append("pullback_to_20ma_or_reclaim")
        risk_notes.append("do_not_chase_overextended_rotation")
    elif entry_mode == "retest_required":
        watch_reasons.append("rotation_retest_required")
        upgrade_conditions.append("reclaim_after_pullback")
    elif entry_mode == "watch_only":
        watch_reasons.append("rotation_watch_only")
        upgrade_conditions.append("medium_momentum_reasserts")
    else:
        upgrade_conditions.append("break_above_trigger")
    if one_month_zscore is not None and one_month_zscore > 2:
        risk_notes.append("one_month_overextension")
    if distance_to_sma_20 is not None and distance_to_sma_20 > 0.12:
        risk_notes.append("extended_from_20ma")
    if market_score < 8:
        watch_reasons.append("market_context_caution")
        risk_notes.append("market_context_caution")

    final_decision, strat_confirmation = _apply_strat_confirmation(
        decision=decision,
        failed_rules=failed_rules,
        passed_rules=passed_rules,
        risk_notes=risk_notes,
        strat_signal=strat_signal,
        strat_plan=strat_plan,
        upgrade_conditions=upgrade_conditions,
        watch_reasons=watch_reasons,
    )
    return ScannerDecision(
        version=ETF_ROTATION_US_ETF_VERSION,
        strategy=ETF_ROTATION_US_ETF_STRATEGY,
        decision=final_decision,
        failed_rules=failed_rules,
        initial_stop=initial_stop,
        metrics={
            **returns,
            "entry_mode": entry_mode,
            "market_context": market_context,
            "one_month_zscore": round(one_month_zscore, 2)
            if one_month_zscore is not None
            else None,
            "rank_3m": round(rank_3m * 100, 1),
            "rank_6m": round(rank_6m * 100, 1),
            "rank_12m": round(rank_12m * 100, 1),
            "score_breakdown": score_breakdown,
            "benchmark_relative_strength": benchmark_metrics,
            "strat_trigger_plan": strat_plan,
        },
        passed_rules=passed_rules,
        risk_notes=_dedupe(risk_notes),
        score=total_score,
        setup_grade=setup_grade,
        setup_type=setup_type,
        total_score=total_score,
        strat_confirmation=strat_confirmation,
        trigger_price=trigger_price,
        upgrade_conditions=_dedupe(upgrade_conditions),
        validation_status="shadow_only",
        watch_reasons=_dedupe(watch_reasons),
    ).model_dump(exclude_none=True)

def _rank_score(rank: float, max_score: float) -> float:
    return round(max(0.0, min(1.0, rank)) * max_score, 2)

def _benchmark_relative_strength_score(
    *,
    facts: dict[str, Any],
    benchmark_facts: dict[str, Any] | None,
    benchmark_symbol: str,
) -> tuple[float, dict[str, Any]]:
    comparisons: list[bool] = []
    deltas: dict[str, float | None] = {}
    for key in ("return_3m", "return_6m", "return_12m"):
        own = _number(facts.get(key))
        benchmark = _number(benchmark_facts.get(key)) if benchmark_facts else None
        delta = own - benchmark if own is not None and benchmark is not None else None
        deltas[f"{key}_vs_benchmark"] = round(delta, 6) if delta is not None else None
        if delta is not None:
            comparisons.append(delta >= 0)
    if not comparisons:
        score = 5.0
    else:
        score = round((sum(1 for passed in comparisons if passed) / len(comparisons)) * 10, 2)
    return score, {
        "benchmark_symbol": benchmark_symbol,
        "score": score,
        **deltas,
    }

def _one_month_overextension_penalty(one_month_zscore: float | None) -> float:
    if one_month_zscore is None:
        return 0.0
    if one_month_zscore > 3:
        return -20.0
    if one_month_zscore > 2:
        return -10.0
    return 0.0

def _rotation_entry_mode(
    *,
    medium_term_strong: bool,
    rank_3m: float,
    rank_6m: float,
    one_month_zscore: float | None,
) -> str:
    if one_month_zscore is not None and one_month_zscore > 3:
        return "watch_only"
    if not medium_term_strong:
        return "watch_only"
    if one_month_zscore is not None and one_month_zscore > 2:
        return "pullback_required"
    if one_month_zscore is not None and one_month_zscore < -1:
        return "retest_required"
    if rank_3m >= 0.65 and rank_6m >= 0.65:
        return "breakout_allowed"
    return "watch_only"

def _rotation_setup_type(
    *,
    entry_mode: str,
    medium_term_strong: bool,
    rank_3m: float,
    rank_6m: float,
    one_month_zscore: float | None,
) -> str:
    if entry_mode == "watch_only" and one_month_zscore is not None and one_month_zscore > 3:
        return "etf_rotation_overextended_leader"
    if entry_mode in {"pullback_required", "retest_required"}:
        return "etf_rotation_pullback_watch"
    if medium_term_strong:
        return "etf_rotation_leader"
    if rank_3m >= 0.65 and rank_6m < 0.5:
        return "etf_rotation_improving"
    return "etf_rotation_weakening"

def _entry_mode_score(entry_mode: str) -> float:
    return {
        "breakout_allowed": 15.0,
        "pullback_required": 10.0,
        "retest_required": 9.0,
        "watch_only": 4.0,
    }.get(entry_mode, 0.0)

def _rotation_trigger_type(entry_mode: str) -> str:
    if entry_mode == "breakout_allowed":
        return "break_above_high"
    if entry_mode == "pullback_required":
        return "pullback_reclaim_20ma"
    if entry_mode == "retest_required":
        return "retest_reclaim"
    return "wait_for_rotation_reclaim"

def _rotation_trigger_price(
    *,
    close: float,
    high: float,
    sma_20: float | None,
    entry_mode: str,
) -> float:
    if entry_mode == "breakout_allowed":
        return round(high * 1.001, 2)
    if sma_20 is not None and entry_mode in {"pullback_required", "retest_required"}:
        return round(max(sma_20, close * 0.98) * 1.005, 2)
    return round(close * 1.005, 2)
