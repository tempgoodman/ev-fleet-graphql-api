from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.dispatcher import dispatch_ev_status_changed
from app.models.ev import EV, EVStatus
from app.schemas.ev import CreateEVInput, UpdateEVInput


def _apply_filters(
    query: Select[tuple[EV]],
    make: str | None,
    max_price: float | None,
    status: str | None,
) -> Select[tuple[EV]]:
    if make:
        query = query.where(EV.make.ilike(f"%{make}%"))

    if max_price is not None:
        query = query.where(EV.monthly_lease_price <= max_price)

    if status:
        normalized_status = status.upper()
        if normalized_status in EVStatus.__members__:
            query = query.where(EV.status == EVStatus[normalized_status])

    return query


async def get_ev(session: AsyncSession, ev_id: UUID) -> EV | None:
    return await session.get(EV, ev_id)


async def list_evs(
    session: AsyncSession,
    make: str | None = None,
    max_price: float | None = None,
    status: str | None = None,
) -> list[EV]:
    query = _apply_filters(select(EV), make, max_price, status)
    result = await session.execute(query)
    return list(result.scalars().all())


async def create_ev(session: AsyncSession, input_data: CreateEVInput) -> EV:
    ev = EV(
        make=input_data.make,
        model=input_data.model,
        battery_capacity_kwh=input_data.battery_capacity_kwh,
        range_miles=input_data.range_miles,
        monthly_lease_price=input_data.monthly_lease_price,
        status=EVStatus(input_data.status.value),
    )
    session.add(ev)
    await session.commit()
    await session.refresh(ev)
    return ev


async def update_ev(session: AsyncSession, ev_id: UUID, input_data: UpdateEVInput) -> EV | None:
    ev = await session.get(EV, ev_id)
    if not ev:
        return None

    old_status = ev.status.value

    if input_data.make is not None:
        ev.make = input_data.make
    if input_data.model is not None:
        ev.model = input_data.model
    if input_data.battery_capacity_kwh is not None:
        ev.battery_capacity_kwh = input_data.battery_capacity_kwh
    if input_data.range_miles is not None:
        ev.range_miles = input_data.range_miles
    if input_data.monthly_lease_price is not None:
        ev.monthly_lease_price = input_data.monthly_lease_price
    if input_data.status is not None:
        ev.status = EVStatus(input_data.status.value)

    await session.commit()
    await session.refresh(ev)

    if ev.status.value != old_status:
        dispatch_ev_status_changed(str(ev.id), old_status, ev.status.value)

    return ev


async def delete_ev(session: AsyncSession, ev_id: UUID) -> bool:
    ev = await session.get(EV, ev_id)
    if not ev:
        return False

    await session.delete(ev)
    await session.commit()
    return True
