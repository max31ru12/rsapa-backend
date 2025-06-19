from typing import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from faker import Faker

from app.core.database.setup_db import Base
from app.core.config import TEST_DB_URL
from app.domains.users.uow import UserUnitOfWork
from app.main import app

pytest_plugins = ("anyio",)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def test_engine() -> AsyncEngine:
    return create_async_engine(TEST_DB_URL, echo=True)


@pytest.fixture(scope="session")
def test_session_factory(test_engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest.fixture(scope="function")
async def test_session(test_session_factory) -> AsyncSession:
    async with test_session_factory() as session:
        yield session
        # Clear data after single test
        await session.rollback()


@pytest.fixture()
def override_user_uow(test_session: AsyncSession):
    return UserUnitOfWork(test_session)


@pytest.fixture(autouse=True)
def override_dependencies(override_user_uow):
    from app.domains.users.uow import get_user_unit_of_work
    app.dependency_overrides[get_user_unit_of_work] = lambda: override_user_uow
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function", autouse=True)
async def setup_database(test_engine) -> AsyncIterator[None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture(scope="function")
async def client() -> AsyncClient:
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="session")
def faker():
    fake = Faker()
    yield fake
