import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.workspaces import service
from app.workspaces.models import User
from app.workspaces.schemas import (
    InviteRequest,
    MembershipOut,
    WorkspaceCreate,
    WorkspaceOut,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceOut, status_code=201)
async def create_workspace(
    data: WorkspaceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.create_workspace_with_owner(db, data, user.id)


@router.get("/{workspace_id}/members", response_model=list[MembershipOut])
async def list_members(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(require_role("owner", "manager", "editor", "viewer")),
):
    return await service.list_memberships(db, workspace_id)


@router.post("/{workspace_id}/invite", response_model=MembershipOut, status_code=201)
async def invite_member(
    workspace_id: uuid.UUID,
    data: InviteRequest,
    db: AsyncSession = Depends(get_db),
    _membership=Depends(require_role("owner")),
):
    return await service.invite_member(db, workspace_id, data.email, data.role)