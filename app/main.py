from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import GraphQLRouter

from app.db.database import get_session
from app.graphql.schema import schema

app = FastAPI(title="EV Fleet GraphQL API")


async def get_context(session: AsyncSession = Depends(get_session)) -> dict[str, AsyncSession]:
    return {"session": session}


app.include_router(GraphQLRouter(schema, context_getter=get_context), prefix="/graphql")
