import uuid

from pydantic import BaseModel, ConfigDict


class FabCreate(BaseModel):
    fab: str


class FabRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fab: str
