from datetime import UTC, datetime
from hashlib import sha1
from typing import Any
from uuid import uuid4

from sqlalchemy import exists, func, inspect, or_, select
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import (
    NotificationEvent,
    NotificationEventUpdate,
    NotificationPreferences,
    NotificationPreferencesUpdate,
)
from backend.app.services.audit_service import AuditService

NOTIFICATION_SEVERITY_RANK = {"info": 0, "warning": 1, "action_required": 2}
NOTIFICATION_TABLES_AVAILABLE_CACHE_KEY = "edgepilot_notification_tables_available"


class NotificationService:
    @staticmethod
    def get_notification_preferences(
        session: Session,
        principal: AuthPrincipal,
    ) -> NotificationPreferences:
        if not NotificationService.notification_tables_available(session):
            return NotificationService.default_notification_preferences_response(principal)
        preferences = NotificationService.notification_preferences_model(session, principal)
        session.commit()
        session.refresh(preferences)
        return NotificationService.notification_preferences_response(preferences)

    @staticmethod
    def update_notification_preferences(
        session: Session,
        principal: AuthPrincipal,
        request: NotificationPreferencesUpdate,
    ) -> NotificationPreferences:
        if not NotificationService.notification_tables_available(session):
            return NotificationService.default_notification_preferences_response(principal, request)
        preferences = NotificationService.notification_preferences_model(session, principal)
        payload = request.model_dump(exclude_unset=True)
        for key, value in payload.items():
            setattr(preferences, key, value)
        preferences.updated_at = datetime.now(UTC)
        AuditService.record(
            session,
            principal,
            "notification_preferences.update",
            "notification_preferences",
            principal.account_id,
        )
        session.commit()
        session.refresh(preferences)
        return NotificationService.notification_preferences_response(preferences)

    @staticmethod
    def notification_preferences_model(
        session: Session,
        principal: AuthPrincipal,
    ) -> db.NotificationPreference:
        preferences = session.get(db.NotificationPreference, principal.account_id)
        if preferences is None:
            preferences = db.NotificationPreference(
                account_id=principal.account_id,
                in_app_enabled=True,
                email_enabled=False,
                sms_enabled=False,
                min_severity="info",
                event_preferences={},
            )
            session.add(preferences)
            session.flush()
        return preferences

    @staticmethod
    def notification_preferences_response(
        preferences: db.NotificationPreference,
    ) -> NotificationPreferences:
        return NotificationPreferences(
            account_id=preferences.account_id,
            in_app_enabled=preferences.in_app_enabled
            if preferences.in_app_enabled is not None
            else True,
            email_enabled=preferences.email_enabled if preferences.email_enabled is not None else False,
            sms_enabled=preferences.sms_enabled if preferences.sms_enabled is not None else False,
            min_severity=preferences.min_severity or "info",
            email_to=preferences.email_to,
            phone_to=preferences.phone_to,
            event_preferences=preferences.event_preferences or {},
            created_at=preferences.created_at,
            updated_at=preferences.updated_at,
        )

    @staticmethod
    def default_notification_preferences_response(
        principal: AuthPrincipal,
        request: NotificationPreferencesUpdate | None = None,
    ) -> NotificationPreferences:
        payload = request.model_dump(exclude_unset=True) if request else {}
        return NotificationPreferences(
            account_id=principal.account_id,
            in_app_enabled=payload.get("in_app_enabled")
            if payload.get("in_app_enabled") is not None
            else True,
            email_enabled=payload.get("email_enabled")
            if payload.get("email_enabled") is not None
            else False,
            sms_enabled=payload.get("sms_enabled")
            if payload.get("sms_enabled") is not None
            else False,
            min_severity=payload.get("min_severity") or "info",
            email_to=payload.get("email_to"),
            phone_to=payload.get("phone_to"),
            event_preferences=payload.get("event_preferences") or {},
            created_at=None,
            updated_at=None,
        )

    @staticmethod
    def list_notifications(
        session: Session,
        principal: AuthPrincipal,
        read: bool | None = None,
        acknowledged: bool | None = None,
        include_snoozed: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[NotificationEvent]:
        if not NotificationService.notification_tables_available(session):
            return []
        statement = NotificationService.notification_list_statement(
            principal=principal,
            read=read,
            acknowledged=acknowledged,
            include_snoozed=include_snoozed,
        )
        rows = session.scalars(
            statement.order_by(db.NotificationEvent.created_at.desc()).offset(offset).limit(limit)
        ).all()
        return [NotificationEvent.model_validate(row) for row in rows]

    @staticmethod
    def count_notifications(
        session: Session,
        principal: AuthPrincipal,
        read: bool | None = None,
        acknowledged: bool | None = None,
        include_snoozed: bool = False,
    ) -> int:
        if not NotificationService.notification_tables_available(session):
            return 0
        statement = NotificationService.notification_list_statement(
            principal=principal,
            read=read,
            acknowledged=acknowledged,
            include_snoozed=include_snoozed,
        )
        return session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def notification_list_statement(
        *,
        principal: AuthPrincipal,
        read: bool | None = None,
        acknowledged: bool | None = None,
        include_snoozed: bool = False,
    ):
        statement = select(db.NotificationEvent).where(
            db.NotificationEvent.account_id == principal.account_id
        )
        statement = statement.where(
            exists().where(
                db.NotificationDeliveryLog.notification_id
                == db.NotificationEvent.notification_id,
                db.NotificationDeliveryLog.channel == "in_app",
                db.NotificationDeliveryLog.status == "delivered",
            )
        )
        if read is True:
            statement = statement.where(db.NotificationEvent.read_at.is_not(None))
        elif read is False:
            statement = statement.where(db.NotificationEvent.read_at.is_(None))
        if acknowledged is True:
            statement = statement.where(db.NotificationEvent.acknowledged_at.is_not(None))
        elif acknowledged is False:
            statement = statement.where(db.NotificationEvent.acknowledged_at.is_(None))
        if not include_snoozed:
            statement = statement.where(
                or_(
                    db.NotificationEvent.snoozed_until.is_(None),
                    db.NotificationEvent.snoozed_until <= datetime.now(UTC),
                )
            )
        return statement

    @staticmethod
    def update_notification(
        session: Session,
        principal: AuthPrincipal,
        notification_id: str,
        request: NotificationEventUpdate,
    ) -> NotificationEvent:
        if not NotificationService.notification_tables_available(session):
            raise ValueError(f"Notification not found: {notification_id}")
        notification = NotificationService.get_notification_model(session, principal, notification_id)
        now = datetime.now(UTC)
        payload = request.model_dump(exclude_unset=True)
        if "read" in payload:
            notification.read_at = now if payload["read"] else None
        if "acknowledged" in payload:
            notification.acknowledged_at = now if payload["acknowledged"] else None
            if payload["acknowledged"]:
                notification.read_at = notification.read_at or now
        if "snoozed_until" in payload:
            notification.snoozed_until = payload["snoozed_until"]
        if payload:
            notification.updated_at = now
            AuditService.record(
                session,
                principal,
                "notification.update",
                "notification",
                notification_id,
            )
            session.commit()
            session.refresh(notification)
        return NotificationEvent.model_validate(notification)

    @staticmethod
    def get_notification_model(
        session: Session,
        principal: AuthPrincipal,
        notification_id: str,
    ) -> db.NotificationEvent:
        notification = session.scalar(
            select(db.NotificationEvent).where(
                db.NotificationEvent.notification_id == notification_id,
                db.NotificationEvent.account_id == principal.account_id,
            )
        )
        if notification is None:
            raise ValueError(f"Notification not found: {notification_id}")
        return notification

    @staticmethod
    def create_notification_event(
        session: Session,
        principal: AuthPrincipal,
        *,
        event_type: str,
        severity: str,
        source_type: str | None = None,
        source_id: str | None = None,
        title: str | None = None,
        body: str | None = None,
        target_view: str | None = None,
        target_id: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> db.NotificationEvent | None:
        if not NotificationService.notification_tables_available(session):
            return None
        preferences = NotificationService.notification_preferences_model(session, principal)
        if not NotificationService.notification_allowed(preferences, event_type, severity):
            return None
        existing = NotificationService.find_existing_notification(
            session,
            principal,
            event_type=event_type,
            source_type=source_type,
            source_id=source_id,
        )
        if existing is not None:
            return existing
        notification_id = NotificationService.notification_id(
            principal.account_id,
            event_type,
            source_type,
            source_id,
        )
        notification = db.NotificationEvent(
            notification_id=notification_id,
            account_id=principal.account_id,
            event_type=event_type,
            severity=severity,
            source_type=source_type,
            source_id=source_id,
            title=title,
            body=body,
            target_view=target_view,
            target_id=target_id,
            metadata_json=metadata_json or {},
        )
        session.add(notification)
        session.flush([notification])
        NotificationService.add_notification_delivery_logs(session, preferences, notification)
        return notification

    @staticmethod
    def notification_allowed(
        preferences: db.NotificationPreference,
        event_type: str,
        severity: str,
    ) -> bool:
        event_preferences = preferences.event_preferences or {}
        if event_preferences.get(event_type) is False:
            return False
        min_severity = preferences.min_severity or "info"
        return NOTIFICATION_SEVERITY_RANK.get(severity, 0) >= NOTIFICATION_SEVERITY_RANK.get(
            min_severity,
            0,
        )

    @staticmethod
    def find_existing_notification(
        session: Session,
        principal: AuthPrincipal,
        *,
        event_type: str,
        source_type: str | None,
        source_id: str | None,
    ) -> db.NotificationEvent | None:
        if source_id is None:
            return None
        return session.scalar(
            select(db.NotificationEvent).where(
                db.NotificationEvent.account_id == principal.account_id,
                db.NotificationEvent.event_type == event_type,
                db.NotificationEvent.source_type == source_type,
                db.NotificationEvent.source_id == source_id,
            )
        )

    @staticmethod
    def notification_id(
        account_id: str,
        event_type: str,
        source_type: str | None,
        source_id: str | None,
    ) -> str:
        raw = "|".join((account_id, event_type, source_type or "", source_id or uuid4().hex))
        return f"notif_{sha1(raw.encode('utf-8')).hexdigest()[:24]}"

    @staticmethod
    def add_notification_delivery_logs(
        session: Session,
        preferences: db.NotificationPreference,
        notification: db.NotificationEvent,
    ) -> None:
        now = datetime.now(UTC)
        if preferences.in_app_enabled is not False:
            session.add(
                db.NotificationDeliveryLog(
                    delivery_id=f"delivery_{notification.notification_id}_in_app",
                    notification_id=notification.notification_id,
                    account_id=notification.account_id,
                    channel="in_app",
                    status="delivered",
                    target="workspace",
                    attempted_at=now,
                    delivered_at=now,
                )
            )
        if preferences.email_enabled and preferences.email_to:
            session.add(
                db.NotificationDeliveryLog(
                    delivery_id=f"delivery_{notification.notification_id}_email",
                    notification_id=notification.notification_id,
                    account_id=notification.account_id,
                    channel="email",
                    status="queued",
                    target=preferences.email_to,
                    attempted_at=now,
                )
            )
        if preferences.sms_enabled and preferences.phone_to:
            session.add(
                db.NotificationDeliveryLog(
                    delivery_id=f"delivery_{notification.notification_id}_sms",
                    notification_id=notification.notification_id,
                    account_id=notification.account_id,
                    channel="sms",
                    status="queued",
                    target=preferences.phone_to,
                    attempted_at=now,
                )
            )

    @staticmethod
    def acknowledge_notifications_for_source(
        session: Session,
        principal: AuthPrincipal,
        *,
        source_type: str,
        source_id: str,
    ) -> None:
        if not NotificationService.notification_tables_available(session):
            return
        now = datetime.now(UTC)
        notifications = session.scalars(
            select(db.NotificationEvent).where(
                db.NotificationEvent.account_id == principal.account_id,
                db.NotificationEvent.source_type == source_type,
                db.NotificationEvent.source_id == source_id,
                db.NotificationEvent.acknowledged_at.is_(None),
            )
        ).all()
        for notification in notifications:
            notification.acknowledged_at = now
            notification.read_at = notification.read_at or now
            notification.updated_at = now

    @staticmethod
    def notification_tables_available(session: Session) -> bool:
        cached = session.info.get(NOTIFICATION_TABLES_AVAILABLE_CACHE_KEY)
        if isinstance(cached, bool):
            return cached

        inspector = inspect(session.connection())
        available = all(
            inspector.has_table(table_name)
            for table_name in (
                "notification_preferences",
                "notification_events",
                "notification_delivery_logs",
            )
        )
        session.info[NOTIFICATION_TABLES_AVAILABLE_CACHE_KEY] = available
        return available
