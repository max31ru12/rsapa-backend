import time
from typing import Annotated

import stripe
from fastapi import APIRouter, Header, Path
from fastapi_exception_responses import Responses
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request

from app.core.config import settings
from app.domains.auth.utils import AdminUserDep, CurrentUserDep
from app.domains.membership.models import MembershipSchema, UpdateMembershipSchema
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


class MembershipNotFoundResponses(Responses):
    MEMBERSHIP_NOT_FOUND = 404, "Membership not found"


@router.put("/{membership_id}", responses=MembershipNotFoundResponses.responses, summary="Update membership")
async def update_membership_stripe_price_id(
    membership_id: Annotated[int, Path(...)],
    update_data: UpdateMembershipSchema,
    service: MembershipServiceDep,
    admin: AdminUserDep,
) -> MembershipSchema:
    try:
        return await service.update_membership(membership_id, update_data.model_dump(exclude_unset=True))
    except ValueError:
        raise MembershipNotFoundResponses.MEMBERSHIP_NOT_FOUND


@router.post("/{membership_id}/checkout-sessions")
async def create_checkout_session(
    membership_id: Annotated[int, Path(...)],
    service: MembershipServiceDep,
    current_user: CurrentUserDep,  # noqa Auth dependency
):
    membership = await service.get_membership_by_kwargs(id=membership_id)
    expires_at = int(time.time()) + 30 * 60
    unit_amount = int(membership.price_usd * 100)

    metadata = {
        "membership_type_id": membership.id,
        "user_id": current_user.id,
    }

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": membership.name,
                    },
                    "unit_amount": unit_amount,
                },
                "quantity": 1,
            }
        ],
        payment_intent_data={
            "metadata": metadata,
        },
        customer_email=current_user.email,
        success_url="http://localhost:3000/membership/stripe/success/{CHECKOUT_SESSION_ID}",
        # cancel_url="http://localhost:4242/cancel",
        expires_at=expires_at,
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

    # Платеж в сессии, для подписки приходят события:
    if event.type == "payment_intent.succeeded" or event.type == "invoice.payment_succeeded":
        # payment_intent = event.data.object
        pass

    # Банк отклоняет операцию, для подписки вызываются события:
    # 1. payment_intent.failed
    # 2. invoice.payment_failed
    elif event.type == "payment_intent.failed" or event.type == "invoice.payment_failed":
        pass

    else:
        pass

        # payment = await service.create_payment(
        #     **metadata,
        #     created_at=created_at,
        #     status=checkout_status,
        #     presentment_amount=presentment_amount,
        #     presentment_currency=presentment_currency,
        # )

    # Для теста просто возвращаем подтверждение
    return {"status": "success", "event_type": event["type"]}
