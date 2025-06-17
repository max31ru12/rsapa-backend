from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.users.repositories import UserRepository


class UserUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self):
        super().__init__()
        self.user_repository = UserRepository(self._session)
