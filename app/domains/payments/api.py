from typing import Annotated

import stripe
from fastapi import APIRouter, Header, Path
from fastapi_exception_responses import Responses
from loguru import logger
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request

from app.core.config import settings
from app.domains.auth.utils import CurrentUserDep
from app.domains.memberships.services import MembershipServiceDep
from app.domains.memberships.utils.common import get_checkout_session_summary_dictionary
from app.domains.payments.schemas import DonationRequestSchema

stripe.api_key = settings.STRIPE_API_KEY
router = APIRouter(prefix="/payments", tags=["Payments"])


class FulfillCheckoutResponses(Responses):
    INVALID_SIGNATURE = 400, "Invalid signature"


@router.post(
    "/stripe/webhook",
    responses=FulfillCheckoutResponses.responses,
    summary="Webhook responsible for handling stripe events",
)
async def fulfill_checkout(
    request: Request,
    service: MembershipServiceDep,
    stripe_signature: str = Header(alias="Stripe-Signature"),
) -> None:
    payload = await request.body()

    logger.info(f"\n\n{payload=} {settings.STRIPE_WEBHOOK_SECRET_KEY=}\n\n")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET_KEY,
        )
        logger.info(f"Event: {event.type}, ")
    except stripe.error.SignatureVerificationError:
        logger.warning("Invalid stripe signature")
        raise FulfillCheckoutResponses.INVALID_SIGNATURE
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    await service.process_stripe_webhook_event(event)

    return None


class GetCheckoutSessionResponses(Responses):
    NOT_A_SUBSCRIPTION_SESSION = 400, "Not a subscription session"
    FORBIDDEN = 403, "Forbidden"


@router.post("/donations/checkout-sessions", summary="Creates a checkout session")
async def create_donation_checkout_session(data: DonationRequestSchema):
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": "Donation"},
                        "unit_amount": data.amount,
                    },
                    "quantity": 1,
                }
            ],
            success_url="http://localhost:3000/payment/donations?success=true&session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:3000/payment/donations?canceled=true",
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/checkout-sessions/{session_id}",
    responses=GetCheckoutSessionResponses.responses,
    summary="Retrieve a checkout session summary by id,",
)
async def get_session_summary_by_id(
    session_id: Annotated[str, Path(...)],
    service: MembershipServiceDep,
    current_user: CurrentUserDep,
) -> dict:
    session = stripe.checkout.Session.retrieve(session_id, expand=["subscription", "invoice", "line_items", "customer"])

    if session["mode"] != "subscription":
        raise GetCheckoutSessionResponses.NOT_A_SUBSCRIPTION_SESSION

    metadata = dict(session.get("metadata") or {})
    user_membership_id = int(metadata["user_membership_id"])
    user_membership = await service.get_user_membership_by_kwargs(id=user_membership_id)

    if user_membership.user_id != current_user.id:
        raise GetCheckoutSessionResponses.FORBIDDEN
    membership_type = await service.get_membership_type_by_kwargs(id=user_membership.membership_type_id)

    return get_checkout_session_summary_dictionary(
        user_membership,
        membership_type,
        session,
    )
