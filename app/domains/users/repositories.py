from app.core.database.base_repository import SQLAlchemyRepository
from app.domains.users.models import User


class UserRepository(SQLAlchemyRepository):
    model = User
