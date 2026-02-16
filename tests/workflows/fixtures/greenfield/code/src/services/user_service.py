import re
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.utils.password_utils import hash_password


class DuplicateEmailError(Exception):
    pass


class WeakPasswordError(Exception):
    pass


_repo = UserRepository()


def get_repo() -> UserRepository:
    return _repo


def register_user(email: str, password: str) -> User:
    """Register a new user after validating email uniqueness and password strength."""
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValueError("Invalid email format")

    if _repo.find_by_email(email) is not None:
        raise DuplicateEmailError(f"Email already registered: {email}")

    _validate_password_strength(password)

    password_hash = hash_password(password)
    user = _repo.create(email=email, password_hash=password_hash)
    return user


def _validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise WeakPasswordError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", password):
        raise WeakPasswordError("Password must contain at least one uppercase letter")
    if not re.search(r"\d", password):
        raise WeakPasswordError("Password must contain at least one digit")
