from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable
import sys
from pathlib import Path

from typing import Any

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.database import Base, get_session
from app.graphql.loaders import create_energy_tariff_by_ev_id_loader
from app.main import app


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[Any, None]:
    test_engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield test_engine

    await test_engine.dispose()


@pytest_asyncio.fixture
async def session_maker(engine: Any) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session(session_maker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def graphql_context(db_session: AsyncSession) -> dict[str, Any]:
    return {
        "session": db_session,
        "energy_tariff_by_ev_id_loader": create_energy_tariff_by_ev_id_loader(db_session),
    }


@pytest_asyncio.fixture
async def graphql_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _get_test_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = _get_test_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def graphql_request(
    graphql_client: AsyncClient,
) -> Callable[[str, dict[str, Any] | None], Awaitable[dict[str, Any]]]:
    async def _request(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await graphql_client.post(
            "/graphql",
            json={"query": query, "variables": variables or {}},
        )
        assert response.status_code == 200
        return response.json()

    return _request
