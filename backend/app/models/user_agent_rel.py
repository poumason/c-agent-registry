import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AssetRole
from app.models.mixins import TimestampMixin, UUIDPKMixin


class UserAgentRel(UUIDPKMixin, TimestampMixin, Base):
    """Per-agent membership/permission grant (the ERD's User_Agent_Rel)."""

    __tablename__ = "user_agent_rels"
    __table_args__ = (UniqueConstraint("user_id", "agent_id", name="uq_user_agent"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False
    )
    role: Mapped[AssetRole] = mapped_column(
        SAEnum(AssetRole, name="asset_role"), nullable=False, default=AssetRole.editor
    )
