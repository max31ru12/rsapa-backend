from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class NewsFilter(BaseModel):
    # email__startswith: Annotated[str | None, Query(description="Email filter")] = None
    # name__startswith: Annotated[str | None, Query(description="Name filter")] = None
    is_published: Annotated[bool, Query(description="Published filter")] = True
