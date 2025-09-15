from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.core.database.base_repository import InvalidOrderAttributeError
from app.domains.auth.utils import AdminUserDep
from app.domains.users.filters import UsersFilter
from app.domains.users.models import UserSchema
from app.domains.users.services import UserServiceDep

router = APIRouter(tags=["Users admin"], prefix="/users")


class UserListResponses(InvalidRequestParamsResponses):
    pass


@router.get("", responses=UserListResponses.responses)
async def get_users(
    user_service: UserServiceDep,
    params: PaginationParamsDep,
    admin: AdminUserDep,  # noqa Admin auth argument
    ordering: OrderingParamsDep = None,
    filters: Annotated[UsersFilter, Depends()] = None,
) -> PaginatedResponse[UserSchema]:
    try:
        users, users_count = await user_service.get_all_paginated_counted(
            order_by=ordering,
            filters=filters.model_dump(exclude_none=True),
            limit=params["limit"],
            offset=params["offset"],
        )
        data = [UserSchema.from_orm(user) for user in users]
        return PaginatedResponse(
            count=users_count,
            data=data,
            page=params["page"],
            page_size=params["page_size"],
        )
    except InvalidOrderAttributeError:
        raise UserListResponses.INVALID_SORTER_FIELD
