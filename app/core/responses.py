from typing import TypeVar, Generic

from fastapi_exception_responses import Responses
from pydantic import BaseModel

DataModel = TypeVar("DataModel", bound=BaseModel)


class PaginatedResponse(BaseModel, Generic[DataModel]):
    count: int
    data: list[DataModel]


class InvalidRequestParamsResponses(Responses):
    INVALID_FILTER_FIELD = 400, "Invalid filter field"
    INVALID_SORTER_FIELD = 400, "Invalid sorter field"
