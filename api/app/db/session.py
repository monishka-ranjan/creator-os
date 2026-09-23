import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from app.core.config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db():
    async with SessionLocal() as session:
        yield session


async def get_workspace_scoped_db(workspace_id: uuid.UUID):
    async with SessionLocal() as session:
        # Postgres SET does not support bind parameters over the wire protocol,
        # so we interpolate directly — safe here because workspace_id is a
        # uuid.UUID, not a raw string, and therefore cannot contain SQL.
        await session.execute(text(f"SET app.current_workspace_id = '{workspace_id}'"))
        yield session