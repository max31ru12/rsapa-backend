from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.setup_db import session_getter
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.membership.models import Membership, UserSubscription
from app.domains.users.infrastructure import UserRepository


class MembershipRepository(SQLAlchemyRepository):
    model = Membership


class UserSubscriptionRepository(SQLAlchemyRepository):
    model = UserSubscription


class MembershipUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.subscription_type_repository = MembershipRepository(self._session)
        self.user_subscription_repository = UserSubscriptionRepository(self._session)
        self.user_repository = UserRepository(self._session)


def get_membership_unit_of_work(session: Annotated[AsyncSession, Depends(session_getter)]) -> MembershipUnitOfWork:
    return MembershipUnitOfWork(session)
