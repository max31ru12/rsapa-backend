from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.setup_db import session_getter
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.users.infrastructure import UserRepository


class AuthUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.user_repository = UserRepository(self._session)


def get_auth_unit_of_work(session: Annotated[AsyncSession, Depends(session_getter)]) -> AuthUnitOfWork:
    return AuthUnitOfWork(session)
