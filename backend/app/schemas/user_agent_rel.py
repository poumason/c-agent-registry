import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AssetRole


class MemberUpsert(BaseModel):
    """Invites always grant editor rights - ownership isn't transferable via this endpoint."""

    user_id: uuid.UUID


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    agent_id: uuid.UUID
    role: AssetRole
    created_at: datetime
    updated_at: datetime
