from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import UUID

import strawberry

from app.events.dispatcher import ev_status_broker
from app.resolvers.ev_resolvers import create_ev, delete_ev, get_ev, list_evs, update_ev
from app.schemas.ev import CreateEVInput, EVStatusChangedType, EVStatusType, EVType, UpdateEVInput


@strawberry.type
class Query:
    @strawberry.field
    async def ev(self, info: strawberry.Info, id: UUID) -> EVType | None:
        session = info.context["session"]
        return await get_ev(session, id)

    @strawberry.field
    async def evs(
        self,
        info: strawberry.Info,
        make: str | None = None,
        max_price: float | None = None,
        status: str | None = None,
    ) -> list[EVType]:
        session = info.context["session"]
        return await list_evs(session, make, max_price, status)


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
    async def watch_ev_status(
        self, ev_id: UUID | None = None
    ) -> AsyncGenerator[EVStatusChangedType, None]:
        async for event in ev_status_broker.subscribe():
            if ev_id is not None and event.ev_id != str(ev_id):
                continue

            yield EVStatusChangedType(
                ev_id=UUID(event.ev_id),
                old_status=EVStatusType(event.old_status),
                new_status=EVStatusType(event.new_status),
            )


schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)
