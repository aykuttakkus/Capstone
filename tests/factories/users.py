from __future__ import annotations

from server.app.core.security import get_password_hash
from server.app.models.sql.models import User


def build_user(email: str = "user@example.com", password: str = "Password123") -> User:
    return User(email=email.lower(), hashed_password=get_password_hash(password))
