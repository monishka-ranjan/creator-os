import uuid
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Session as SessionModel
from app.auth.schemas import LoginRequest, SignupRequest
from app.workspaces.models import User

_hasher = PasswordHasher()

SESSION_LIFETIME = timedelta(days=14)


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        _hasher.verify(hashed, plain)
        return True
    except VerifyMismatchError:
        return False


async def create_user(db: AsyncSession, data: SignupRequest) -> User:
    existing = await db.scalar(select(User).where(User.email == data.email))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

    user = User(
        email=data.email,
        name=data.name,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, data: LoginRequest) -> User:
    user = await db.scalar(select(User).where(User.email == data.email))
    if not user or not verify_password(data.password, user.hashed_password):
        # Deliberately identical error for "no such user" and "wrong password" —
        # see explanation below.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    return user


async def create_session(db: AsyncSession, user_id: uuid.UUID) -> SessionModel:
    session = SessionModel(
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + SESSION_LIFETIME,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: uuid.UUID) -> SessionModel | None:
    session = await db.scalar(select(SessionModel).where(SessionModel.id == session_id))
    if not session or session.expires_at < datetime.now(timezone.utc):
        return None
    return session


async def delete_session(db: AsyncSession, session_id: uuid.UUID) -> None:
    session = await db.scalar(select(SessionModel).where(SessionModel.id == session_id))
    if session:
        await db.delete(session)
        await db.commit()