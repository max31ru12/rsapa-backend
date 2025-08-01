from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.setup_db import session_getter
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.news.models import News


class NewsRepository(SQLAlchemyRepository):
    model = News


class NewsUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.news_repository = NewsRepository(self._session)


def get_news_unit_of_work(session: Annotated[AsyncSession, Depends(session_getter)]) -> NewsUnitOfWork:
    return NewsUnitOfWork(session)
