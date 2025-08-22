from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SubscriptionStatusEnum(str, Enum):
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"


class MembershipSummary(BaseModel):
    id: int
    name: str
    # при желании замени на свой MembershipTypeEnum
    type: str
    end_date: datetime = Field(..., description="Окончание действия в UTC")
    status_db: str  # или ваш MembershipStatusEnum


class SubscriptionSummary(BaseModel):
    id: str
    status: SubscriptionStatusEnum


class PaymentSummary(BaseModel):
    amount_total: Optional[int] = Field(None, description="Сумма в минимальных единицах валюты (например, центы)")
    currency: Optional[str] = Field(None, examples=["usd", "eur"])
    invoice_id: Optional[str] = None


class CheckoutSessionSummaryResponse(BaseModel):
    membership: MembershipSummary
    subscription: SubscriptionSummary
    payment: Optional[PaymentSummary] = None
