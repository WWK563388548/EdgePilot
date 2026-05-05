"""notification events

Revision ID: 0009_notification_events
Revises: 0008_strat_trigger_layer
Create Date: 2026-05-05
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0009_notification_events"
down_revision: str | None = "0008_strat_trigger_layer"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notification_preferences (
            account_id TEXT PRIMARY KEY REFERENCES accounts(account_id),
            in_app_enabled BOOLEAN DEFAULT TRUE,
            email_enabled BOOLEAN DEFAULT FALSE,
            sms_enabled BOOLEAN DEFAULT FALSE,
            min_severity TEXT DEFAULT 'info',
            email_to TEXT,
            phone_to TEXT,
            event_preferences JSONB,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notification_events (
            notification_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL REFERENCES accounts(account_id),
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            source_type TEXT,
            source_id TEXT,
            title TEXT,
            body TEXT,
            target_view TEXT,
            target_id TEXT,
            metadata_json JSONB,
            read_at TIMESTAMPTZ,
            acknowledged_at TIMESTAMPTZ,
            snoozed_until TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_notification_events_account_source_event
        ON notification_events (account_id, event_type, source_type, source_id)
        WHERE source_id IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_notification_events_account_created
        ON notification_events (account_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_notification_events_account_read
        ON notification_events (account_id, read_at, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_notification_events_source
        ON notification_events (account_id, source_type, source_id)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notification_delivery_logs (
            delivery_id TEXT PRIMARY KEY,
            notification_id TEXT NOT NULL REFERENCES notification_events(notification_id),
            account_id TEXT NOT NULL REFERENCES accounts(account_id),
            channel TEXT NOT NULL,
            status TEXT NOT NULL,
            target TEXT,
            provider_message_id TEXT,
            error_message TEXT,
            attempted_at TIMESTAMPTZ,
            delivered_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_notification_delivery_notification
        ON notification_delivery_logs (notification_id, channel)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_notification_delivery_account_created
        ON notification_delivery_logs (account_id, created_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_notification_delivery_account_created")
    op.execute("DROP INDEX IF EXISTS idx_notification_delivery_notification")
    op.execute("DROP TABLE IF EXISTS notification_delivery_logs")
    op.execute("DROP INDEX IF EXISTS idx_notification_events_source")
    op.execute("DROP INDEX IF EXISTS idx_notification_events_account_read")
    op.execute("DROP INDEX IF EXISTS idx_notification_events_account_created")
    op.execute("DROP INDEX IF EXISTS idx_notification_events_account_source_event")
    op.execute("DROP TABLE IF EXISTS notification_events")
    op.execute("DROP TABLE IF EXISTS notification_preferences")
