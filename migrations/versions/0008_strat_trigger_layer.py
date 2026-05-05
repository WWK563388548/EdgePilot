"""strat trigger layer

Revision ID: 0008_strat_trigger_layer
Revises: 0007_portfolio_risk_exit_v2
Create Date: 2026-05-05
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0008_strat_trigger_layer"
down_revision: str | None = "0007_portfolio_risk_exit_v2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS strat_signals (
            signal_id TEXT PRIMARY KEY,
            symbol_id TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            ts TIMESTAMPTZ NOT NULL,
            bar_type TEXT NOT NULL,
            previous_bar_type TEXT,
            pattern TEXT,
            direction TEXT,
            trigger_price DOUBLE PRECISION,
            trigger_stop DOUBLE PRECISION,
            invalidation TEXT,
            timeframe_continuity JSONB,
            quality_score DOUBLE PRECISION,
            can_create_trade_alone BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_strat_signals_symbol_tf_ts
        ON strat_signals (symbol_id, timeframe, ts DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_strat_signals_pattern_direction
        ON strat_signals (pattern, direction)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_strat_signals_pattern_direction")
    op.execute("DROP INDEX IF EXISTS idx_strat_signals_symbol_tf_ts")
    op.execute("DROP TABLE IF EXISTS strat_signals")
