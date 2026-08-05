import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import VersionStatus


class AgentVersionCreate(BaseModel):
    url: str | None = None
    streaming: bool = False
    default_input_modes: list[str] = []
    default_output_modes: list[str] = []


class AgentVersionUpdate(BaseModel):
    url: str | None = None
    streaming: bool | None = None
    default_input_modes: list[str] | None = None
    default_output_modes: list[str] | None = None


class AgentVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    agent_id: uuid.UUID
    version: int
    url: str | None
    streaming: bool
    default_input_modes: list[str]
    default_output_modes: list[str]
    status: VersionStatus
    package_path: str | None
    created_by: uuid.UUID
    updated_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
