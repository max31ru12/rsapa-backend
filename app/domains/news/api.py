from fastapi import APIRouter

from app.core.database.base_repository import InvalidOrderAttributeError
from app.core.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.domains.news.models import NewsSchema
from app.domains.news.services import NewsServiceDep

router = APIRouter(prefix="/news", tags=["News"])


@router.post("/")
async def create_news():
    return "News created"


@router.get("/")
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
