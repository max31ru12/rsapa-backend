import pytest
from faker import Faker
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


async def test_register(
        client: AsyncClient,
        faker: Faker,
):
    password = faker.password()
    user_data = {
      "email": faker.email(),
      "password": password,
      "repeat_password": password,
      "firstname": faker.first_name(),
      "lastname": faker.last_name(),
}

    response = await client.post("api/auth/register", json=user_data)
    assert response.status_code == 201
