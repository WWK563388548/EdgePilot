"""pa engine foundation

Revision ID: 0003_pa_engine_foundation
Revises: 0002_auth_orm_account_scope
Create Date: 2026-04-30
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003_pa_engine_foundation"
down_revision: str | None = "0002_auth_orm_account_scope"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pa_facts (
            fact_id TEXT PRIMARY KEY,
            symbol_id TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            ts TIMESTAMPTZ NOT NULL,
            facts JSONB NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_pa_facts_symbol_tf_ts "
        "ON pa_facts (symbol_id, timeframe, ts DESC)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pa_structures (
            structure_id TEXT PRIMARY KEY,
            symbol_id TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            ts TIMESTAMPTZ NOT NULL,
            structure_type TEXT NOT NULL,
            confidence DOUBLE PRECISION,
            metrics JSONB,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_pa_structures_symbol_tf_ts "
        "ON pa_structures (symbol_id, timeframe, ts DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_pa_structures_type "
        "ON pa_structures (structure_type)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pa_setups (
            setup_id TEXT PRIMARY KEY,
            symbol_id TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            detected_ts TIMESTAMPTZ NOT NULL,
            setup_type TEXT NOT NULL,
            setup_grade TEXT,
            pa_quality_score DOUBLE PRECISION,
            structure_score DOUBLE PRECISION,
            location_score DOUBLE PRECISION,
            volume_score DOUBLE PRECISION,
            trend_rs_score DOUBLE PRECISION,
            context_score DOUBLE PRECISION,
            risk_stop_score DOUBLE PRECISION,
            followthrough_score DOUBLE PRECISION,
            entry_plan JSONB,
            exit_plan JSONB,
            invalidation JSONB,
            status TEXT,
            validation_status TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_pa_setups_symbol_tf_detected "
        "ON pa_setups (symbol_id, timeframe, detected_ts DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_pa_setups_filters "
        "ON pa_setups (setup_type, status, validation_status)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pa_calibration_stats (
            stat_id TEXT PRIMARY KEY,
            setup_type TEXT NOT NULL,
            market_regime TEXT,
            sector_context TEXT,
            timeframe TEXT,
            sample_size INTEGER,
            win_rate DOUBLE PRECISION,
            average_r DOUBLE PRECISION,
            median_r DOUBLE PRECISION,
            profit_factor DOUBLE PRECISION,
            false_breakout_rate DOUBLE PRECISION,
            avg_mfe_r DOUBLE PRECISION,
            avg_mae_r DOUBLE PRECISION,
            max_drawdown_pct DOUBLE PRECISION,
            confidence_level TEXT,
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_pa_calibration_filters "
        "ON pa_calibration_stats (setup_type, market_regime, sector_context, timeframe)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_pa_calibration_filters")
    op.execute("DROP TABLE IF EXISTS pa_calibration_stats")
    op.execute("DROP INDEX IF EXISTS idx_pa_setups_filters")
    op.execute("DROP INDEX IF EXISTS idx_pa_setups_symbol_tf_detected")
    op.execute("DROP TABLE IF EXISTS pa_setups")
    op.execute("DROP INDEX IF EXISTS idx_pa_structures_type")
    op.execute("DROP INDEX IF EXISTS idx_pa_structures_symbol_tf_ts")
    op.execute("DROP TABLE IF EXISTS pa_structures")
    op.execute("DROP INDEX IF EXISTS idx_pa_facts_symbol_tf_ts")
    op.execute("DROP TABLE IF EXISTS pa_facts")
