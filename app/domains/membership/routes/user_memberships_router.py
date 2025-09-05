import stripe
from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.core.config import settings
from app.domains.auth.utils import CurrentUserDep
from app.domains.membership.dependencies import CurrentUserMembershipDep
from app.domains.membership.models import ExtendedUserMembershipSchema
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
async def get_current_user_membership(membership: CurrentUserMembershipDep) -> ExtendedUserMembershipSchema:
    if membership is None:
        raise CurrentUserMembershipResponses.MEMBERSHIP_NOT_FOUND

    return ExtendedUserMembershipSchema.from_orm(membership)


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
) -> None:
    try:
        await service.cancel_membership(current_user.id)
    except ValueError:
        raise CancelMembershipResponses.NO_ACTIVE_MEMBERSHIP

    # return UserMembershipSchema.from_orm(updated_membership)
