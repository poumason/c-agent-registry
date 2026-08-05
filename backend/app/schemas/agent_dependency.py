import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import DependencyType


class AgentDependencyCreate(BaseModel):
    dependency_id: uuid.UUID
    type: DependencyType


class AgentDependencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_slug: str
    dependency_id: uuid.UUID
    type: DependencyType
    created_at: datetime
