"""rework role enums

Revision ID: 80066d16e0ee
Revises: 24a4391219c0
Create Date: 2026-08-05 22:06:48.796906

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '80066d16e0ee'
down_revision: Union[str, Sequence[str], None] = '24a4391219c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # user_role: {admin, owner, member} -> {admin, reviewer, member}. Existing 'owner'
    # rows lose the (now removed) global-reviewer system role and become plain members;
    # admins can promote specific people to 'reviewer' afterward.
    op.execute("ALTER TYPE user_role RENAME TO user_role_old")
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'reviewer', 'member')")
    op.execute(
        """
        ALTER TABLE users ALTER COLUMN role TYPE user_role USING (
            CASE role::text
                WHEN 'owner' THEN 'member'
                ELSE role::text
            END
        )::user_role
        """
    )
    op.execute("DROP TYPE user_role_old")

    # asset_role (per-agent): {admin, editor, reviewer} -> {owner, editor}. Agent creators
    # previously granted the per-agent 'admin' role become the agent's 'owner'; the
    # per-agent 'reviewer' value was never actually written by the app, mapped defensively.
    op.execute("ALTER TYPE asset_role RENAME TO asset_role_old")
    op.execute("CREATE TYPE asset_role AS ENUM ('owner', 'editor')")
    op.execute(
        """
        ALTER TABLE user_agent_rels ALTER COLUMN role TYPE asset_role USING (
            CASE role::text
                WHEN 'admin' THEN 'owner'
                WHEN 'reviewer' THEN 'editor'
                ELSE role::text
            END
        )::asset_role
        """
    )
    op.execute("DROP TYPE asset_role_old")


def downgrade() -> None:
    op.execute("ALTER TYPE user_role RENAME TO user_role_new")
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'owner', 'member')")
    op.execute(
        """
        ALTER TABLE users ALTER COLUMN role TYPE user_role USING (
            CASE role::text
                WHEN 'reviewer' THEN 'member'
                ELSE role::text
            END
        )::user_role
        """
    )
    op.execute("DROP TYPE user_role_new")

    op.execute("ALTER TYPE asset_role RENAME TO asset_role_new")
    op.execute("CREATE TYPE asset_role AS ENUM ('admin', 'editor', 'reviewer')")
    op.execute(
        """
        ALTER TABLE user_agent_rels ALTER COLUMN role TYPE asset_role USING (
            CASE role::text
                WHEN 'owner' THEN 'admin'
                ELSE role::text
            END
        )::asset_role
        """
    )
    op.execute("DROP TYPE asset_role_new")
