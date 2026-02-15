"""In-memory user storage for brownfield test project."""

_users = []
_next_id = 1


def get_all_users():
    return list(_users)


def add_user(name, email):
    global _next_id
    user = {"id": _next_id, "name": name, "email": email}
    _users.append(user)
    _next_id += 1
    return user


def get_user_by_id(user_id):
    for user in _users:
        if user["id"] == user_id:
            return user
    return None


def reset():
    global _users, _next_id
    _users = []
    _next_id = 1
