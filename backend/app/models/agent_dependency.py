import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import DependencyType
from app.models.mixins import TimestampMixin, UUIDPKMixin


class AgentDependency(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "agent_dependencies"
    __table_args__ = (
        UniqueConstraint(
            "agent_slug", "dependency_id", "type", name="uq_agent_dependency"
        ),
    )

    agent_slug: Mapped[str] = mapped_column(
        ForeignKey("agent_versions.slug"), nullable=False, index=True
    )
    # Polymorphic: points into skills.id or mcps.id depending on `type`. No DB-level FK
    # since it can reference either table.
    dependency_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    type: Mapped[DependencyType] = mapped_column(
        SAEnum(DependencyType, name="dependency_type"), nullable=False
    )
