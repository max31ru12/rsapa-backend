from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, Path
from fastapi_exception_responses import Responses
from pydantic import TypeAdapter

from app.core.common.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.common.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.core.config import settings
from app.core.database.base_repository import InvalidOrderAttributeError
from app.domains.auth.utils import AdminUserDep
from app.domains.memberships.filters import UserMembershipsFilter
from app.domains.memberships.models import (
    ExtendedUserMembershipSchema,
    MembershipTypeSchema,
    UpdateUserMembershipSchema,
    UserMembershipSchema,
)
from app.domains.memberships.services import MembershipServiceDep

stripe.api_key = settings.STRIPE_API_KEY
router = APIRouter(prefix="/memberships", tags=["Admin Membership"])


@router.get(
    "/membership-types",
    summary="Retrieve all memberships type",
)
async def get_all_membership_types(
    service: MembershipServiceDep,
) -> list[MembershipTypeSchema]:
    membership_list, _ = await service.get_all_membership_types()
    data = [MembershipTypeSchema.from_orm(item) for item in membership_list]
    return data


class UserMembershipListResponses(InvalidRequestParamsResponses):
    pass


@router.get(
    "/user-memberships",
    responses=UserMembershipListResponses.responses,
    summary="Retrieve all paginated filtered and counted user memberships",
)
async def get_all_user_memberships(
    service: MembershipServiceDep,
    params: PaginationParamsDep,
    admin: AdminUserDep,  # noqa
    ordering: OrderingParamsDep = None,
    filters: Annotated[UserMembershipsFilter, Depends()] = None,
) -> PaginatedResponse[ExtendedUserMembershipSchema]:
    try:
        user_memberships, count = await service.get_joined_membership(
            order_by=ordering,
            filters=filters.model_dump(exclude_none=True),
            limit=params["limit"],
            offset=params["offset"],
        )
        # валидация списка объектов-моделей
        ta = TypeAdapter(list[ExtendedUserMembershipSchema])
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
    USER_MEMBERSHIP_NOT_FOUND = 404, "User memberships not found"


@router.put(
    "/{user_membership_id}", responses=UpdateUserMembershipResponses.responses, summary="Update user memberships"
)
async def update_user_membership(
    user_membership_id: Annotated[int, Path(...)],
    update_data: UpdateUserMembershipSchema,
    service: MembershipServiceDep,
    admin: AdminUserDep,  # noqa
) -> UserMembershipSchema:
    try:
        updated_user_membership = await service.update_user_membership(
            user_membership_id, update_data.model_dump(exclude_unset=True)
        )
    except ValueError:
        raise UpdateUserMembershipResponses.USER_MEMBERSHIP_NOT_FOUND

    return UserMembershipSchema.from_orm(updated_user_membership)
