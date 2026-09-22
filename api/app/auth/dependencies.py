import uuid

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.router import COOKIE_NAME
from app.db.session import get_db
from app.workspaces.models import User


async def get_current_user(
    creatoros_session: uuid.UUID | None = Cookie(default=None, alias=COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creatoros_session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    session = await service.get_session(db, creatoros_session)
    if session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired or invalid")

    user = await db.get(User, session.user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user