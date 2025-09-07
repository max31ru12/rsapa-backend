from typing import Annotated

from fastapi import Depends

from app.domains.payments.infrastructure import PaymentUnitOfWork, get_payment_unit_of_work


class PaymentService:
    def __init__(self, uow):
        self.uow: PaymentUnitOfWork = uow


def get_payment_service(
    uow: Annotated[PaymentUnitOfWork, Depends(get_payment_unit_of_work)],
) -> PaymentService:
    return PaymentService(uow)


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
