from typing import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.setup_db import session_getter


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
