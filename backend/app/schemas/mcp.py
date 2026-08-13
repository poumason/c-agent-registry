import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AvailabilityStatus


class MCPFabCreate(BaseModel):
    fab_id: uuid.UUID
    host: str


class MCPFabRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mcp_id: uuid.UUID
    fab_id: uuid.UUID
    host: str
    status: AvailabilityStatus
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MCPFabSyncItem(MCPFabRead):
    # True when `status` flipped during the sync run this item came back from.
    changed: bool


class MCPRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    version: str
    description: str | None
    category: str | None
    tags: list[str]
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # Per-fab deployments (host/status/last_synced_at moved here — see MCPFab).
    fabs: list[MCPFabRead] = []


class MCPSyncMcpItem(MCPRead):
    fabs: list[MCPFabSyncItem] = []


class MCPSyncResult(BaseModel):
    synced_at: datetime
    # Counts are over (mcp, fab) rows, not distinct MCPs — an MCP deployed in 3 fabs
    # contributes up to 3 to `total`.
    total: int
    available: int
    unavailable: int
    items: list[MCPSyncMcpItem]
