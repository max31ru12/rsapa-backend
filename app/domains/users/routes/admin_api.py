from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.params import Path
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.core.database.base_repository import InvalidOrderAttributeError
from app.domains.permissions.models import PermissionSchema
from app.domains.permissions.services import PermissionServiceDep
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
    permissions_service: PermissionServiceDep,
    current_user_permissions: UserPermissionsDep,
    admin: AdminUserDep,
) -> list[PermissionSchema]:
    permissions = await permissions_service.get_user_permissions(user_id)

    return [PermissionSchema.from_orm(permission) for permission in permissions]


class ManagePermissionsResponses(Responses):
    CANT_ASSIGN_PERMISSIONS = 403, "Don't have enough permissions to assign permissions"
    USER_NOT_FOUND = 404, "User with provided ID not found"


@router.post(
    "/{user_id}/permissions", responses=ManagePermissionsResponses.responses, summary="Assign permissions to user"
)
async def assign_permissions(
    user_id: Annotated[int, Path()],
    permissions_service: PermissionServiceDep,
    current_user_permissions: UserPermissionsDep,
    admin: AdminUserDep,
    permissions_ids: list[int],
):
    if "permissions.create" not in current_user_permissions:
        raise ManagePermissionsResponses.CANT_ASSIGN_PERMISSIONS

    try:
        await permissions_service.assign_permissions_to_user(user_id, permissions_ids)
    except ValueError:
        raise ManagePermissionsResponses.USER_NOT_FOUND


@router.delete("/{user_id}/permissions")
async def remove_user_permissions(
    user_id: Annotated[int, Path()],
    permissions_service: PermissionServiceDep,
    current_user_permissions: UserPermissionsDep,
    admin: AdminUserDep,
    permissions_ids: list[int],
):
    if "permissions.delete" not in current_user_permissions:
        raise ManagePermissionsResponses.CANT_ASSIGN_PERMISSIONS
    try:
        await permissions_service.remove_permissions_from_user(user_id, permissions_ids)
    except ValueError:
        raise ManagePermissionsResponses.USER_NOT_FOUND
