from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPKMixin


class Fab(UUIDPKMixin, Base):
    """A physical fab (廠區), e.g. F15, F12, F18. Low-churn reference data — new rows
    only show up when a new fab opens, so unlike most tables here it deliberately has
    no TimestampMixin."""

    __tablename__ = "fabs"

    fab: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
