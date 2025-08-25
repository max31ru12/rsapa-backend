from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

from app.domains.membership.models import MembershipStatusEnum, MembershipTypeEnum


class UserMembershipsFilter(BaseModel):
    approved: Annotated[bool | None, Query(description="Approved user membership filter")] = None
    status: Annotated[MembershipStatusEnum | None, Query(description="Membership stripe status")] = None
    user__email__startswith: Annotated[str | None, Query(description="Email filter")] = None
    membership_type__type__eq: Annotated[MembershipTypeEnum | None, Query(description="Membership type status")] = None
