from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import GraphQLRouter

from app.db.database import Base, engine, get_session
from app.graphql.schema import schema


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="EV Fleet GraphQL API", lifespan=lifespan)


async def get_context(session: AsyncSession = Depends(get_session)) -> dict[str, AsyncSession]:
    return {"session": session}


app.include_router(GraphQLRouter(schema, context_getter=get_context), prefix="/graphql")
