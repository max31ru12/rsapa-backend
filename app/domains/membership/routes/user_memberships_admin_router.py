from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, Path
from fastapi_exception_responses import Responses
from pydantic import TypeAdapter

from app.core.config import settings
from app.core.database.base_repository import InvalidOrderAttributeError
from app.core.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.domains.membership.filters import UserMembershipsFilter
from app.domains.membership.models import FullUserMembershipSchema, UpdateUserMembershipSchema, UserMembershipSchema
from app.domains.membership.services import MembershipServiceDep

stripe.api_key = settings.STRIPE_API_KEY
router = APIRouter(prefix="/user-memberships", tags=["User memberships admin"])


class UserMembershipListResponses(InvalidRequestParamsResponses):
    pass


@router.get(
    "/",
    responses=UserMembershipListResponses.responses,
    summary="Retrieve all paginated filtered and counted user memberships",
)
async def get_all_user_memberships(
    service: MembershipServiceDep,
    params: PaginationParamsDep,
    # admin: AdminUserDep,  # noqa
    ordering: OrderingParamsDep = None,
    filters: Annotated[UserMembershipsFilter, Depends()] = None,
) -> PaginatedResponse[FullUserMembershipSchema]:
    try:
        user_memberships, count = await service.get_joined_membership(
            order_by=ordering,
            filters=filters.model_dump(exclude_none=True),
            limit=params["limit"],
            offset=params["offset"],
        )
        # валидация списка объектов-моделей
        ta = TypeAdapter(list[FullUserMembershipSchema])
        data = ta.validate_python(user_memberships)
        return PaginatedResponse(
            count=count,
            data=data,
            page=params["page"],
            page_size=params["page_size"],
        )
    except InvalidOrderAttributeError:
        raise UserMembershipListResponses.INVALID_SORTER_FIELD


class UpdateUserMembershipResponses(Responses):
    USER_MEMBERSHIP_NOT_FOUND = 404, "User membership not found"


@router.put(
    "/{user_membership_id}", responses=UpdateUserMembershipResponses.responses, summary="Update user membership"
)
async def update_user_membership(
    user_membership_id: Annotated[int, Path(...)],
    update_data: UpdateUserMembershipSchema,
    service: MembershipServiceDep,
    # admin: AdminUserDep,  # noqa
) -> UserMembershipSchema:
    try:
        updated_user_membership = await service.update_user_membership(
            user_membership_id, update_data.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise UpdateUserMembershipResponses.USER_MEMBERSHIP_NOT_FOUND

    return UserMembershipSchema.from_orm(updated_user_membership)
