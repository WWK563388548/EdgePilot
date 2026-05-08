"""tenant-lite data capability foundation

Revision ID: 0011_tenant_lite_data_capability
Revises: 0010_job_runs
Create Date: 2026-05-08
"""

from collections.abc import Sequence

from alembic import op

from backend.app.core.config import settings

revision: str = "0011_tenant_lite_data_capability"
down_revision: str | None = "0010_job_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenants (
            tenant_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT UNIQUE,
            owner_user_id TEXT REFERENCES users(user_id),
            status TEXT DEFAULT 'active',
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenant_memberships (
            tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
            user_id TEXT NOT NULL REFERENCES users(user_id),
            role TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (tenant_id, user_id)
        )
        """
    )
    op.execute("ALTER TABLE accounts ADD COLUMN IF NOT EXISTS tenant_id TEXT")
    op.execute(
        """
        INSERT INTO tenants (tenant_id, name, status)
        SELECT DISTINCT 'tenant_' || account_id, name, 'active'
        FROM accounts
        WHERE account_id IS NOT NULL
        ON CONFLICT (tenant_id) DO NOTHING
        """
    )
    op.execute(
        """
        UPDATE accounts
        SET tenant_id = 'tenant_' || account_id
        WHERE tenant_id IS NULL
        """
    )
    op.execute(
        """
        INSERT INTO tenant_memberships (tenant_id, user_id, role)
        SELECT DISTINCT accounts.tenant_id, account_memberships.user_id, account_memberships.role
        FROM account_memberships
        JOIN accounts ON accounts.account_id = account_memberships.account_id
        WHERE accounts.tenant_id IS NOT NULL
        ON CONFLICT (tenant_id, user_id) DO NOTHING
        """
    )
    op.execute(
        """
        UPDATE tenants
        SET owner_user_id = first_membership.user_id
        FROM (
            SELECT DISTINCT ON (accounts.tenant_id)
                accounts.tenant_id,
                account_memberships.user_id
            FROM accounts
            JOIN account_memberships ON account_memberships.account_id = accounts.account_id
            ORDER BY accounts.tenant_id, account_memberships.created_at
        ) AS first_membership
        WHERE tenants.tenant_id = first_membership.tenant_id
          AND tenants.owner_user_id IS NULL
        """
    )
    op.execute("ALTER TABLE accounts ALTER COLUMN tenant_id SET NOT NULL")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_accounts_tenant_id'
            ) THEN
                ALTER TABLE accounts
                ADD CONSTRAINT fk_accounts_tenant_id
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id);
            END IF;
        END $$;
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_accounts_tenant_id ON accounts (tenant_id)")

    op.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS tenant_id TEXT")
    op.execute(
        """
        UPDATE audit_logs
        SET tenant_id = accounts.tenant_id
        FROM accounts
        WHERE audit_logs.account_id = accounts.account_id
          AND audit_logs.tenant_id IS NULL
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_audit_logs_tenant_id'
            ) THEN
                ALTER TABLE audit_logs
                ADD CONSTRAINT fk_audit_logs_tenant_id
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id);
            END IF;
        END $$;
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_tenant_id ON audit_logs (tenant_id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS legal_acknowledgements (
            acknowledgement_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
            user_id TEXT NOT NULL REFERENCES users(user_id),
            document_key TEXT NOT NULL,
            document_version TEXT NOT NULL,
            acknowledged_at TIMESTAMPTZ DEFAULT now(),
            ip_address TEXT,
            user_agent TEXT,
            metadata_json JSONB
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_legal_ack_tenant_user_doc
        ON legal_acknowledgements (tenant_id, user_id, document_key, document_version)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenant_api_keys (
            credential_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
            provider TEXT NOT NULL,
            label TEXT,
            status TEXT DEFAULT 'configured',
            encrypted_payload TEXT,
            key_fingerprint TEXT,
            last_verified_at TIMESTAMPTZ,
            metadata_json JSONB,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tenant_api_keys_tenant_provider
        ON tenant_api_keys (tenant_id, provider)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenant_data_capabilities (
            capability_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
            capability_key TEXT NOT NULL,
            provider TEXT,
            market TEXT,
            asset_type TEXT,
            timeframe TEXT,
            status TEXT NOT NULL,
            source TEXT,
            reason TEXT,
            last_checked_at TIMESTAMPTZ,
            metadata_json JSONB,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_tenant_data_capabilities_unique
        ON tenant_data_capabilities (tenant_id, capability_key)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tenant_data_capabilities_status
        ON tenant_data_capabilities (tenant_id, status)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenant_job_states (
            tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
            job_type TEXT NOT NULL,
            enabled BOOLEAN DEFAULT true,
            status TEXT DEFAULT 'idle',
            rate_limit_per_minute INTEGER,
            next_allowed_at TIMESTAMPTZ,
            last_run_id TEXT,
            metadata_json JSONB,
            updated_at TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (tenant_id, job_type)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tenant_job_states_status
        ON tenant_job_states (tenant_id, status)
        """
    )

    _seed_default_capabilities()
    _seed_default_job_states()


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_tenant_job_states_status")
    op.execute("DROP TABLE IF EXISTS tenant_job_states")
    op.execute("DROP INDEX IF EXISTS idx_tenant_data_capabilities_status")
    op.execute("DROP INDEX IF EXISTS idx_tenant_data_capabilities_unique")
    op.execute("DROP TABLE IF EXISTS tenant_data_capabilities")
    op.execute("DROP INDEX IF EXISTS idx_tenant_api_keys_tenant_provider")
    op.execute("DROP TABLE IF EXISTS tenant_api_keys")
    op.execute("DROP INDEX IF EXISTS idx_legal_ack_tenant_user_doc")
    op.execute("DROP TABLE IF EXISTS legal_acknowledgements")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_tenant_id")
    op.execute("ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS fk_audit_logs_tenant_id")
    op.execute("ALTER TABLE audit_logs DROP COLUMN IF EXISTS tenant_id")
    op.execute("DROP INDEX IF EXISTS ix_accounts_tenant_id")
    op.execute("ALTER TABLE accounts DROP CONSTRAINT IF EXISTS fk_accounts_tenant_id")
    op.execute("ALTER TABLE accounts DROP COLUMN IF EXISTS tenant_id")
    op.execute("DROP TABLE IF EXISTS tenant_memberships")
    op.execute("DROP TABLE IF EXISTS tenants")


def _seed_default_capabilities() -> None:
    polygon_configured = bool(settings.polygon_api_key)
    default_capabilities = [
        (
            "market_data.us_etf_daily",
            "polygon",
            "US",
            "etf",
            "1d",
            "available" if polygon_configured else "missing",
            "env" if polygon_configured else "env_or_tenant_credential",
            None
            if polygon_configured
            else "POLYGON_API_KEY or tenant Polygon credential is not configured",
        ),
        (
            "execution_import.csv",
            "manual_csv",
            "multi",
            "multi",
            None,
            "disabled",
            "planned",
            "CSV execution import is planned for the next implementation phase",
        ),
        (
            "notifications.in_app",
            "edgepilot",
            None,
            None,
            None,
            "available",
            "app",
            None,
        ),
        (
            "broker_sync.read_only",
            "byok",
            "multi",
            "multi",
            None,
            "disabled",
            "planned",
            "Read-only broker sync is deferred until CSV import is validated",
        ),
    ]
    values = ",\n".join(
        f"('{key}', {sql(provider)}, {sql(market)}, {sql(asset_type)}, {sql(timeframe)}, "
        f"{sql(status)}, {sql(source)}, {sql(reason)})"
        for key, provider, market, asset_type, timeframe, status, source, reason in default_capabilities
    )
    op.execute(
        f"""
        WITH defaults (
            capability_key,
            provider,
            market,
            asset_type,
            timeframe,
            status,
            source,
            reason
        ) AS (
            VALUES
            {values}
        )
        INSERT INTO tenant_data_capabilities (
            capability_id,
            tenant_id,
            capability_key,
            provider,
            market,
            asset_type,
            timeframe,
            status,
            source,
            reason
        )
        SELECT
            'cap_' || substr(md5(tenants.tenant_id || ':' || defaults.capability_key), 1, 24),
            tenants.tenant_id,
            defaults.capability_key,
            defaults.provider,
            defaults.market,
            defaults.asset_type,
            defaults.timeframe,
            defaults.status,
            defaults.source,
            defaults.reason
        FROM tenants
        CROSS JOIN defaults
        ON CONFLICT (tenant_id, capability_key) DO NOTHING
        """
    )


def _seed_default_job_states() -> None:
    op.execute(
        """
        INSERT INTO tenant_job_states (
            tenant_id,
            job_type,
            enabled,
            status,
            rate_limit_per_minute,
            metadata_json
        )
        SELECT
            tenant_id,
            'market_refresh_scan',
            true,
            'idle',
            2,
            '{"scope":"tenant","notes":"Foundation shell for per-tenant automation throttling"}'::jsonb
        FROM tenants
        ON CONFLICT (tenant_id, job_type) DO NOTHING
        """
    )


def sql(value: str | None) -> str:
    if value is None:
        return "NULL"
    return "'" + value.replace("'", "''") + "'"
