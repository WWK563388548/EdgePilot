"""scanner outcomes

Revision ID: 0005_scanner_outcomes
Revises: 0004_candidate_pa_setup_bridge
Create Date: 2026-05-04
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005_scanner_outcomes"
down_revision: str | None = "0004_candidate_pa_setup_bridge"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS scanner_outcomes (
            outcome_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL REFERENCES accounts(account_id),
            candidate_id TEXT NOT NULL UNIQUE REFERENCES candidates(candidate_id),
            pa_setup_id TEXT REFERENCES pa_setups(setup_id),
            symbol_id TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            detected_ts TIMESTAMPTZ NOT NULL,
            setup_type TEXT,
            setup_grade TEXT,
            score_total DOUBLE PRECISION,
            reference_close DOUBLE PRECISION,
            entry_trigger DOUBLE PRECISION,
            initial_stop DOUBLE PRECISION,
            bars_available INTEGER NOT NULL DEFAULT 0,
            evaluation_status TEXT NOT NULL,
            latest_evaluated_ts TIMESTAMPTZ,
            triggered_entry BOOLEAN,
            trigger_ts TIMESTAMPTZ,
            stopped_out BOOLEAN,
            stop_ts TIMESTAMPTZ,
            stop_hit_before_trigger BOOLEAN,
            false_breakout BOOLEAN,
            forward_return_5d DOUBLE PRECISION,
            forward_return_10d DOUBLE PRECISION,
            forward_return_20d DOUBLE PRECISION,
            forward_return_60d DOUBLE PRECISION,
            mfe_5d DOUBLE PRECISION,
            mfe_10d DOUBLE PRECISION,
            mfe_20d DOUBLE PRECISION,
            mfe_60d DOUBLE PRECISION,
            mae_5d DOUBLE PRECISION,
            mae_10d DOUBLE PRECISION,
            mae_20d DOUBLE PRECISION,
            mae_60d DOUBLE PRECISION,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_scanner_outcomes_candidate "
        "ON scanner_outcomes (candidate_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_scanner_outcomes_setup "
        "ON scanner_outcomes (pa_setup_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_scanner_outcomes_account_status "
        "ON scanner_outcomes (account_id, evaluation_status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_scanner_outcomes_symbol_detected "
        "ON scanner_outcomes (symbol_id, timeframe, detected_ts DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_scanner_outcomes_symbol_detected")
    op.execute("DROP INDEX IF EXISTS idx_scanner_outcomes_account_status")
    op.execute("DROP INDEX IF EXISTS idx_scanner_outcomes_setup")
    op.execute("DROP INDEX IF EXISTS idx_scanner_outcomes_candidate")
    op.execute("DROP TABLE IF EXISTS scanner_outcomes")
