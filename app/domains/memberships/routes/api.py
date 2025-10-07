import time
from datetime import datetime
from typing import Annotated

import stripe
from fastapi import APIRouter, Path, Query
from fastapi_exception_responses import Responses
from loguru import logger

from app.core.config import settings
from app.domains.memberships.dependencies import CurrentUserMembershipDep
from app.domains.memberships.models import (
    ExtendedUserMembershipSchema,
    MembershipStatusEnum,
    MembershipTypeEnum,
    MembershipTypeSchema,
    UpdateMembershipTypeSchema,
)
from app.domains.memberships.schemas import UpdateAction
from app.domains.memberships.services import MembershipServiceDep
from app.domains.memberships.utils.checkout_session_utils import (
    check_membership_type_already_purchased,
    check_session_is_locked,
)
from app.domains.shared.deps import AdminUserDep, CurrentUserDep

stripe.api_key = settings.STRIPE_API_KEY
router = APIRouter(prefix="/memberships", tags=["Membership"])


logger.add("logs/checkout_info.log", rotation="30 days", level="INFO")
logger.add("logs/checkout_errors.log", rotation="30 days", level="ERROR", backtrace=True, diagnose=True)


@router.get(
    "/user-memberships/current-user-membership",
    summary="Get Current user memberships",
)
async def get_current_user_membership(membership: CurrentUserMembershipDep) -> ExtendedUserMembershipSchema | None:
    if membership is None:
        return None
    return ExtendedUserMembershipSchema.from_orm(membership)


class CancelMembershipResponses(Responses):
    NO_ACTIVE_MEMBERSHIP = 404, "Active memberships for current user not found"


@router.put(
    "/user-memberships/current-user-membership",
    responses=CancelMembershipResponses.responses,
    summary="Cancel or resume active current user memberships",
)
async def update_membership(
    current_user: CurrentUserDep,
    service: MembershipServiceDep,
    action: Annotated[UpdateAction, Query(...)],
) -> None:
    user_membership = await service.get_user_membership_by_kwargs(user_id=current_user.id)
    if user_membership is None:
        raise CancelMembershipResponses.NO_ACTIVE_MEMBERSHIP

    if action == UpdateAction.CANCEL:
        await service.cancel_membership(current_user.id)
    elif action == UpdateAction.RESUME:
        await service.resume_membership(current_user.id)


@router.get(
    "/membership-types",
    summary="Retrieve all memberships type",
)
async def get_all_membership_types(
    service: MembershipServiceDep,
) -> list[MembershipTypeSchema]:
    membership_list, _ = await service.get_all_membership_types()
    data = [MembershipTypeSchema.from_orm(item) for item in membership_list]
    return data


class MembershipTypesDetailResponses(Responses):
    MEMBERSHIP_TYPE_NOT_FOUND = 404, "Membership with provided id type not found"


@router.get(
    "/membership-types/{membership_type_id}",
    responses=MembershipTypesDetailResponses.responses,
    summary="Get memberships type detail page by id",
)
async def get_membership_detail(
    membership_type_id: Annotated[int, Path(...)],
    service: MembershipServiceDep,
) -> MembershipTypeSchema:
    membership_type = await service.get_membership_type_by_kwargs(id=membership_type_id)
    if membership_type is None:
        raise MembershipTypesDetailResponses.MEMBERSHIP_TYPE_NOT_FOUND
    return MembershipTypeSchema.from_orm(membership_type)


class MembershipNotFoundResponses(Responses):
    MEMBERSHIP_NOT_FOUND = 404, "Membership not found"


@router.put(
    "/membership-types/{membership_type_id}",
    responses=MembershipNotFoundResponses.responses,
    summary="Update memberships type",
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
    FORBIDDEN_MEMBERSHIP_TYPE = 403, "You can't purchase the memberships type with provided id"
    MEMBERSHIP_TYPE_NOT_FOUND = 404, "Membership type with provided id not found"
    MEMBERSHIP_ALREADY_PURCHASED = 409, "Membership with provided id is already purchased"
    PAYMENT_PROVIDER_ERROR = 502, "Payment provider error"


@router.post(
    "/membership-types/{membership_type_id}/checkout-sessions",
    status_code=201,
    responses=CreateCheckoutSessionResponses.responses,
    summary="Creates a checkout session for purchasing the provided memberships",
)
async def create_checkout_session(
    membership_type_id: Annotated[int, Path(...)],
    service: MembershipServiceDep,
    current_user: CurrentUserDep,  # noqa Auth dependency
) -> str:
    membership = await service.get_user_membership_by_kwargs(user_id=current_user.id)
    target_membership_type = await service.get_membership_type_by_kwargs(id=membership_type_id)
    checkout_session_expires_at = int(time.time()) + 30 * 60

    logger.info(
        f"Create checkout session called: user_id={current_user.id} membershipType={target_membership_type.type}"
    )

    if target_membership_type is None:
        raise CreateCheckoutSessionResponses.MEMBERSHIP_TYPE_NOT_FOUND

    if target_membership_type.type == MembershipTypeEnum.HONORARY:
        raise CreateCheckoutSessionResponses.FORBIDDEN_MEMBERSHIP_TYPE

    if membership is not None and check_membership_type_already_purchased(membership, target_membership_type):
        raise CreateCheckoutSessionResponses.MEMBERSHIP_ALREADY_PURCHASED

    if membership is not None and (check_session_is_locked(membership)):
        logger.warning(
            f"Duplicate memberships attempt: user_id={current_user.id}, membership_type_id={membership_type_id}"
        )
        return membership.checkout_url

    if membership is None:
        membership = await service.create_membership(
            status=MembershipStatusEnum.INCOMPLETE,
            user_id=current_user.id,
            membership_type_id=target_membership_type.id,
        )
        membership_creation_log_message = f"""
            Membership created:
            id={membership.id}
            user_id={membership.user_id}
            status={membership.status}
            membershipType={target_membership_type.type}
        """
        logger.info(membership_creation_log_message)

    metadata = {
        "membership_type_id": str(target_membership_type.id),
        "user_id": str(current_user.id),
        "user_membership_id": str(membership.id),
    }

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[
                {
                    "price": target_membership_type.stripe_price_id,
                    "quantity": 1,
                }
            ],
            metadata=metadata,
            subscription_data={"metadata": metadata},  # передается в invoice.paid
            customer_email=current_user.email,
            success_url=f"{settings.FRONTEND_DOMAIN}/payment/membership?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_DOMAIN}/payment/membership?canceled=true",
            expires_at=checkout_session_expires_at,
        )
    except stripe.error.StripeError as e:
        logger.exception(f"Stripe API error: {str(e)}")
        raise CreateCheckoutSessionResponses.PAYMENT_PROVIDER_ERROR
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise e

    membership_data = {
        "status": MembershipStatusEnum.INCOMPLETE,
        "membership_type_id": target_membership_type.id,
        "checkout_url": session.url,
        "checkout_session_expires_at": datetime.fromtimestamp(checkout_session_expires_at),
    }

    await service.update_user_membership(membership.id, membership_data)

    logger.info(
        f"""Membership - add checkout info:
        Stripe session id = {session.id}
        Stripe price id = {target_membership_type.stripe_price_id}\n"""
    )

    return session.url
