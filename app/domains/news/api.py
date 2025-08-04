from typing import Annotated

from fastapi import APIRouter, Path
from fastapi_exception_responses import Responses

from app.core.database.base_repository import InvalidOrderAttributeError
from app.core.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.domains.auth.utils import AdminUserDep
from app.domains.news.models import CreateNewsSchema, NewsSchema, UpdateNewsSchema
from app.domains.news.services import NewsServiceDep

router = APIRouter(prefix="/news", tags=["News"])


@router.post("/", summary="Create news")
async def create_news(
    body: CreateNewsSchema,
    admin: AdminUserDep,
    service: NewsServiceDep,
):
    news = await service.create_news(**body.model_dump(), author_id=admin.id)
    return news


class UpdateNewsResponses(Responses):
    NEWS_NOT_FOUND = 404, "News with provided id not found"


@router.put(
    "/{news_id}",
    summary="Update news by id",
    responses=UpdateNewsResponses.responses,
)
async def update_news(
    news_id: Annotated[int, Path(...)],
    body: UpdateNewsSchema,
    # admin: AdminUserDep,
    service: NewsServiceDep,
) -> None:
    try:
        await service.update_news(news_id, body.model_dump())
    except ValueError:
        raise UpdateNewsResponses.NEWS_NOT_FOUND


@router.get(
    "/",
    summary="Paginated, ordered, filtered list of news",
    responses=InvalidRequestParamsResponses.responses,
)
async def get_all_news(
    news_service: NewsServiceDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    # filters: Annotated[ContactMessagesFilter, Depends()] = None,
) -> PaginatedResponse[NewsSchema]:
    try:
        news, news_count = await news_service.get_all_paginated_counted(
            order_by=ordering,
            limit=params["limit"],
            offset=params["offset"],
        )
        data = [NewsSchema.from_orm(single_news) for single_news in news]
        return PaginatedResponse(
            count=news_count,
            data=data,
            page=params["page"],
            page_size=params["page_size"],
        )
    except InvalidOrderAttributeError:
        raise InvalidRequestParamsResponses.INVALID_SORTER_FIELD
