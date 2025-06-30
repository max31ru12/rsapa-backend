import os
from typing import Annotated

from fastapi import APIRouter, File, Path, UploadFile
from fastapi_exception_responses import Responses

from app.core.config import BASE_DIR
from app.core.database.base_repository import InvalidOrderAttributeError
from app.core.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.domains.auth.utils import CurrentUserDep
from app.domains.users.models import UpdateUserSchema, UserSchema
from app.domains.users.services import UserServiceDep
from app.domains.users.utils import write_file

router = APIRouter(tags=["users"])


@router.get("/current-user")
async def get_current_user(user: CurrentUserDep) -> UserSchema:
    return user


class UserListResponses(InvalidRequestParamsResponses):
    pass


@router.get("/", responses=UserListResponses.responses)
async def get_all_users(
    service: UserServiceDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
) -> PaginatedResponse[UserSchema]:
    try:
        users = await service.get_all(*params, ordering)
        data = [UserSchema.from_orm(user) for user in users]
        return PaginatedResponse(count=len(users), data=data)
    except InvalidOrderAttributeError:
        raise UserListResponses.INVALID_SORTER_FIELD


class GetUserResponses(Responses):
    USER_NOT_FOUND = 404, "User with the provided email was not found"


@router.get("/{user_id}", summary="Get user by id", responses=GetUserResponses.responses)
async def get_user(
    user_id: Annotated[int, Path(...)],
    service: UserServiceDep,
) -> UserSchema:
    user = await service.get_user_by_kwargs(id=user_id)
    if user is None:
        raise GetUserResponses.USER_NOT_FOUND
    return UserSchema.from_orm(user)


class UpdateUserDataResponses(Responses):
    USER_NOT_FOUND = 404, "User with the provided email was not found"
    PERMISSION_DENIED = 403, "You do not have permission to update this user"


@router.put("/{user_id}", summary="Update user data", responses=UpdateUserDataResponses.responses)
async def update_user_data(
    service: UserServiceDep,
    current_user: CurrentUserDep,
    user_id: Annotated[int, Path(...)],
    update_data: UpdateUserSchema | None = None,
) -> UserSchema:
    if not (current_user.id == user_id or current_user.stuff):
        raise UpdateUserDataResponses.PERMISSION_DENIED

    try:
        user = await service.update_user(user_id=user_id, update_data=update_data.model_dump(exclude_none=True))
    except ValueError:
        raise UpdateUserDataResponses.USER_NOT_FOUND
    return UserSchema.from_orm(user)


class SetAvatarResponses(Responses):
    INVALID_CONTENT_TYPE = 422, "Invalid avatar content type"
    USER_NOT_FOUND = 404, "User with provided id not found"


@router.put(
    "/{user_id}/avatar", summary="Upload user avatar image", status_code=201, responses=SetAvatarResponses.responses
)
async def upload_user_avatar(
    service: UserServiceDep,
    user: CurrentUserDep,
    user_id: Annotated[int, Path()],
    file: Annotated[UploadFile, File(...)],
):
    if not file.content_type.startswith("image/"):
        raise SetAvatarResponses.INVALID_CONTENT_TYPE

    relative_filepath = await write_file(file)

    try:
        await service.set_user_avatar(user_id=user_id, avatar_path=relative_filepath)
    except ValueError:
        os.remove(BASE_DIR / relative_filepath)
        raise SetAvatarResponses.USER_NOT_FOUND

    return {"path": relative_filepath}
