import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import VersionStatus


class AgentVersionCreate(BaseModel):
    streaming: bool = False
    default_input_modes: list[str] = []
    default_output_modes: list[str] = []


class AgentVersionUpdate(BaseModel):
    streaming: bool | None = None
    default_input_modes: list[str] | None = None
    default_output_modes: list[str] | None = None
    # Agent card "skills" payload — see AgentVersion.skills' model comment. A raw list
    # of user-authored objects (id/name/description/tags/examples/inputModes/
    # outputModes per the A2A skill shape), not validated field-by-field here.
    skills: list[Any] | None = None


class AgentVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    agent_id: uuid.UUID
    version: int
    streaming: bool
    default_input_modes: list[str]
    default_output_modes: list[str]
    status: VersionStatus
    package_path: str | None
    skills: list[Any]
    created_by: uuid.UUID
    updated_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
