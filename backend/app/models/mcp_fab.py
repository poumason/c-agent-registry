import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AvailabilityStatus
from app.models.mixins import TimestampMixin


class MCPFab(TimestampMixin, Base):
    """An MCP server's per-fab deployment: host/status/last_synced_at used to live
    directly on MCP, but an MCP server is deployed (and synced) independently in each
    fab, so those fields moved here — MCP now only holds fab-independent metadata."""

    __tablename__ = "mcp_fabs"

    mcp_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mcps.id"), primary_key=True
    )
    fab_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fabs.id"), primary_key=True
    )
    host: Mapped[str] = mapped_column(String(1024), nullable=False)
    # Refreshed by POST /mcps/sync, which heuristically probes http(s) hosts.
    status: Mapped[AvailabilityStatus] = mapped_column(
        SAEnum(AvailabilityStatus, name="availability_status"),
        nullable=False,
        default=AvailabilityStatus.available,
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
