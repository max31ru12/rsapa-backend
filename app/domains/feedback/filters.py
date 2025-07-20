from typing import Annotated

from fastapi import Query
from pydantic import BaseModel


class ContactMessagesFilter(BaseModel):
    email__startswith: Annotated[str | None, Query(description="Email filter")] = None
    name__startswith: Annotated[str | None, Query(description="Name filter")] = None
