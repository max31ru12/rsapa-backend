from typing import Annotated

from fastapi import Depends

from app.domains.auth.utils import CurrentUserDep
from app.domains.membership.models import UserMembership
from app.domains.membership.services import MembershipServiceDep


async def current_user_membership(
    current_user: CurrentUserDep, membership_service: MembershipServiceDep
) -> UserMembership | None:
    membership = await membership_service.get_membership_by_kwargs(user_id=current_user.id)
    return membership


CurrentUserMembershipDep = Annotated[UserMembership | None, Depends(current_user_membership)]
