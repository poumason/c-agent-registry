import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ReviewResult
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Review(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "reviews"

    agent_slug: Mapped[str] = mapped_column(
        ForeignKey("agent_versions.slug"), nullable=False, index=True
    )
    # User this review row is assigned to (an eligible reviewer at submit time).
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result: Mapped[ReviewResult] = mapped_column(
        SAEnum(ReviewResult, name="review_result"), nullable=False, default=ReviewResult.pending
    )
    # Set once the assigned reviewer actually signs off (mirrors reviewer_id at decision time).
    signoff_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    # Reviewer's note. Required by the API when rejecting; optional on approval.
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
