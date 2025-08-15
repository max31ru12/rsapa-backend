from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, List

from pydantic import BaseModel
from sqlalchemy import Enum as SQLAEnum, ForeignKey, Numeric, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.setup_db import Base

if TYPE_CHECKING:
    from app.domains.users.models import User


class MembershipTypeEnum(Enum):
    ACTIVE = "ACTIVE"
    TRAINEE = "TRAINEE"
    AFFILIATE = "AFFILIATE"
    HONORARY = "HONORARY"
    PATHWAY = "PATHWAY"


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[MembershipTypeEnum] = mapped_column(
        SQLAEnum(MembershipTypeEnum, name="membership_type_enum"),
        nullable=False,
    )
    price_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    duration: Mapped[int] = mapped_column(nullable=False, default=365)
    description: Mapped[str] = mapped_column(nullable=True)

    is_purchasable: Mapped[bool] = mapped_column(nullable=False, default=True, server_default=text("true"))

    subscriptions: Mapped[List["UserSubscription"]] = relationship(back_populates="membership")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    start_date: Mapped[date] = mapped_column(default=func.current_date())
    end_date: Mapped[date] = mapped_column()

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="subscriptions")

    # Исправлено: тип, имя столбца и имя таблицы в FK
    membership_id: Mapped[int] = mapped_column(ForeignKey("memberships.id"))
    membership: Mapped[Membership] = relationship(back_populates="subscriptions")


class MembershipSchema(BaseModel):
    id: int
    name: str
    type: MembershipTypeEnum
    price_usd: float
    duration: int
    description: str
    is_purchasable: bool

    model_config = {
        "from_attributes": True,
    }
