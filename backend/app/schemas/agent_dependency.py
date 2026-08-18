import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import DependencySource, DependencyType


class AgentDependencyCreate(BaseModel):
    dependency_id: str
    type: DependencyType
    # Omitted by existing/older clients -> legacy, preserving today's behavior
    # (resolve against the first-party skills/mcps tables) without requiring every
    # caller to know about the registry migration.
    source: DependencySource = DependencySource.legacy
    # Required once the version is deployed to 1+ fabs (for legacy skill/mcp
    # dependencies); omitted otherwise. See app/services/fab_scope.py.
    fab_id: uuid.UUID | None = None


class AgentDependencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_slug: str
    dependency_id: str
    type: DependencyType
    source: DependencySource
    fab_id: uuid.UUID | None
    created_at: datetime
