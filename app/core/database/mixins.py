import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class ICMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False
    )
