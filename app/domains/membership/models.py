from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import DateTime, Enum as SQLAEnum, ForeignKey, Numeric, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base

if TYPE_CHECKING:
    from app.domains.users.models import User


class MembershipTypeEnum(Enum):
    ACTIVE = "ACTIVE"
    TRAINEE = "TRAINEE"
    AFFILIATE = "AFFILIATE"
    HONORARY = "HONORARY"
    PATHWAY = "PATHWAY"


class MembershipType(Base):
    __tablename__ = "membership_types"

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

    payments: Mapped[list["MembershipPayment"]] = relationship("MembershipPayment", back_populates="membership_type")


class MembershipStatusEnum(Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELED = "CANCELED"
    PENDING = "PENDING"


class UserMembership(Base, UCIMixin):
    __tablename__ = "users_memberships"

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    status: Mapped[MembershipStatusEnum] = mapped_column(
        SQLAEnum(MembershipStatusEnum, name="membership_type_enum"),
        nullable=False,
        default=MembershipStatusEnum.PENDING,
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", back_populates="memberships")

    membership_type_id: Mapped[int] = mapped_column(ForeignKey("membership_types.id"), nullable=False)
    membership_type: Mapped["MembershipType"] = relationship("MembershipType", back_populates="user_memberships")

    payment_id: Mapped[int] = mapped_column(
        ForeignKey("membership_payments.id"),
        unique=True,
        nullable=False,
    )
    payment: Mapped["MembershipPayment"] = relationship("MembershipPayment", back_populates="payed_membership")


class MembershipPayment(Base):
    __tablename__ = "membership_payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    currency: Mapped[str] = mapped_column(default="usd")
    status: Mapped[str] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", back_populates="membership_payments")

    membership_type_id: Mapped[int] = mapped_column(ForeignKey("membership_types.id"))
    membership_type: Mapped["MembershipType"] = relationship("MembershipType", back_populates="payments")

    payed_membership = relationship("Membership", back_populates="payment")


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
