from typing import Any

import pytest
from faker import Faker

from app.domains.users.infrastructure import UserUnitOfWork
from app.domains.users.models import User


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
) -> [User, dict]:
    user_creation_data = user_data.copy()
    user = await user_uow.user_repository.create(**user_creation_data)

    return user, user_data
