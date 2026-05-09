from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import (
    ExitAlert,
    ExitAlertCreate,
    ExitAlertEvaluationRequest,
    ExitAlertEvaluationResponse,
    ExitAlertUpdate,
)


def _number_from_record(data: dict | None, key: str) -> float | None:
    value = data.get(key) if data else None
    if isinstance(value, int | float):
        return float(value)
    return None


class BusinessExitAlertsMixin:
    @classmethod
    def create_exit_alert(
        cls,
        session: Session,
        principal: AuthPrincipal,
        request: ExitAlertCreate,
    ) -> ExitAlert:
        cls._get_position_model(session, principal, request.position_id)
        alert = db.ExitAlert(
            alert_id=request.alert_id or f"alert_{uuid4().hex}",
            account_id=principal.account_id,
            position_id=request.position_id,
            level=request.level,
            action=request.action,
            reason=request.reason,
            new_stop=request.new_stop,
            triggered_rules=request.triggered_rules,
            snoozed_until=request.snoozed_until,
            acknowledged=request.acknowledged,
        )
        session.add(alert)
        cls._audit(session, principal, "exit_alert.create", "exit_alert", alert.alert_id)
        session.commit()
        session.refresh(alert)
        return ExitAlert.model_validate(alert)

    @classmethod
    def evaluate_exit_alerts(
        cls,
        session: Session,
        principal: AuthPrincipal,
        request: ExitAlertEvaluationRequest,
    ) -> ExitAlertEvaluationResponse:
        statement = select(db.Position).where(
            db.Position.account_id == principal.account_id,
            db.Position.status.in_(("planned", "open", "reduce")),
        )
        if request.position_id:
            statement = statement.where(db.Position.position_id == request.position_id)
        statement = statement.order_by(db.Position.updated_at.desc())
        if request.limit is not None:
            statement = statement.limit(request.limit)

        positions = list(session.scalars(statement).all())
        if request.position_id and not positions:
            raise ValueError(f"Position not found: {request.position_id}")

        skipped_positions = 0
        duplicate_alerts = 0
        symbols: set[str] = set()
        created: list[db.ExitAlert] = []
        for position in positions:
            latest_bar = cls._latest_bar(session, position.symbol_id)
            latest_fact = cls._latest_fact(session, position.symbol_id)
            market_context = cls._latest_market_context(session)
            if latest_bar is None:
                skipped_positions += 1
                continue
            symbols.add(position.symbol_id)
            for spec in cls._exit_alert_specs(position, latest_bar, latest_fact, market_context):
                alert_id = f"alert_{position.position_id}_{spec['rule']}_{latest_bar.ts.date().isoformat()}"
                if session.get(db.ExitAlert, alert_id) is not None:
                    duplicate_alerts += 1
                    continue
                alert = db.ExitAlert(
                    alert_id=alert_id,
                    account_id=principal.account_id,
                    position_id=position.position_id,
                    alert_ts=latest_bar.ts,
                    level=spec["level"],
                    action=spec["action"],
                    reason=spec["reason"],
                    new_stop=spec["new_stop"],
                    triggered_rules=spec["rule"],
                    acknowledged=False,
                )
                session.add(alert)
                created.append(alert)
                cls._create_notification_event(
                    session,
                    principal,
                    event_type=cls._exit_alert_notification_type(spec["rule"]),
                    severity=cls._exit_alert_notification_severity(spec["rule"], spec["level"]),
                    source_type="exit_alert",
                    source_id=alert.alert_id,
                    title=cls._exit_alert_notification_title(position, spec),
                    body=cls._exit_alert_notification_body(position, spec),
                    target_view="alerts",
                    target_id=alert.alert_id,
                    metadata_json={
                        "alert_id": alert.alert_id,
                        "position_id": position.position_id,
                        "symbol_id": position.symbol_id,
                        "level": spec["level"],
                        "action": spec["action"],
                        "reason": spec["reason"],
                        "rule": spec["rule"],
                        "new_stop": spec["new_stop"],
                        "bar_ts": latest_bar.ts.isoformat() if latest_bar.ts else None,
                    },
                )

        if positions:
            cls._audit(
                session,
                principal,
                "exit_alert.evaluate",
                "exit_alert",
                request.position_id,
            )
        session.commit()
        for alert in created:
            session.refresh(alert)
        return ExitAlertEvaluationResponse(
            account_id=principal.account_id,
            positions_evaluated=len(positions),
            alerts_created=len(created),
            skipped_positions=skipped_positions,
            duplicate_alerts=duplicate_alerts,
            symbols_processed=sorted(symbols),
            alerts=[ExitAlert.model_validate(alert) for alert in created],
        )

    @staticmethod
    def _exit_alert_notification_type(rule: object) -> str:
        if rule == "planned_entry_trigger_reached":
            return "position_entry_triggered"
        if rule == "daily_close_below_current_stop":
            return "position_hard_stop"
        if rule == "first_trim_target_reached_2r":
            return "position_trim_target"
        if rule == "move_stop_to_breakeven_after_1r":
            return "position_breakeven_stop"
        if rule == "trail_stop_to_20ma_after_profit":
            return "position_trailing_stop"
        if rule == "market_regime_risk_off":
            return "portfolio_risk_warning"
        return "position_exit_alert"

    @staticmethod
    def _exit_alert_notification_severity(rule: object, level: object) -> str:
        if rule in {"planned_entry_trigger_reached", "daily_close_below_current_stop"}:
            return "action_required"
        if rule in {"first_trim_target_reached_2r", "market_regime_risk_off"}:
            return "warning"
        numeric_level = level if isinstance(level, int) else 0
        if numeric_level >= 4:
            return "action_required"
        if numeric_level >= 2:
            return "warning"
        return "info"

    @staticmethod
    def _exit_alert_notification_title(position: db.Position, spec: dict[str, object]) -> str:
        rule = spec["rule"]
        if rule == "planned_entry_trigger_reached":
            return f"{position.symbol_id} entry trigger reached"
        if rule == "daily_close_below_current_stop":
            return f"{position.symbol_id} hard stop alert"
        if rule == "first_trim_target_reached_2r":
            return f"{position.symbol_id} reached 2R trim area"
        return f"{position.symbol_id} position alert"

    @staticmethod
    def _exit_alert_notification_body(position: db.Position, spec: dict[str, object]) -> str:
        rule = spec["rule"]
        if rule == "planned_entry_trigger_reached":
            return "Review the planned entry trigger and decide whether to enter."
        if rule == "daily_close_below_current_stop":
            return "Daily close is below the tracked stop. Review exit action."
        if rule == "first_trim_target_reached_2r":
            return "Price reached the first trim area. Review partial profit taking."
        if rule == "move_stop_to_breakeven_after_1r":
            return "Position reached 1R. Review moving stop to breakeven."
        if rule == "trail_stop_to_20ma_after_profit":
            return "Position is profitable. Review trailing stop near the 20MA."
        return "Review the latest position alert."

    @staticmethod
    def _latest_bar(session: Session, symbol_id: str, timeframe: str = "1d") -> db.Bar | None:
        return session.scalar(
            select(db.Bar)
            .where(db.Bar.symbol_id == symbol_id, db.Bar.timeframe == timeframe)
            .order_by(db.Bar.ts.desc())
            .limit(1)
        )

    @staticmethod
    def _latest_fact(session: Session, symbol_id: str, timeframe: str = "1d") -> db.PAFact | None:
        return session.scalar(
            select(db.PAFact)
            .where(db.PAFact.symbol_id == symbol_id, db.PAFact.timeframe == timeframe)
            .order_by(db.PAFact.ts.desc())
            .limit(1)
        )

    @staticmethod
    def _latest_market_context(session: Session) -> db.MarketContextSnapshot | None:
        return session.scalar(
            select(db.MarketContextSnapshot)
            .order_by(db.MarketContextSnapshot.snapshot_ts.desc())
            .limit(1)
        )

    @classmethod
    def _exit_alert_specs(
        cls,
        position: db.Position,
        latest_bar: db.Bar,
        latest_fact: db.PAFact | None,
        market_context: db.MarketContextSnapshot | None,
    ) -> list[dict[str, object]]:
        close = latest_bar.close
        high = latest_bar.high
        if close is None:
            return []

        stop = position.current_stop or position.initial_stop
        if position.status == "planned":
            if position.entry_price is not None and high is not None and high >= position.entry_price:
                return [
                    {
                        "rule": "planned_entry_trigger_reached",
                        "level": 1,
                        "action": "review_entry",
                        "reason": "planned_entry_trigger_reached",
                        "new_stop": stop,
                    }
                ]
            return []

        specs: list[dict[str, object]] = []
        if stop is not None and close <= stop:
            specs.append(
                {
                    "rule": "daily_close_below_current_stop",
                    "level": 4,
                    "action": "exit",
                    "reason": "daily_close_below_current_stop",
                    "new_stop": stop,
                }
            )

        facts = latest_fact.facts if latest_fact else None
        sma_20 = _number_from_record(facts, "sma_20")
        sma_50 = _number_from_record(facts, "sma_50")
        relative_volume = _number_from_record(facts, "relative_volume")
        current_r = cls._position_r_from_close(position, close, stop)
        if sma_20 is not None and sma_50 is not None and close < sma_20 and close < sma_50:
            specs.append(
                {
                    "rule": "close_below_20_50ma_support",
                    "level": 2,
                    "action": "review_exit",
                    "reason": "close_below_20_50ma_support",
                    "new_stop": stop,
                }
            )
        elif sma_50 is not None and close < sma_50:
            specs.append(
                {
                    "rule": "close_below_50ma",
                    "level": 2,
                    "action": "tighten_stop",
                    "reason": "close_below_50ma",
                    "new_stop": stop,
                }
            )
        elif sma_20 is not None and close < sma_20:
            specs.append(
                {
                    "rule": "close_below_20ma",
                    "level": 1,
                    "action": "watch_pullback",
                    "reason": "close_below_20ma",
                    "new_stop": stop,
                }
            )

        risk_stop = position.initial_stop or stop
        risk = position.entry_price - risk_stop if position.entry_price is not None and risk_stop is not None else None
        if (
            risk is not None
            and risk > 0
            and position.entry_price is not None
            and close >= position.entry_price + risk
            and close < position.entry_price + (2 * risk)
            and (stop is None or stop < position.entry_price)
        ):
            specs.append(
                {
                    "rule": "move_stop_to_breakeven_after_1r",
                    "level": 1,
                    "action": "tighten_stop",
                    "reason": "move_stop_to_breakeven_after_1r",
                    "new_stop": position.entry_price,
                }
            )
        if risk is not None and risk > 0 and position.entry_price is not None and close >= position.entry_price + (2 * risk):
            specs.append(
                {
                    "rule": "first_trim_target_reached_2r",
                    "level": 1,
                    "action": "trim",
                    "reason": "first_trim_target_reached_2r",
                    "new_stop": max(stop, position.entry_price),
                }
            )
        if (
            current_r is not None
            and current_r >= 2
            and sma_20 is not None
            and stop is not None
            and sma_20 > stop
            and close > sma_20
        ):
            specs.append(
                {
                    "rule": "trail_stop_to_20ma_after_profit",
                    "level": 1,
                    "action": "tighten_stop",
                    "reason": "trail_stop_to_20ma_after_profit",
                    "new_stop": round(max(stop, sma_20 * 0.98), 6),
                }
            )
        if (
            current_r is not None
            and current_r < 0.5
            and position.entry_date is not None
            and (cls._days_since_entry(latest_bar, position) or 0) >= 20
        ):
            specs.append(
                {
                    "rule": "time_stop_no_progress_20d",
                    "level": 1,
                    "action": "review_exit",
                    "reason": "time_stop_no_progress_20d",
                    "new_stop": stop,
                }
            )
        if (
            position.entry_price is not None
            and position.entry_date is not None
            and (cls._days_since_entry(latest_bar, position) or 9999) <= 10
            and close < position.entry_price
            and relative_volume is not None
            and relative_volume >= 1.2
        ):
            specs.append(
                {
                    "rule": "failed_breakout_heavy_volume",
                    "level": 2,
                    "action": "review_exit",
                    "reason": "failed_breakout_heavy_volume",
                    "new_stop": stop,
                }
            )
        if (
            market_context is not None
            and cls._market_context_is_risk_off(market_context)
            and sma_20 is not None
            and close < sma_20
        ):
            specs.append(
                {
                    "rule": "market_regime_risk_off",
                    "level": 2,
                    "action": "review_exit",
                    "reason": "market_regime_risk_off",
                    "new_stop": stop,
                }
            )
        return specs

    @staticmethod
    def _position_r_from_close(
        position: db.Position,
        close: float,
        stop: float | None,
    ) -> float | None:
        risk_stop = position.initial_stop or stop
        if position.entry_price is None or risk_stop is None:
            return None
        risk = position.entry_price - risk_stop
        if risk <= 0:
            return None
        return round((close - position.entry_price) / risk, 6)

    @staticmethod
    def _days_since_entry(latest_bar: db.Bar, position: db.Position) -> int | None:
        if position.entry_date is None:
            return None
        bar_ts = latest_bar.ts
        entry_ts = position.entry_date
        if bar_ts.tzinfo is not None and entry_ts.tzinfo is None:
            entry_ts = entry_ts.replace(tzinfo=bar_ts.tzinfo)
        elif bar_ts.tzinfo is None and entry_ts.tzinfo is not None:
            entry_ts = entry_ts.replace(tzinfo=None)
        return (bar_ts - entry_ts).days

    @staticmethod
    def _market_context_is_risk_off(market_context: db.MarketContextSnapshot) -> bool:
        risk_level = (market_context.risk_level or "").lower()
        us_bias = (market_context.us_bias or "").lower()
        return risk_level in {"shock", "risk_off", "red"} or us_bias in {
            "bearish",
            "risk_off",
            "down",
        }

    @classmethod
    def list_exit_alerts(
        cls,
        session: Session,
        principal: AuthPrincipal,
        acknowledged: bool | None = None,
        include_snoozed: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ExitAlert]:
        statement = cls._exit_alert_list_statement(
            principal=principal,
            acknowledged=acknowledged,
            include_snoozed=include_snoozed,
        )
        rows = session.scalars(
            statement.order_by(db.ExitAlert.alert_ts.desc()).offset(offset).limit(limit)
        ).all()
        return [ExitAlert.model_validate(row) for row in rows]

    @classmethod
    def count_exit_alerts(
        cls,
        session: Session,
        principal: AuthPrincipal,
        acknowledged: bool | None = None,
        include_snoozed: bool = False,
    ) -> int:
        statement = cls._exit_alert_list_statement(
            principal=principal,
            acknowledged=acknowledged,
            include_snoozed=include_snoozed,
        )
        return session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def _exit_alert_list_statement(
        *,
        principal: AuthPrincipal,
        acknowledged: bool | None = None,
        include_snoozed: bool = False,
    ):
        statement = select(db.ExitAlert).where(db.ExitAlert.account_id == principal.account_id)
        if acknowledged is not None:
            statement = statement.where(db.ExitAlert.acknowledged == acknowledged)
        if not include_snoozed:
            statement = statement.where(
                or_(
                    db.ExitAlert.snoozed_until.is_(None),
                    db.ExitAlert.snoozed_until <= datetime.now(UTC),
                )
            )
        return statement

    @classmethod
    def update_exit_alert(
        cls,
        session: Session,
        principal: AuthPrincipal,
        alert_id: str,
        request: ExitAlertUpdate,
    ) -> ExitAlert:
        alert = cls._get_exit_alert_model(session, principal, alert_id)
        payload = request.model_dump(exclude_unset=True)
        for key, value in payload.items():
            setattr(alert, key, value)
        if payload:
            if payload.get("acknowledged") is True:
                cls._acknowledge_notifications_for_source(
                    session,
                    principal,
                    source_type="exit_alert",
                    source_id=alert.alert_id,
                )
            cls._audit(session, principal, "exit_alert.update", "exit_alert", alert_id)
            session.commit()
            session.refresh(alert)
        return ExitAlert.model_validate(alert)

    @staticmethod
    def _get_exit_alert_model(
        session: Session,
        principal: AuthPrincipal,
        alert_id: str,
    ) -> db.ExitAlert:
        alert = session.scalar(
            select(db.ExitAlert).where(
                db.ExitAlert.alert_id == alert_id,
                db.ExitAlert.account_id == principal.account_id,
            )
        )
        if alert is None:
            raise ValueError(f"Exit alert not found: {alert_id}")
        return alert
