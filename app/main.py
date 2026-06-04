from typing import Any

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import GraphQLRouter

from app.db.database import get_session
from app.graphql.loaders import create_energy_tariff_by_ev_id_loader
from app.graphql.schema import schema

app = FastAPI(title="EV Fleet GraphQL API")


async def get_context(session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    return {
        "session": session,
        "energy_tariff_by_ev_id_loader": create_energy_tariff_by_ev_id_loader(session),
    }


app.include_router(GraphQLRouter(schema, context_getter=get_context), prefix="/graphql")
