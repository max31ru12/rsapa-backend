from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class AmountDetails(BaseModel):
    tip: Dict[str, Any]


class CardOptions(BaseModel):
    installments: Optional[Any]
    mandate_options: Optional[Any]
    network: Optional[str]
    request_three_d_secure: Optional[str]


class PaymentMethodOptions(BaseModel):
    card: Optional[CardOptions]


class PresentmentDetails(BaseModel):
    presentment_amount: int
    presentment_currency: str


class PaymentIntentObject(BaseModel):
    id: str
    object: str
    amount: int
    amount_capturable: int
    amount_details: AmountDetails
    amount_received: int
    application: Optional[Any]
    application_fee_amount: Optional[int]
    automatic_payment_methods: Optional[Any]
    canceled_at: Optional[int]
    cancellation_reason: Optional[str]
    capture_method: Optional[str]
    client_secret: Optional[str]
    confirmation_method: Optional[str]
    created: int
    currency: str
    customer: Optional[str]
    description: Optional[str]
    excluded_payment_method_types: Optional[List[str]]
    last_payment_error: Optional[Any]
    latest_charge: Optional[str]
    livemode: bool
    metadata: Dict[str, str]
    next_action: Optional[Any]
    on_behalf_of: Optional[str]
    payment_method: Optional[str]
    payment_method_configuration_details: Optional[Any]
    payment_method_options: Optional[PaymentMethodOptions]
    payment_method_types: List[str]
    presentment_details: Optional[PresentmentDetails]
    processing: Optional[Any]
    receipt_email: Optional[str]
    review: Optional[str]
    setup_future_usage: Optional[str]
    shipping: Optional[Any]
    source: Optional[str]
    statement_descriptor: Optional[str]
    statement_descriptor_suffix: Optional[str]
    status: str
    transfer_data: Optional[Any]
    transfer_group: Optional[str]

    model_config = ConfigDict(extra="ignore")


class PaymentIntentWrapper(BaseModel):
    object: dict


class PayloadSchema(BaseModel):
    id: str
    object: str
    api_version: str
    created: int
    data: PaymentIntentWrapper
    livemode: bool
    pending_webhooks: int
    request: dict[str, Any]
    type: str

    model_config = ConfigDict(extra="ignore")

    @property
    def created_dt(self):
        return datetime.fromtimestamp(self.created, tz=timezone.utc)
