import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.workspaces.models import Membership, User, Workspace
from app.workspaces.schemas import WorkspaceCreate


async def create_workspace_with_owner(
    db: AsyncSession, data: WorkspaceCreate, owner_id: uuid.UUID
) -> Workspace:
    workspace = Workspace(name=data.name)
    db.add(workspace)
    await db.flush()  # assigns workspace.id without committing yet

    membership = Membership(workspace_id=workspace.id, user_id=owner_id, role="owner")
    db.add(membership)

    await db.commit()
    await db.refresh(workspace)
    return workspace


async def list_memberships(db: AsyncSession, workspace_id: uuid.UUID) -> list[Membership]:
    result = await db.execute(
        select(Membership).where(Membership.workspace_id == workspace_id)
    )
    return list(result.scalars().all())


async def invite_member(
    db: AsyncSession, workspace_id: uuid.UUID, email: str, role: str
) -> Membership:
    user = await db.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No CreatorOS account exists for that email yet",
        )

    existing = await db.scalar(
        select(Membership).where(
            Membership.workspace_id == workspace_id, Membership.user_id == user.id
        )
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "This person is already a member")

    membership = Membership(workspace_id=workspace_id, user_id=user.id, role=role)
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership