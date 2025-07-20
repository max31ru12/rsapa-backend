from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.feedback.models import ContactMessage


class ContactMessageRepository(SQLAlchemyRepository):
    model = ContactMessage


class ContactMessageUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.contact_message_repository = ContactMessageRepository(self._session)


def get_contact_message_unit_of_work() -> ContactMessageUnitOfWork:
    return ContactMessageUnitOfWork()
