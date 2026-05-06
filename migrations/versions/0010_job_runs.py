"""job runs

Revision ID: 0010_job_runs
Revises: 0009_notification_events
Create Date: 2026-05-06
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0010_job_runs"
down_revision: str | None = "0009_notification_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS job_runs (
            run_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL REFERENCES accounts(account_id),
            job_type TEXT NOT NULL,
            status TEXT NOT NULL,
            trigger TEXT,
            records_written INTEGER DEFAULT 0,
            error_message TEXT,
            metadata_json JSONB,
            started_at TIMESTAMPTZ DEFAULT now(),
            completed_at TIMESTAMPTZ,
            duration_ms INTEGER
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_job_runs_account_started
        ON job_runs (account_id, started_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_job_runs_account_status
        ON job_runs (account_id, status, started_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_job_runs_account_status")
    op.execute("DROP INDEX IF EXISTS idx_job_runs_account_started")
    op.execute("DROP TABLE IF EXISTS job_runs")
