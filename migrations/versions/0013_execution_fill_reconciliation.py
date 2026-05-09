"""execution fill reconciliation

Revision ID: 0013_execution_fill_reconciliation
Revises: 0012_execution_import_ledger
Create Date: 2026-05-09
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0013_execution_fill_reconciliation"
down_revision: str | None = "0012_execution_import_ledger"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)")
    op.execute("ALTER TABLE execution_fills ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active'")
    op.execute(
        """
        ALTER TABLE execution_fills
        ADD COLUMN IF NOT EXISTS reconciliation_status TEXT DEFAULT 'matched'
        """
    )
    op.execute("ALTER TABLE execution_fills ADD COLUMN IF NOT EXISTS reconciliation_note TEXT")
    op.execute("ALTER TABLE execution_fills ADD COLUMN IF NOT EXISTS reconciled_at TIMESTAMPTZ")
    op.execute(
        """
        UPDATE execution_fills AS fill
        SET reconciliation_status = CASE
                WHEN position.status = 'review_needed' THEN 'review_needed'
                ELSE 'matched'
            END,
            status = COALESCE(fill.status, 'active')
        FROM positions AS position
        WHERE fill.position_id = position.position_id
          AND (fill.reconciliation_status IS NULL OR fill.reconciliation_status = 'matched')
        """
    )
    op.execute(
        """
        UPDATE execution_fills
        SET status = COALESCE(status, 'active'),
            reconciliation_status = COALESCE(reconciliation_status, 'matched')
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_execution_fills_reconciliation
        ON execution_fills (account_id, status, reconciliation_status, executed_at DESC)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_execution_fills_reconciliation")
    op.execute("ALTER TABLE execution_fills DROP COLUMN IF EXISTS reconciled_at")
    op.execute("ALTER TABLE execution_fills DROP COLUMN IF EXISTS reconciliation_note")
    op.execute("ALTER TABLE execution_fills DROP COLUMN IF EXISTS reconciliation_status")
    op.execute("ALTER TABLE execution_fills DROP COLUMN IF EXISTS status")
