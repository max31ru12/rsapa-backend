import pytest
from faker import Faker


@pytest.fixture(scope="function")
def register_user_data(faker: Faker):
    password = faker.password()
    return {
        "email": faker.email(),
        "password": password,
        "repeat_password": password,
        "firstname": faker.first_name(),
        "lastname": faker.last_name(),
    }


@pytest.fixture(scope="function")
def user_data(faker: Faker):
    password = faker.password()
    return {
        "email": faker.email(),
        "password": password,
        "firstname": faker.first_name(),
        "lastname": faker.last_name(),
    }


@pytest.fixture(scope="function")
def login_data(faker: Faker):
    return {
        "email": faker.email(),
        "password": faker.password(),
    }
