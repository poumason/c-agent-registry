import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SkillFab(Base):
    """Which fabs a skill is available in. Pure availability junction, no per-fab
    data — skill content lives in MinIO, shared globally, unlike an MCP server's
    per-fab host (see MCPFab). No `updated_at`: there's no mutable state here beyond
    the link itself existing."""

    __tablename__ = "skill_fabs"

    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skills.id"), primary_key=True
    )
    fab_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fabs.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
