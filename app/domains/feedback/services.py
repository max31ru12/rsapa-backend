from typing import Annotated, Any

from fastapi import Depends

from app.core.utils.mail import send_email
from app.domains.feedback.infrastructure import FeedbackUnitOfWork, get_feedback_unit_of_work
from app.domains.feedback.models import CreateContactMessageSchema, CreateSponsorshipRequestSchema


class FeedbackService:
    def __init__(self, uow):
        self.uow: FeedbackUnitOfWork = uow

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

            await self.uow.contact_message_repository.update(contact_message_id, {"answered": True})

        await send_email(
            to_email=contact_message.email,
            subject=subject,
            body=answer_message,
            plain=plain,
        )

    async def create_sponsorship_request(self, data: CreateSponsorshipRequestSchema):
        async with self.uow:
            return await self.uow.sponsorship_request_repository.create(**data.model_dump())

    async def get_all_sponsorship_requests(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ):
        async with self.uow:
            return await self.uow.sponsorship_request_repository.list(limit, offset, order_by, filters)


def get_feedback_service(
    uow: Annotated[FeedbackUnitOfWork, Depends(get_feedback_unit_of_work)],
) -> FeedbackService:
    return FeedbackService(uow)


FeedbackServiceDep = Annotated[FeedbackService, Depends(get_feedback_service)]
