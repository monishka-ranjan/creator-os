import uuid

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings


@pytest_asyncio.fixture
async def db_session():
    """A raw session against the real dev database, no workspace scoping applied."""
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    await engine.dispose()


async def _scoped_session(workspace_id: uuid.UUID):
    engine = create_async_engine(settings.app_database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    session = Session()
    await session.execute(text(f"SET app.current_workspace_id = '{workspace_id}'"))
    return session, engine