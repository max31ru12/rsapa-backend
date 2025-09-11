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
from app.domains.membership.models import MembershipStatusEnum
from app.domains.membership.services import MembershipServiceDep

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

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET_KEY,
        )
        logger.info(f"Event: {event, type}, ")
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
    user_membership = await service.get_membership_by_kwargs(id=user_membership_id)

    if user_membership.user_id != current_user.id:
        raise GetCheckoutSessionResponses.FORBIDDEN

    stripe_subscription = session["subscription"]
    membership_type = await service.get_membership_type_by_kwargs(id=user_membership.membership_type_id)

    return {
        "membership": {
            "id": user_membership.id,
            "type": membership_type.type,
            "status_db": user_membership.status,
            "current_period_end": user_membership.current_period_end,
        },
        "subscription": {
            "id": stripe_subscription["id"],
            "status": MembershipStatusEnum(stripe_subscription["status"]),
        },
        "payment": {
            "amount_total": session.get("amount_total"),
            "currency": session.get("currency"),
            "invoice_id": session["invoice"]["id"],
        },
    }
