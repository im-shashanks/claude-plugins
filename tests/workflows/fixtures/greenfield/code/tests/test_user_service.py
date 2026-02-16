import pytest
from src.services.user_service import register_user, DuplicateEmailError, WeakPasswordError, get_repo
from src.utils.password_utils import verify_password


@pytest.fixture(autouse=True)
def _reset_repo():
    yield
    get_repo().reset()


def test_register_user_success():
    user = register_user("alice@example.com", "Str0ngPass")
    assert user.email == "alice@example.com"
    assert user.id is not None
    assert user.created_at is not None


def test_duplicate_email():
    register_user("bob@example.com", "Str0ngPass")
    with pytest.raises(DuplicateEmailError):
        register_user("bob@example.com", "An0therPass")


def test_weak_password_too_short():
    with pytest.raises(WeakPasswordError, match="at least 8 characters"):
        register_user("carol@example.com", "Sh0rt")


def test_weak_password_no_uppercase():
    with pytest.raises(WeakPasswordError, match="uppercase"):
        register_user("dave@example.com", "nouppercase1")


def test_weak_password_no_digit():
    with pytest.raises(WeakPasswordError, match="digit"):
        register_user("eve@example.com", "NoDigitHere")


def test_password_is_hashed():
    user = register_user("frank@example.com", "Str0ngPass")
    assert user.password_hash != "Str0ngPass"
    assert verify_password("Str0ngPass", user.password_hash)
