from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.events.event_hub import subscribe_ev_status, trigger_ev_status_publish
from app.graphql.schema import Subscription
from app.models.ev import EV, EVStatus
from app.resolvers.ev_resolvers import update_ev
from app.schemas.ev import EVStatusType, UpdateEVInput


class EventHubTests(unittest.IsolatedAsyncioTestCase):
    async def test_multiple_subscribers_for_same_ev_receive_same_status(self) -> None:
        subscriber_one = subscribe_ev_status("ev-1")
        subscriber_two = subscribe_ev_status("ev-1")

        task_one = asyncio.create_task(anext(subscriber_one))
        task_two = asyncio.create_task(anext(subscriber_two))
        await asyncio.sleep(0)

        await trigger_ev_status_publish("ev-1", "LEASED")

        self.assertEqual(await task_one, "LEASED")
        self.assertEqual(await task_two, "LEASED")

        await subscriber_one.aclose()
        await subscriber_two.aclose()

    async def test_subscribers_only_receive_events_for_requested_ev(self) -> None:
        subscriber_one = subscribe_ev_status("ev-1")
        subscriber_two = subscribe_ev_status("ev-2")

        task_one = asyncio.create_task(anext(subscriber_one))
        task_two = asyncio.create_task(anext(subscriber_two))
        await asyncio.sleep(0)

        await trigger_ev_status_publish("ev-1", "MAINTENANCE")

        self.assertEqual(await task_one, "MAINTENANCE")
        self.assertFalse(task_two.done())

        await trigger_ev_status_publish("ev-2", "LEASED")
        self.assertEqual(await task_two, "LEASED")

        await subscriber_one.aclose()
        await subscriber_two.aclose()

    async def test_subscription_stream_yields_published_status(self) -> None:
        subscription = Subscription()
        status_stream = subscription.watch_ev_status("ev-3")
        status_task = asyncio.create_task(anext(status_stream))
        await asyncio.sleep(0)

        await trigger_ev_status_publish("ev-3", "AVAILABLE")

        self.assertEqual(await status_task, "AVAILABLE")
        await status_stream.aclose()


class UpdateEvPublishTests(unittest.IsolatedAsyncioTestCase):
    async def test_update_ev_publishes_status_when_it_changes(self) -> None:
        ev = EV(
            id=uuid4(),
            make="Tesla",
            model="Model 3",
            battery_capacity_kwh=75,
            range_miles=330,
            monthly_lease_price=499.99,
            status=EVStatus.AVAILABLE,
        )
        session = AsyncMock()
        session.get = AsyncMock(return_value=ev)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with patch(
            "app.resolvers.ev_resolvers.trigger_ev_status_publish", new=AsyncMock()
        ) as publish:
            await update_ev(session, ev.id, UpdateEVInput(status=EVStatusType.LEASED))

        publish.assert_awaited_once_with(str(ev.id), EVStatus.LEASED.value)

    async def test_update_ev_does_not_publish_when_status_is_unchanged(self) -> None:
        ev = EV(
            id=uuid4(),
            make="Tesla",
            model="Model Y",
            battery_capacity_kwh=75,
            range_miles=320,
            monthly_lease_price=529.99,
            status=EVStatus.AVAILABLE,
        )
        session = AsyncMock()
        session.get = AsyncMock(return_value=ev)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with patch(
            "app.resolvers.ev_resolvers.trigger_ev_status_publish", new=AsyncMock()
        ) as publish:
            await update_ev(
                session, ev.id, UpdateEVInput(status=EVStatusType.AVAILABLE)
            )

        publish.assert_not_awaited()

    async def test_update_ev_does_not_publish_if_commit_fails(self) -> None:
        ev = EV(
            id=uuid4(),
            make="Tesla",
            model="Model X",
            battery_capacity_kwh=100,
            range_miles=340,
            monthly_lease_price=699.99,
            status=EVStatus.AVAILABLE,
        )
        session = AsyncMock()
        session.get = AsyncMock(return_value=ev)
        session.commit = AsyncMock(side_effect=RuntimeError("commit failed"))
        session.refresh = AsyncMock()

        with patch(
            "app.resolvers.ev_resolvers.trigger_ev_status_publish", new=AsyncMock()
        ) as publish:
            with self.assertRaises(RuntimeError):
                await update_ev(
                    session, ev.id, UpdateEVInput(status=EVStatusType.LEASED)
                )

        publish.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
