from typing import Annotated

from fastapi import Depends

from app.domains.users.models import User
from app.domains.users.uow import UserUnitOfWork


class UserService:

    def __init__(self):
        self.uow = UserUnitOfWork()

    async def get_all(self, limit: int = None, offset: int = None, order_by: str = None) -> list[User]:
        async with self.uow:
            return await self.uow.user_repository.list(limit, offset, order_by)

    async def create(self, **kwargs):
        async with self.uow:
            return await self.uow.user_repository.create(**kwargs)

    async def get_by_kwargs(self, **kwargs) -> User:
        async with self.uow:
            return await self.uow.user_repository.get_first_by_kwargs(**kwargs)


def get_user_service():
    return UserService()


UserServiceDep = Annotated[UserService, Depends(get_user_service)]