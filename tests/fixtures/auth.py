from typing import Any

import pytest
from faker import Faker

from app.domains.auth.utils import create_access_token, create_refresh_token
from app.domains.users.infrastructure import UserUnitOfWork
from app.domains.users.models import User

pytestmark = pytest.mark.anyio


@pytest.fixture(scope="function")
def register_user_data(faker: Faker) -> dict[str, Any]:
    password = faker.password()
    return {
        "email": faker.email(),
        "password": password,
        "repeat_password": password,
        "firstname": faker.first_name(),
        "lastname": faker.last_name(),
        "institution": faker.pystr(min_chars=2),
        "role": faker.pystr(min_chars=2),
    }


@pytest.fixture(scope="function")
def user_data(register_user_data: dict[str, Any]) -> dict[str, Any]:
    user_data = register_user_data.copy()
    user_data.pop("repeat_password")
    return user_data


@pytest.fixture(scope="function")
async def test_user(
    user_uow: UserUnitOfWork,
    user_data: dict[str | Any],
) -> User:
    user_creation_data = user_data.copy()
    user = await user_uow.user_repository.create(**user_creation_data)

    return user


@pytest.fixture(scope="function")
def authentication_data(
    test_user: User,
) -> [dict[str, str], dict[str, str], str]:
    user = test_user
    access_token = create_access_token({"email": user.email})
    refresh_token = create_refresh_token({"email": user.email}, remember_me=False)

    return {"Authorization": f"Bearer {access_token}"}, {"refresh_token": refresh_token}, user.email


@pytest.fixture
def authentication_data_factory(user_uow: UserUnitOfWork, faker: Faker):
    async def _factory():
        from app.domains.auth.utils import create_access_token, create_refresh_token

        user_data = {
            "email": faker.email(),
            "password": faker.password(),
            "firstname": faker.first_name(),
            "lastname": faker.last_name(),
            "institution": faker.company(),
            "role": faker.job(),
        }

        async with user_uow:
            user = await user_uow.user_repository.create(**user_data)

        access_token = create_access_token({"email": user.email})
        refresh_token = create_refresh_token({"email": user.email}, remember_me=False)

        return {"Authorization": f"Bearer {access_token}"}, {"refresh_token": refresh_token}, user.email

    return _factory
