"""candidate pa setup bridge

Revision ID: 0004_candidate_pa_setup_bridge
Revises: 0003_pa_engine_foundation
Create Date: 2026-04-30
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004_candidate_pa_setup_bridge"
down_revision: str | None = "0003_pa_engine_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE candidates ADD COLUMN IF NOT EXISTS pa_setup_id TEXT")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_candidates_pa_setup_id'
            ) THEN
                ALTER TABLE candidates
                ADD CONSTRAINT fk_candidates_pa_setup_id
                FOREIGN KEY (pa_setup_id) REFERENCES pa_setups(setup_id);
            END IF;
        END $$;
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_candidates_pa_setup_id ON candidates (pa_setup_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_candidates_pa_setup_id")
    op.execute("ALTER TABLE candidates DROP CONSTRAINT IF EXISTS fk_candidates_pa_setup_id")
    op.execute("ALTER TABLE candidates DROP COLUMN IF EXISTS pa_setup_id")
