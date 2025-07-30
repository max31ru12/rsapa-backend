from typing import Any

import pytest
from faker import Faker


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
