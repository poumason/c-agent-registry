import uuid

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import VersionStatus
from app.models.mixins import TimestampMixin


class AgentVersion(TimestampMixin, Base):
    __tablename__ = "agent_versions"
    __table_args__ = (UniqueConstraint("agent_id", "version", name="uq_agent_version_number"),)

    # PK is the slug per the ERD, e.g. "{agent.slug}-v{version}"
    slug: Mapped[str] = mapped_column(String(255), primary_key=True)

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    streaming: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    default_input_modes: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    default_output_modes: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    status: Mapped[VersionStatus] = mapped_column(
        SAEnum(VersionStatus, name="version_status"), nullable=False, default=VersionStatus.draft
    )
    # MinIO object key of the generated package zip, set once a review approves this version.
    package_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    updated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
