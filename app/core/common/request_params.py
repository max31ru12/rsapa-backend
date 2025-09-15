from typing import Annotated

from fastapi.params import Depends, Query


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Page size"),
) -> dict:
    """returns limit, and offset  page_size, page_size * (page - 1)"""
    return {
        "limit": page_size,
        "offset": page_size * (page - 1),
        "page": page,
        "page_size": page_size,
    }


PaginationParamsDep = Annotated[tuple[int, int], Depends(get_pagination_params)]
OrderingParamsDep = Annotated[str | None, Query(description="Sorting parameters")]
