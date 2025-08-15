from typing import Annotated, Sequence

from fastapi.params import Depends

from app.domains.membership.infrastructure import MembershipUnitOfWork, get_membership_unit_of_work
from app.domains.membership.models import Membership


class MembershipService:
    def __init__(self, uow):
        self.uow: MembershipUnitOfWork = uow

    async def get_all_memberships(self) -> Sequence[Membership]:
        async with self.uow:
            return await self.uow.subscription_type_repository.list()

    async def get_membership_by_kwargs(self, **kwargs) -> Membership:
        async with self.uow:
            return await self.uow.subscription_type_repository.get_first_by_kwargs(**kwargs)


def get_membership_service(
    uow: Annotated[MembershipUnitOfWork, Depends(get_membership_unit_of_work)],
) -> MembershipService:
    return MembershipService(uow)


MembershipServiceDep = Annotated[MembershipService, Depends(get_membership_service)]
