import uuid
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ReviewResult


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_slug: str
    reviewer_id: uuid.UUID
    priority: int
    result: ReviewResult
    signoff_by: uuid.UUID | None
    comment: str | None
    created_at: datetime
    updated_at: datetime


class ReviewDecision(BaseModel):
    result: Literal[ReviewResult.approved, ReviewResult.rejected]
    # Required when rejecting so the submitter knows what to fix; optional on approval.
    comment: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def require_comment_on_reject(self) -> Self:
        if self.result == ReviewResult.rejected and not (self.comment and self.comment.strip()):
            raise ValueError("comment is required when rejecting")
        return self


class SubmitForReview(BaseModel):
    reviewer_ids: list[uuid.UUID] = Field(min_length=1)


class ReviewerCandidate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
