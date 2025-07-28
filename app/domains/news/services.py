from typing import Annotated, Any

from fastapi import Depends

from app.domains.news.infrastructure import NewsUnitOfWork, get_news_unit_of_work


class NewsService:
    def __init__(self, uow):
        self.uow: NewsUnitOfWork = uow

    async def get_all_paginated_counted(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ):
        async with self.uow:
            return await self.uow.news_repository.list(limit, offset, order_by, filters)


def get_news_service(
    uow: Annotated[NewsUnitOfWork, Depends(get_news_unit_of_work)],
) -> NewsService:
    return NewsService(uow)


NewsServiceDep = Annotated[NewsService, Depends(get_news_service)]
