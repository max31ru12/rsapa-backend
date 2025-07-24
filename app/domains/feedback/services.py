from typing import Annotated, Any

from fastapi import Depends

from app.core.utils.mail import send_email
from app.domains.feedback.infrastructure import ContactMessageUnitOfWork, get_contact_message_unit_of_work
from app.domains.feedback.models import CreateContactMessageSchema


class ContactMessageService:
    def __init__(self, uow):
        self.uow: ContactMessageUnitOfWork = uow

    async def create_contact_message(self, data: CreateContactMessageSchema):
        message_data = data.model_dump()
        async with self.uow:
            return await self.uow.contact_message_repository.create(**message_data)

    async def get_all_paginated_counted(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ):
        async with self.uow:
            return await self.uow.contact_message_repository.list(limit, offset, order_by, filters)

    async def answer_contact_message(self, contact_message_id: int, subject, answer_message: str, plain: bool = True):
        async with self.uow:
            contact_message = await self.uow.contact_message_repository.get_first_by_kwargs(id=contact_message_id)

            if contact_message is None:
                raise ValueError("There is no contact message with provided id")

        await send_email(
            to_email=contact_message.email,
            subject=subject,
            body=answer_message,
            plain=plain,
        )


def get_contact_message_service(
    uow: Annotated[ContactMessageUnitOfWork, Depends(get_contact_message_unit_of_work)],
) -> ContactMessageService:
    return ContactMessageService(uow)


ContactMessageServiceDep = Annotated[ContactMessageService, Depends(get_contact_message_service)]
