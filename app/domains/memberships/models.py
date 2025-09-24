from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Enum as SQLAEnum, ForeignKey, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.database.mixins import UCIMixin
from app.core.database.setup_db import Base
from app.domains.users.models import UserSchema

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
    stripe_price_id: Mapped[str] = mapped_column(
        default=settings.STRIPE_PRICE_ID_TEST, server_default=settings.STRIPE_PRICE_ID_TEST
    )

    user_memberships: Mapped[list["UserMembership"]] = relationship("UserMembership", back_populates="membership_type")


class MembershipStatusEnum(Enum):
    INCOMPLETE = "incomplete"  # подписка создана, первый платеж не прошел
    INCOMPLETE_EXPIRED = "incomplete_expired"  # Подписка не активировалась, тк первый платеж не прошел
    TRIALING = "trialing"  # Пробный период
    ACTIVE = "active"  # Активна
    PAST_DUE = "past_due"  # Подписка активна, но последний платеж не прошел
    CANCELED = "canceled"  # Отменена (только после оплаченного периода)
    UNPAID = "unpaid"  # не пытается больше взять оплату


class ApprovalStatusEnum(Enum):
    APPROVED = "APPROVED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


class UserMembership(Base, UCIMixin):
    __tablename__ = "users_memberships"

    status: Mapped[MembershipStatusEnum] = mapped_column(
        SQLAEnum(MembershipStatusEnum, name="users_membership_enum"),
        nullable=False,
        default=MembershipStatusEnum.INCOMPLETE,
    )
    approval_status: Mapped[ApprovalStatusEnum] = mapped_column(
        SQLAEnum(ApprovalStatusEnum, name="approval_status_enum"),
        nullable=False,
        default=ApprovalStatusEnum.PENDING,
        server_default=text("'PENDING'"),
    )

    stripe_subscription_id: Mapped[str] = mapped_column(nullable=True)
    stripe_customer_id: Mapped[str] = mapped_column(nullable=True, unique=True)
    latest_invoice_id: Mapped[str] = mapped_column(nullable=True, unique=True)

    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    has_access: Mapped[bool] = mapped_column(default=False)
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False, server_default=text("false"))

    checkout_session_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    checkout_url: Mapped[str] = mapped_column(nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    user: Mapped["User"] = relationship("User", back_populates="memberships")

    membership_type_id: Mapped[int] = mapped_column(ForeignKey("membership_types.id"), nullable=False)
    membership_type: Mapped["MembershipType"] = relationship("MembershipType", back_populates="user_memberships")


class UpdateMembershipTypeSchema(BaseModel):
    type: Optional[MembershipTypeEnum] = Field(None)
    description: Optional[str] = Field(None)
    is_purchasable: Optional[bool] = Field(None)
    stripe_price_id: Optional[str] = Field(None)
    price_usd: Optional[float] = Field(None)


class MembershipTypeSchema(BaseModel):
    id: int
    name: str
    type: MembershipTypeEnum
    price_usd: float
    duration: int
    description: str
    is_purchasable: bool
    stripe_price_id: str

    model_config = {
        "from_attributes": True,
    }


class UpdateUserMembershipSchema(BaseModel):
    approval_status: ApprovalStatusEnum = Field(None)


class UserMembershipSchema(BaseModel):
    id: int

    created_at: datetime
    updated_at: datetime

    status: MembershipStatusEnum
    approval_status: ApprovalStatusEnum

    stripe_subscription_id: str | None
    stripe_customer_id: str | None

    current_period_end: datetime | None
    has_access: bool
    cancel_at_period_end: bool

    checkout_session_expires_at: datetime | None
    checkout_url: str | None
    latest_invoice_id: str | None

    user_id: int
    membership_type_id: int

    model_config = {
        "from_attributes": True,
    }


class ExtendedUserMembershipSchema(UserMembershipSchema):
    user: UserSchema
    membership_type: MembershipTypeSchema

    model_config = {
        "from_attributes": True,
    }
