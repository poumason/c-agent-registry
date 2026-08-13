import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SkillFabCreate(BaseModel):
    fab_id: uuid.UUID


class SkillFabRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: uuid.UUID
    fab_id: uuid.UUID
    created_at: datetime
