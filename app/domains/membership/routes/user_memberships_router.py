import stripe
from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.core.config import settings
from app.domains.auth.utils import CurrentUserDep
from app.domains.membership.dependencies import CurrentUserMembershipDep
from app.domains.membership.models import MembershipStatusEnum, UpdatedMembershipSchema, UserMembershipSchema
from app.domains.membership.services import MembershipServiceDep

stripe.api_key = settings.STRIPE_API_KEY
router = APIRouter(prefix="/user-memberships", tags=["User memberships"])


class CurrentUserMembershipResponses(Responses):
    MEMBERSHIP_NOT_FOUND = 404, "Membership for current user not found"


@router.get(
    "/current-user-membership",
    responses=CurrentUserMembershipResponses.responses,
    summary="Get Current user membership",
)
async def get_current_user_membership(membership: CurrentUserMembershipDep) -> UserMembershipSchema:
    if membership is None:
        raise CurrentUserMembershipResponses.MEMBERSHIP_NOT_FOUND

    return UserMembershipSchema.from_orm(membership)


class CancelMembershipResponses(Responses):
    NO_ACTIVE_MEMBERSHIP = 404, "Active membership for current user not found"


@router.put(
    "/current-user-membership",
    responses=CancelMembershipResponses.responses,
    summary="Cancel active current user membership",
)
async def cancel_membership(
    current_user: CurrentUserDep,
    service: MembershipServiceDep,
) -> UpdatedMembershipSchema:
    membership = await service.get_membership_by_kwargs(user_id=current_user.id, status=MembershipStatusEnum.ACTIVE)

    if membership is None:
        raise CancelMembershipResponses.NO_ACTIVE_MEMBERSHIP

    updated_membership = await service.update_user_membership(membership.id, {"status": MembershipStatusEnum.CANCELED})
    stripe.Subscription.modify(membership.stripe_subscription_id, cancel_at_period_end=True)

    return UpdatedMembershipSchema.from_orm(updated_membership)
