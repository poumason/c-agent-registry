import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MCPCreate(BaseModel):
    name: str
    version: str
    description: str | None = None
    category: str | None = None
    tags: list[str] = []
    host: str


class MCPRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    version: str
    description: str | None
    category: str | None
    tags: list[str]
    created_by: uuid.UUID
    host: str
    created_at: datetime
    updated_at: datetime
