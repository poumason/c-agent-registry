import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentFabEntry(BaseModel):
    fab_id: uuid.UUID
    url: str


class AgentFabSetRequest(BaseModel):
    # Replace-all semantics: this is the complete desired set of fab deployments for
    # the version, not a delta — matches the "checkbox + url per row, one Save
    # button" panel it's built for.
    fabs: list[AgentFabEntry]


class AgentFabRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fab_id: uuid.UUID
    agent_version_slug: str
    url: str | None
    created_at: datetime
    updated_at: datetime
