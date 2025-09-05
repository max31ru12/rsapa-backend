from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.domains.membership.models import MembershipStatusEnum, UserMembershipSchema


class SubscriptionSummary(BaseModel):
    id: str
    status: MembershipStatusEnum


class PaymentSummary(BaseModel):
    amount_total: Optional[int] = Field(None, description="Сумма в минимальных единицах валюты (например, центы)")
    currency: Optional[str] = Field(None, examples=["usd", "eur"])
    invoice_id: Optional[str] = None


class CheckoutSessionSummaryResponse(BaseModel):
    membership: UserMembershipSchema
    subscription: SubscriptionSummary
    payment: Optional[PaymentSummary] = None


class UpdateAction(Enum):
    RESUME = "resume"
    CANCEL = "cancel"
