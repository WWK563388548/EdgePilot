from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from backend.app import models as db

ONEIL_CORE_US_ETF_STRATEGY = "oneil_core_us_etf"
ONEIL_CORE_US_ETF_VERSION = "oneil_core_us_etf_v2"
ETF_ROTATION_US_ETF_STRATEGY = "etf_rotation_us_etf"
ETF_ROTATION_US_ETF_VERSION = "etf_rotation_us_etf_v1"
MAX20D_WARNING_VERSION = "max20d_warning_v1"


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
    decision: str
    entry_plan: dict[str, Any]
    exit_plan: dict[str, Any]
    invalidation: dict[str, Any]
    metrics: dict[str, Any]
    scanner_decision: dict[str, Any]
    strategy_name: str = ONEIL_CORE_US_ETF_STRATEGY
    strategy_version: str = ONEIL_CORE_US_ETF_VERSION


@dataclass(frozen=True)
class SetupQuality:
    setup_type: str
    base_score: float
    passed_rules: list[str]
    failed_rules: list[str]

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

def _setup_grade(total_score: float) -> str:
    if total_score >= 85:
        return "A"
    if total_score >= 75:
        return "B"
    if total_score >= 65:
        return "C"
    return "D"

def _apply_strat_confirmation(
    *,
    decision: str,
    failed_rules: list[dict[str, Any]],
    passed_rules: list[dict[str, Any]],
    risk_notes: list[str],
    strat_signal: db.StratSignal | None,
    strat_plan: dict[str, Any] | None,
    upgrade_conditions: list[str],
    watch_reasons: list[str],
) -> tuple[str, dict[str, Any]]:
    armed_plan = _usable_strat_plan(strat_plan)
    if strat_signal is None and armed_plan is None:
        watch_reasons.append("strat_signal_missing")
        upgrade_conditions.append("strat_bullish_trigger_needed")
        return decision, {
            "status": "missing",
            "base_decision": decision,
            "final_decision": decision,
            "reason": "strat_signal_missing",
            "can_create_trade_alone": False,
        }

    if armed_plan is not None:
        for rule in armed_plan.get("no_chase_rules", []):
            if isinstance(rule, dict) and rule.get("level") == "block":
                _add_rule_key(failed_rules, key=str(rule.get("code")), passed=False)
                risk_notes.append(str(rule.get("code")))
        if armed_plan.get("status") == "blocked":
            watch_reasons.append("strat_no_chase_blocked")
            return decision, {
                "status": "blocked",
                "base_decision": decision,
                "final_decision": decision,
                "bar_type": armed_plan.get("latest_bar_type"),
                "pattern": armed_plan.get("pattern"),
                "direction": armed_plan.get("direction"),
                "trigger_price": armed_plan.get("trigger_price"),
                "trigger_stop": armed_plan.get("trigger_stop"),
                "order_type": armed_plan.get("order_type"),
                "stop_limit_price": armed_plan.get("stop_limit_price"),
                "max_entry_price": armed_plan.get("max_entry_price"),
                "no_chase_rules": armed_plan.get("no_chase_rules", []),
                "reason": "strat_no_chase_blocked",
                "can_create_trade_alone": False,
            }

        if not (strat_signal is not None and strat_signal.pattern and strat_signal.direction):
            watch_reasons.append("strat_pending_trigger_armed")
            upgrade_conditions.append("strat_trigger_price_reached")
            return decision, {
                "status": "armed",
                "base_decision": decision,
                "final_decision": decision,
                "bar_type": armed_plan.get("latest_bar_type"),
                "pattern": armed_plan.get("pattern"),
                "direction": armed_plan.get("direction"),
                "trigger_price": armed_plan.get("trigger_price"),
                "trigger_stop": armed_plan.get("trigger_stop"),
                "order_type": armed_plan.get("order_type"),
                "stop_limit_price": armed_plan.get("stop_limit_price"),
                "max_entry_price": armed_plan.get("max_entry_price"),
                "no_chase_rules": armed_plan.get("no_chase_rules", []),
                "reason": "strat_pending_trigger_armed",
                "can_create_trade_alone": False,
            }

    payload = {
        "status": "wait",
        "base_decision": decision,
        "final_decision": decision,
        "bar_type": strat_signal.bar_type if strat_signal is not None else armed_plan.get("latest_bar_type"),
        "pattern": strat_signal.pattern if strat_signal is not None else armed_plan.get("pattern"),
        "direction": strat_signal.direction if strat_signal is not None else armed_plan.get("direction"),
        "trigger_price": strat_signal.trigger_price if strat_signal is not None else armed_plan.get("trigger_price"),
        "trigger_stop": strat_signal.trigger_stop if strat_signal is not None else armed_plan.get("trigger_stop"),
        "reason": "strat_waiting_for_trigger",
        "can_create_trade_alone": False,
    }
    if strat_signal.pattern and strat_signal.direction == "long":
        _add_rule_key(passed_rules, key="strat_bullish_trigger", passed=True)
        payload["status"] = "confirm"
        payload["reason"] = "strat_bullish_trigger"
        return decision, payload

    if strat_signal.pattern and strat_signal.direction == "short":
        _add_rule_key(failed_rules, key="strat_bearish_trigger", passed=False)
        watch_reasons.append("strat_bearish_downgrade")
        risk_notes.append("strat_bearish_context")
        payload["status"] = "downgrade"
        payload["final_decision"] = decision
        payload["reason"] = "strat_bearish_trigger"
        return decision, payload

    watch_reasons.append("strat_waiting_for_trigger")
    upgrade_conditions.append("strat_bullish_trigger_needed")
    return decision, payload

def _usable_strat_plan(strat_plan: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(strat_plan, dict):
        return None
    if strat_plan.get("direction") != "long":
        return None
    if strat_plan.get("status") not in {"armed", "blocked"}:
        return None
    if strat_plan.get("trigger_price") is None or strat_plan.get("trigger_stop") is None:
        return None
    return strat_plan

def _add_score_rule(
    passed_rules: list[dict[str, Any]],
    failed_rules: list[dict[str, Any]],
    *,
    score: float,
    max_score: float,
    threshold: float,
    passed_key: str,
    failed_key: str,
) -> None:
    passed = score >= threshold
    target = passed_rules if passed else failed_rules
    target.append(
        {
            "key": passed_key if passed else failed_key,
            "score": round(score, 2),
            "max_score": max_score,
            "passed": passed,
            "threshold": threshold,
        }
    )

def _add_boolean_rule(
    passed_rules: list[dict[str, Any]],
    failed_rules: list[dict[str, Any]],
    *,
    passed: bool,
    passed_key: str,
    failed_key: str,
) -> None:
    _add_rule_key(
        passed_rules if passed else failed_rules,
        key=passed_key if passed else failed_key,
        passed=passed,
    )

def _add_rule_key(target: list[dict[str, Any]], *, key: str, passed: bool) -> None:
    if any(rule.get("key") == key for rule in target):
        return
    target.append({"key": key, "passed": passed})

def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _max20d_warning(facts: dict[str, Any]) -> dict[str, Any]:
    max_20d_return = _number(facts.get("max_20d_return"))
    lottery_risk = str(facts.get("max_20d_lottery_risk") or "unknown")
    suggested_action = str(facts.get("max_20d_suggested_action") or "unknown")
    if lottery_risk not in {"low", "medium", "high", "unknown"}:
        lottery_risk = "unknown"
    if suggested_action not in {"allow", "watch", "avoid_chase", "unknown"}:
        suggested_action = "unknown"
    return {
        "version": MAX20D_WARNING_VERSION,
        "production_status": "analytics_warning",
        "max_20d_return": round(max_20d_return, 6) if max_20d_return is not None else None,
        "lottery_risk": lottery_risk,
        "suggested_action": suggested_action,
        "influenced_decision": False,
        "thresholds": {
            "medium": 0.05,
            "high": 0.08,
        },
    }


def _number(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
