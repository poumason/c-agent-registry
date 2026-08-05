from app.models.enums import AssetRole, UserRole
from app.models.user import User
from app.models.user_agent_rel import UserAgentRel


def can_manage_agent(user: User, membership: UserAgentRel | None) -> bool:
    """Can create/edit versions, dependencies, and manage membership on this agent.

    System admin/owner can manage any agent (owner: "調整 agent 的所有參數").
    Otherwise requires a per-agent admin/editor grant (Asset_Role).
    """
    if user.role in (UserRole.admin, UserRole.owner):
        return True
    return membership is not None and membership.role in (AssetRole.admin, AssetRole.editor)


def can_administer_agent(user: User, membership: UserAgentRel | None) -> bool:
    """Can manage membership (grant/revoke per-agent roles)."""
    if user.role in (UserRole.admin, UserRole.owner):
        return True
    return membership is not None and membership.role == AssetRole.admin
