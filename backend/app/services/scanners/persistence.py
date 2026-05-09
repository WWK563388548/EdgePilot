from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.services.scanners.common import ScoredETFSetup

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
        "status": scored.decision,
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
    payload = {
        "account_id": account_id,
        "symbol_id": scored.symbol_id,
        "scan_date": scored.detected_ts.date(),
        "strategy_name": scored.strategy_name,
        "setup_type": scored.setup_type,
        "pa_setup_id": setup_id,
        "score_total": scored.total_score,
        "entry_trigger": scored.entry_plan.get("trigger_price"),
        "initial_stop": scored.exit_plan.get("initial_stop"),
        "decision": scored.decision,
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
            "source": scored.strategy_version,
            "strategy_name": scored.strategy_name,
            "pa_setup_id": setup_id,
            "validation_status": "shadow_only",
            "score_breakdown": scored.entry_plan["score_breakdown"],
            "scanner_decision": scored.scanner_decision,
        },
        sort_keys=True,
    )

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
