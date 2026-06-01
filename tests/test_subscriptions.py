from __future__ import annotations

import asyncio
import uuid

import pytest

from app.graphql.schema import Subscription, schema
from app.models.ev import EV, EVStatus


@pytest.mark.asyncio
async def test_watch_ev_status_receives_event_on_update(db_session):
    ev_id = uuid.uuid4()
    ev = EV(
        id=ev_id,
        make="Tesla",
        model="Model Y",
        battery_capacity_kwh=81,
        range_miles=310,
        monthly_lease_price=649.0,
        status=EVStatus.AVAILABLE,
    )
    db_session.add(ev)
    await db_session.commit()

    context = {"session": db_session}

    subscription = Subscription().watch_ev_status(ev_id=ev_id)

    next_event_task = asyncio.create_task(asyncio.wait_for(subscription.__anext__(), timeout=2))
    await asyncio.sleep(0)

    mutation = """
    mutation Update($id: UUID!) {
      updateEv(id: $id, input: { status: LEASED }) {
        id
        status
      }
    }
    """

    result = await schema.execute(
        mutation,
        variable_values={"id": str(ev_id)},
        context_value=context,
    )

    assert result.errors is None
    assert result.data["updateEv"]["status"] == "LEASED"

    event = await next_event_task
    assert str(event.ev_id) == str(ev_id)
    assert event.old_status.value == "AVAILABLE"
    assert event.new_status.value == "LEASED"

    await subscription.aclose()
