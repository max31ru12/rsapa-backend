from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, DateTime, Enum as SQLAEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database.setup_db import Base


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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

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
    payment_intent_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    charge_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    invoice_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    subscription_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    checkout_session_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)

    price_id: Mapped[Optional[str]] = mapped_column(String(128))
    product_id: Mapped[Optional[str]] = mapped_column(String(128))

    billing_reason: Mapped[Optional[str]] = mapped_column(String(64))  # из invoice.billing_reason
    receipt_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    livemode: Mapped[bool] = mapped_column(default=False)
    description: Mapped[Optional[str]] = mapped_column(String(512))

    # Диагностика/ошибки
    failure_code: Mapped[Optional[str]] = mapped_column(String(128))
    failure_message: Mapped[Optional[str]] = mapped_column(String(1024))
    payment_method_type: Mapped[Optional[str]] = mapped_column(String(64))
    pm_last4: Mapped[Optional[str]] = mapped_column(String(8))

    stripe_created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    _metadata: Mapped[Optional[dict]] = mapped_column(JSON)
