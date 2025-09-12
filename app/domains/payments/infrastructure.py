from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.setup_db import session_getter
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.payments.models import Payment


class PaymentRepository(SQLAlchemyRepository[Payment]):
    model = Payment


class PaymentUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.payment_repository = PaymentRepository(self._session)


def get_payment_unit_of_work(session: Annotated[AsyncSession, Depends(session_getter)]) -> PaymentUnitOfWork:
    return PaymentUnitOfWork(session)
