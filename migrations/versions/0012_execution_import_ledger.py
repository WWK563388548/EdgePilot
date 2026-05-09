"""execution import ledger

Revision ID: 0012_execution_import_ledger
Revises: 0011_tenant_lite_data_capability
Create Date: 2026-05-09
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0012_execution_import_ledger"
down_revision: str | None = "0011_tenant_lite_data_capability"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS execution_imports (
            import_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL REFERENCES accounts(account_id),
            broker TEXT NOT NULL,
            source_filename TEXT,
            status TEXT NOT NULL,
            rows_total INTEGER DEFAULT 0,
            rows_imported INTEGER DEFAULT 0,
            rows_skipped INTEGER DEFAULT 0,
            rows_failed INTEGER DEFAULT 0,
            error_message TEXT,
            metadata_json JSONB,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_execution_imports_account_created
        ON execution_imports (account_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_execution_imports_account_status
        ON execution_imports (account_id, status, created_at DESC)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS execution_fills (
            fill_id TEXT PRIMARY KEY,
            import_id TEXT NOT NULL REFERENCES execution_imports(import_id),
            account_id TEXT NOT NULL REFERENCES accounts(account_id),
            position_id TEXT,
            idempotency_key TEXT NOT NULL,
            broker TEXT NOT NULL,
            broker_account_id TEXT,
            broker_order_id TEXT,
            broker_execution_id TEXT,
            symbol_id TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity DOUBLE PRECISION NOT NULL,
            price DOUBLE PRECISION NOT NULL,
            gross_amount DOUBLE PRECISION,
            fees DOUBLE PRECISION,
            net_amount DOUBLE PRECISION,
            currency TEXT,
            executed_at TIMESTAMPTZ NOT NULL,
            raw_row_json JSONB,
            created_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_execution_fills_account_executed
        ON execution_fills (account_id, executed_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_execution_fills_account_symbol
        ON execution_fills (account_id, symbol_id, executed_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_execution_fills_position
        ON execution_fills (position_id, executed_at DESC)
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_execution_fills_idempotency
        ON execution_fills (idempotency_key)
        """
    )

    op.execute(
        """
        UPDATE tenant_data_capabilities
        SET status = 'available',
            source = 'app',
            reason = NULL,
            updated_at = now()
        WHERE capability_key = 'execution_import.csv'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_execution_fills_idempotency")
    op.execute("DROP INDEX IF EXISTS idx_execution_fills_position")
    op.execute("DROP INDEX IF EXISTS idx_execution_fills_account_symbol")
    op.execute("DROP INDEX IF EXISTS idx_execution_fills_account_executed")
    op.execute("DROP TABLE IF EXISTS execution_fills")
    op.execute("DROP INDEX IF EXISTS idx_execution_imports_account_status")
    op.execute("DROP INDEX IF EXISTS idx_execution_imports_account_created")
    op.execute("DROP TABLE IF EXISTS execution_imports")
    op.execute(
        """
        UPDATE tenant_data_capabilities
        SET status = 'disabled',
            source = 'planned',
            reason = 'CSV execution import is planned for the next implementation phase',
            updated_at = now()
        WHERE capability_key = 'execution_import.csv'
        """
    )
