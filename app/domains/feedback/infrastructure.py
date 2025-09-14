from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.setup_db import session_getter
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.feedback.models import ContactMessage, SponsorshipRequest


class ContactMessageRepository(SQLAlchemyRepository[ContactMessage]):
    model = ContactMessage


class SponsorshipRequestRepository(SQLAlchemyRepository[SponsorshipRequest]):
    model = SponsorshipRequest


class FeedbackUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.contact_message_repository = ContactMessageRepository(self._session)
        self.sponsorship_request_repository = SponsorshipRequestRepository(self._session)


def get_feedback_unit_of_work(
    session: Annotated[AsyncSession, Depends(session_getter)],
) -> FeedbackUnitOfWork:
    return FeedbackUnitOfWork(session)
