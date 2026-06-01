from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class EVStatusChangedEvent:
    ev_id: str
    old_status: str
    new_status: str


class InMemoryPubSubBroker:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[EVStatusChangedEvent]] = set()

    async def subscribe(self) -> AsyncIterator[EVStatusChangedEvent]:
        queue: asyncio.Queue[EVStatusChangedEvent] = asyncio.Queue()
        self._subscribers.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._subscribers.discard(queue)

    def publish(self, event: EVStatusChangedEvent) -> None:
        for subscriber in list(self._subscribers):
            subscriber.put_nowait(event)


ev_status_broker = InMemoryPubSubBroker()


def dispatch_ev_status_changed(ev_id: str, old_status: str, new_status: str) -> None:
    ev_status_broker.publish(
        EVStatusChangedEvent(ev_id=ev_id, old_status=old_status, new_status=new_status)
    )
