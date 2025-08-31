import time
from datetime import datetime, timedelta, timezone
from typing import Annotated

import stripe
from fastapi import APIRouter, Header, Path
from fastapi_exception_responses import Responses
from starlette import status
from starlette.exceptions import HTTPException
from starlette.requests import Request

from app.core.config import settings
from app.domains.auth.utils import AdminUserDep, CurrentUserDep
from app.domains.membership.models import (
    MembershipStatusEnum,
    MembershipTypeEnum,
    MembershipTypeSchema,
    UpdateMembershipTypeSchema,
    UserMembershipSchema,
)
from app.domains.membership.schemas import CheckoutSessionSummaryResponse
from app.domains.membership.services import MembershipServiceDep
from app.domains.membership.utils.checkout_session_utils import (
    check_membership_type_already_purchased,
    check_session_is_locked,
)
from app.domains.membership.utils.webhook_utils import (
    process_checkout_session_completed,
    process_customer_subscription_deleted,
    process_customer_subscription_updated,
    process_invoice_payment_failed,
)

stripe.api_key = settings.STRIPE_API_KEY
router = APIRouter(prefix="", tags=["Membership types"])


@router.get("/membership-types")
async def get_all_memberships(
    service: MembershipServiceDep,
) -> list[MembershipTypeSchema]:
    membership_list, _ = await service.get_all_membership_types()
    data = [MembershipTypeSchema.from_orm(item) for item in membership_list]
    return data


@router.get("/membership-types/{membership_type_id}")
async def get_membership_detail(
    membership_type_id: Annotated[int, Path(...)],
    service: MembershipServiceDep,
) -> MembershipTypeSchema:
    membership_type = await service.get_membership_type_by_kwargs(id=membership_type_id)
    return MembershipTypeSchema.from_orm(membership_type)


class MembershipNotFoundResponses(Responses):
    MEMBERSHIP_NOT_FOUND = 404, "Membership not found"


@router.put(
    "/membership-types/{membership_type_id}",
    responses=MembershipNotFoundResponses.responses,
    summary="Update membership type",
)
async def update_membership_type(
    membership_type_id: Annotated[int, Path(...)],
    update_data: UpdateMembershipTypeSchema,
    service: MembershipServiceDep,
    admin: AdminUserDep,  # noqa
) -> MembershipTypeSchema:
    try:
        return await service.update_membership_type(membership_type_id, update_data.model_dump(exclude_unset=True))
    except ValueError:
        raise MembershipNotFoundResponses.MEMBERSHIP_NOT_FOUND


class CreateCheckoutSessionResponses(Responses):
    FORBIDDEN_MEMBERSHIP_TYPE = 403, "You can't purchase the membership type with provided id"
    MEMBERSHIP_TYPE_NOT_FOUND = 404, "Membership type with provided id not found"
    MEMBERSHIP_ALREADY_PURCHASED = 409, "Membership with provided id is already purchased"


@router.post(
    "/membership-types/{membership_type_id}/checkout-sessions",
    status_code=201,
    responses=CreateCheckoutSessionResponses.responses,
    summary="Creates a checkout session for purchasing the provided membership",
)
async def create_checkout_session(
    membership_type_id: Annotated[int, Path(...)],
    service: MembershipServiceDep,
    current_user: CurrentUserDep,  # noqa Auth dependency
) -> str:
    now = datetime.utcnow()
    membership = await service.get_membership_by_kwargs(user_id=current_user.id)
    target_membership_type = await service.get_membership_type_by_kwargs(id=membership_type_id)
    checkout_session_expires_at = int(time.time()) + 30 * 60

    if target_membership_type is None:
        raise CreateCheckoutSessionResponses.MEMBERSHIP_TYPE_NOT_FOUND

    if target_membership_type.type == MembershipTypeEnum.HONORARY:
        raise CreateCheckoutSessionResponses.FORBIDDEN_MEMBERSHIP_TYPE

    if membership is not None and check_membership_type_already_purchased(membership, target_membership_type):
        raise CreateCheckoutSessionResponses.MEMBERSHIP_ALREADY_PURCHASED

    if membership is not None and (check_session_is_locked(membership)):
        return membership.checkout_url

    if membership is None:
        membership = await service.create_membership(
            status=MembershipStatusEnum.INCOMPLETE,
            user_id=current_user.id,
            membership_type_id=target_membership_type.id,
            checkout_session_expires_at=datetime.fromtimestamp(checkout_session_expires_at, tz=timezone.utc),
        )

    metadata = {
        "membership_type_id": str(target_membership_type.id),
        "user_id": str(current_user.id),
        "user_membership_id": str(membership.id),
    }

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[
            {
                "price": target_membership_type.stripe_price_id,
                "quantity": 1,
            }
        ],
        metadata=metadata,
        subscription_data={"metadata": metadata},
        customer_email=current_user.email,
        success_url="http://localhost:3000/payment/membership?success=true&session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://localhost:3000/payment/membership?canceled=true",
        expires_at=checkout_session_expires_at,
    )

    membership_data = {
        "status": MembershipStatusEnum.INCOMPLETE,
        "end_date": now + timedelta(days=365),
        "membership_type_id": target_membership_type.id,
        "checkout_url": session.url,
        "checkout_session_expires_at": datetime.fromtimestamp(checkout_session_expires_at),
    }

    await service.update_user_membership(membership.id, membership_data)

    return session.url


@router.post("/stripe/webhook")
async def fulfill_checkout(
    request: Request,
    service: MembershipServiceDep,
    stripe_signature: str = Header(alias="Stripe-Signature"),
) -> UserMembershipSchema | None:
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
        return await process_checkout_session_completed(data, metadata, service)

    elif event.type == "payment_intent.succeeded":
        pass

    elif event.type == "customer.subscription.updated":
        # Обновление подписки
        return await process_customer_subscription_updated(data, service)

    elif event.type == "invoice.payment_failed":
        return await process_invoice_payment_failed(data, service)

    elif event.type == "customer.subscription.deleted":
        return await process_customer_subscription_deleted(data, service)

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
