from sqlalchemy.orm import Session

from app.core.exceptions import conflict, unauthorized
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas import TokenOut, UserCreate, UserLogin, UserOut


def signup(db: Session, payload: UserCreate) -> UserOut:
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise conflict("Email already registered")

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


def login(db: Session, payload: UserLogin) -> TokenOut:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise unauthorized("Invalid email or password")
    token = create_access_token(user.id)
    return TokenOut(access_token=token)
