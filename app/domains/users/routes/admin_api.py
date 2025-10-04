from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.params import Path

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.core.database.base_repository import InvalidOrderAttributeError
from app.domains.auth.services import AuthServiceDep
from app.domains.permissions.models import PermissionSchema
from app.domains.shared.deps import AdminUserDep, UserPermissionsDep
from app.domains.users.filters import UsersFilter
from app.domains.users.models import UserSchema
from app.domains.users.services import UserServiceDep

router = APIRouter(tags=["Admin Users"], prefix="/users")


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


@router.get("/{user_id}/permissions")
async def get_user_permissions(
    user_id: Annotated[int, Path()],
    auth_service: AuthServiceDep,
    current_user_permissions: UserPermissionsDep,
    admin: AdminUserDep,
) -> list[PermissionSchema]:
    permissions = await auth_service.get_user_permissions(user_id)

    return [PermissionSchema.from_orm(permission) for permission in permissions]


@router.post("/{user_id}/permissions")
async def assign_permissions(
    user_id: Annotated[int, Path()],
    auth_service: AuthServiceDep,
    current_user_permissions: UserPermissionsDep,
    admin: AdminUserDep,
    permissions_ids: list[int],
):
    return permissions_ids
