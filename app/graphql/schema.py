from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID

import strawberry

from app.events.event_hub import subscribe_ev_status
from app.resolvers.ev_resolvers import create_ev, delete_ev, get_ev, list_evs, update_ev
from app.schemas.ev import CreateEVInput, EVType, UpdateEVInput


@strawberry.type
class Query:
    @strawberry.field
    async def ev(self, info: strawberry.Info, id: UUID) -> EVType | None:
        session = info.context["session"]
        return await get_ev(session, info, id)

    @strawberry.field
    async def evs(
        self,
        info: strawberry.Info,
        make: str | None = None,
        max_price: float | None = None,
        status: str | None = None,
    ) -> list[EVType]:
        session = info.context["session"]
        return await list_evs(session, info, make, max_price, status)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_ev(self, info: strawberry.Info, input: CreateEVInput) -> EVType:
        session = info.context["session"]
        return await create_ev(session, input)

    @strawberry.mutation
    async def update_ev(self, info: strawberry.Info, id: UUID, input: UpdateEVInput) -> EVType | None:
        session = info.context["session"]
        return await update_ev(session, id, input)

    @strawberry.mutation
    async def delete_ev(self, info: strawberry.Info, id: UUID) -> bool:
        session = info.context["session"]
        return await delete_ev(session, id)


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def watch_ev_status(self, ev_id: str) -> AsyncGenerator[str, None]:
        async for status in subscribe_ev_status(ev_id):
            yield status


schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
