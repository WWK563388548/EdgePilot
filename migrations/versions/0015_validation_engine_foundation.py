"""validation engine foundation

Revision ID: 0015_validation_engine_foundation
Revises: 0014_position_exit_profile
Create Date: 2026-05-20
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0015_validation_engine_foundation"
down_revision: str | None = "0014_position_exit_profile"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS test_runs (
            test_run_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL REFERENCES accounts(account_id),
            strategy_name TEXT NOT NULL,
            stage TEXT NOT NULL,
            run_type TEXT NOT NULL,
            status TEXT NOT NULL,
            sample_count INTEGER,
            trades_count INTEGER,
            win_rate DOUBLE PRECISION,
            profit_factor DOUBLE PRECISION,
            expectancy_r DOUBLE PRECISION,
            max_drawdown_pct DOUBLE PRECISION,
            execution_drag_r DOUBLE PRECISION,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            metadata_json JSONB,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_test_runs_account_strategy_completed
        ON test_runs(account_id, strategy_name, completed_at)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_test_runs_account_status
        ON test_runs(account_id, status)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS simulated_trades (
            simulated_trade_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL REFERENCES accounts(account_id),
            test_run_id TEXT REFERENCES test_runs(test_run_id),
            strategy_name TEXT NOT NULL,
            symbol_id TEXT NOT NULL,
            side TEXT,
            entry_ts TIMESTAMPTZ,
            exit_ts TIMESTAMPTZ,
            entry_price DOUBLE PRECISION,
            exit_price DOUBLE PRECISION,
            quantity DOUBLE PRECISION,
            pnl DOUBLE PRECISION,
            r_multiple DOUBLE PRECISION,
            status TEXT,
            metadata_json JSONB,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_simulated_trades_account_strategy_exit
        ON simulated_trades(account_id, strategy_name, exit_ts)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_simulated_trades_test_run
        ON simulated_trades(test_run_id)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS signal_funnel_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL REFERENCES accounts(account_id),
            strategy_name TEXT NOT NULL,
            stage TEXT,
            scan_date DATE NOT NULL,
            scanned_count INTEGER,
            rejected_count INTEGER,
            watch_count INTEGER,
            candidate_count INTEGER,
            planned_count INTEGER,
            accepted_count INTEGER,
            rejection_breakdown JSONB,
            metadata_json JSONB,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_signal_funnel_account_strategy_date
        ON signal_funnel_snapshots(account_id, strategy_name, scan_date)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS go_live_gates (
            gate_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL REFERENCES accounts(account_id),
            strategy_name TEXT NOT NULL,
            stage TEXT NOT NULL,
            status TEXT NOT NULL,
            required_trades INTEGER,
            min_profit_factor DOUBLE PRECISION,
            min_expectancy_r DOUBLE PRECISION,
            max_drawdown_pct DOUBLE PRECISION,
            max_execution_drag_r DOUBLE PRECISION,
            current_trades INTEGER,
            current_profit_factor DOUBLE PRECISION,
            current_expectancy_r DOUBLE PRECISION,
            current_max_drawdown_pct DOUBLE PRECISION,
            current_execution_drag_r DOUBLE PRECISION,
            reasons JSONB,
            evaluated_at TIMESTAMPTZ,
            metadata_json JSONB,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_go_live_gates_unique
        ON go_live_gates(account_id, strategy_name)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_go_live_gates_account_status
        ON go_live_gates(account_id, status)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS strategy_kill_switch_status (
            account_id TEXT NOT NULL REFERENCES accounts(account_id),
            strategy_name TEXT NOT NULL,
            status TEXT NOT NULL,
            reason TEXT,
            paused_by_user_id TEXT REFERENCES users(user_id),
            paused_at TIMESTAMPTZ,
            expires_at TIMESTAMPTZ,
            metadata_json JSONB,
            updated_at TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (account_id, strategy_name)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_strategy_kill_switch_account_status
        ON strategy_kill_switch_status(account_id, status)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS strategy_kill_switch_status")
    op.execute("DROP TABLE IF EXISTS go_live_gates")
    op.execute("DROP TABLE IF EXISTS signal_funnel_snapshots")
    op.execute("DROP TABLE IF EXISTS simulated_trades")
    op.execute("DROP TABLE IF EXISTS test_runs")
