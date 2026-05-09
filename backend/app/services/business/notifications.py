from __future__ import annotations

from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from backend.app import models as db
from backend.app.core.auth import AuthPrincipal
from backend.app.schemas.business import (
    NotificationEvent,
    NotificationEventUpdate,
    NotificationPreferences,
    NotificationPreferencesUpdate,
)
from backend.app.services.notification_service import (
    NOTIFICATION_TABLES_AVAILABLE_CACHE_KEY,
    NotificationService,
)


class BusinessNotificationsMixin:
    @classmethod
    def get_notification_preferences(
        cls,
        session: Session,
        principal: AuthPrincipal,
    ) -> NotificationPreferences:
        if not cls._notification_tables_available(session):
            return cls._default_notification_preferences_response(principal)
        return NotificationService.get_notification_preferences(session, principal)

    @classmethod
    def update_notification_preferences(
        cls,
        session: Session,
        principal: AuthPrincipal,
        request: NotificationPreferencesUpdate,
    ) -> NotificationPreferences:
        if not cls._notification_tables_available(session):
            return cls._default_notification_preferences_response(principal, request)
        return NotificationService.update_notification_preferences(session, principal, request)

    @staticmethod
    def _notification_preferences_model(
        session: Session,
        principal: AuthPrincipal,
    ) -> db.NotificationPreference:
        return NotificationService.notification_preferences_model(session, principal)

    @staticmethod
    def _notification_preferences_response(
        preferences: db.NotificationPreference,
    ) -> NotificationPreferences:
        return NotificationService.notification_preferences_response(preferences)

    @staticmethod
    def _default_notification_preferences_response(
        principal: AuthPrincipal,
        request: NotificationPreferencesUpdate | None = None,
    ) -> NotificationPreferences:
        return NotificationService.default_notification_preferences_response(principal, request)

    @classmethod
    def list_notifications(
        cls,
        session: Session,
        principal: AuthPrincipal,
        read: bool | None = None,
        acknowledged: bool | None = None,
        include_snoozed: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[NotificationEvent]:
        if not cls._notification_tables_available(session):
            return []
        return NotificationService.list_notifications(
            session=session,
            principal=principal,
            read=read,
            acknowledged=acknowledged,
            include_snoozed=include_snoozed,
            limit=limit,
            offset=offset,
        )

    @classmethod
    def count_notifications(
        cls,
        session: Session,
        principal: AuthPrincipal,
        read: bool | None = None,
        acknowledged: bool | None = None,
        include_snoozed: bool = False,
    ) -> int:
        if not cls._notification_tables_available(session):
            return 0
        return NotificationService.count_notifications(
            session=session,
            principal=principal,
            read=read,
            acknowledged=acknowledged,
            include_snoozed=include_snoozed,
        )

    @staticmethod
    def _notification_list_statement(
        *,
        principal: AuthPrincipal,
        read: bool | None = None,
        acknowledged: bool | None = None,
        include_snoozed: bool = False,
    ):
        return NotificationService.notification_list_statement(
            principal=principal,
            read=read,
            acknowledged=acknowledged,
            include_snoozed=include_snoozed,
        )

    @classmethod
    def update_notification(
        cls,
        session: Session,
        principal: AuthPrincipal,
        notification_id: str,
        request: NotificationEventUpdate,
    ) -> NotificationEvent:
        if not cls._notification_tables_available(session):
            raise ValueError(f"Notification not found: {notification_id}")
        return NotificationService.update_notification(session, principal, notification_id, request)

    @staticmethod
    def _get_notification_model(
        session: Session,
        principal: AuthPrincipal,
        notification_id: str,
    ) -> db.NotificationEvent:
        return NotificationService.get_notification_model(session, principal, notification_id)

    @classmethod
    def _create_notification_event(
        cls,
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
        if not cls._notification_tables_available(session):
            return None
        return NotificationService.create_notification_event(
            session=session,
            principal=principal,
            event_type=event_type,
            severity=severity,
            source_type=source_type,
            source_id=source_id,
            title=title,
            body=body,
            target_view=target_view,
            target_id=target_id,
            metadata_json=metadata_json,
        )

    @staticmethod
    def _notification_allowed(
        preferences: db.NotificationPreference,
        event_type: str,
        severity: str,
    ) -> bool:
        return NotificationService.notification_allowed(preferences, event_type, severity)

    @staticmethod
    def _find_existing_notification(
        session: Session,
        principal: AuthPrincipal,
        *,
        event_type: str,
        source_type: str | None,
        source_id: str | None,
    ) -> db.NotificationEvent | None:
        return NotificationService.find_existing_notification(
            session,
            principal,
            event_type=event_type,
            source_type=source_type,
            source_id=source_id,
        )

    @staticmethod
    def _notification_id(
        account_id: str,
        event_type: str,
        source_type: str | None,
        source_id: str | None,
    ) -> str:
        return NotificationService.notification_id(account_id, event_type, source_type, source_id)

    @staticmethod
    def _add_notification_delivery_logs(
        session: Session,
        preferences: db.NotificationPreference,
        notification: db.NotificationEvent,
    ) -> None:
        NotificationService.add_notification_delivery_logs(session, preferences, notification)

    @staticmethod
    def _acknowledge_notifications_for_source(
        session: Session,
        principal: AuthPrincipal,
        *,
        source_type: str,
        source_id: str,
    ) -> None:
        NotificationService.acknowledge_notifications_for_source(
            session,
            principal,
            source_type=source_type,
            source_id=source_id,
        )

    @staticmethod
    def _notification_tables_available(session: Session) -> bool:
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
