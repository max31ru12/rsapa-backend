from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from faker import Faker
from jose import jwt

from app.core.config import settings
from app.domains.users.uow import UserUnitOfWork
from tests.auth.utils import decode_jwt

pytestmark = pytest.mark.anyio


async def test_login(
    client,
    user_uow: UserUnitOfWork,
    faker: Faker,
    user_data: dict[str | Any],
) -> None:
    async with user_uow:
        await user_uow.user_repository.create(**user_data)

    response = await client.post(
        "/api/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
            "remember_me": False,
        },
    )
    jwt_decoded = jwt.decode(response.json()["access_token"], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert response.status_code == 200
    assert jwt_decoded["email"] == user_data["email"]


async def test_remember_me(
    client,
    user_uow: UserUnitOfWork,
    faker: Faker,
    user_data: dict[str | Any],
) -> None:
    async with user_uow:
        await user_uow.user_repository.create(**user_data)

    response = await client.post(
        "/api/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
            "remember_me": False,
        },
    )
    access_token = response.json()["access_token"]
    payload = decode_jwt(access_token)

    assert response.status_code == 200
    assert payload["email"] == user_data["email"]


async def test_access_token_expiry(
    client,
    user_uow: UserUnitOfWork,
    user_data: dict[str, Any],
):
    async with user_uow:
        await user_uow.user_repository.create(**user_data)

    response = await client.post(
        "/api/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
            "remember_me": False,
        },
    )

    access_token = response.json()["access_token"]
    payload = decode_jwt(access_token)

    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    expected_delta = timedelta(hours=settings.ACCESS_TOKEN_LIFESPAN_HOURS)

    assert response.status_code == 200
    assert now + expected_delta - timedelta(seconds=5) <= exp <= now + expected_delta + timedelta(seconds=5)


async def test_refresh_token_expiry_with_remember_me(
    client,
    user_uow: UserUnitOfWork,
    user_data: dict[str, Any],
):
    async with user_uow:
        await user_uow.user_repository.create(**user_data)

    response = await client.post(
        "/api/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
            "remember": True,
        },
    )

    refresh_token = response.json()["refresh_token"]
    payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    expected_delta = timedelta(days=settings.REFRESH_TOKEN_REMEMBER_ME_LIFETIME_DAYS)

    assert response.status_code == 200
    assert now + expected_delta - timedelta(seconds=5) <= exp <= now + expected_delta + timedelta(seconds=5)


async def test_refresh_token_expiry(
    client,
    user_uow: UserUnitOfWork,
    user_data: dict[str, Any],
):
    async with user_uow:
        await user_uow.user_repository.create(**user_data)

    response = await client.post(
        "/api/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
            "remember": False,
        },
    )

    refresh_token = response.json()["refresh_token"]
    payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    expected_delta = timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS)

    assert now + expected_delta - timedelta(seconds=5) <= exp <= now + expected_delta + timedelta(seconds=5)


async def test_user_does_not_exist(
    client,
    user_uow: UserUnitOfWork,
    faker: Faker,
    user_data: dict[str | Any],
) -> None:
    response = await client.post(
        "/api/auth/login",
        json={
            "email": user_data["email"],
            "password": user_data["password"],
            "remember_me": True,
        },
    )

    assert response.status_code == 401
