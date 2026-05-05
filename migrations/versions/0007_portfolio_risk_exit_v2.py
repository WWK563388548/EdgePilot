"""portfolio risk monitor and exit v2

Revision ID: 0007_portfolio_risk_exit_v2
Revises: 0006_account_risk_settings
Create Date: 2026-05-05
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0007_portfolio_risk_exit_v2"
down_revision: str | None = "0006_account_risk_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE account_risk_settings
        ADD COLUMN IF NOT EXISTS max_total_risk_pct DOUBLE PRECISION
        """
    )
    op.execute(
        """
        ALTER TABLE exit_alerts
        ADD COLUMN IF NOT EXISTS snoozed_until TIMESTAMPTZ
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE exit_alerts DROP COLUMN IF EXISTS snoozed_until")
    op.execute("ALTER TABLE account_risk_settings DROP COLUMN IF EXISTS max_total_risk_pct")
