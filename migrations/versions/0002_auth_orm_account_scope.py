"""auth ownership and account-scoped business tables

Revision ID: 0002_auth_orm_account_scope
Revises: 0001_baseline_schema
Create Date: 2026-04-26
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_auth_orm_account_scope"
down_revision: str | None = "0001_baseline_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            external_subject TEXT NOT NULL UNIQUE,
            email TEXT,
            display_name TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            last_login_at TIMESTAMPTZ
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_external_subject ON users (external_subject)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS account_memberships (
            account_id TEXT NOT NULL REFERENCES accounts(account_id),
            user_id TEXT NOT NULL REFERENCES users(user_id),
            role TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (account_id, user_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            audit_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL REFERENCES accounts(account_id),
            actor_user_id TEXT REFERENCES users(user_id),
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT,
            metadata_json TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_account_id ON audit_logs (account_id)")

    op.execute(
        """
        INSERT INTO accounts (account_id, name)
        VALUES ('acct_local', 'Local Dev')
        ON CONFLICT (account_id) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO users (user_id, external_subject, email, display_name)
        VALUES ('user_local', 'local-dev', 'local@edgepilot.dev', 'Local Dev')
        ON CONFLICT (user_id) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO account_memberships (account_id, user_id, role)
        VALUES ('acct_local', 'user_local', 'owner')
        ON CONFLICT (account_id, user_id) DO NOTHING
        """
    )

    for table in ("candidates", "positions", "exit_alerts", "trades_journal"):
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS account_id TEXT")
        op.execute(f"UPDATE {table} SET account_id = 'acct_local' WHERE account_id IS NULL")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN account_id SET NOT NULL")
        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'fk_{table}_account_id'
                ) THEN
                    ALTER TABLE {table}
                    ADD CONSTRAINT fk_{table}_account_id
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id);
                END IF;
            END $$;
            """
        )

    op.execute("DROP INDEX IF EXISTS idx_candidates_scan_date")
    op.execute("DROP INDEX IF EXISTS idx_candidates_decision")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_candidates_account_scan_date "
        "ON candidates (account_id, scan_date DESC, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_candidates_account_decision "
        "ON candidates (account_id, decision)"
    )

    op.execute("DROP INDEX IF EXISTS idx_positions_status")
    op.execute("DROP INDEX IF EXISTS idx_positions_symbol_status")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_positions_account_status "
        "ON positions (account_id, status, updated_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_positions_account_symbol_status "
        "ON positions (account_id, symbol_id, status)"
    )

    op.execute("DROP INDEX IF EXISTS idx_exit_alerts_ack_level")
    op.execute("DROP INDEX IF EXISTS idx_exit_alerts_position")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_exit_alerts_account_ack_level "
        "ON exit_alerts (account_id, acknowledged, level DESC, alert_ts DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_exit_alerts_account_position "
        "ON exit_alerts (account_id, position_id, alert_ts DESC)"
    )

    op.execute("DROP INDEX IF EXISTS idx_trades_journal_entry_ts")
    op.execute("DROP INDEX IF EXISTS idx_trades_journal_symbol")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_trades_journal_account_entry_ts "
        "ON trades_journal (account_id, entry_ts DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_trades_journal_account_symbol "
        "ON trades_journal (account_id, symbol_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_trades_journal_account_symbol")
    op.execute("DROP INDEX IF EXISTS idx_trades_journal_account_entry_ts")
    op.execute("DROP INDEX IF EXISTS idx_exit_alerts_account_position")
    op.execute("DROP INDEX IF EXISTS idx_exit_alerts_account_ack_level")
    op.execute("DROP INDEX IF EXISTS idx_positions_account_symbol_status")
    op.execute("DROP INDEX IF EXISTS idx_positions_account_status")
    op.execute("DROP INDEX IF EXISTS idx_candidates_account_decision")
    op.execute("DROP INDEX IF EXISTS idx_candidates_account_scan_date")

    for table in ("trades_journal", "exit_alerts", "positions", "candidates"):
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_account_id")
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS account_id")

    op.execute("DROP TABLE IF EXISTS audit_logs")
    op.execute("DROP TABLE IF EXISTS account_memberships")
    op.execute("DROP TABLE IF EXISTS accounts")
    op.execute("DROP TABLE IF EXISTS users")

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_candidates_scan_date "
        "ON candidates (scan_date DESC, created_at DESC)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidates_decision ON candidates (decision)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_positions_status "
        "ON positions (status, updated_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_positions_symbol_status ON positions (symbol_id, status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_exit_alerts_ack_level "
        "ON exit_alerts (acknowledged, level DESC, alert_ts DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_exit_alerts_position "
        "ON exit_alerts (position_id, alert_ts DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_trades_journal_entry_ts "
        "ON trades_journal (entry_ts DESC)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_trades_journal_symbol ON trades_journal (symbol_id)")
