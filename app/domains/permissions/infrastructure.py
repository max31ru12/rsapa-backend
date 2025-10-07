from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.setup_db import session_getter
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.permissions.models import Permission, UserPermission
from app.domains.users.infrastructure import UserRepository


class PermissionRepository(SQLAlchemyRepository):
    model = Permission


class UserPermissionRepository(SQLAlchemyRepository):
    model = UserPermission


class PermissionsUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.user_repository = UserRepository(self._session)
        self.permission_repository = PermissionRepository(self._session)
        self.user_permission_repository = UserPermissionRepository(self._session)


def get_permissions_unit_of_work(session: Annotated[AsyncSession, Depends(session_getter)]) -> PermissionsUnitOfWork:
    return PermissionsUnitOfWork(session)
