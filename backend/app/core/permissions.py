from app.models.enums import AssetRole, UserRole
from app.models.user import User
from app.models.user_agent_rel import UserAgentRel


def can_manage_agent(user: User, membership: UserAgentRel | None) -> bool:
    """Can create/edit versions and dependencies on this agent.

    System admin can manage any agent. Otherwise requires per-agent membership —
    owner and editor have equal content permissions.
    """
    if user.role == UserRole.admin:
        return True
    return membership is not None


def can_administer_agent(user: User, membership: UserAgentRel | None) -> bool:
    """Can manage membership (invite/remove editors) on this agent.

    Only the agent's owner (or system admin) may do this — ownership itself isn't
    granted or revoked through membership management.
    """
    if user.role == UserRole.admin:
        return True
    return membership is not None and membership.role == AssetRole.owner
