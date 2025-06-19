from datetime import datetime

from passlib.hash import bcrypt
from sqlalchemy import func, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.setup_db import Base


class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    firstname: Mapped[str] = mapped_column(nullable=False)
    lastname: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    stuff: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False
    )

    _password: Mapped[str] = mapped_column()

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, value: str) -> None:
        self._password = bcrypt.hash(value)

    def verify_password(self, plain_password: str) -> bool:
        return bcrypt.verify(plain_password, self._password)
