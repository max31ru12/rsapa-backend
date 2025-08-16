import time
from typing import Annotated

import stripe
from fastapi import APIRouter, Header, Path
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request

from app.core.config import settings
from app.domains.auth.utils import CurrentUserDep
from app.domains.membership.models import MembershipSchema
from app.domains.membership.services import MembershipServiceDep

stripe.api_key = settings.STRIPE_API_KEY
router = APIRouter(prefix="/membership", tags=["Membership"])


@router.get("")
async def get_all_memberships(
    service: MembershipServiceDep,
) -> list[MembershipSchema]:
    membership_list, _ = await service.get_all_memberships()
    data = [MembershipSchema.from_orm(item) for item in membership_list]
    return data


@router.get("/{membership_id}")
async def get_membership_detail(
    membership_id: Annotated[int, Path(...)],
    service: MembershipServiceDep,
) -> MembershipSchema:
    membership_type = await service.get_membership_by_kwargs(id=membership_id)
    return MembershipSchema.from_orm(membership_type)


@router.post("/{membership_id}/checkout-sessions")
async def create_checkout_session(
    membership_id: Annotated[int, Path(...)],
    service: MembershipServiceDep,
    current_user: CurrentUserDep,  # noqa Auth dependency
):
    membership = await service.get_membership_by_kwargs(id=membership_id)
    expires_timedelta_seconds = 30 * 60

    # metadata = {"membership_id": membership.id}

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": membership.name,
                    },
                    "unit_amount": 2000,
                },
                "quantity": 1,
            }
        ],
        metadata={},
        customer_email=current_user.email,
        success_url="http://localhost:3000/membership/stripe/success/{CHECKOUT_SESSION_ID}",
        # cancel_url="http://localhost:4242/cancel",
        expires_at=int(time.time()) + expires_timedelta_seconds,
    )

    return session.url


@router.post("/stripe/webhook")
async def fulfill_checkout(
    request: Request,
    service: MembershipServiceDep,
    stripe_signature: str = Header(alias="Stripe-Signature"),
):
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET_KEY,
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    await service.create_payment()

    # Для теста просто возвращаем подтверждение
    return {"status": "success", "event_type": event["type"]}
