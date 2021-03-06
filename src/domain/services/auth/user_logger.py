from src.domain.exceptions.invalid_login_exception import InvalidLoginException
from src.domain.models.user import User
from src.domain.repositories.user_repository import UserRepository


class UserLogger:

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def login_user(self, email: str, password: str) -> User:
        user_id = User.email_to_id(email)
        user = self._user_repository.get(user_id)
        if user is None or not user.password_matches(password):
            raise InvalidLoginException()
        return user
