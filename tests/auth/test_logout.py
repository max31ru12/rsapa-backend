import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_logout(
    client: AsyncClient,
    authentication_data: [dict[str, str], dict[str, str], str],
):
    authorization_header, refresh_token_cookie, _ = authentication_data

    response = await client.post("api/auth/logout", headers=authorization_header, cookies=refresh_token_cookie)

    assert response.status_code == 200
    assert "refresh_token" not in response.cookies.keys()


async def test_logout_not_authenticated(
    client: AsyncClient,
) -> None:
    response = await client.post("api/auth/logout")

    assert response.status_code == 401
