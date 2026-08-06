import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AgentVisibility


class AgentCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None
    provider: str | None = None
    visibility: AgentVisibility = AgentVisibility.private


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    provider: str | None = None
    visibility: AgentVisibility | None = None


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    provider: str | None
    visibility: AgentVisibility
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
