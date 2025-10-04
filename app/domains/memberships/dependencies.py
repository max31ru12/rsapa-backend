from typing import Annotated

from fastapi import Depends

from app.domains.memberships.models import UserMembership
from app.domains.memberships.services import MembershipServiceDep
from app.domains.shared.deps import CurrentUserDep


async def current_user_membership(
    current_user: CurrentUserDep, membership_service: MembershipServiceDep
) -> UserMembership | None:
    membership = await membership_service.get_user_membership_by_kwargs(user_id=current_user.id)
    return membership


CurrentUserMembershipDep = Annotated[UserMembership | None, Depends(current_user_membership)]
