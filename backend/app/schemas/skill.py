import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    version: str
    description: str | None
    category: str | None
    tags: list[str]
    created_by: uuid.UUID
    bucket_path: str
    mcp_dependency: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime
