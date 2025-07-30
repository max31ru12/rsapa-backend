from typing import Any

import pytest
from faker import Faker

from app.domains.users.infrastructure import UserUnitOfWork
from app.domains.users.models import User


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
        "subscription_type_id": 1,
    }


@pytest.fixture(scope="function")
def user_data(register_user_data: dict[str, Any]) -> dict[str, Any]:
    user_data = register_user_data.copy()
    user_data.pop("repeat_password")
    return user_data


@pytest.fixture(scope="function")
def login_data(faker: Faker):
    return {
        "email": faker.email(),
        "password": faker.password(),
    }


@pytest.fixture(scope="function")
async def test_user_with_data(
    user_uow: UserUnitOfWork,
    user_data: dict[str | Any],
) -> dict[str, User | dict]:
    user_creation_data = user_data.copy()
    user_creation_data.pop("subscription_type_id")
    user = await user_uow.user_repository.create(**user_creation_data)

    return {"user": user, "user_data": user_data}
