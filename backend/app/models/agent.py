import uuid
from datetime import datetime

from sqlalchemy import Enum as SAEnum
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
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
    # MinIO object key for the agent's icon image. Null until the owner uploads one
    # (upload API + bucket wiring land in a follow-up commit) — the frontend falls
    # back to a bundled default icon when this is null, so there's no DB-level default.
    icon_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # Free-form, same convention as MCP/Skill/AIModel's `tags` — not an enum.
    category: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=lambda: ["tool"]
    )
    hello_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_questions: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    # PAT (personal access token) audience value this agent expects a caller's token
    # to carry. Column only for now — actual verification logic lands separately.
    audience: Mapped[str | None] = mapped_column(String(500), nullable=True)
    doc_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    # Soft delete: set on DELETE /agents/{slug}, never physically removed. Every read path
    # filters this out so a deleted agent is 404 everywhere, not just hidden from lists.
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
