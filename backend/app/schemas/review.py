import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReviewResult


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_slug: str
    reviewer_id: uuid.UUID
    priority: int
    result: ReviewResult
    signoff_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ReviewDecision(BaseModel):
    result: Literal[ReviewResult.approved, ReviewResult.rejected]


class SubmitForReview(BaseModel):
    reviewer_ids: list[uuid.UUID] = Field(min_length=1)


class ReviewerCandidate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
