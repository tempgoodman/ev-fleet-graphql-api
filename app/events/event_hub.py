from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import AsyncGenerator

_SUBSCRIBERS: dict[str, set[asyncio.Queue[str]]] = defaultdict(set)


def _ev_status_channel(ev_id: str) -> str:
    return f"ev_status:{ev_id}"


async def publish(channel: str, payload: str) -> None:
    for queue in list(_SUBSCRIBERS.get(channel, ())):
        await queue.put(payload)


async def trigger_ev_status_publish(ev_id: str, new_status: str) -> None:
    await publish(_ev_status_channel(ev_id), new_status)


async def subscribe(channel: str) -> AsyncGenerator[str, None]:
    queue: asyncio.Queue[str] = asyncio.Queue()
    _SUBSCRIBERS[channel].add(queue)
    try:
        while True:
            yield await queue.get()
    finally:
        subscribers = _SUBSCRIBERS.get(channel)
        if subscribers is None:
            return
        subscribers.discard(queue)
        if not subscribers:
            _SUBSCRIBERS.pop(channel, None)


async def subscribe_ev_status(ev_id: str) -> AsyncGenerator[str, None]:
    async for status in subscribe(_ev_status_channel(ev_id)):
        yield status
