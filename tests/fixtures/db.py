from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from server.app.core.database import Base
from server.app.models.sql.models import User
from tests.factories.users import build_user


async def _create_all(engine) -> None:  # type: ignore[no-untyped-def]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture
def db_engine(db_path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    asyncio.run(_create_all(engine))
    yield engine
    asyncio.run(engine.dispose())


@pytest.fixture
def db_session_factory(db_engine):
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest.fixture
async def db_session(db_session_factory):
    async with db_session_factory() as session:
        yield session


@pytest.fixture
def authenticated_user(db_session_factory) -> User:
    async def create_user() -> User:
        async with db_session_factory() as session:
            user = build_user(email="auth@example.com")
            session.add(user)
            await session.commit()
            result = await session.execute(select(User).where(User.email == "auth@example.com"))
            return result.scalar_one()

    return asyncio.run(create_user())
