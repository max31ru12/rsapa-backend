import time
from datetime import datetime, timedelta
from typing import Annotated

import stripe
from fastapi import APIRouter, Header, Path
from fastapi_exception_responses import Responses
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request

from app.core.config import settings
from app.domains.auth.utils import AdminUserDep, CurrentUserDep
from app.domains.membership.models import MembershipSchema, MembershipStatusEnum, UpdateMembershipSchema
from app.domains.membership.schemas import CheckoutSessionSummaryResponse
from app.domains.membership.services import MembershipServiceDep

stripe.api_key = settings.STRIPE_API_KEY
router = APIRouter(prefix="/memberships", tags=["Membership"])


@router.get("")
async def get_all_memberships(
    service: MembershipServiceDep,
) -> list[MembershipSchema]:
    membership_list, _ = await service.get_all_membership_types()
    data = [MembershipSchema.from_orm(item) for item in membership_list]
    return data


@router.get("/{membership_id}")
async def get_membership_detail(
    membership_id: Annotated[int, Path(...)],
    service: MembershipServiceDep,
) -> MembershipSchema:
    membership_type = await service.get_membership_type_by_kwargs(id=membership_id)
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
        return await service.update_membership_type(membership_id, update_data.model_dump(exclude_unset=True))
    except ValueError:
        raise MembershipNotFoundResponses.MEMBERSHIP_NOT_FOUND


@router.post("/{membership_id}/checkout-sessions")
async def create_checkout_session(
    membership_id: Annotated[int, Path(...)],
    service: MembershipServiceDep,
    current_user: CurrentUserDep,  # noqa Auth dependency
):
    membership_type = await service.get_membership_type_by_kwargs(id=membership_id)
    checkout_expires_at = int(time.time()) + 30 * 60

    user_membership = await service.create_membership(
        status=MembershipStatusEnum.INCOMPLETE,
        end_date=datetime.utcnow() + timedelta(days=365),
        user_id=current_user.id,
        membership_type_id=membership_type.id,
    )

    metadata = {
        "membership_type_id": str(membership_type.id),
        "user_id": str(current_user.id),
        "user_membership_id": str(user_membership.id),
    }

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[
            {
                "price": membership_type.stripe_price_id,
                "quantity": 1,
            }
        ],
        metadata=metadata,
        subscription_data={"metadata": metadata},
        customer_email=current_user.email,
        success_url="http://localhost:3000/payment/membership?success=true&session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://localhost:3000/payment/membership?canceled=true",
        expires_at=checkout_expires_at,
    )

    return session.url


@router.post("/stripe/webhook")
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
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    data = event["data"]["object"]
    metadata = data.metadata

    if event.type == "checkout.session.completed":
        subscription_id = data["subscription"]
        subscription = stripe.Subscription.retrieve(subscription_id)
        user_membership_id = int(metadata["user_membership_id"])

        await service.update_membership(
            user_membership_id,
            {
                "status": MembershipStatusEnum(subscription.status),
                "stripe_subscription_id": subscription_id,
            },
        )

        return

    elif event.type == "customer.subscription.updated":
        # Обновление подписки
        pass

    elif event.type in ("customer.subscription.deleted", "invoice.payment_failed"):
        # Удаление или неоплата подписки
        pass


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
) -> CheckoutSessionSummaryResponse:
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

    return CheckoutSessionSummaryResponse(
        membership={
            "id": str(user_membership.id),
            "name": str(membership_type.name),
            "type": str(membership_type.type),
            "end_date": str(user_membership.end_date),
            "status_db": str(user_membership.status),
        },
        subscription={
            "id": str(stripe_subscription["id"]),
            "status": str(stripe_subscription["status"]),
        },
        payment={
            "amount_total": str(session.get("amount_total")),
            "currency": str(session.get("currency")),
            "invoice_id": str(session.get("invoice")),
        },
    )
