from __future__ import annotations

from typing import Any

from backend.app import models as db
from backend.app.schemas.scanner import ScannerDecision
from backend.app.services.scanners.common import (
    ScoredETFSetup,
    SetupQuality,
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

def _score_oneil_core_setup(
    *,
    fact: db.PAFact,
    rank_3m: float,
    rank_6m: float,
    market_score: float,
    market_context: dict[str, Any],
    strat_signal: db.StratSignal | None,
    strat_plan: dict[str, Any] | None,
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
    close_position = _number(facts.get("close_position_in_range"))
    pct_from_52w_high = _number(facts.get("pct_from_52w_high"))
    relative_volume = _number(facts.get("relative_volume"))
    volume_sma_20 = _number(facts.get("volume_sma_20"))
    distance_to_sma_20 = _number(facts.get("distance_to_sma_20_pct"))
    sma_20_slope = _number(facts.get("sma_20_slope_pct"))
    volatility_contraction = bool(facts.get("volatility_contraction"))

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
    rs_score = _rs_score(rank_3m=rank_3m, rank_6m=rank_6m)
    volume_score = _volume_score(close=close, volume_sma_20=volume_sma_20, relative_volume=relative_volume)
    setup_quality = _detect_setup_quality(
        close=close,
        close_position=close_position,
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
        volatility_contraction=volatility_contraction,
    )
    if setup_quality is None:
        return None
    setup_type = setup_quality.setup_type
    base_score = setup_quality.base_score

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
    base_decision = "candidate" if total_score >= 75 else "watch"
    score_breakdown = {
        "trend": trend_score,
        "relative_strength": rs_score,
        "volume_liquidity": volume_score,
        "base_setup": base_score,
        "market_context": market_score,
        "fundamental_lite": fundamental_lite_score,
        "total": total_score,
    }
    scanner_decision = _scanner_decision(
        base_score=base_score,
        base_depth=base_depth,
        close_position=close_position,
        decision=base_decision,
        distance_to_sma_20=distance_to_sma_20,
        initial_stop=initial_stop,
        market_score=market_score,
        quality_failed_rules=setup_quality.failed_rules,
        quality_passed_rules=setup_quality.passed_rules,
        rank_3m=rank_3m,
        rank_6m=rank_6m,
        relative_volume=relative_volume,
        risk_stop_score=risk_stop_score,
        rs_score=rs_score,
        setup_grade=setup_grade,
        setup_type=setup_type,
        total_score=total_score,
        trend_score=trend_score,
        trigger_price=trigger_price,
        volume_score=volume_score,
        strat_signal=strat_signal,
        strat_plan=strat_plan,
    )
    decision = scanner_decision.get("decision", base_decision)

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
        decision=decision,
        entry_plan={
            "side": "long",
            "trigger_type": "break_above_high" if setup_type != "pullback_to_20ma" else "reclaim_momentum",
            "trigger_price": trigger_price,
            "timeframe": fact.timeframe,
            "strat_trigger_plan": strat_plan,
            "score_breakdown": score_breakdown,
            "scanner_decision": scanner_decision,
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
            "scanner_decision": scanner_decision,
            "market_context": market_context,
            "facts_snapshot": {
                key: facts.get(key)
                for key in (
                    "close",
                    "relative_volume",
                    "pct_from_52w_high",
                    "base_depth_60d",
                    "close_position_in_range",
                    "volatility_contraction",
                    "sma_20_slope_pct",
                    "return_3m",
                    "return_6m",
                )
            },
        },
        scanner_decision=scanner_decision,
    )

def _rs_score(*, rank_3m: float, rank_6m: float) -> float:
    return round((rank_3m * 10.0) + (rank_6m * 15.0), 2)

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

def _detect_setup_quality(
    *,
    close: float,
    close_position: float | None,
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
    volatility_contraction: bool,
) -> SetupQuality | None:
    if (
        high_60d is not None
        and close >= high_60d * 0.98
        and (base_depth is None or base_depth <= 0.35)
        and (relative_volume is None or relative_volume >= 1.0)
    ):
        score = 9.0
        passed_rules = ["setup_location"]
        failed_rules: list[str] = []
        if close >= high_60d * 0.995:
            score += 1.5
            passed_rules.append("breakout_near_pivot")
        if relative_volume is not None and relative_volume >= 1.2:
            score += 2.0
            passed_rules.append("breakout_volume_confirmed")
        else:
            failed_rules.append("breakout_volume_missing")
        if close_position is not None and close_position >= 0.7:
            score += 1.5
            passed_rules.append("breakout_close_near_high")
        else:
            failed_rules.append("weak_close_position")
        if base_depth is not None and base_depth <= 0.25:
            score += 1.0
            passed_rules.append("base_depth_healthy")
        elif base_depth is not None and base_depth > 0.35:
            failed_rules.append("base_too_deep")
        if volatility_contraction:
            score += 1.0
            passed_rules.append("volatility_contraction")
        return SetupQuality("breakout", min(15.0, round(score, 2)), passed_rules, failed_rules)
    if (
        sma_20 is not None
        and sma_50 is not None
        and distance_to_sma_20 is not None
        and abs(distance_to_sma_20) <= 0.04
        and close > sma_50
        and (relative_volume is None or relative_volume <= 1.25)
    ):
        score = 8.0
        passed_rules = ["setup_location"]
        failed_rules: list[str] = []
        if abs(distance_to_sma_20) <= 0.025:
            score += 2.0
            passed_rules.append("pullback_near_20ma")
        if relative_volume is not None and relative_volume <= 1.0:
            score += 2.0
            passed_rules.append("pullback_volume_quiet")
        else:
            failed_rules.append("pullback_volume_heavy")
        if close > sma_20:
            score += 1.0
            passed_rules.append("hold_above_20ma")
        if close_position is not None and close_position >= 0.5:
            score += 1.0
            passed_rules.append("supportive_close_position")
        else:
            failed_rules.append("weak_close_position")
        if volatility_contraction:
            score += 1.0
            passed_rules.append("volatility_contraction")
        return SetupQuality("pullback_to_20ma", min(15.0, round(score, 2)), passed_rules, failed_rules)
    if (
        sma_50 is not None
        and low < sma_50 < close
        and (relative_volume is None or relative_volume >= 1.0)
    ):
        score = 9.0
        passed_rules = ["setup_location", "reclaim_50ma"]
        failed_rules: list[str] = []
        if relative_volume is not None and relative_volume >= 1.1:
            score += 2.0
            passed_rules.append("reclaim_volume_confirmed")
        else:
            failed_rules.append("volume_confirmation_missing")
        if close_position is not None and close_position >= 0.6:
            score += 1.5
            passed_rules.append("supportive_close_position")
        else:
            failed_rules.append("weak_close_position")
        return SetupQuality("failed_breakdown_reclaim", min(15.0, round(score, 2)), passed_rules, failed_rules)
    if pct_from_52w_high is not None and pct_from_52w_high >= -0.12 and trend_score >= 18:
        score = 7.0
        passed_rules = ["setup_location", "leader_near_high"]
        failed_rules: list[str] = []
        if volatility_contraction:
            score += 1.0
            passed_rules.append("volatility_contraction")
        if base_depth is not None and base_depth <= 0.25:
            score += 1.0
            passed_rules.append("base_depth_healthy")
        if close_position is not None and close_position >= 0.6:
            score += 1.0
            passed_rules.append("supportive_close_position")
        return SetupQuality("oneil_leader_watch", min(15.0, round(score, 2)), passed_rules, failed_rules)
    return None

def _followthrough_score(facts: dict[str, Any]) -> float:
    score = 0.0
    if facts.get("close_near_high"):
        score += 5
    relative_volume = _number(facts.get("relative_volume"))
    if relative_volume is not None and relative_volume >= 1.2:
        score += 5
    return score

def _scanner_decision(
    *,
    base_score: float,
    base_depth: float | None,
    close_position: float | None,
    decision: str,
    distance_to_sma_20: float | None,
    initial_stop: float,
    market_score: float,
    quality_failed_rules: list[str],
    quality_passed_rules: list[str],
    rank_3m: float,
    rank_6m: float,
    relative_volume: float | None,
    risk_stop_score: float,
    rs_score: float,
    setup_grade: str,
    setup_type: str,
    total_score: float,
    trend_score: float,
    trigger_price: float,
    volume_score: float,
    strat_signal: db.StratSignal | None,
    strat_plan: dict[str, Any] | None,
) -> dict[str, Any]:
    passed_rules: list[dict[str, Any]] = []
    failed_rules: list[dict[str, Any]] = []

    _add_score_rule(
        passed_rules,
        failed_rules,
        score=trend_score,
        max_score=25,
        threshold=18,
        passed_key="trend_aligned",
        failed_key="trend_needs_alignment",
    )
    _add_score_rule(
        passed_rules,
        failed_rules,
        score=rs_score,
        max_score=25,
        threshold=12.5,
        passed_key="relative_strength_leader",
        failed_key="relative_strength_lagging",
    )
    _add_score_rule(
        passed_rules,
        failed_rules,
        score=volume_score,
        max_score=15,
        threshold=8,
        passed_key="volume_liquidity",
        failed_key="volume_confirmation_missing",
    )
    _add_score_rule(
        passed_rules,
        failed_rules,
        score=base_score,
        max_score=15,
        threshold=9,
        passed_key="setup_location",
        failed_key="setup_location_unclear",
    )
    _add_score_rule(
        passed_rules,
        failed_rules,
        score=market_score,
        max_score=10,
        threshold=8,
        passed_key="market_support",
        failed_key="market_context_caution",
    )
    _add_score_rule(
        passed_rules,
        failed_rules,
        score=risk_stop_score,
        max_score=10,
        threshold=7,
        passed_key="risk_contained",
        failed_key="risk_too_wide",
    )
    _add_boolean_rule(
        passed_rules,
        failed_rules,
        passed=rank_3m >= 0.7 and rank_6m >= 0.7,
        passed_key="rs_top_quartile",
        failed_key="rs_not_leading",
    )
    for key in quality_passed_rules:
        _add_rule_key(passed_rules, key=key, passed=True)
    for key in quality_failed_rules:
        _add_rule_key(failed_rules, key=key, passed=False)

    watch_reasons = ["shadow_only", "needs_trigger_confirmation"]
    if decision == "watch":
        watch_reasons.insert(0, "score_below_candidate")
    if volume_score < 8 or "breakout_volume_missing" in quality_failed_rules:
        watch_reasons.append("volume_needs_confirmation")
    if "weak_close_position" in quality_failed_rules:
        watch_reasons.append("weak_close_position")
    if market_score < 8:
        watch_reasons.append("market_context_caution")

    upgrade_conditions = ["break_above_trigger", "hold_above_20_50ma"]
    if (
        volume_score < 8
        or relative_volume is None
        or relative_volume < 1.2
        or "breakout_volume_missing" in quality_failed_rules
    ):
        upgrade_conditions.append("volume_expansion")
    if market_score < 8:
        upgrade_conditions.append("market_context_green")

    risk_notes = ["initial_stop_required", "invalidates_below_stop"]
    if distance_to_sma_20 is not None and distance_to_sma_20 > 0.12:
        risk_notes.append("extended_from_20ma")
    if "base_too_deep" in quality_failed_rules:
        risk_notes.append("base_too_deep")
    if "weak_close_position" in quality_failed_rules:
        risk_notes.append("weak_close_position")
    if market_score < 8:
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
        decision=final_decision,
        failed_rules=failed_rules,
        initial_stop=initial_stop,
        metrics={
            "base_depth": base_depth,
            "close_position_in_range": close_position,
            "relative_volume": relative_volume,
            "rs_percentile_3m": round(rank_3m * 100, 1),
            "rs_percentile_6m": round(rank_6m * 100, 1),
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

def _trigger_price(*, setup_type: str, close: float, high: float) -> float:
    if setup_type == "pullback_to_20ma":
        return round(close * 1.005, 2)
    return round(high * 1.001, 2)
