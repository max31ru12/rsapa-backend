from datetime import datetime

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base


class ContactMessage(Base, UCIMixin):
    __tablename__ = "contact_messages"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False)
    subject: Mapped[str] = mapped_column(String(256), nullable=False)
    message: Mapped[str] = mapped_column(String(256), nullable=False)
    answered: Mapped[bool] = mapped_column(default=False, server_default=text("false"))


class SponsorshipRequest(Base, UCIMixin):
    __tablename__ = "sponsorship_requests"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False)
    company: Mapped[str] = mapped_column(String(256), nullable=False)
    message: Mapped[str] = mapped_column(nullable=False)


class CreateContactMessageSchema(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    email: EmailStr
    subject: str = Field(min_length=2, max_length=128)
    message: str = Field(min_length=2, max_length=256)


class ContactMessageSchema(CreateContactMessageSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    answered: bool

    model_config = {
        "from_attributes": True,
    }


class CreateSponsorshipRequestSchema(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    email: EmailStr
    company: str = Field(min_length=2, max_length=128)
    message: str = Field(min_length=2, max_length=256)


class SponsorshipRequestSchema(CreateSponsorshipRequestSchema):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
