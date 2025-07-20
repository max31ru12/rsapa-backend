from datetime import datetime

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.mixins import ICMixin
from app.core.database.setup_db import Base


class ContactMessage(Base, ICMixin):
    __tablename__ = "contact_messages"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    email: Mapped[str] = mapped_column(String(256), nullable=False)
    subject: Mapped[str] = mapped_column(String(256), nullable=False)
    message: Mapped[str] = mapped_column(String(256), nullable=False)
    answered: Mapped[bool] = mapped_column(default=False, server_default=text("false"))


class CreateContactMessageSchema(BaseModel):
    name: str = Field(min_lingth=2, max_length=128)
    email: EmailStr
    subject: str = Field(min_lingth=2, max_length=128)
    message: str = Field(min_lingth=2, max_length=256)


class ContactMessageSchema(CreateContactMessageSchema):
    id: int
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }
