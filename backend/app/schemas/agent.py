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
    icon_path: str | None = None
    category: list[str] = ["tool"]
    hello_msg: str | None = None
    example_questions: list[str] = []
    audience: str | None = None
    doc_url: str | None = None


class AgentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    provider: str | None = None
    visibility: AgentVisibility | None = None
    icon_path: str | None = None
    category: list[str] | None = None
    hello_msg: str | None = None
    example_questions: list[str] | None = None
    audience: str | None = None
    doc_url: str | None = None


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
    icon_path: str | None
    category: list[str]
    hello_msg: str | None
    example_questions: list[str]
    audience: str | None
    doc_url: str | None


class AgentListResponse(BaseModel):
    items: list[AgentRead]
    total: int
    limit: int
    offset: int
