from typing import Annotated, Any, Sequence

from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.domains.membership.infrastructure import MembershipUnitOfWork, get_membership_unit_of_work
from app.domains.membership.models import MembershipType, UserMembership


class MembershipService:
    def __init__(self, uow):
        self.uow: MembershipUnitOfWork = uow

    async def get_all_membership_types(self) -> Sequence[MembershipType]:
        async with self.uow:
            return await self.uow.membership_repository.list()

    async def get_membership_type_by_kwargs(self, **kwargs) -> MembershipType:
        async with self.uow:
            return await self.uow.membership_repository.get_first_by_kwargs(**kwargs)

    async def update_membership_type(self, membership_type_id: int, update_data: dict) -> MembershipType:
        async with self.uow:
            return await self.uow.membership_repository.update(membership_type_id, update_data)

    async def get_all_paginated_counted_user_memberships(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ) -> [list[UserMembership], int]:
        async with self.uow:
            return await self.uow.user_membership_repository.list(limit, offset, order_by, filters)

    async def create_membership(self, **kwargs) -> UserMembership:
        async with self.uow:
            return await self.uow.user_membership_repository.create(**kwargs)

    async def get_membership_by_kwargs(self, **kwargs) -> UserMembership:
        async with self.uow:
            return await self.uow.user_membership_repository.get_first_by_kwargs(**kwargs)

    async def update_membership(self, membership_id: int, update_data: dict) -> UserMembership:
        async with self.uow:
            return await self.uow.user_membership_repository.update(membership_id, update_data)

    async def get_joined_membership(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ):
        stmt = (
            select(UserMembership)
            .join(UserMembership.user)
            .join(UserMembership.membership_type)
            .options(selectinload(UserMembership.user), selectinload(UserMembership.membership_type))
        )
        async with self.uow:
            result = await self.uow.user_membership_repository.list(limit, offset, order_by, filters, stmt)
            return result


def get_membership_service(
    uow: Annotated[MembershipUnitOfWork, Depends(get_membership_unit_of_work)],
) -> MembershipService:
    return MembershipService(uow)


MembershipServiceDep = Annotated[MembershipService, Depends(get_membership_service)]
