from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.params import Path
from fastapi_exception_responses import Responses

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.core.database.base_repository import InvalidOrderAttributeError
from app.domains.memberships.models import ExtendedUserMembershipSchema
from app.domains.memberships.services import MembershipServiceDep
from app.domains.permissions.models import PermissionSchema
from app.domains.permissions.services import PermissionServiceDep
from app.domains.shared.deps import AdminUserDep, UserPermissionsDep
from app.domains.users.filters import UsersFilter
from app.domains.users.models import UpdateUserByAdminSchema, UserSchema
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


class UpdateUserByAdminResponses(Responses):
    CANT_GRANT_ADMIN_ROLE = 403, "Don't have enough permissions to grand admin role"
    CANT_REVOKE_ADMIN_ROLE = 403, "Don't have enough permissions to revoke admin role"
    USER_NOT_FOUND = 404, "User with provided ID not found"


@router.patch(
    "/{user_id}",
    responses=UpdateUserByAdminResponses.responses,
    summary="Update user profile data by admin",
)
async def update_user_by_admin(
    user_id: Annotated[int, Path()],
    user_service: UserServiceDep,
    admin: AdminUserDep,  # noqa Admin auth argument
    permissions: UserPermissionsDep,
    update_data: UpdateUserByAdminSchema,
):
    if update_data.stuff is True and "admin.create" not in permissions:
        raise UpdateUserByAdminResponses.CANT_GRANT_ADMIN_ROLE
    if update_data.stuff is not True and "admin.delete" not in permissions:
        raise UpdateUserByAdminResponses.CANT_REVOKE_ADMIN_ROLE
    if update_data.stuff and admin.id == user_id:
        raise UpdateUserByAdminResponses.CANT_REVOKE_ADMIN_ROLE

    try:
        return await user_service.update_user(user_id, update_data.model_dump())
    except ValueError:
        raise UpdateUserByAdminResponses.USER_NOT_FOUND


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
    CANT_MANAGE_PERMISSIONS = 403, "Don't have enough permissions to manage user permissions"
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
        raise ManagePermissionsResponses.CANT_MANAGE_PERMISSIONS

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
        raise ManagePermissionsResponses.CANT_MANAGE_PERMISSIONS
    try:
        await permissions_service.remove_permissions_from_user(user_id, permissions_ids)
    except ValueError:
        raise ManagePermissionsResponses.USER_NOT_FOUND


@router.put("/{user_id}/permissions")
async def set_user_permissions(
    user_id: Annotated[int, Path()],
    permissions_service: PermissionServiceDep,
    current_user_permissions: UserPermissionsDep,
    admin: AdminUserDep,
    permissions_ids: list[int],
):
    if "permissions.update" not in current_user_permissions:
        raise ManagePermissionsResponses.CANT_MANAGE_PERMISSIONS
    try:
        return await permissions_service.set_users_permissions(user_id, permissions_ids)
    except ValueError:
        raise ManagePermissionsResponses.USER_NOT_FOUND


class ManageUserMembershipResponses(Responses):
    CANT_MANAGE_USER_MEMBERSHIPS = 403, "Don't have enough permissions to manage user memberships"
    MEMBERSHIP_NOT_FOUND = 404, "User membership with with provided user ID not found"


@router.get("/{user_id}/user-membership")
async def get_user_membership(
    user_id: Annotated[int, Path()],
    current_user_permissions: UserPermissionsDep,
    membership_service: MembershipServiceDep,
) -> ExtendedUserMembershipSchema:
    if "user_memberships.read" not in current_user_permissions:
        raise ManageUserMembershipResponses.CANT_MANAGE_USER_MEMBERSHIPS

    user_membership = await membership_service.get_user_membership_by_kwargs(user_id=user_id)

    if user_membership is None:
        raise ManageUserMembershipResponses.MEMBERSHIP_NOT_FOUND

    return user_membership
