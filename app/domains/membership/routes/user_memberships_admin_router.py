from typing import Annotated

import stripe
from fastapi import APIRouter, Depends
from pydantic import TypeAdapter

from app.core.config import settings
from app.core.database.base_repository import InvalidOrderAttributeError
from app.core.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.domains.membership.filters import UserMembershipsFilter
from app.domains.membership.models import FullUserMembershipSchema
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
    # admin: AdminUserDep,  # noqa Admin auth argument
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


@router.delete("/")
async def get_joined_user_memberships(
    service: MembershipServiceDep,
):
    data = await service.get_joined_membership()
    return data
