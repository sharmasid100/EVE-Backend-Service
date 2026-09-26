from __future__ import annotations

from typing import Generator, Optional
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import unauthorized
from app.core.security import decode_access_token
from app.db import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized()
    try:
        user_id = decode_access_token(credentials.credentials)
        uid = UUID(user_id)
    except (ValueError, TypeError):
        raise unauthorized() from None

    user = db.get(User, uid)
    if user is None:
        raise unauthorized()
    return user
