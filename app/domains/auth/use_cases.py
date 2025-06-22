from typing import Sequence

from fastapi_exception_responses import Responses
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.models import SubscriptionType
from app.domains.users.models import User


class RegisterResponses(Responses):
    PASSWORDS_DONT_MATCH = 400, "Passwords don't match"
    EMAIL_ALREADY_IN_USE = 409, "Provided email is already in use"


async def register_user(register_form_data, user_service) -> User:
    data = register_form_data.model_dump()

    if (await user_service.get_by_kwargs(email=data["email"])) is not None:
        raise RegisterResponses.EMAIL_ALREADY_IN_USE

    if data["password"] != data["repeat_password"]:
        raise RegisterResponses.PASSWORDS_DONT_MATCH

    del data["repeat_password"]
    return await user_service.create(**data)


async def get_subscriptions(session: AsyncSession) -> Sequence[SubscriptionType]:
    async with session:
        result = await session.execute(select(SubscriptionType))
        return result.scalars().all()
