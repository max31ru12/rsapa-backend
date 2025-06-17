from typing import Annotated

from fastapi.params import Query, Depends


def get_pagination_params(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(25, ge=1, le=100, description="Page size"),
) -> [int, int]:
    return page_size, page_size * (page - 1)


PaginationParamsDep = Annotated[tuple[int, int], Depends(get_pagination_params)]
OrderingParamsDep = Annotated[str | None, Query(description="Sorting parameters")]