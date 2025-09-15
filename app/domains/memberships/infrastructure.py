from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.setup_db import session_getter
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.memberships.models import MembershipType, UserMembership
from app.domains.payments.infrastructure import PaymentRepository
from app.domains.users.infrastructure import UserRepository


class MembershipRepository(SQLAlchemyRepository[MembershipType]):
    model = MembershipType


class UserMembershipRepository(SQLAlchemyRepository[UserMembership]):
    model = UserMembership


class MembershipUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.membership_repository = MembershipRepository(self._session)
        self.user_membership_repository = UserMembershipRepository(self._session)
        self.user_repository = UserRepository(self._session)
        self.payment_repository = PaymentRepository(self._session)


def get_membership_unit_of_work(session: Annotated[AsyncSession, Depends(session_getter)]) -> MembershipUnitOfWork:
    return MembershipUnitOfWork(session)
