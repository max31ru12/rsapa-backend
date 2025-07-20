from app.core.database.base_repository import SQLAlchemyRepository
from app.core.database.unit_of_work import SQLAlchemyUnitOfWork
from app.domains.users.models import User


class UserRepository(SQLAlchemyRepository):
    model = User


class UserUnitOfWork(SQLAlchemyUnitOfWork):
    def __init__(self, session=None):
        super().__init__(session)
        self.user_repository = UserRepository(self._session)


def get_user_unit_of_work() -> UserUnitOfWork:
    return UserUnitOfWork()
