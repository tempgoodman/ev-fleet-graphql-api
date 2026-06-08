from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any, Coroutine, cast

import pytest

from app.graphql.schema import Subscription
from app.models.ev import EV, EVStatus


@pytest.mark.asyncio
async def test_watch_ev_status_receives_update_from_update_ev_mutation(
    graphql_request,
    db_session,
) -> None:
    ev = EV(
        make="Tesla",
        model="Model 3",
        battery_capacity_kwh=75,
        range_miles=330,
        monthly_lease_price=499.99,
        status=EVStatus.AVAILABLE,
    )
    db_session.add(ev)
    await db_session.commit()
    await db_session.refresh(ev)

    subscription = Subscription()
    status_stream = cast(
        AsyncGenerator[str, None],
        cast(Any, subscription.watch_ev_status)(str(ev.id)),
    )
    first_event: asyncio.Task[str] = asyncio.create_task(
        cast(Coroutine[Any, Any, str], anext(status_stream))
    )
    await asyncio.sleep(0)

    mutation_payload = await graphql_request(
        """
        mutation UpdateEvStatus($id: UUID!, $input: UpdateEVInput!) {
          updateEv(id: $id, input: $input) {
            id
            status
          }
        }
        """,
        {
            "id": str(ev.id),
            "input": {
                "status": "LEASED",
            },
        },
    )

    assert "errors" not in mutation_payload

    event = await asyncio.wait_for(first_event, timeout=2)
    assert event == "LEASED"

    await status_stream.aclose()
