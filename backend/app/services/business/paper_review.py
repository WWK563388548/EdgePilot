from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import ExitAlert, PaperReviewPosition, PaperReviewSummary


ACTIVE_REVIEW_STATUSES = ("planned", "open", "reduce", "exit_pending", "review_needed")
ACTION_PRIORITY = {
    "fix_plan": 0,
    "review_alert": 1,
    "confirm_entry": 2,
    "review_position": 3,
    "evaluate_alerts": 4,
    "review_reduced_position": 5,
    "wait_for_entry": 6,
}
STATUS_PRIORITY = {
    "review_needed": 0,
    "exit_pending": 1,
    "open": 2,
    "reduce": 3,
    "planned": 4,
}


def _candidate_id_from_position(position_id: str) -> str | None:
    if not position_id.startswith("plan_"):
        return None
    candidate_id = position_id.removeprefix("plan_")
    return candidate_id or None


def _dict_value(data: dict[str, Any] | None, key: str) -> Any:
    return data.get(key) if isinstance(data, dict) else None


def _number_value(data: dict[str, Any] | None, key: str) -> float | None:
    value = _dict_value(data, key)
    return float(value) if isinstance(value, int | float) else None


def _string_value(data: dict[str, Any] | None, key: str) -> str | None:
    value = _dict_value(data, key)
    return value if isinstance(value, str) and value else None


def _candidate_role(candidate: db.Candidate | None) -> str | None:
    if candidate is None:
        return None
    if candidate.decision != "candidate":
        return "watch_candidate"
    if candidate.strategy_name == "etf_rotation_us_etf":
        return "primary_candidate"
    if candidate.strategy_name == "oneil_core_us_etf":
        return "satellite_confirmation"
    return "primary_candidate"


def _position_has_missing_plan_fields(position: db.Position) -> bool:
    if position.status not in {"planned", "open", "reduce", "exit_pending", "review_needed"}:
        return False
    return (
        position.entry_price is None
        or position.initial_stop is None
        or position.current_stop is None
        or position.quantity is None
        or position.quantity <= 0
    )


def _actionable_alerts(
    position: db.Position,
    alerts: list[db.ExitAlert],
) -> list[db.ExitAlert]:
    return [
        alert
        for alert in alerts
        if alert.reason != "planned_entry_trigger_reached" or position.status == "planned"
    ]


def _next_action(position: db.Position, latest_alert: db.ExitAlert | None) -> tuple[str, str]:
    if _position_has_missing_plan_fields(position):
        return "fix_plan", "missing_plan_fields"
    if latest_alert is not None:
        if latest_alert.reason == "planned_entry_trigger_reached" and position.status == "planned":
            return "confirm_entry", "planned_entry_triggered"
        return "review_alert", latest_alert.reason or "active_exit_alert"
    if position.status == "planned":
        return "wait_for_entry", "planned_waiting_for_trigger"
    if position.status == "open":
        return "evaluate_alerts", "open_needs_exit_alert_check"
    if position.status == "reduce":
        return "review_reduced_position", "reduced_needs_trailing_review"
    return "review_position", "position_needs_manual_review"


class BusinessPaperReviewMixin:
    @classmethod
    def paper_review_summary(
        cls,
        session: Session,
        principal: AuthPrincipal,
        limit: int = 100,
    ) -> PaperReviewSummary:
        all_positions = session.scalars(
            select(db.Position)
            .where(
                db.Position.account_id == principal.account_id,
                db.Position.status.in_(ACTIVE_REVIEW_STATUSES),
            )
            .order_by(db.Position.updated_at.desc())
        ).all()

        position_ids = [position.position_id for position in all_positions]
        alerts_by_position: dict[str, list[db.ExitAlert]] = defaultdict(list)
        if position_ids:
            now = datetime.now(UTC)
            alerts = session.scalars(
                select(db.ExitAlert)
                .where(
                    db.ExitAlert.account_id == principal.account_id,
                    db.ExitAlert.position_id.in_(position_ids),
                    or_(db.ExitAlert.acknowledged.is_(False), db.ExitAlert.acknowledged.is_(None)),
                    or_(db.ExitAlert.snoozed_until.is_(None), db.ExitAlert.snoozed_until <= now),
                )
                .order_by(db.ExitAlert.alert_ts.desc())
            ).all()
            for alert in alerts:
                alerts_by_position[alert.position_id].append(alert)

        action_counts: Counter[str] = Counter()
        open_alert_count = 0
        high_priority_alert_count = 0
        next_action_by_position: dict[str, tuple[str, str]] = {}
        latest_alert_by_position: dict[str, db.ExitAlert | None] = {}
        actionable_alerts_by_position: dict[str, list[db.ExitAlert]] = {}
        for position in all_positions:
            position_alerts = alerts_by_position.get(position.position_id, [])
            actionable_alerts = _actionable_alerts(position, position_alerts)
            latest_alert = actionable_alerts[0] if actionable_alerts else None
            open_alert_count += len(actionable_alerts)
            high_priority_alert_count += sum(
                1 for alert in actionable_alerts if (alert.level or 0) >= 3
            )
            action, reason = _next_action(position, latest_alert)
            next_action_by_position[position.position_id] = (action, reason)
            latest_alert_by_position[position.position_id] = latest_alert
            actionable_alerts_by_position[position.position_id] = actionable_alerts
            action_counts[action] += 1

        def _row_priority(position: db.Position) -> tuple[int, int, int, float]:
            action, _ = next_action_by_position[position.position_id]
            latest_alert = latest_alert_by_position.get(position.position_id)
            return (
                ACTION_PRIORITY.get(action, 99),
                -(latest_alert.level or 0) if latest_alert is not None else 0,
                STATUS_PRIORITY.get(position.status or "", 99),
                -(position.updated_at.timestamp() if position.updated_at else 0.0),
            )

        ordered_positions = sorted(all_positions, key=_row_priority)
        visible_positions = ordered_positions[:limit]

        candidate_ids = {
            candidate_id
            for candidate_id in (
                _candidate_id_from_position(position.position_id) for position in visible_positions
            )
            if candidate_id is not None
        }
        candidates_by_id: dict[str, db.Candidate] = {}
        setups_by_id: dict[str, db.PASetup] = {}
        if candidate_ids:
            candidate_rows = session.scalars(
                select(db.Candidate).where(
                    db.Candidate.account_id == principal.account_id,
                    db.Candidate.candidate_id.in_(candidate_ids),
                )
            ).all()
            candidates_by_id = {candidate.candidate_id: candidate for candidate in candidate_rows}
            setup_ids = {
                candidate.pa_setup_id
                for candidate in candidate_rows
                if isinstance(candidate.pa_setup_id, str) and candidate.pa_setup_id
            }
            if setup_ids:
                setup_rows = session.scalars(
                    select(db.PASetup).where(db.PASetup.setup_id.in_(setup_ids))
                ).all()
                setups_by_id = {setup.setup_id: setup for setup in setup_rows}

        rows: list[PaperReviewPosition] = []
        for position in visible_positions:
            position_alerts = actionable_alerts_by_position.get(position.position_id, [])
            latest_alert = latest_alert_by_position.get(position.position_id)
            action, reason = next_action_by_position[position.position_id]

            candidate_id = _candidate_id_from_position(position.position_id)
            candidate = candidates_by_id.get(candidate_id or "")
            setup = (
                setups_by_id.get(candidate.pa_setup_id)
                if candidate and candidate.pa_setup_id
                else None
            )
            scanner_decision = (
                cls._candidate_scanner_decision(candidate, setup.entry_plan if setup else None)
                if candidate is not None
                else None
            )
            metrics = scanner_decision.metrics if scanner_decision is not None else {}
            max20d_warning = _dict_value(metrics, "max20d_warning")

            rows.append(
                PaperReviewPosition(
                    position=cls._position_response(session, principal, position),
                    next_action=action,
                    next_action_reason=reason,
                    candidate_id=candidate_id,
                    candidate_role=_candidate_role(candidate),
                    scanner_decision=scanner_decision.decision if scanner_decision else None,
                    entry_mode=_string_value(metrics, "entry_mode")
                    or _string_value(setup.entry_plan if setup else None, "entry_mode"),
                    max_20d_return=_number_value(max20d_warning, "max_20d_return"),
                    max_20d_lottery_risk=_string_value(max20d_warning, "lottery_risk"),
                    max_20d_suggested_action=_string_value(max20d_warning, "suggested_action"),
                    latest_alert=ExitAlert.model_validate(latest_alert) if latest_alert else None,
                    open_alert_count=len(position_alerts),
                    risk_notes=scanner_decision.risk_notes if scanner_decision else [],
                )
            )

        return PaperReviewSummary(
            account_id=principal.account_id,
            generated_at=datetime.now(UTC),
            total_positions=len(all_positions),
            planned_count=sum(1 for position in all_positions if position.status == "planned"),
            open_count=sum(1 for position in all_positions if position.status == "open"),
            reduced_count=sum(1 for position in all_positions if position.status == "reduce"),
            review_needed_count=sum(
                1
                for position in all_positions
                if position.status in {"review_needed", "exit_pending"}
            ),
            open_alert_count=open_alert_count,
            high_priority_alert_count=high_priority_alert_count,
            action_counts=dict(action_counts),
            positions=rows,
        )
