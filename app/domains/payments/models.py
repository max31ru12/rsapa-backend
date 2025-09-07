from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum as SQLAEnum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.setup_db import Base

if TYPE_CHECKING:
    from app.domains.users.models import User


class PaymentType(str, Enum):
    ONE_TIME = "ONE_TIME"
    SUBSCRIPTION_INITIAL = "SUBSCRIPTION_INITIAL"
    SUBSCRIPTION_RENEWAL = "SUBSCRIPTION_RENEWAL"
    REFUND = "REFUND"


class PaymentStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    REQUIRES_PAYMENT_METHOD = "REQUIRES_PAYMENT_METHOD"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    UNPAID = "unpaid"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    type: Mapped[PaymentType] = mapped_column(
        SQLAEnum(PaymentType, name="payment_type_enum"),
        nullable=False,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SQLAEnum(PaymentStatus, name="payment_status_enum"),
        nullable=False,
    )

    amount_total: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(nullable=False)

    # Stripe IDs
    payment_intent_id: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    charge_id: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    invoice_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    subscription_id: Mapped[str] = mapped_column(String(128), index=True)
    checkout_session_id: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    stripe_customer_id: Mapped[str] = mapped_column(String(128), index=True)

    price_id: Mapped[str] = mapped_column(String(128))
    product_id: Mapped[str] = mapped_column(String(128))

    billing_reason: Mapped[str] = mapped_column(String(64))  # из invoice.billing_reason
    receipt_url: Mapped[str] = mapped_column(String(512), nullable=True)

    livemode: Mapped[bool] = mapped_column(default=False)
    description: Mapped[str] = mapped_column(String(512), nullable=True)

    # Диагностика/ошибки
    failure_code: Mapped[str] = mapped_column(String(128), nullable=True)
    failure_message: Mapped[str] = mapped_column(String(1024), nullable=True)
    payment_method_type: Mapped[str] = mapped_column(String(64), nullable=True)
    pm_last4: Mapped[str] = mapped_column(String(8), nullable=True)

    stripe_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    _metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped["User"] = relationship("User", back_populates="payments")
