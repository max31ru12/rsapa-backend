from typing import Annotated, Any

from fastapi import Depends

from app.domains.news.infrastructure import NewsUnitOfWork, get_news_unit_of_work
from app.domains.news.models import News


class NewsService:
    def __init__(self, uow):
        self.uow: NewsUnitOfWork = uow

    async def get_all_paginated_counted(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ):
        async with self.uow:
            return await self.uow.news_repository.list(limit, offset, order_by, filters)

    async def create_news(self, **kwargs) -> News:
        async with self.uow:
            return await self.uow.news_repository.create(**kwargs)

    async def update_news(self, news_id: int, update_data: dict[str | Any]) -> None:
        async with self.uow:
            news = await self.uow.news_repository.get_first_by_kwargs(id=news_id)
            if news is None:
                raise ValueError("There is no such user with provided id")
            await self.uow.news_repository.update(news_id, update_data)


def get_news_service(
    uow: Annotated[NewsUnitOfWork, Depends(get_news_unit_of_work)],
) -> NewsService:
    return NewsService(uow)


NewsServiceDep = Annotated[NewsService, Depends(get_news_service)]
