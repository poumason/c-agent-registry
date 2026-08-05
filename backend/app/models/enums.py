import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    reviewer = "reviewer"
    member = "member"


class UserStatus(str, enum.Enum):
    active = "active"
    disabled = "disabled"


class AgentVisibility(str, enum.Enum):
    private = "private"
    internal = "internal"
    public = "public"


class AssetRole(str, enum.Enum):
    """Per-agent role granted via User_Agent_Rel (the diagram's Asset_Role).

    owner = the agent's creator (exactly one per agent, invites/removes editors).
    editor = an invited co-maintainer with equal content permissions.
    """

    owner = "owner"
    editor = "editor"


class VersionStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"
    active = "active"
    archived = "archived"


class ReviewResult(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class DependencyType(str, enum.Enum):
    skill = "skill"
    mcp = "mcp"
