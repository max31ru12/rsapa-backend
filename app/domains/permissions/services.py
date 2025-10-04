from typing import Annotated

from fastapi import Depends
from fastapi_exception_responses import Responses
from sqlalchemy import select

from app.domains.permissions.infrastructure import PermissionsUnitOfWork, get_permissions_unit_of_work
from app.domains.permissions.models import Permission, UserPermission


class RegisterResponses(Responses):
    PASSWORDS_DONT_MATCH = 400, "Passwords don't match"
    EMAIL_ALREADY_IN_USE = 409, "Provided email is already in use"


class AuthService:
    def __init__(self, uow):
        self.uow: PermissionsUnitOfWork = uow

    async def get_all_permissions(self):
        async with self.uow:
            return await self.uow.permission_repository.list()

    async def get_user_permissions(self, user_id: int) -> list[Permission]:
        async with self.uow:
            stmt = (
                select(Permission)
                .join(UserPermission, Permission.id == UserPermission.permission_id)
                .where(UserPermission.user_id == user_id)
            )
            result = await self.uow._session.execute(stmt)
            permissions = result.scalars().all()
            return permissions


def get_permissions_service(
    uow: Annotated[PermissionsUnitOfWork, Depends(get_permissions_unit_of_work)],
) -> AuthService:
    return AuthService(uow)


PermissionServiceDep = Annotated[AuthService, Depends(get_permissions_service)]
