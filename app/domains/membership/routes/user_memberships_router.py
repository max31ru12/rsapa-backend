import stripe
from fastapi import APIRouter
from fastapi_exception_responses import Responses

from app.core.config import settings
from app.domains.auth.utils import CurrentUserDep
from app.domains.membership.dependencies import CurrentUserMembershipDep
from app.domains.membership.models import ExtendedUserMembershipSchema
from app.domains.membership.schemas import UpdateAction
from app.domains.membership.services import MembershipServiceDep

stripe.api_key = settings.STRIPE_API_KEY
router = APIRouter(prefix="/user-memberships", tags=["User memberships"])


@router.get(
    "/current-user-membership",
    summary="Get Current user membership",
)
async def get_current_user_membership(membership: CurrentUserMembershipDep) -> ExtendedUserMembershipSchema | None:
    if membership is None:
        return None
    return ExtendedUserMembershipSchema.from_orm(membership)


class CancelMembershipResponses(Responses):
    NO_ACTIVE_MEMBERSHIP = 404, "Active membership for current user not found"


@router.put(
    "/current-user-membership",
    responses=CancelMembershipResponses.responses,
    summary="Cancel active current user membership",
)
async def update_membership(
    current_user: CurrentUserDep,
    service: MembershipServiceDep,
    action: UpdateAction,
) -> None:
    if action == UpdateAction.CANCEL:
        try:
            await service.cancel_membership(current_user.id)
        except ValueError:
            raise CancelMembershipResponses.NO_ACTIVE_MEMBERSHIP

    elif action == UpdateAction.RESUME:
        try:
            await service.resume_membership(current_user.id)
        except ValueError:
            raise CancelMembershipResponses.NO_ACTIVE_MEMBERSHIP
