from pymodelio import pymodelio_model, Attribute
from pymodelio.validators import StringValidator, EmailValidator

from src.common.id_generator import IdGenerator
from src.common.hashing import hash_password


@pymodelio_model
class User:
    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 32
    PASSWORD_VALIDATION_PATTERN = '^(?=.*[0-9]+.*)(?=.*[a-z]+.*)(?=.*[A-Z]+.*)[\\S]{8,32}$'
    _username: Attribute[str](validator=StringValidator(min_len=MIN_USERNAME_LENGTH, max_len=MAX_USERNAME_LENGTH))
    _email: Attribute[str](validator=EmailValidator())
    _password: Attribute[str](
        validator=StringValidator(nullable=True, regex=PASSWORD_VALIDATION_PATTERN, message='is not valid')
    )
    _hashed_password: Attribute[str](validator=StringValidator(message='is not valid'))

    def __before_validate__(self) -> None:
        # Force the email to be lowercase
        if self._email:
            self._email = self._email.lower()
        if self._password is not None:
            self._hashed_password = hash_password(self._password)

    @property
    def username(self) -> str:
        return self._username

    @property
    def email(self) -> str:
        return self._email

    @property
    def user_id(self) -> str:
        return User.email_to_id(self.email)

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @staticmethod
    def email_to_id(email: str) -> str:
        return IdGenerator.generate_id(email)

    def password_matches(self, non_hashed_password) -> bool:
        return self.hashed_password == hash_password(non_hashed_password)
