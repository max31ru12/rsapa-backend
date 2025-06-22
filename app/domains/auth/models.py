from datetime import date
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLAEnum, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.setup_db import Base

if TYPE_CHECKING:
    from app.domains.users.models import User


class SubscriptionTypeEnum(Enum):
    TRAINEE = "TRAINEE"
    ADJUNCT = "ADJUNCT"


class SubscriptionType(Base):
    __tablename__ = "subscription_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[SubscriptionTypeEnum] = mapped_column(
        SQLAEnum(SubscriptionTypeEnum, name="SubscriptionType"), nullable=False
    )
    price_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    duration: Mapped[int] = mapped_column(nullable=False, default=30)
    description: Mapped[str] = mapped_column(nullable=True)

    subscriptions: Mapped["UserSubscription"] = relationship(back_populates="subscription_type")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    start_date: Mapped[date] = mapped_column(default=func.current_date())
    end_date: Mapped[date] = mapped_column()

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="subscriptions")

    subscription_type_id: Mapped[id] = mapped_column(ForeignKey("subscription_types.id"))
    subscription_type: Mapped[SubscriptionType] = relationship(back_populates="subscriptions")
