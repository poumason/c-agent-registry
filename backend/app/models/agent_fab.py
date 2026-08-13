import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class AgentFab(TimestampMixin, Base):
    """Where a given agent version is deployed: each (fab, agent version) pair gets
    its own k8s service URL, since the same version can run in more than one fab."""

    __tablename__ = "agent_fabs"

    fab_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fabs.id"), primary_key=True
    )
    # FK is to AgentVersion.slug, not Agent.slug — deployment is scoped to a specific
    # version, matching AgentDependency.agent_slug's existing (if confusingly named)
    # convention of pointing at agent_versions.slug.
    agent_version_slug: Mapped[str] = mapped_column(
        String(255), ForeignKey("agent_versions.slug"), primary_key=True
    )
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
