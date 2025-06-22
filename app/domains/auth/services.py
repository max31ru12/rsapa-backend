from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends
from fastapi_exception_responses import Responses

from app.domains.auth.database import AuthUnitOfWork, get_auth_unit_of_work
from app.domains.auth.schemas import RegisterFormData


class RegisterResponses(Responses):
    PASSWORDS_DONT_MATCH = 400, "Passwords don't match"
    EMAIL_ALREADY_IN_USE = 409, "Provided email is already in use"


class AuthService:
    def __init__(self, uow):
        self.uow: AuthUnitOfWork = uow

    async def register_user(self, register_form_data: RegisterFormData):
        """Creates or extends subscription"""

        user_data = register_form_data.model_dump()
        subscription_type_id = user_data.pop("subscription_type_id")

        if (await self.uow.user_repository.get_first_by_kwargs(email=user_data["email"])) is not None:
            raise RegisterResponses.EMAIL_ALREADY_IN_USE

        if user_data["password"] != user_data.pop("repeat_password"):
            raise RegisterResponses.PASSWORDS_DONT_MATCH

        async with self.uow:
            subscription_type = await self.uow.subscription_type_repository.get_first_by_kwargs(id=subscription_type_id)
            user = await self.uow.user_repository.create(**user_data)

            await self.uow._session.flush()

            await self.uow.user_subscription_repository.create(
                user_id=user.id,
                end_date=datetime.now(tz=timezone.utc) + timedelta(days=subscription_type.duration),
                subscription_type_id=subscription_type.id,
            )
            return user


def get_auth_service(uow: Annotated[AuthUnitOfWork, Depends(get_auth_unit_of_work)]) -> AuthService:
    return AuthService(uow)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
