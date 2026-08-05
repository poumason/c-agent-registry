import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Skill(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    # MinIO object key (under the skills bucket) where the uploaded skill files live.
    bucket_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    # Optional MCPs this skill depends on.
    mcp_dependency: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list
    )
