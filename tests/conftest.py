from typing import AsyncIterator

import pytest
from faker import Faker
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import TEST_DB_URL
from app.core.database.setup_db import Base, session_getter
from app.domains.auth.infrastructure import AuthUnitOfWork
from app.domains.auth.models import SubscriptionType
from app.domains.users.infrastructure import UserUnitOfWork

pytest_plugins = ("anyio",)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def test_engine() -> AsyncEngine:
    """Creates test engine"""
    return create_async_engine(TEST_DB_URL, echo=True)


@pytest.fixture(scope="session")
def test_session_factory(test_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Returns test session factory"""
    return async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest.fixture(scope="function")
async def test_session(test_session_factory: async_sessionmaker[AsyncSession]) -> AsyncSession:
    """Yields test session for test database"""
    async with test_session_factory() as session:
        yield session
        # Clear data after single test
        await session.rollback()
        await session.close()


@pytest.fixture(scope="session")
async def setup_database(test_engine: AsyncEngine) -> AsyncIterator[None]:
    """Setups database"""
    from app.domains.news.models import News  # noqa raises Mapper initialization errors withot this import

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    async with test_engine.begin() as conn:
        pass
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def insert_test_data(
    setup_database: AsyncIterator[None],
    test_engine: AsyncEngine,
) -> None:
    async_session = async_sessionmaker(bind=test_engine, expire_on_commit=False)
    async with async_session() as session:
        session.add_all(
            [
                SubscriptionType(
                    name="Trainee Basic",
                    type="TRAINEE",
                    price_usd=10.00,
                    duration=30,
                    description="Monthly basic trainee plan",
                ),
                SubscriptionType(
                    name="Trainee Standard",
                    type="TRAINEE",
                    price_usd=25.00,
                    duration=90,
                    description="Quarterly trainee plan",
                ),
                SubscriptionType(
                    name="Trainee Premium",
                    type="TRAINEE",
                    price_usd=90.00,
                    duration=365,
                    description="Annual trainee plan",
                ),
                SubscriptionType(
                    name="Adjunct Basic",
                    type="ADJUNCT",
                    price_usd=10.00,
                    duration=30,
                    description="Monthly basic adjunct plan",
                ),
                SubscriptionType(
                    name="Adjunct Standard",
                    type="ADJUNCT",
                    price_usd=25.00,
                    duration=90,
                    description="Quarterly adjunct plan",
                ),
                SubscriptionType(
                    name="Adjunct Premium",
                    type="ADJUNCT",
                    price_usd=90.00,
                    duration=365,
                    description="Annual adjunct plan",
                ),
            ]
        )
        await session.commit()


@pytest.fixture(scope="function")
async def client(
    insert_test_data: None,
    test_session: AsyncSession,
) -> AsyncClient:
    from app.main import app

    async def test_session_getter() -> AsyncIterator[AsyncSession]:
        yield test_session

    app.dependency_overrides[session_getter] = test_session_getter

    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def faker() -> Faker:
    fake = Faker()
    yield fake


@pytest.fixture()
def auth_uow(test_session: AsyncSession) -> AuthUnitOfWork:
    return AuthUnitOfWork(test_session)


@pytest.fixture()
def user_uow(test_session: AsyncSession) -> UserUnitOfWork:
    return UserUnitOfWork(test_session)
