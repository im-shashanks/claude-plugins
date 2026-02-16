import uuid
from datetime import datetime, timezone
from src.models.user import User


class UserRepository:
    def __init__(self):
        self._store: dict[str, User] = {}
        self._email_index: dict[str, str] = {}

    def create(self, email: str, password_hash: str) -> User:
        if email in self._email_index:
            raise ValueError(f"Duplicate email: {email}")

        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=email,
            password_hash=password_hash,
            created_at=datetime.now(timezone.utc),
        )
        self._store[user_id] = user
        self._email_index[email] = user_id
        return user

    def find_by_email(self, email: str) -> User | None:
        user_id = self._email_index.get(email)
        return self._store.get(user_id) if user_id else None

    def find_by_id(self, user_id: str) -> User | None:
        return self._store.get(user_id)

    def reset(self) -> None:
        self._store.clear()
        self._email_index.clear()
