from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.setup_db import session_getter
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.feedback.models import ContactMessage


class ContactMessageRepository(SQLAlchemyRepository):
    model = ContactMessage


class ContactMessageUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.contact_message_repository = ContactMessageRepository(self._session)


def get_contact_message_unit_of_work(
    session: Annotated[AsyncSession, Depends(session_getter)],
) -> ContactMessageUnitOfWork:
    return ContactMessageUnitOfWork(session)
