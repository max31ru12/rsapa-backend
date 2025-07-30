from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base

if TYPE_CHECKING:
    from app.domains.users.models import User


class News(Base, UCIMixin):
    __tablename__ = "news"

    body: Mapped[str] = mapped_column(String(), nullable=False)

    is_published: Mapped[bool] = mapped_column(default=True, server_default=text("true"))

    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    author: Mapped["User"] = relationship("User", back_populates="news")


class NewsSchema(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    body: str
    is_published: bool
    author_id: int

    model_config = {"from_attributes": True}
