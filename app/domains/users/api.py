from fastapi import APIRouter

from app.core.database.base_repository import InvalidOrderAttributeError
from app.core.request_params import PaginationParamsDep, OrderingParamsDep
from app.core.responses import PaginatedResponse, InvalidRequestParamsResponses
from app.domains.users.schemas import User
from app.domains.users.services import UserServiceDep

router = APIRouter(tags=["users"])


class UserListResponses(InvalidRequestParamsResponses):
    pass


@router.get("/", responses=UserListResponses.get_responses())
async def get_all_users(
        service: UserServiceDep,
        params: PaginationParamsDep,
        ordering: OrderingParamsDep = None,
) -> PaginatedResponse[User]:
    try:
        users = await service.get_all(*params, ordering)
        data = [User.from_orm(user) for user in users]
        return PaginatedResponse(count=len(users), data=data)
    except InvalidOrderAttributeError:
        raise UserListResponses.INVALID_SORTER_FIELD


