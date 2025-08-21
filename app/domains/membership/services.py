from typing import Annotated, Sequence

from fastapi.params import Depends

from app.domains.membership.infrastructure import MembershipUnitOfWork, get_membership_unit_of_work
from app.domains.membership.models import MembershipPayment, MembershipType


class MembershipService:
    def __init__(self, uow):
        self.uow: MembershipUnitOfWork = uow

    async def get_all_memberships(self) -> Sequence[MembershipType]:
        async with self.uow:
            return await self.uow.membership_repository.list()

    async def get_membership_by_kwargs(self, **kwargs) -> MembershipType:
        async with self.uow:
            return await self.uow.membership_repository.get_first_by_kwargs(**kwargs)

    async def create_payment(self, **kwargs) -> MembershipPayment:
        async with self.uow:
            return await self.uow.membership_payment_repository.create(**kwargs)

    async def update_membership(self, membership_id: int, update_data: dict) -> MembershipPayment:
        async with self.uow:
            return await self.uow.membership_repository.update(membership_id, update_data)


def get_membership_service(
    uow: Annotated[MembershipUnitOfWork, Depends(get_membership_unit_of_work)],
) -> MembershipService:
    return MembershipService(uow)


MembershipServiceDep = Annotated[MembershipService, Depends(get_membership_service)]
