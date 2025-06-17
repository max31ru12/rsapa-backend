from typing import Annotated

from fastapi import Depends

from app.domains.users.uow import UserUnitOfWork


class UserService:

    def __init__(self):
        self.uow = UserUnitOfWork()

    async def get_all_users(self, limit: int = None, offset: int = None, order_by: str = None):
        return await self.uow.user_repository.list(limit, offset, order_by)


def get_user_service():
    return UserService()


UserServiceDep = Annotated[UserService, Depends(get_user_service)]