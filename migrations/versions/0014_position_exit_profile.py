"""position exit profile

Revision ID: 0014_position_exit_profile
Revises: 0013_execution_fill_reconciliation
Create Date: 2026-05-10
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0014_position_exit_profile"
down_revision: str | None = "0013_execution_fill_reconciliation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE positions ADD COLUMN IF NOT EXISTS exit_profile TEXT")
    op.execute(
        """
        UPDATE positions
        SET exit_profile = CASE
                WHEN strategy_name = 'etf_rotation_us_etf' THEN 'etf_rotation_trend'
                WHEN strategy_name = 'oneil_core_us_etf' THEN 'momentum_leader'
                ELSE exit_profile
            END
        WHERE exit_profile IS NULL
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE positions DROP COLUMN IF EXISTS exit_profile")
