from datetime import datetime
from typing import TYPE_CHECKING

from passlib.hash import bcrypt
from pydantic import BaseModel
from sqlalchemy import Boolean, DateTime, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.setup_db import Base
from app.domains.auth.models import UserSubscription

if TYPE_CHECKING:
    from app.domains.auth.models import UserSubscription


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    firstname: Mapped[str] = mapped_column(nullable=False)
    lastname: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    stuff: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False
    )
    pending: Mapped[bool] = mapped_column(default=True, nullable=True, server_default=text("true"))
    institution: Mapped[str] = mapped_column()
    role: Mapped[str] = mapped_column()

    subscriptions: Mapped["UserSubscription"] = relationship(back_populates="user")

    _password: Mapped[str] = mapped_column()
    avatar_path: Mapped[str] = mapped_column(nullable=True, unique=True)

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, value: str) -> None:
        self._password = bcrypt.hash(value)

    def verify_password(self, plain_password: str) -> bool:
        return bcrypt.verify(plain_password, self._password)


class UserSchema(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: str
    stuff: bool
    description: str | None
    created_at: datetime
    institution: str
    role: str
    avatar_path: str | None

    model_config = {
        "from_attributes": True,
    }


class UpdateUserSchema(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    description: str | None = None
    institution: str | None = None
    role: str | None = None
