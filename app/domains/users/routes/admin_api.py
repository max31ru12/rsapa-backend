from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.database.base_repository import InvalidOrderAttributeError
from app.core.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.domains.users.models import UserSchema
from app.domains.users.services import UserServiceDep

router = APIRouter(tags=["Users admin"], prefix="/admin/users")


class UserListResponses(InvalidRequestParamsResponses):
    pass


class UsersFilter(BaseModel):
    pending: Annotated[bool | None, Query(description="Pending filter")] = None
    stuff: Annotated[bool | None, Query(description="Stuff filter")] = None
    email__icontains: Annotated[str | None, Query(description="Email contains")] = None


@router.get("/")
async def get_users(
    user_service: UserServiceDep,
    params: PaginationParamsDep,
    # admin: AdminUserDep,  # noqa Admin auth argument
    ordering: OrderingParamsDep = None,
    filters: Annotated[UsersFilter, Depends()] = None,
) -> PaginatedResponse[UserSchema]:
    try:
        users = await user_service.get_all(*params, ordering, filters.model_dump(exclude_none=True))
        data = [UserSchema.from_orm(user) for user in users]
        return PaginatedResponse(count=len(users), data=data)
    except InvalidOrderAttributeError:
        raise UserListResponses.INVALID_SORTER_FIELD
