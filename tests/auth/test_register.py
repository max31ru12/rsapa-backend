from typing import Any

import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.users.uow import UserUnitOfWork

pytestmark = pytest.mark.anyio


async def test_register(
    client: AsyncClient,
    register_user_data: dict[str | Any],
    user_uow: UserUnitOfWork,
) -> None:
    response = await client.post("api/auth/register", json=register_user_data)
    async with user_uow:
        user = await user_uow.user_repository.get_first_by_kwargs(email=register_user_data["email"])

        assert response.status_code == 201
    assert user is not None


async def test_email_already_in_use(
    client: AsyncClient,
    register_user_data: dict[str | Any],
    user_uow: UserUnitOfWork,
) -> None:
    user_data = register_user_data.copy()
    del user_data["repeat_password"]
    async with user_uow:
        await user_uow.user_repository.create(**user_data)

    response = await client.post("api/auth/register", json=register_user_data)
    assert response.status_code == 409


async def test_passwords_dont_match(client: AsyncClient, register_user_data: dict[str | Any], faker: Faker) -> None:
    register_user_data["repeat_password"] = faker.password()
    response = await client.post("api/auth/register", json=register_user_data)
    assert response.status_code == 400
