"""fab scoped agent dependencies

Revision ID: 9e0528b844c5
Revises: 0de67c8351cc
Create Date: 2026-08-18 22:54:43.793660

Adds `agent_dependencies.fab_id` so a legacy skill/mcp dependency can be scoped to
one specific fab a version is deployed to, instead of applying uniformly to every
fab the version reaches (see docs/history for the write-up). NULL keeps exactly one
meaning: this dependency has no fab dimension — always true for type=model or
source=registry, and also true for a legacy skill/mcp dependency on a version that
isn't deployed to any fab yet.

Existing data is backfilled rather than dropped (unlike 0de67c8351cc's mcps.host
etc., which had nothing meaningful to backfill into): every existing type=skill/mcp
row is expanded across whatever fabs its version was already deployed to at
migration time, so post-migration behavior matches what the old "must cover every
deployed fab" rule already enforced. A version with zero fabs deployed keeps its
dependency at fab_id=NULL.
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e0528b844c5'
down_revision: Union[str, Sequence[str], None] = '0de67c8351cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('agent_dependencies', sa.Column('fab_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'agent_dependencies_fab_id_fkey', 'agent_dependencies', 'fabs', ['fab_id'], ['id']
    )

    bind = op.get_bind()
    legacy_rows = bind.execute(
        sa.text(
            "SELECT id, agent_slug FROM agent_dependencies WHERE type IN ('skill', 'mcp')"
        )
    ).fetchall()
    for row in legacy_rows:
        fab_ids = [
            r[0]
            for r in bind.execute(
                sa.text("SELECT fab_id FROM agent_fabs WHERE agent_version_slug = :slug"),
                {"slug": row.agent_slug},
            ).fetchall()
        ]
        if not fab_ids:
            continue
        bind.execute(
            sa.text("UPDATE agent_dependencies SET fab_id = :fab_id WHERE id = :id"),
            {"fab_id": fab_ids[0], "id": row.id},
        )
        if len(fab_ids) > 1:
            original = bind.execute(
                sa.text(
                    "SELECT dependency_id, type, source FROM agent_dependencies WHERE id = :id"
                ),
                {"id": row.id},
            ).one()
            for extra_fab_id in fab_ids[1:]:
                bind.execute(
                    sa.text(
                        "INSERT INTO agent_dependencies "
                        "(id, agent_slug, dependency_id, type, source, fab_id) "
                        "VALUES (:id, :agent_slug, :dependency_id, :type, :source, :fab_id)"
                    ),
                    {
                        "id": uuid.uuid4(),
                        "agent_slug": row.agent_slug,
                        "dependency_id": original.dependency_id,
                        "type": original.type,
                        "source": original.source,
                        "fab_id": extra_fab_id,
                    },
                )

    op.drop_constraint('uq_agent_dependency', 'agent_dependencies', type_='unique')
    op.create_unique_constraint(
        'uq_agent_dependency',
        'agent_dependencies',
        ['agent_slug', 'dependency_id', 'type', 'source', 'fab_id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_agent_dependency', 'agent_dependencies', type_='unique')

    # Collapse fab-split rows back to one per (agent_slug, dependency_id, type,
    # source), keeping the earliest row and discarding the rest — this loses which
    # fabs a dependency was scoped to, same kind of accepted, one-directional data
    # loss as 0de67c8351cc's downgrade.
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "DELETE FROM agent_dependencies a USING agent_dependencies b "
            "WHERE a.agent_slug = b.agent_slug AND a.dependency_id = b.dependency_id "
            "AND a.type = b.type AND a.source = b.source AND a.id > b.id"
        )
    )

    op.create_unique_constraint(
        'uq_agent_dependency', 'agent_dependencies', ['agent_slug', 'dependency_id', 'type', 'source']
    )
    op.drop_constraint('agent_dependencies_fab_id_fkey', 'agent_dependencies', type_='foreignkey')
    op.drop_column('agent_dependencies', 'fab_id')
