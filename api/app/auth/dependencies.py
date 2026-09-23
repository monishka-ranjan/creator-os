import uuid

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.router import COOKIE_NAME
from app.db.session import get_db
from app.workspaces.models import User
from sqlalchemy import select
from app.workspaces.models import Membership

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

async def get_membership(
    db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID
) -> Membership | None:
    return await db.scalar(
        select(Membership).where(
            Membership.workspace_id == workspace_id,
            Membership.user_id == user_id,
        )
    )


def require_role(*allowed: str):
    async def checker(
        workspace_id: uuid.UUID,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> Membership:
        membership = await get_membership(db, workspace_id, user.id)
        if not membership or membership.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted for this workspace")
        return membership

    return checker