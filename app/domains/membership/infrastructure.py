from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.setup_db import session_getter
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.membership.models import MembershipPayment, MembershipType, UserMembership
from app.domains.users.infrastructure import UserRepository


class MembershipRepository(SQLAlchemyRepository):
    model = MembershipType


class UserMembershipRepository(SQLAlchemyRepository):
    model = UserMembership


class MembershipPaymentRepository(SQLAlchemyRepository):
    model = MembershipPayment


class MembershipUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.membership_repository = MembershipRepository(self._session)
        self.user_membership_repository = UserMembershipRepository(self._session)
        self.user_repository = UserRepository(self._session)
        self.membership_payment_repository = MembershipPaymentRepository(self._session)


def get_membership_unit_of_work(session: Annotated[AsyncSession, Depends(session_getter)]) -> MembershipUnitOfWork:
    return MembershipUnitOfWork(session)
