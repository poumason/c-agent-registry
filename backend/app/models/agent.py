import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AgentVisibility
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Agent(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "agents"

    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    visibility: Mapped[AgentVisibility] = mapped_column(
        SAEnum(AgentVisibility, name="agent_visibility"),
        nullable=False,
        default=AgentVisibility.private,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    # Soft delete: set on DELETE /agents/{slug}, never physically removed. Every read path
    # filters this out so a deleted agent is 404 everywhere, not just hidden from lists.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
