from datetime import datetime
from typing import TYPE_CHECKING, Annotated

import phonenumbers
from passlib.hash import bcrypt
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError
from sqlalchemy import Boolean, DateTime, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.setup_db import Base
from app.domains.shared.types import Password

if TYPE_CHECKING:
    from app.domains.memberships.models import UserMembership
    from app.domains.news.models import News
    from app.domains.payments.models import Payment


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    firstname: Mapped[str] = mapped_column(nullable=False)
    lastname: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True, unique=True)
    stuff: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False
    )
    pending: Mapped[bool] = mapped_column(default=True, nullable=True, server_default=text("true"))
    institution: Mapped[str] = mapped_column()
    role: Mapped[str] = mapped_column()

    last_password_change: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    email_confirmed: Mapped[bool] = mapped_column(default=False, server_default=text("false"))

    news: Mapped[list["News"]] = relationship("News", back_populates="author")
    memberships: Mapped[list["UserMembership"]] = relationship("UserMembership", back_populates="user")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="user")

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
    phone_number: str | None
    pending: bool
    last_password_change: datetime | None
    email_confirmed: bool

    model_config = {
        "from_attributes": True,
    }


class UpdateUserSchema(BaseModel):
    firstname: Annotated[str | None, Field(min_length=2)] = None
    lastname: Annotated[str | None, Field(min_length=2)] = None
    description: str | None = None
    institution: Annotated[str | None, Field(min_length=2)] = None
    role: str | None = None
    phone_number: Annotated[str | None, Field()] = None

    @field_validator("phone_number")
    def validate_phone_number(cls, value):
        if value is None or value.strip() == "":
            return None
        try:
            parsed = phonenumbers.parse(value, None)
            if not phonenumbers.is_valid_number(parsed):
                raise PydanticCustomError("phone_number.invalid", "Invalid phone number format")
        except phonenumbers.NumberParseException:
            raise PydanticCustomError("phone_number.unparsable", "Invalid phone number format")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: Password
    confirm_new_password: Password

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.new_password != self.confirm_new_password:
            raise PydanticCustomError(
                "password_mismatch",  # internal code
                "Passwords do not match",  # user-facing message
            )
        return self

    @field_validator("new_password", "confirm_new_password")
    def validate_password(cls, v):
        if len(v) < 4:
            raise PydanticCustomError("password_too_short", "Password should have at least 4 characters")
        return v
