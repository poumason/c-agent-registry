"""fab scoped schema

Revision ID: 0de67c8351cc
Revises: 0850e047f539
Create Date: 2026-08-12 22:15:49.449528

Schema-only change (see docs/superpowers/specs/2026-08-12-fab-scoped-schema-design.md):
adds fab (廠區) scoping for agent deployments / MCP hosts / skill availability, new
Agent metadata fields, and a `model` dependency type. No application logic changes
here — `mcps.py`'s endpoints and `POST /mcps/sync` reference the columns dropped from
`mcps` below and will not work again until a follow-up commit rewrites them against
`mcp_fabs`; this was a deliberate, accepted tradeoff (see spec, section 5).

Existing `mcps.host` / `status` / `last_synced_at` data is dropped along with the
columns, not migrated into `mcp_fabs` — there's no fab to attribute historical rows
to (see spec's "既有資料遷移" note). Confirmed acceptable for this project's current
(pre-launch, no real data yet) stage.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0de67c8351cc'
down_revision: Union[str, Sequence[str], None] = '0850e047f539'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # `dependency_type` already exists in the DB (skill, mcp) — can only extend it
    # with ADD VALUE, not recreate it like DependencySource was. Safe to run inside
    # this migration's transaction because nothing in this same migration writes a
    # `type='model'` row (Postgres forbids using a new enum value in the transaction
    # that added it).
    op.execute("ALTER TYPE dependency_type ADD VALUE IF NOT EXISTS 'model'")

    op.create_table(
        'fabs',
        sa.Column('fab', sa.String(length=50), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fab'),
    )
    op.create_table(
        'mcp_fabs',
        sa.Column('mcp_id', sa.UUID(), nullable=False),
        sa.Column('fab_id', sa.UUID(), nullable=False),
        sa.Column('host', sa.String(length=1024), nullable=False),
        sa.Column(
            'status',
            postgresql.ENUM('available', 'unavailable', name='availability_status', create_type=False),
            server_default='available',
            nullable=False,
        ),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['fab_id'], ['fabs.id']),
        sa.ForeignKeyConstraint(['mcp_id'], ['mcps.id']),
        sa.PrimaryKeyConstraint('mcp_id', 'fab_id'),
    )
    op.create_table(
        'skill_fabs',
        sa.Column('skill_id', sa.UUID(), nullable=False),
        sa.Column('fab_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['fab_id'], ['fabs.id']),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id']),
        sa.PrimaryKeyConstraint('skill_id', 'fab_id'),
    )
    op.create_table(
        'agent_fabs',
        sa.Column('fab_id', sa.UUID(), nullable=False),
        sa.Column('agent_version_slug', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agent_version_slug'], ['agent_versions.slug']),
        sa.ForeignKeyConstraint(['fab_id'], ['fabs.id']),
        sa.PrimaryKeyConstraint('fab_id', 'agent_version_slug'),
    )

    # NOT NULL array/JSON columns added to tables that may already have rows: backfill
    # existing rows via a one-time server_default, then drop the server_default so the
    # column goes back to being purely app-defaulted (matching every other tags/array
    # column in this codebase, none of which carry a DB-level default).
    op.add_column(
        'agent_versions',
        sa.Column(
            'skills', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
    )
    op.alter_column('agent_versions', 'skills', server_default=None)
    op.drop_column('agent_versions', 'url')

    op.add_column('agents', sa.Column('icon_path', sa.String(length=1024), nullable=True))
    op.add_column(
        'agents',
        sa.Column(
            'category', postgresql.ARRAY(sa.String()), nullable=False, server_default=sa.text("'{tool}'")
        ),
    )
    op.alter_column('agents', 'category', server_default=None)
    op.add_column('agents', sa.Column('hello_msg', sa.Text(), nullable=True))
    op.add_column(
        'agents',
        sa.Column(
            'example_questions', postgresql.ARRAY(sa.String()), nullable=False, server_default=sa.text("'{}'")
        ),
    )
    op.alter_column('agents', 'example_questions', server_default=None)
    op.add_column('agents', sa.Column('audience', sa.String(length=500), nullable=True))
    op.add_column('agents', sa.Column('doc_url', sa.String(length=2048), nullable=True))

    op.drop_column('mcps', 'host')
    op.drop_column('mcps', 'status')
    op.drop_column('mcps', 'last_synced_at')


def downgrade() -> None:
    """Downgrade schema.

    Note: this does NOT remove 'model' from the `dependency_type` enum — Postgres has
    no DROP VALUE for enums, only a full type recreation (create new type, migrate
    every dependent column, drop old type), which isn't worth the risk for a
    downgrade path. Any `agent_dependencies` row with type='model' would need to be
    deleted by hand first if you actually needed the enum value gone, mirroring how
    f64afce7bce0's downgrade deletes registry-sourced rows before narrowing that enum.
    """
    op.add_column('mcps', sa.Column('last_synced_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('mcps', sa.Column('status', postgresql.ENUM('available', 'unavailable', name='availability_status'), server_default=sa.text("'available'::availability_status"), autoincrement=False, nullable=False))
    op.add_column('mcps', sa.Column('host', sa.VARCHAR(length=1024), autoincrement=False, nullable=False))

    op.drop_column('agents', 'doc_url')
    op.drop_column('agents', 'audience')
    op.drop_column('agents', 'example_questions')
    op.drop_column('agents', 'hello_msg')
    op.drop_column('agents', 'category')
    op.drop_column('agents', 'icon_path')

    op.add_column('agent_versions', sa.Column('url', sa.VARCHAR(length=2048), autoincrement=False, nullable=True))
    op.drop_column('agent_versions', 'skills')

    op.drop_table('agent_fabs')
    op.drop_table('skill_fabs')
    op.drop_table('mcp_fabs')
    op.drop_table('fabs')
