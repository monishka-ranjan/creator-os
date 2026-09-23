import uuid

import pytest
from sqlalchemy import select

from app.workspaces.models import Membership, User, Workspace
from tests.conftest import _scoped_session


@pytest.mark.asyncio
async def test_rls_blocks_cross_workspace_membership_read(db_session):
    user_a = User(
        email=f"rls-a-{uuid.uuid4()}@test.local",
        name="RLS Test A",
        hashed_password="x",
    )
    user_b = User(
        email=f"rls-b-{uuid.uuid4()}@test.local",
        name="RLS Test B",
        hashed_password="x",
    )
    workspace_a = Workspace(name="RLS Workspace A")
    workspace_b = Workspace(name="RLS Workspace B")
    db_session.add_all([user_a, user_b, workspace_a, workspace_b])
    await db_session.flush()

    membership_a = Membership(workspace_id=workspace_a.id, user_id=user_a.id, role="owner")
    membership_b = Membership(workspace_id=workspace_b.id, user_id=user_b.id, role="owner")
    db_session.add_all([membership_a, membership_b])
    await db_session.commit()

    try:
        scoped_session, scoped_engine = await _scoped_session(workspace_a.id)
        try:
            result = await scoped_session.execute(
                select(Membership).where(Membership.workspace_id == workspace_b.id)
            )
            leaked_rows = result.scalars().all()

            assert leaked_rows == [], (
                "RLS failed: a session scoped to workspace A could read "
                "workspace B's membership data."
            )

            own_result = await scoped_session.execute(
                select(Membership).where(Membership.workspace_id == workspace_a.id)
            )
            assert len(own_result.scalars().all()) == 1
        finally:
            await scoped_session.close()
            await scoped_engine.dispose()
    finally:
        await db_session.delete(membership_a)
        await db_session.delete(membership_b)
        await db_session.delete(workspace_a)
        await db_session.delete(workspace_b)
        await db_session.delete(user_a)
        await db_session.delete(user_b)
        await db_session.commit()