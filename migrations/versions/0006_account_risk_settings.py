"""account risk settings

Revision ID: 0006_account_risk_settings
Revises: 0005_scanner_outcomes
Create Date: 2026-05-04
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006_account_risk_settings"
down_revision: str | None = "0005_scanner_outcomes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS account_risk_settings (
            account_id TEXT PRIMARY KEY REFERENCES accounts(account_id),
            account_equity DOUBLE PRECISION,
            max_risk_per_trade_pct DOUBLE PRECISION,
            max_open_positions INTEGER,
            max_risk_distance_pct DOUBLE PRECISION,
            shadow_only_requires_paper BOOLEAN DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS account_risk_settings")
