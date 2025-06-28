from typing import Annotated

from fastapi import APIRouter, File, UploadFile
from fastapi_exception_responses import Responses

from app.core.database.base_repository import InvalidOrderAttributeError
from app.core.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.domains.auth.utils import CurrentUserDep
from app.domains.users.models import UpdateUserSchema, UserSchema
from app.domains.users.services import UserServiceDep
from app.utils import write_file

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


@router.put(
    "/{user_id}",
    summary="Update user data",
)
async def update_user_data(
    service: UserServiceDep,
    user: CurrentUserDep,
    update_data: UpdateUserSchema | None = None,
) -> UserSchema:
    user = await service.update_user(user_id=user.id, update_data=update_data.model_dump(exclude_none=True))
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
    file: Annotated[UploadFile, File(...)],
):
    if not file.content_type.startswith("image/"):
        raise SetAvatarResponses.INVALID_CONTENT_TYPE

    relative_filepath = await write_file(file)

    try:
        await service.set_user_avatar(user_id=user.id, avatar_path=relative_filepath)
    except ValueError:
        raise SetAvatarResponses.USER_NOT_FOUND

    return {"path": relative_filepath}
