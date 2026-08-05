from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import UserRole, UserStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"), nullable=False, default=UserRole.member
    )
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, name="user_status"), nullable=False, default=UserStatus.active
    )
